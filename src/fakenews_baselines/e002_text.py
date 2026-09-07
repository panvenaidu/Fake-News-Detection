"""BP-6W-v1 implementation for the E002 BERT text-only baseline.

This module intentionally contains no E003 or E004 model code.  It validates
the immutable paired cohort, provides deterministic text data loading, trains
the approved BERT classifier, and writes auditable experiment artifacts.
"""

from __future__ import annotations

import csv
import copy
import hashlib
import json
import math
import os
import platform
import random
import subprocess
import sys
import time
import traceback
from contextlib import nullcontext
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import numpy as np
import pandas as pd
import torch
from PIL import Image
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    confusion_matrix,
    f1_score,
    precision_recall_fscore_support,
)
from torch import Tensor, nn
from torch.optim import AdamW
from torch.utils.data import DataLoader, Dataset
from transformers import BertModel, BertTokenizerFast, get_linear_schedule_with_warmup


LABEL_NAMES = [
    "True",
    "Satire/Parody",
    "Misleading Content",
    "Imposter Content",
    "False Connection",
    "Manipulated Content",
]
REQUIRED_MANIFEST_COLUMNS = {
    "id",
    "split",
    "clean_title",
    "6_way_label",
    "image_path",
}


class ManifestValidationError(ValueError):
    """Raised when the fixed paired cohort does not meet BP-6W-v1 rules."""


@dataclass(frozen=True)
class ManifestInfo:
    """Verified, immutable-cohort metadata recorded with each run."""

    path: str
    sha256: str
    rows: int
    split_counts: Dict[str, int]
    class_counts: Dict[str, Dict[str, int]]


@dataclass(frozen=True)
class RunPaths:
    """Artifact locations for one E002 seed run."""

    root: Path
    checkpoints: Path
    metrics: Path


class TextClassificationDataset(Dataset):
    """Minimal immutable text/label view over one verified manifest split."""

    def __init__(self, dataframe: pd.DataFrame) -> None:
        self._ids = dataframe["id"].astype(str).tolist()
        self._texts = dataframe["clean_title"].astype(str).tolist()
        self._labels = dataframe["6_way_label"].astype(int).tolist()

    def __len__(self) -> int:
        return len(self._labels)

    def __getitem__(self, index: int) -> Dict[str, Any]:
        return {
            "id": self._ids[index],
            "text": self._texts[index],
            "label": self._labels[index],
        }


class BertTextClassifier(nn.Module):
    """BERT pooled/CLS representation followed by the approved 6-class head."""

    def __init__(
        self,
        model_name: str,
        model_revision: Optional[str],
        dropout: float,
        num_classes: int,
    ) -> None:
        super().__init__()
        load_kwargs: Dict[str, Any] = {}
        if model_revision:
            load_kwargs["revision"] = model_revision
        self.bert = BertModel.from_pretrained(model_name, **load_kwargs)
        self.dropout = nn.Dropout(dropout)
        self.classifier = nn.Linear(self.bert.config.hidden_size, num_classes)

    def forward(self, input_ids: Tensor, attention_mask: Tensor) -> Tensor:
        outputs = self.bert(input_ids=input_ids, attention_mask=attention_mask)
        representation = outputs.pooler_output
        if representation is None:
            representation = outputs.last_hidden_state[:, 0]
        return self.classifier(self.dropout(representation))


def load_json_config(path: Path) -> Dict[str, Any]:
    """Load an E002 JSON configuration without applying implicit defaults."""
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def sha256_file(path: Path) -> str:
    """Return the SHA-256 digest for a file without loading it all at once."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_and_validate_manifest(config: Dict[str, Any], project_root: Path) -> Tuple[pd.DataFrame, ManifestInfo]:
    """Load and validate the fixed verified paired manifest before an E002 run."""
    manifest_path = project_root / config["data"]["manifest_path"]
    if not manifest_path.is_file():
        raise ManifestValidationError(f"Verified manifest is missing: {manifest_path}")

    digest = sha256_file(manifest_path)
    expected_digest = config["data"]["manifest_sha256"]
    if digest != expected_digest:
        raise ManifestValidationError(
            "Verified manifest SHA-256 does not match the BP-6W-v1 configuration: "
            f"expected {expected_digest}, got {digest}."
        )

    dataframe = pd.read_csv(manifest_path, dtype={"id": str})
    missing_columns = REQUIRED_MANIFEST_COLUMNS.difference(dataframe.columns)
    if missing_columns:
        raise ManifestValidationError(
            f"Verified manifest is missing required columns: {sorted(missing_columns)}"
        )
    if dataframe["id"].isna().any() or dataframe["id"].duplicated().any():
        raise ManifestValidationError("Verified manifest contains missing or duplicate IDs.")
    if dataframe["clean_title"].isna().any() or (
        dataframe["clean_title"].astype(str).str.strip() == ""
    ).any():
        raise ManifestValidationError("Verified manifest contains blank clean_title values.")
    if dataframe["image_path"].isna().any() or (
        dataframe["image_path"].astype(str).str.strip() == ""
    ).any():
        raise ManifestValidationError("Verified manifest contains blank image_path values.")

    actual_split_counts = {
        str(split): int(count)
        for split, count in dataframe["split"].value_counts().sort_index().items()
    }
    expected_split_counts = {
        str(split): int(count)
        for split, count in config["data"]["expected_split_counts"].items()
    }
    if actual_split_counts != expected_split_counts:
        raise ManifestValidationError(
            "Verified manifest split counts differ from BP-6W-v1: "
            f"expected {expected_split_counts}, got {actual_split_counts}."
        )

    labels = pd.to_numeric(dataframe["6_way_label"], errors="raise").astype(int)
    expected_labels = set(range(config["task"]["num_classes"]))
    actual_labels = set(labels.unique().tolist())
    if actual_labels != expected_labels:
        raise ManifestValidationError(
            f"Expected labels {sorted(expected_labels)}, got {sorted(actual_labels)}."
        )
    dataframe["6_way_label"] = labels

    class_counts = {
        split: {
            str(label): int(count)
            for label, count in group["6_way_label"].value_counts().sort_index().items()
        }
        for split, group in dataframe.groupby("split", sort=True)
    }
    info = ManifestInfo(
        path=str(manifest_path),
        sha256=digest,
        rows=len(dataframe),
        split_counts=actual_split_counts,
        class_counts=class_counts,
    )
    return dataframe, info


def validate_paired_images(
    dataframe: pd.DataFrame,
    project_root: Path,
    limit: Optional[int] = None,
) -> int:
    """Assert that paired image files exist and can be decoded to RGB.

    Full E002 training calls this on every verified manifest row before the
    tokenizer/model are loaded.  The separate smoke test passes a small,
    explicitly reported subset because it is not a canonical experiment run.
    """
    validated = 0
    rows: Iterable[Tuple[Any, Any]] = dataframe[["id", "image_path"]].itertuples(
        index=False, name=None
    )
    for item_id, image_path in rows:
        if limit is not None and validated >= limit:
            break
        candidate = Path(str(image_path))
        if not candidate.is_absolute():
            candidate = project_root / candidate
        try:
            with Image.open(candidate) as image:
                image.load()
                image.convert("RGB")
        except (FileNotFoundError, OSError, ValueError) as error:
            raise ManifestValidationError(
                f"Paired image validation failed for id={item_id}, path={candidate}: {error}"
            ) from error
        validated += 1
    if limit is not None and validated != min(limit, len(dataframe)):
        raise ManifestValidationError("Could not validate the requested smoke-test images.")
    return validated


def set_deterministic_seed(seed: int) -> None:
    """Seed Python, NumPy and PyTorch under BP-6W-v1 reproducibility rules."""
    os.environ["PYTHONHASHSEED"] = str(seed)
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    torch.use_deterministic_algorithms(True, warn_only=True)
    if torch.backends.cudnn.is_available():
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False


def seed_worker(worker_id: int) -> None:
    """Seed each DataLoader worker from the PyTorch-initialized worker seed."""
    worker_seed = torch.initial_seed() % 2**32
    random.seed(worker_seed)
    np.random.seed(worker_seed)


class BertTextCollator:
    """Picklable dynamic-padding collator compatible with macOS worker spawning."""

    def __init__(self, tokenizer: BertTokenizerFast, max_length: int) -> None:
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __call__(self, examples: List[Dict[str, Any]]) -> Dict[str, Any]:
        encoded = self.tokenizer(
            [example["text"] for example in examples],
            max_length=self.max_length,
            truncation=True,
            padding=True,
            return_tensors="pt",
        )
        encoded["labels"] = torch.tensor(
            [example["label"] for example in examples], dtype=torch.long
        )
        encoded["ids"] = [example["id"] for example in examples]
        return encoded



def make_collate_fn(tokenizer: BertTokenizerFast, max_length: int) -> BertTextCollator:
    """Build a picklable collator with dynamic longest-in-batch padding."""
    return BertTextCollator(tokenizer, max_length)


def make_dataloader(
    dataframe: pd.DataFrame,
    tokenizer: BertTokenizerFast,
    config: Dict[str, Any],
    seed: int,
    shuffle: bool,
    batch_size: Optional[int] = None,
) -> DataLoader:
    """Create a deterministically seeded E002 DataLoader for one fixed split."""
    generator = torch.Generator()
    generator.manual_seed(seed)
    loader_workers = int(config["data_loader"]["num_workers"])
    return DataLoader(
        TextClassificationDataset(dataframe),
        batch_size=batch_size or int(config["training"]["micro_batch_size"]),
        shuffle=shuffle,
        num_workers=loader_workers,
        collate_fn=make_collate_fn(tokenizer, int(config["tokenizer"]["max_length"])),
        pin_memory=torch.cuda.is_available(),
        worker_init_fn=seed_worker if loader_workers else None,
        generator=generator,
        persistent_workers=False,
    )


def select_device(require_cuda: bool) -> torch.device:
    """Return CUDA for canonical training or fail rather than silently substitute."""
    if require_cuda and not torch.cuda.is_available():
        raise RuntimeError(
            "BP-6W-v1 canonical E002 training requires CUDA, but CUDA is unavailable. "
            "No CPU/MPS training fallback will be used."
        )
    return torch.device("cuda" if torch.cuda.is_available() else "cpu")


def make_optimizer(model: nn.Module, config: Dict[str, Any]) -> AdamW:
    """Construct approved AdamW groups, excluding bias and normalization decay."""
    no_decay_terms = ("bias", "LayerNorm.weight", "layer_norm.weight")
    decay_parameters = []
    no_decay_parameters = []
    for name, parameter in model.named_parameters():
        if not parameter.requires_grad:
            continue
        if any(term in name for term in no_decay_terms):
            no_decay_parameters.append(parameter)
        else:
            decay_parameters.append(parameter)
    return AdamW(
        [
            {"params": decay_parameters, "weight_decay": config["optimizer"]["weight_decay"]},
            {"params": no_decay_parameters, "weight_decay": 0.0},
        ],
        lr=config["optimizer"]["learning_rate"],
        betas=tuple(config["optimizer"]["betas"]),
        eps=config["optimizer"]["epsilon"],
    )


def parameter_counts(model: nn.Module) -> Dict[str, int]:
    """Return total and trainable parameter counts for experiment metadata."""
    return {
        "total": sum(parameter.numel() for parameter in model.parameters()),
        "trainable": sum(
            parameter.numel() for parameter in model.parameters() if parameter.requires_grad
        ),
    }


def build_metrics(labels: List[int], predictions: List[int], loss: float) -> Dict[str, Any]:
    """Calculate every BP-6W-v1 classification metric for one split."""
    class_labels = list(range(len(LABEL_NAMES)))
    precision, recall, f1_values, support = precision_recall_fscore_support(
        labels,
        predictions,
        labels=class_labels,
        zero_division=0,
    )
    raw_matrix = confusion_matrix(labels, predictions, labels=class_labels)
    normalized_matrix = raw_matrix.astype(float)
    row_sums = normalized_matrix.sum(axis=1, keepdims=True)
    np.divide(normalized_matrix, row_sums, out=normalized_matrix, where=row_sums != 0)
    return {
        "loss": float(loss),
        "macro_f1": float(f1_score(labels, predictions, average="macro", zero_division=0)),
        "accuracy": float(accuracy_score(labels, predictions)),
        "balanced_accuracy": float(balanced_accuracy_score(labels, predictions)),
        "weighted_f1": float(f1_score(labels, predictions, average="weighted", zero_division=0)),
        "per_class": {
            LABEL_NAMES[label]: {
                "precision": float(precision[label]),
                "recall": float(recall[label]),
                "f1": float(f1_values[label]),
                "support": int(support[label]),
            }
            for label in class_labels
        },
        "confusion_matrix": raw_matrix.tolist(),
        "normalized_confusion_matrix": normalized_matrix.tolist(),
    }


def move_batch_to_device(batch: Dict[str, Any], device: torch.device) -> Dict[str, Tensor]:
    """Move tensor portions of a collated E002 batch to the selected device."""
    return {
        "input_ids": batch["input_ids"].to(device, non_blocking=True),
        "attention_mask": batch["attention_mask"].to(device, non_blocking=True),
        "labels": batch["labels"].to(device, non_blocking=True),
    }


def evaluate(
    model: nn.Module,
    dataloader: DataLoader,
    criterion: nn.Module,
    device: torch.device,
    amp_enabled: bool,
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """Evaluate a split and return metrics plus ID-linked predictions."""
    model.eval()
    losses: List[float] = []
    labels: List[int] = []
    predictions: List[int] = []
    prediction_rows: List[Dict[str, Any]] = []
    autocast_context = (
        torch.autocast(device_type="cuda", dtype=torch.float16) if amp_enabled else nullcontext()
    )
    with torch.no_grad():
        for batch in dataloader:
            device_batch = move_batch_to_device(batch, device)
            with autocast_context:
                logits = model(
                    input_ids=device_batch["input_ids"],
                    attention_mask=device_batch["attention_mask"],
                )
                loss = criterion(logits, device_batch["labels"])
            batch_predictions = logits.argmax(dim=1).detach().cpu().tolist()
            batch_labels = device_batch["labels"].detach().cpu().tolist()
            losses.append(float(loss.item()) * len(batch_labels))
            labels.extend(batch_labels)
            predictions.extend(batch_predictions)
            prediction_rows.extend(
                {
                    "id": item_id,
                    "true_label": true_label,
                    "predicted_label": predicted_label,
                }
                for item_id, true_label, predicted_label in zip(
                    batch["ids"], batch_labels, batch_predictions
                )
            )
    average_loss = sum(losses) / len(labels)
    return build_metrics(labels, predictions, average_loss), prediction_rows


def atomic_json_dump(payload: Dict[str, Any], path: Path) -> None:
    """Write a JSON artifact atomically to avoid partial experiment records."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_suffix(path.suffix + ".tmp")
    with temporary_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")
    temporary_path.replace(path)


def write_confusion_csv(matrix: List[List[float]], path: Path) -> None:
    """Write a labelled raw or normalized six-class confusion matrix."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["true_label", *LABEL_NAMES])
        for name, values in zip(LABEL_NAMES, matrix):
            writer.writerow([name, *values])


def write_prediction_csv(rows: List[Dict[str, Any]], path: Path) -> None:
    """Write ID-linked test predictions as an auditable small CSV artifact."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["id", "true_label", "predicted_label"])
        writer.writeheader()
        writer.writerows(rows)


def create_run_paths(project_root: Path, config: Dict[str, Any], run_id: str) -> RunPaths:
    """Create the fixed artifact structure for one seed-specific E002 run."""
    root = project_root / config["artifacts"]["output_root"] / run_id
    checkpoints = root / "checkpoints"
    metrics = root / "metrics"
    checkpoints.mkdir(parents=True, exist_ok=True)
    metrics.mkdir(parents=True, exist_ok=True)
    return RunPaths(root=root, checkpoints=checkpoints, metrics=metrics)


def git_commit(project_root: Path) -> Optional[str]:
    """Record the current source revision when Git metadata is available."""
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=project_root, text=True
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def source_hashes(project_root: Path) -> Dict[str, str]:
    """Hash the E002 implementation and runner source recorded with each run."""
    source_paths = [
        project_root / "src" / "fakenews_baselines" / "e002_text.py",
        project_root / "scripts" / "run_e002.py",
    ]
    return {
        str(path.relative_to(project_root)): sha256_file(path)
        for path in source_paths
        if path.is_file()
    }


def pip_freeze() -> List[str]:
    """Capture installed package versions without making environment changes."""
    try:
        output = subprocess.check_output(
            [sys.executable, "-m", "pip", "freeze"], text=True, stderr=subprocess.STDOUT
        )
    except (OSError, subprocess.CalledProcessError) as error:
        return [f"pip freeze unavailable: {error}"]
    return sorted(line for line in output.splitlines() if line)


def collect_environment(device: torch.device, amp_enabled: bool) -> Dict[str, Any]:
    """Gather the recorded software, device, precision and package context."""
    import transformers

    cuda_info: Dict[str, Any] = {"available": torch.cuda.is_available()}
    if torch.cuda.is_available():
        cuda_info.update(
            {
                "device_name": torch.cuda.get_device_name(0),
                "device_count": torch.cuda.device_count(),
                "total_memory_bytes": torch.cuda.get_device_properties(0).total_memory,
                "driver": torch.version.cuda,
            }
        )
    return {
        "platform": platform.platform(),
        "python": sys.version,
        "executable": sys.executable,
        "torch": torch.__version__,
        "transformers": transformers.__version__,
        "device": str(device),
        "cuda": cuda_info,
        "amp": {"enabled": amp_enabled, "dtype": "float16" if amp_enabled else None},
        "pip_freeze": pip_freeze(),
    }


def checkpoint_is_better(
    current_metrics: Dict[str, Any], best_metrics: Optional[Dict[str, Any]]
) -> bool:
    """Apply BP-6W-v1 checkpoint ranking: Macro-F1, loss, then earlier epoch."""
    if best_metrics is None:
        return True
    current_f1 = current_metrics["macro_f1"]
    best_f1 = best_metrics["macro_f1"]
    if current_f1 > best_f1:
        return True
    if current_f1 < best_f1:
        return False
    return current_metrics["loss"] < best_metrics["loss"]


def train_one_seed(
    config: Dict[str, Any],
    project_root: Path,
    seed: int,
) -> Dict[str, Any]:
    """Run one canonical CUDA E002 seed under the frozen BP-6W-v1 protocol."""
    run_id = f"E002-bert-base-uncased-6way-BP6Wv1-s{seed}"
    paths = create_run_paths(project_root, config, run_id)
    started_at = time.perf_counter()
    try:
        set_deterministic_seed(seed)
        device = select_device(require_cuda=True)
        if torch.cuda.is_available():
            torch.cuda.reset_peak_memory_stats(device)
        manifest, manifest_info = load_and_validate_manifest(config, project_root)
        validated_images = validate_paired_images(manifest, project_root)

        model_config = config["model"]
        tokenizer = BertTokenizerFast.from_pretrained(
            model_config["name"], revision=model_config["revision"]
        )
        model = BertTextClassifier(
            model_name=model_config["name"],
            model_revision=model_config["revision"],
            dropout=float(model_config["classifier_dropout"]),
            num_classes=int(config["task"]["num_classes"]),
        ).to(device)
        amp_enabled = device.type == "cuda" and bool(config["training"]["use_cuda_amp"])

        train_loader = make_dataloader(
            manifest[manifest["split"] == "train"], tokenizer, config, seed, shuffle=True
        )
        validation_loader = make_dataloader(
            manifest[manifest["split"] == "validate"], tokenizer, config, seed, shuffle=False
        )
        test_loader = make_dataloader(
            manifest[manifest["split"] == "test"], tokenizer, config, seed, shuffle=False
        )
        optimizer = make_optimizer(model, config)
        planned_updates_per_epoch = math.ceil(
            len(train_loader) / int(config["training"]["gradient_accumulation_steps"])
        )
        planned_total_updates = planned_updates_per_epoch * int(config["training"]["max_epochs"])
        warmup_steps = int(planned_total_updates * float(config["scheduler"]["warmup_ratio"]))
        scheduler = get_linear_schedule_with_warmup(
            optimizer,
            num_warmup_steps=warmup_steps,
            num_training_steps=planned_total_updates,
        )
        scaler = torch.amp.GradScaler("cuda", enabled=amp_enabled)
        criterion = nn.CrossEntropyLoss()
        metadata = {
            "run_id": run_id,
            "protocol_id": config["protocol_id"],
            "seed": seed,
            "git_commit": git_commit(project_root),
            "config_sha256": sha256_file(project_root / config["_config_path"]),
            "source_sha256": source_hashes(project_root),
            "manifest": manifest_info.__dict__,
            "paired_images_validated": validated_images,
            "environment": collect_environment(device, amp_enabled),
            "parameter_counts": parameter_counts(model),
            "model": {
                "name": model_config["name"],
                "requested_revision": model_config["revision"],
                "resolved_revision": getattr(model.bert.config, "_commit_hash", None),
                "tokenizer_revision": getattr(tokenizer, "init_kwargs", {}).get("_commit_hash"),
            },
            "batching": {
                "micro_batch_size": config["training"]["micro_batch_size"],
                "gradient_accumulation_steps": config["training"]["gradient_accumulation_steps"],
                "effective_batch_size": config["training"]["effective_batch_size"],
            },
            "scheduler": {
                "planned_total_updates": planned_total_updates,
                "warmup_steps": warmup_steps,
            },
        }
        atomic_json_dump(config, paths.root / "resolved_config.json")
        atomic_json_dump(metadata, paths.root / "run_metadata.json")

        best_metrics: Optional[Dict[str, Any]] = None
        best_epoch: Optional[int] = None
        best_checkpoint = paths.checkpoints / "best.pt"
        early_stop_reference_f1: Optional[float] = None
        non_improving_epochs = 0
        epoch_records: List[Dict[str, Any]] = []
        train_samples_seen = 0
        training_started_at = time.perf_counter()
        accumulation_steps = int(config["training"]["gradient_accumulation_steps"])

        for epoch in range(1, int(config["training"]["max_epochs"]) + 1):
            model.train()
            optimizer.zero_grad(set_to_none=True)
            loss_sum = 0.0
            epoch_samples = 0
            optimizer_steps = 0
            for batch_index, batch in enumerate(train_loader, start=1):
                device_batch = move_batch_to_device(batch, device)
                autocast_context = (
                    torch.autocast(device_type="cuda", dtype=torch.float16)
                    if amp_enabled
                    else nullcontext()
                )
                with autocast_context:
                    logits = model(
                        input_ids=device_batch["input_ids"],
                        attention_mask=device_batch["attention_mask"],
                    )
                    loss = criterion(logits, device_batch["labels"])
                batch_size = len(device_batch["labels"])
                loss_sum += float(loss.detach().item()) * batch_size
                epoch_samples += batch_size
                scaler.scale(loss / accumulation_steps).backward()
                is_update_step = (
                    batch_index % accumulation_steps == 0 or batch_index == len(train_loader)
                )
                if is_update_step:
                    scaler.unscale_(optimizer)
                    torch.nn.utils.clip_grad_norm_(
                        model.parameters(), max_norm=float(config["training"]["max_grad_norm"])
                    )
                    scaler.step(optimizer)
                    scaler.update()
                    optimizer.zero_grad(set_to_none=True)
                    scheduler.step()
                    optimizer_steps += 1

            validation_metrics, _ = evaluate(
                model, validation_loader, criterion, device, amp_enabled
            )
            train_samples_seen += epoch_samples
            record = {
                "epoch": epoch,
                "train_loss": loss_sum / epoch_samples,
                "train_samples": epoch_samples,
                "optimizer_steps": optimizer_steps,
                "learning_rate": optimizer.param_groups[0]["lr"],
                "validation": validation_metrics,
            }
            epoch_records.append(record)
            atomic_json_dump({"epochs": epoch_records}, paths.metrics / "epoch_metrics.json")

            if checkpoint_is_better(validation_metrics, best_metrics):
                best_metrics = validation_metrics
                best_epoch = epoch
                torch.save(
                    {
                        "epoch": epoch,
                        "model_state_dict": model.state_dict(),
                        "optimizer_state_dict": optimizer.state_dict(),
                        "scheduler_state_dict": scheduler.state_dict(),
                        "validation_metrics": validation_metrics,
                        "seed": seed,
                    },
                    best_checkpoint,
                )

            has_required_gain = early_stop_reference_f1 is None or (
                validation_metrics["macro_f1"]
                >= early_stop_reference_f1 + float(config["early_stopping"]["min_delta"])
            )
            if has_required_gain:
                early_stop_reference_f1 = validation_metrics["macro_f1"]
                non_improving_epochs = 0
            elif epoch > int(config["early_stopping"]["start_after_epoch"]):
                non_improving_epochs += 1

            if (
                epoch > int(config["early_stopping"]["start_after_epoch"])
                and non_improving_epochs >= int(config["early_stopping"]["patience"])
            ):
                break

        if best_metrics is None or best_epoch is None or not best_checkpoint.is_file():
            raise RuntimeError("No validation checkpoint was written during E002 training.")
        checkpoint = torch.load(best_checkpoint, map_location=device, weights_only=False)
        model.load_state_dict(checkpoint["model_state_dict"])
        test_metrics, prediction_rows = evaluate(model, test_loader, criterion, device, amp_enabled)
        write_prediction_csv(prediction_rows, paths.metrics / "test_predictions.csv")
        write_confusion_csv(test_metrics["confusion_matrix"], paths.metrics / "test_confusion_raw.csv")
        write_confusion_csv(
            test_metrics["normalized_confusion_matrix"],
            paths.metrics / "test_confusion_normalized.csv",
        )
        atomic_json_dump(test_metrics, paths.metrics / "test_metrics.json")
        total_seconds = time.perf_counter() - started_at
        training_seconds = time.perf_counter() - training_started_at
        summary = {
            "run_id": run_id,
            "status": "completed",
            "selected_epoch": best_epoch,
            "selected_validation_metrics": best_metrics,
            "test_metrics": test_metrics,
            "runtime_seconds": total_seconds,
            "training_seconds": training_seconds,
            "throughput_samples_per_second": train_samples_seen / training_seconds
            if training_seconds > 0
            else None,
            "peak_memory_bytes": torch.cuda.max_memory_allocated(device)
            if torch.cuda.is_available()
            else None,
        }
        atomic_json_dump(summary, paths.root / "run_summary.json")
        return summary
    except Exception as error:
        atomic_json_dump(
            {
                "run_id": run_id,
                "status": "failed",
                "error_type": type(error).__name__,
                "error": str(error),
                "traceback": traceback.format_exc(),
            },
            paths.root / "execution_error.json",
        )
        raise


def run_smoke_test(config: Dict[str, Any], project_root: Path) -> Dict[str, Any]:
    """Perform the required non-canonical CPU smoke test and remove its checkpoint.

    This deliberately does not call ``train_one_seed`` and cannot produce a
    canonical experiment result.  It verifies one small real-manifest batch,
    a complete forward/backward/optimizer path, and checkpoint writing.
    """
    smoke_config = config["smoke_test"]
    run_id = "E002-bert-base-uncased-6way-BP6Wv1-smoke-cpu"
    paths = create_run_paths(project_root, config, run_id)
    started_at = time.perf_counter()
    try:
        set_deterministic_seed(int(smoke_config["seed"]))
        device = torch.device("cpu")
        manifest, manifest_info = load_and_validate_manifest(config, project_root)
        train_rows = manifest[manifest["split"] == "train"].head(
            int(smoke_config["batch_size"])
        )
        validated_images = validate_paired_images(train_rows, project_root)
        model_config = config["model"]
        tokenizer = BertTokenizerFast.from_pretrained(
            model_config["name"], revision=model_config["revision"]
        )
        smoke_loader_config = copy.deepcopy(config)
        smoke_loader_config["data_loader"]["num_workers"] = int(
            smoke_config["num_workers"]
        )
        dataloader = make_dataloader(
            train_rows,
            tokenizer,
            smoke_loader_config,
            seed=int(smoke_config["seed"]),
            shuffle=False,
            batch_size=int(smoke_config["batch_size"]),
        )
        batch = next(iter(dataloader))
        model = BertTextClassifier(
            model_name=model_config["name"],
            model_revision=model_config["revision"],
            dropout=float(model_config["classifier_dropout"]),
            num_classes=int(config["task"]["num_classes"]),
        ).to(device)
        criterion = nn.CrossEntropyLoss()
        optimizer = make_optimizer(model, config)
        device_batch = move_batch_to_device(batch, device)
        logits = model(
            input_ids=device_batch["input_ids"], attention_mask=device_batch["attention_mask"]
        )
        loss = criterion(logits, device_batch["labels"])
        loss.backward()
        torch.nn.utils.clip_grad_norm_(
            model.parameters(), max_norm=float(config["training"]["max_grad_norm"])
        )
        optimizer.step()
        optimizer.zero_grad(set_to_none=True)
        checkpoint_path = paths.checkpoints / "smoke_checkpoint.pt"
        torch.save(
            {"model_state_dict": model.state_dict(), "loss": float(loss.item())}, checkpoint_path
        )
        checkpoint_size = checkpoint_path.stat().st_size
        if checkpoint_size <= 0:
            raise RuntimeError("Smoke-test checkpoint was created but is empty.")
        checkpoint_path.unlink()
        summary = {
            "run_id": run_id,
            "status": "passed",
            "scope": "non-canonical CPU smoke test; no training metrics",
            "protocol_id": config["protocol_id"],
            "device": "cpu",
            "amp_enabled": False,
            "seed": smoke_config["seed"],
            "data_loader_workers": smoke_config["num_workers"],
            "manifest": manifest_info.__dict__,
            "image_validation_scope": {
                "validated_rows": validated_images,
                "note": "Smoke-only subset; canonical runs validate every paired image."
            },
            "checks": {
                "imports": True,
                "tokenizer": True,
                "dataset_loading": True,
                "one_batch": {
                    "batch_size": int(device_batch["labels"].shape[0]),
                    "input_ids_shape": list(device_batch["input_ids"].shape),
                    "attention_mask_shape": list(device_batch["attention_mask"].shape),
                },
                "forward_pass": {"logits_shape": list(logits.shape)},
                "loss": float(loss.item()),
                "backward_pass": True,
                "optimizer_step": True,
                "checkpoint_writing": {
                    "bytes_written": checkpoint_size,
                    "removed_after_verification": True,
                },
            },
            "model": {
                "name": model_config["name"],
                "requested_revision": model_config["revision"],
                "resolved_revision": getattr(model.bert.config, "_commit_hash", None),
                "parameter_counts": parameter_counts(model),
            },
            "runtime_seconds": time.perf_counter() - started_at,
        }
        atomic_json_dump(config, paths.root / "resolved_config.json")
        atomic_json_dump(summary, paths.root / "smoke_test_summary.json")
        return summary
    except Exception as error:
        atomic_json_dump(
            {
                "run_id": run_id,
                "status": "failed",
                "error_type": type(error).__name__,
                "error": str(error),
                "traceback": traceback.format_exc(),
            },
            paths.root / "smoke_test_error.json",
        )
        raise
