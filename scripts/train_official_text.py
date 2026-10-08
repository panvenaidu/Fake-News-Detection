"""Fine-tune two text encoders on the unchanged official Fakeddit splits.

Designed for an authorized Colab CUDA runtime. No image downloads; no metadata
features. Every attempt has its own folder and preserves machine-readable proof.
"""
import argparse
import gc
import hashlib
import json
import math
import os
import platform
import random
import shutil
import subprocess
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")
import numpy as np
import pandas as pd
import sklearn
import torch
import transformers
from sklearn.metrics import (accuracy_score, balanced_accuracy_score,
                            classification_report, confusion_matrix, f1_score)
from torch.utils.data import DataLoader, Dataset
from transformers import (AutoModelForSequenceClassification, AutoTokenizer,
                          DataCollatorWithPadding, get_linear_schedule_with_warmup)

LABELS = ["True", "Satire/Parody", "Misleading Content", "Imposter Content",
          "False Connection", "Manipulated Content"]


class Tee:
    def __init__(self, stream, path):
        self.stream = stream
        self.file = open(path, "a", buffering=1)

    def write(self, value):
        self.stream.write(value)
        self.file.write(value)

    def flush(self):
        self.stream.flush()
        self.file.flush()

    def __getattr__(self, name):
        # Hugging Face progress bars inspect isatty/encoding/fileno.
        return getattr(self.stream, name)


def utc():
    return datetime.now(timezone.utc).isoformat()


def save_json(path, value):
    path = Path(path)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")
    tmp.replace(path)


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as stream:
        for b in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(b)
    return h.hexdigest()


class Titles(Dataset):
    def __init__(self, frame, tokenizer, length):
        self.labels = frame["6_way_label"].astype(int).to_numpy()
        self.encoded = {"input_ids": [], "attention_mask": []}
        for start in range(0, len(frame), 8192):
            batch = tokenizer(frame.clean_title.iloc[start:start + 8192].tolist(),
                              truncation=True, max_length=length, padding=False)
            for key in self.encoded:
                self.encoded[key].extend(batch[key])

    def __len__(self):
        return len(self.labels)

    def __getitem__(self, index):
        return {**{k: v[index] for k, v in self.encoded.items()},
                "labels": int(self.labels[index])}


def metrics(y, pred, loss):
    return {"accuracy": float(accuracy_score(y, pred)),
            "macro_f1": float(f1_score(y, pred, average="macro", labels=range(6), zero_division=0)),
            "weighted_f1": float(f1_score(y, pred, average="weighted", zero_division=0)),
            "balanced_accuracy": float(balanced_accuracy_score(y, pred)),
            "loss": float(loss), "samples": len(y)}


@torch.inference_mode()
def evaluate(model, loader):
    model.eval()
    ys, ps, cs = [], [], []
    loss_sum = 0.0
    for batch in loader:
        batch = {k: v.cuda(non_blocking=True) for k, v in batch.items()}
        with torch.autocast("cuda", dtype=torch.float16):
            out = model(**batch)
        probs = out.logits.float().softmax(-1)
        loss_sum += float(out.loss) * len(batch["labels"])
        ys.extend(batch["labels"].cpu().tolist())
        ps.extend(probs.argmax(-1).cpu().tolist())
        cs.extend(probs.max(-1).values.cpu().tolist())
    return metrics(ys, ps, loss_sum / len(ys)), ys, ps, cs


def export_eval(folder, split, frame, result):
    values, y, p, confidence = result
    save_json(folder / f"{split}_metrics.json", values)
    save_json(folder / f"{split}_classification_report.json",
              classification_report(y, p, labels=range(6), target_names=LABELS,
                                    output_dict=True, zero_division=0))
    pd.DataFrame(confusion_matrix(y, p, labels=range(6)), index=LABELS,
                 columns=LABELS).to_csv(folder / f"{split}_confusion_matrix.csv")
    pd.DataFrame({"id": frame.id, "true_label": y, "predicted_label": p,
                  "confidence": confidence}).to_csv(folder / f"{split}_predictions.csv", index=False)


def train_one(spec, cfg, frames, folder, resume=False):
    started = time.monotonic()
    seed = cfg["seed"]
    random.seed(seed); np.random.seed(seed); torch.manual_seed(seed); torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.benchmark = False
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.use_deterministic_algorithms(True, warn_only=True)
    torch.cuda.reset_peak_memory_stats()
    if resume and (folder / "result.json").exists():
        print("Preserving completed model:", spec["name"], flush=True)
        return json.loads((folder / "result.json").read_text())
    folder.mkdir(parents=True, exist_ok=resume)
    save_json(folder / "config.json", {**cfg, "selected_model": spec})
    source_name = "train_official_text.py" if not resume else "resumed_source_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + ".py"
    shutil.copy2(__file__, folder / source_name)
    save_json(folder / "status.json", {"state": "initializing", "updated_utc": utc()})
    tokenizer = AutoTokenizer.from_pretrained(spec["checkpoint"], revision=spec["revision"])
    model = AutoModelForSequenceClassification.from_pretrained(
        spec["checkpoint"], revision=spec["revision"], num_labels=6,
        id2label=dict(enumerate(LABELS)), label2id={s: i for i, s in enumerate(LABELS)},
        attn_implementation="sdpa").cuda()
    tokenizer.save_pretrained(folder / "tokenizer")
    model.config.save_pretrained(folder)
    print(spec["name"], "tokenizing official titles", flush=True)
    data = {k: Titles(v, tokenizer, cfg["max_length"]) for k, v in frames.items()}
    collate = DataCollatorWithPadding(tokenizer, pad_to_multiple_of=8)
    generator = torch.Generator().manual_seed(seed)
    loaders = {k: DataLoader(v, batch_size=cfg["batch_size"] if k == "train" else cfg["eval_batch_size"],
                            shuffle=k == "train", generator=generator if k == "train" else None,
                            num_workers=2, pin_memory=True, collate_fn=collate,
                            persistent_workers=True) for k, v in data.items()}
    groups = [{"params": [], "weight_decay": cfg["weight_decay"]},
              {"params": [], "weight_decay": 0.0}]
    for name, param in model.named_parameters():
        groups[int(name.endswith("bias") or "norm" in name.lower())]["params"].append(param)
    optimizer = torch.optim.AdamW(groups, lr=spec["learning_rate"], eps=1e-8)
    steps = len(loaders["train"]) * cfg["max_epochs"]
    scheduler = get_linear_schedule_with_warmup(optimizer, math.ceil(steps * cfg["warmup_fraction"]), steps)
    scaler = torch.amp.GradScaler("cuda")
    best = None; patience_reference = -1.0; stale = 0; updates = 0; skips = 0
    history = []; train_seconds = 0.0; recovery = None; start_epoch = 1
    if resume and (folder / "resume_checkpoint.pt").exists():
        recovery = torch.load(folder / "resume_checkpoint.pt", map_location="cuda", weights_only=False)
        model.load_state_dict(recovery["model"])
        optimizer.load_state_dict(recovery["optimizer"])
        scheduler.load_state_dict(recovery["scheduler"])
        scaler.load_state_dict(recovery["scaler"])
        best = recovery["best"]; patience_reference = recovery["patience_reference"]
        stale = recovery["stale"]; history = recovery["history"]
        updates = recovery["updates"]; skips = recovery["skips"]
        train_seconds = recovery["train_seconds_completed"]
        start_epoch = recovery["epoch"] + int(recovery["epoch_finished"])
        print("Restoring", spec["name"], "epoch", start_epoch, "after step",
              recovery["step_in_epoch"], flush=True)

    def restore_random(state):
        random.setstate(state["python_rng"]); np.random.set_state(state["numpy_rng"])
        torch.set_rng_state(state["torch_rng"].cpu())
        torch.cuda.set_rng_state_all([s.cpu() for s in state["cuda_rng"]])

    def checkpoint(epoch, index, finished, loss_sum, samples_seen, epoch_elapsed, sampler_start):
        save_json(folder / "status.json", {"state": "checkpointing", "model": spec["name"],
                  "epoch": epoch, "step": index, "updated_utc": utc()})
        state = {"epoch": epoch, "step_in_epoch": index, "epoch_finished": finished,
                 "model": model.state_dict(), "optimizer": optimizer.state_dict(),
                 "scheduler": scheduler.state_dict(), "scaler": scaler.state_dict(), "best": best,
                 "patience_reference": patience_reference, "stale": stale, "history": history,
                 "updates": updates, "skips": skips, "python_rng": random.getstate(),
                 "numpy_rng": np.random.get_state(), "torch_rng": torch.get_rng_state(),
                 "cuda_rng": torch.cuda.get_rng_state_all(), "loader_rng": generator.get_state(),
                 "sampler_start": sampler_start, "train_loss_sum": loss_sum,
                 "samples_seen": samples_seen, "epoch_elapsed": epoch_elapsed,
                 "train_seconds_completed": train_seconds}
        torch.save(state, folder / "resume_checkpoint.pt.tmp")
        (folder / "resume_checkpoint.pt.tmp").replace(folder / "resume_checkpoint.pt")
        save_json(folder / "recovery_checkpoint.json", {"epoch": epoch, "step": index,
                  "epoch_finished": finished, "saved_utc": utc(), "optimizer_updates": updates})
        with (folder / "checkpoint_history.jsonl").open("a") as stream:
            stream.write(json.dumps({"epoch": epoch, "step": index, "epoch_finished": finished,
                         "saved_utc": utc(), "optimizer_updates": updates}) + "\n")
        print("CHECKPOINT SAVED", spec["name"], "epoch", epoch, "step", index, flush=True)

    if recovery and recovery["epoch_finished"]:
        generator.set_state(recovery["loader_rng"].cpu()); restore_random(recovery)
        if len(history) >= cfg["min_epochs"] and stale >= cfg["patience"]:
            start_epoch = cfg["max_epochs"] + 1
    for epoch in range(start_epoch, cfg["max_epochs"] + 1):
        model.train(); train_start = time.monotonic(); total_loss = 0.0; seen = 0
        skip_batches = 0; elapsed_before_resume = 0.0
        if recovery and not recovery["epoch_finished"] and epoch == recovery["epoch"]:
            generator.set_state(recovery["sampler_start"].cpu())
            skip_batches = recovery["step_in_epoch"]
            total_loss = recovery["train_loss_sum"]; seen = recovery["samples_seen"]
            elapsed_before_resume = recovery["epoch_elapsed"]
        sampler_start = generator.get_state()
        for index, batch in enumerate(loaders["train"], 1):
            if index <= skip_batches:
                continue
            if recovery and index == skip_batches + 1:
                restore_random(recovery)
                recovery = None
            batch = {k: v.cuda(non_blocking=True) for k, v in batch.items()}
            optimizer.zero_grad(set_to_none=True)
            with torch.autocast("cuda", dtype=torch.float16):
                out = model(**batch)
            if not torch.isfinite(out.loss):
                raise RuntimeError("Non-finite loss; run aborted without removing samples")
            scaler.scale(out.loss).backward()
            scaler.unscale_(optimizer)
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            scale_before = scaler.get_scale()
            scaler.step(optimizer); scaler.update()
            if scaler.get_scale() >= scale_before:
                scheduler.step(); updates += 1
            else:
                skips += 1
            total_loss += float(out.loss.detach()) * len(batch["labels"]); seen += len(batch["labels"])
            if index % 500 == 0 or index == len(loaders["train"]):
                elapsed = elapsed_before_resume + time.monotonic() - train_start
                state = {"state": "training", "model": spec["name"], "epoch": epoch,
                         "step": index, "steps_per_epoch": len(loaders["train"]),
                         "samples_seen_this_epoch": seen, "samples_per_second": seen / elapsed,
                         "epoch_remaining_seconds": (len(data["train"]) - seen) / (seen / elapsed),
                         "optimizer_updates": updates, "skipped_updates": skips, "updated_utc": utc()}
                save_json(folder / "status.json", state)
                print(f"{spec['name']} epoch {epoch} step {index}/{len(loaders['train'])} "
                      f"loss {total_loss/seen:.4f} speed {seen/elapsed:.1f}/s", flush=True)
            if index % cfg["recovery_checkpoint_every_steps"] == 0:
                checkpoint(epoch, index, False, total_loss, seen,
                           elapsed_before_resume + time.monotonic() - train_start, sampler_start)
        if recovery:
            restore_random(recovery); recovery = None
        train_seconds += elapsed_before_resume + time.monotonic() - train_start
        val_result = evaluate(model, loaders["validation"])
        val = val_result[0]
        history.append({"epoch": epoch, "train_loss": total_loss / seen, "validation": val,
                        "optimizer_updates": updates, "skipped_updates": skips})
        save_json(folder / "history.json", history)
        improved = best is None or (val["macro_f1"], -val["loss"]) > (best["metrics"]["macro_f1"], -best["metrics"]["loss"])
        if improved:
            best = {"epoch": epoch, "metrics": val}
            torch.save(model.state_dict(), folder / "best_weights.pt.tmp")
            (folder / "best_weights.pt.tmp").replace(folder / "best_weights.pt")
            save_json(folder / "best_checkpoint.json", best)
            export_eval(folder, "validation", frames["validation"], val_result)
        if val["macro_f1"] >= patience_reference + cfg["min_delta"]:
            patience_reference = val["macro_f1"]; stale = 0
        else:
            stale += 1
        checkpoint(epoch, len(loaders["train"]), True, total_loss, seen, 0.0, sampler_start)
        print(spec["name"], "EPOCH", epoch, "VALIDATION", json.dumps(val), flush=True)
        if epoch >= cfg["min_epochs"] and stale >= cfg["patience"]:
            break
    model.load_state_dict(torch.load(folder / "best_weights.pt", map_location="cuda", weights_only=True))
    # Test is accessed only after the validation-selected checkpoint is fixed.
    test = evaluate(model, loaders["test"])
    export_eval(folder, "test", frames["test"], test)
    result = {"model": spec, "seed": seed, "protocol_id": cfg["protocol_id"],
              "checkpoint_epoch": best["epoch"], "validation": best["metrics"], "test": test[0],
              "epochs_completed": len(history), "training_seconds": train_seconds,
              "total_seconds": time.monotonic() - started,
              "peak_gpu_allocated_bytes": torch.cuda.max_memory_allocated(),
              "optimizer_updates": updates, "skipped_updates": skips,
              "single_seed": True, "completed_utc": utc()}
    save_json(folder / "result.json", result)
    save_json(folder / "status.json", {"state": "complete", "updated_utc": utc(), "result": result})
    print("FINAL RESULT", json.dumps(result), flush=True)
    del model, optimizer, scheduler, loaders, data; gc.collect(); torch.cuda.empty_cache()
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--data", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--resume-attempt", help="Existing cloud attempt folder; restores recovery checkpoints")
    args = parser.parse_args()
    if not torch.cuda.is_available():
        raise RuntimeError("Cloud CUDA GPU required; refusing CPU training")
    cfg = json.loads(Path(args.config).read_text())
    attempt = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    root = Path(args.resume_attempt) if args.resume_attempt else Path(args.output) / (cfg["protocol_id"] + "_seed42_" + attempt)
    if args.resume_attempt:
        if json.loads((root / "protocol.json").read_text()) != cfg:
            raise ValueError("Resume protocol differs; refusing to mix experiments")
    else:
        root.mkdir(parents=True, exist_ok=False)
    sys.stdout = Tee(sys.stdout, root / "training.log")
    sys.stderr = Tee(sys.stderr, root / "stderr.log")
    shutil.copy2(args.config, root / "protocol.json")
    environment_name = "environment.json" if not args.resume_attempt else "environment_resume_" + attempt + ".json"
    save_json(root / environment_name, {"utc": utc(), "python": sys.version,
              "platform": platform.platform(), "torch": torch.__version__,
              "transformers": transformers.__version__, "sklearn": sklearn.__version__,
              "numpy": np.__version__, "pandas": pd.__version__, "cuda": torch.version.cuda,
              "gpu": torch.cuda.get_device_name(0), "gpu_bytes": torch.cuda.get_device_properties(0).total_memory,
              "source_sha256": sha(__file__), "resume": bool(args.resume_attempt),
              "nvidia_smi": subprocess.check_output(["nvidia-smi"], text=True)})
    freeze_name = "pip_freeze.txt" if not args.resume_attempt else "pip_freeze_resume_" + attempt + ".txt"
    (root / freeze_name).write_text(subprocess.check_output([sys.executable, "-m", "pip", "freeze"], text=True))
    frames = {}; evidence = {}; ids = set()
    for split, info in cfg["splits"].items():
        path = Path(args.data) / info["filename"]
        if sha(path) != info["sha256"]:
            raise ValueError(f"Official file hash mismatch: {path}")
        frame = pd.read_csv(path, sep="\t", dtype=str, keep_default_na=False,
                            usecols=["id", "clean_title", "6_way_label"])
        if len(frame) != info["rows"] or frame.id.duplicated().any() or frame.clean_title.str.strip().eq("").any():
            raise ValueError(f"Official cohort validation failed: {split}")
        if not frame["6_way_label"].isin([str(i) for i in range(6)]).all() or ids.intersection(frame.id):
            raise ValueError("Invalid labels or split overlap")
        ids.update(frame.id); frames[split] = frame
        evidence[split] = {**info, "label_counts": frame["6_way_label"].value_counts().sort_index().to_dict()}
    save_json(root / "dataset_evidence.json", evidence)
    print("ATTEMPT", str(root), "OFFICIAL COUNTS", {k: len(v) for k, v in frames.items()}, flush=True)
    results = []
    for spec in cfg["models"]:
        folder = root / spec["name"]
        try:
            results.append(train_one(spec, cfg, frames, folder, resume=bool(args.resume_attempt)))
            save_json(root / "results_summary.json", results)
        except Exception:
            folder.mkdir(parents=True, exist_ok=True)
            (folder / "error.txt").write_text(traceback.format_exc())
            save_json(folder / "status.json", {"state": "failed", "updated_utc": utc(),
                      "reason": traceback.format_exc()})
            raise
    # Small portable evidence bundle excludes large weights/checkpoints.
    import zipfile
    with zipfile.ZipFile(root / "text_results_evidence.zip", "w", zipfile.ZIP_DEFLATED) as bundle:
        for file in root.rglob("*"):
            if file.is_file() and file.suffix not in [".pt", ".zip", ".tmp"]:
                bundle.write(file, file.relative_to(root))
    print("ALL TEXT MODELS COMPLETE", str(root), flush=True)


if __name__ == "__main__":
    main()
