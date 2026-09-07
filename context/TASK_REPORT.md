# Task Report — Reproducible Baseline Protocol (`BP-6W-v1`)

## Task and Status

Define a reproducible, fair experimental protocol for E002 text-only, E003 image-only and E004 text+image Fakeddit baselines before model implementation or training.

**Completed — protocol decision only.** No implementation, training, inference, download, re-sampling or manifest change occurred.

## Protocol Decisions

### Shared cohort and task

- Use `data/verified_paired_manifest.csv` for every baseline, preserving `split`: **62,635 train, 6,685 validation, 6,675 test** (75,995 total).
- Use only `clean_title`, local paired image and `6_way_label`. The locked mapping is 0 True, 1 Satire/Parody, 2 Misleading Content, 3 Imposter Content, 4 False Connection, 5 Manipulated Content.
- The validated manifest has zero blank titles and zero duplicate IDs. Before every run, verify all listed image paths exist and decode as RGB. Abort rather than silently dropping an item.
- Primary task: 6-way. Use unweighted cross-entropy, no resampling, macro-F1 as primary metric, and class-wise analysis. A 2-way control may be run only after all 6-way baselines, with the same protocol and only the label/output dimension changed.

### E002 — Text-only

- Model: end-to-end fine-tuned `bert-base-uncased` plus 6-way linear classifier; classifier dropout 0.2.
- Input: stored `clean_title`, with no additional semantic rewriting or metadata; `BertTokenizerFast`, 128-token maximum including special tokens, truncation, dynamic longest-in-batch padding.
- Optimizer: AdamW, LR `2e-5`, weight decay 0.01 (except bias/norm), betas `(0.9, 0.999)`, epsilon `1e-8`.
- T4/A100 batch: 32 with accumulation 1; target effective batch is 32.

### E003 — Image-only

- Model: end-to-end fine-tuned `ResNet50_Weights.IMAGENET1K_V2` plus dropout 0.2 and 6-way linear classifier.
- Input: convert to RGB. Training uses `RandomResizedCrop(224, scale=(0.8, 1.0), ratio=(0.75, 1.333), bilinear, antialias=True)`; validation/test use `Resize(232, bilinear, antialias=True)` then `CenterCrop(224)`; ImageNet V2 mean/std. Do not flip or colour-jitter, because images may contain written evidence.
- Optimizer: AdamW, LR `1e-4`, weight decay `1e-4` (except bias/norm), same betas/epsilon.
- T4/A100 batch: 32 with accumulation 1; effective batch 32.

### E004 — Text + Image

- Model: end-to-end fine-tuned BERT-base and ResNet-50 using the identical E002/E003 inputs. Project BERT CLS 768→512 and ResNet pooled 2048→512, LayerNorm each, element-wise maximum fusion, then `512→256→6` MLP with GELU and dropout 0.2.
- Optimizer: AdamW groups: BERT `2e-5` / decay 0.01; ResNet `1e-4` / decay `1e-4`; new projections and MLP `1e-3` / decay 0.01; exclusions for bias/norm apply.
- T4/A100 batch: 8 with accumulation 4; effective batch 32.

### Shared training and selection

- Do not freeze encoders. Clip gradient norm at 1.0.
- Maximum 10 epochs. Evaluate validation data after every epoch. After completing 3 epochs, stop after two consecutive epochs without a macro-F1 increase of at least 0.001.
- Scheduler: 10% linear warm-up over planned optimizer updates, then linear decay to zero.
- Seeds: 42, 43 and 44. Select the best checkpoint per seed by validation macro-F1; ties resolve by lower validation loss, then earlier epoch. Test once per selected seed and report mean ± standard deviation, never best test seed.
- `BP-6W-v1` has no model-specific tuning sweep. Any later sweep requires an amendment, validation-only selection and an equal, documented budget across all baselines.

## Evaluation, Reproducibility and Resource Logging

- Report macro-F1 (primary), accuracy, balanced accuracy, weighted-F1, per-class precision/recall/F1/support with `zero_division=0`, and raw plus row-normalized 6×6 confusion matrices.
- Use CUDA AMP with `torch.amp.autocast("cuda", float16)` and `torch.amp.GradScaler("cuda")` for canonical cloud/CUDA runs. M3/MPS is for development/smoke checks unless CUDA is unavailable.
- Seed Python, NumPy, PyTorch, DataLoader generator and workers; use deterministic algorithms where supported, deterministic cuDNN and `benchmark=False`. Record hardware/software because deterministic equality is only expected within the documented environment.
- For every run, record: run ID, protocol/config and code hashes; manifest SHA-256 and split/class counts; model/weight/tokenizer revisions; parameter counts (total/trainable); device, VRAM, driver and package versions; AMP; micro/effective batch; epoch metrics; selected checkpoint; test predictions/metrics/confusion matrix; runtime, throughput, peak memory; and OOM/non-finite events.
- Naming: `E00X-<model>-6way-BP6Wv1-s<seed>`.

## Evidence and Reasoning

- [Nakamura, Levy and Wang (LREC 2020)](https://aclanthology.org/2020.lrec-1.755/) provides the Fakeddit 6-way and BERT/ResNet maximum-fusion benchmark precedent.
- [Stepanova and Ross (GenBench 2023)](https://aclanthology.org/2023.genbench-1.6/) shows why Fakeddit's fine-grained imbalance requires macro and class-wise reporting.
- [TorchVision ResNet-50 V2 documentation](https://docs.pytorch.org/vision/stable/models/generated/torchvision.models.resnet50.html) specifies the selected pretrained weights and inference preprocessing; its model card reports 25,557,032 parameters.
- [Hugging Face padding/truncation documentation](https://huggingface.co/docs/transformers/main/pad_truncation) supports dynamic padding and explicit maximum-length truncation.
- [PyTorch reproducibility guidance](https://docs.pytorch.org/docs/stable/notes/randomness.html) specifies worker seeding; [PyTorch AMP guidance](https://docs.pytorch.org/docs/stable/amp) specifies autocast with gradient scaling for CUDA FP16.

The protocol prioritizes controlled comparisons: all baselines use the same paired rows, splits, seed count, effective batch, epoch cap, selection rule and metrics. Learning-rate and weight-decay groups differ only by pretrained encoder/new-head type and are fixed before training; this preserves standard transfer-learning scales without tuning one baseline more heavily.

## Unresolved Decisions Requiring Approval or Later Measurement

1. **RTX 3050 VRAM:** unknown. Measure before local CUDA use. If needed, lower only micro-batch and raise accumulation to keep effective batch 32; record it.
2. **Canonical execution location:** recommend Colab T4/A100 for reported results. Confirm this before implementation so all canonical runs share one CUDA/software environment.
3. **Protocol exception policy:** any learning-rate sweep, class-weighted loss, augmentation change, frozen encoder, or data-eligibility change requires an explicit documented amendment and equal comparison budget.

## What Was Not Done

- No model code, configuration code, training loop, data loader, checkpoint, benchmark, or smoke test was created or run.
- No data or image was downloaded, removed, re-sampled, or modified; the 80K source manifest and 75,995-row verified manifest remain unchanged.
- No final research contribution/gap was chosen.

## Recommended Next Step

Approve the canonical CUDA environment and confirm the RTX 3050 VRAM if local training is intended. Then authorize implementation of `BP-6W-v1`, beginning with E002 and preserving this protocol unchanged.

## Date

2026-09-08 — Codex
