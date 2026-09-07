# Task Report — E002 Text-Only Implementation and Smoke Test

## Task Performed

Implemented E002 only: the reusable `BP-6W-v1` text data pipeline, BERT-base-uncased six-class classifier, canonical CUDA training entry point, metric/artifact logging, frozen configuration, and required pre-training smoke test.

## Status

**Implementation complete; smoke test passed; canonical training not started.** This task did not implement or start E003/E004.

## Files Created or Changed

- `src/fakenews_baselines/__init__.py` — baseline package marker.
- `src/fakenews_baselines/e002_text.py` — E002-only manifest validation, deterministic loader, model, training/evaluation, logging, artifact, and smoke-test components.
- `configs/e002_text_bp6w_v1.json` — frozen E002 configuration, manifest hash/counts, protocol settings, approved seeds, and BERT revision.
- `scripts/run_e002.py` — canonical CUDA-only E002 runner for seed 42/43/44.
- `scripts/smoke_test_e002.py` — non-canonical CPU smoke-test runner.
- `requirements.txt` — declares PyTorch, Transformers, and Safetensors dependencies for E002.
- `results/experiments/e002_text/E002-bert-base-uncased-6way-BP6Wv1-smoke-cpu/resolved_config.json` — resolved smoke configuration.
- `results/experiments/e002_text/E002-bert-base-uncased-6way-BP6Wv1-smoke-cpu/smoke_test_summary.json` — verified smoke-test evidence.
- `context/PROJECT_CONTEXT.md`, `context/EXPERIMENT_LOG.md`, and this report — current factual project state.

`context/DECISIONS.md` was intentionally not changed: implementation made no new research/protocol decision.

## Dataset and Cohort Used

- Manifest: `data/verified_paired_manifest.csv`, read only and unchanged.
- SHA-256: `fc74cb42288d366131ac764bf02f9212bacd7cab0af68442a003beaaff9fde20`.
- Cohort: 75,995 paired samples — 62,635 train / 6,685 validation / 6,675 test.
- Input: stored `clean_title`; label: `6_way_label` with the approved mapping.
- The smoke test loaded the fixed manifest and decoded the first two train-row paired images as RGB. Canonical training code validates every paired image before loading tokenizer/model.

## Exact Protocol Implemented

- E002 model: end-to-end `bert-base-uncased`, BERT pooler output with CLS fallback, dropout 0.2, linear six-class classifier.
- Tokenizer: `BertTokenizerFast`, maximum 128 tokens including special tokens, truncation, and dynamic longest-in-batch padding.
- Optimizer: AdamW, LR `2e-5`, weight decay 0.01 except bias/normalization parameters, betas `(0.9, 0.999)`, epsilon `1e-8`.
- Training: effective batch 32 (`32 x 1` configured), maximum 10 epochs, linear 10% warm-up then decay, gradient clipping 1.0, unweighted cross-entropy, end-to-end fine-tuning.
- Selection: validation Macro-F1; exact ties use lower validation loss then earlier epoch. Early stopping begins only after epoch 3 and requires two consecutive epochs without a Macro-F1 gain of at least 0.001.
- Seeds: 42, 43, 44 only. Canonical runner requires CUDA and uses AMP/mixed precision when supported.
- Evaluation/artifacts: required aggregate/per-class metrics, raw/normalized confusion matrices, ID-linked test predictions, runtime/throughput/peak-memory fields, environment, versions, manifest/code/config hashes, model revision, and exception logs.

## Smoke-Test Result

**Passed** on 2026-09-08 as an explicitly non-canonical CPU implementation check. It did not perform any training epoch, validation evaluation, test evaluation, or reportable model measurement.

- Device/precision: CPU, AMP disabled; seed 42; zero DataLoader workers for this smoke-only check.
- Imports and tokenizer: passed.
- Dataset/manifest: passed; manifest hash and all expected split counts matched.
- One dynamic-padded batch: two examples, `input_ids`/attention mask shape `[2, 34]`.
- Forward pass: logits shape `[2, 6]`.
- Loss: `2.625950574874878`.
- Backward pass, gradient clipping, and optimizer step: passed.
- Checkpoint writing: passed; 438,028,532-byte checkpoint was verified then deleted. No large checkpoint remains.
- Model parameters: 109,486,854 total and trainable.
- BERT revision: `86b5e0934494bd15c9632b12f734a8a67f723594`.

The first smoke invocation found a real macOS DataLoader pickling error caused by a nested collator function. It was corrected by using a top-level collator class, and the final smoke rerun passed. No failed artifact was retained.

## Training and Seed Status

- Canonical E002 training: **not started**.
- Seed 42: not started.
- Seed 43: not started.
- Seed 44: not started.
- Actual validation/test metrics: none. No values are invented or inferred from the smoke-test loss.

## Errors and Blockers

- The initial local Python environment lacked `transformers` and `scikit-learn`; temporary isolated dependencies in `/private/tmp/e002-deps` were used only for smoke verification. The repository was not given a virtual environment.
- This Mac reports PyTorch 2.8.0 with CUDA unavailable and MPS unavailable. Per BP-6W-v1 and task instructions, canonical training must not fall back to CPU/MPS and remains pending a CUDA environment.
- A temporary `urllib3` LibreSSL warning appeared during smoke execution. It did not prevent the passed tokenizer/model or training-step verification.

## What Was Not Completed

- No full E002 training, validation sweep, test evaluation, or seed aggregation.
- No canonical CUDA run, model checkpoint retention, or reportable performance metric.
- No E003 image-only or E004 text+image implementation/run.
- No manifest/data/image modification, resampling, augmentation, class weighting, or protocol amendment.

## Current Project State

The 75,995-row verified paired cohort remains intact and hash-locked by configuration. E002 is ready to run unchanged in a canonical CUDA environment. Context files now record the implementation and smoke-test evidence; no new decision was made.

## Immediate Next Step

Move the committed E002 code/configuration to a CUDA environment, confirm available VRAM, run the full paired-image preflight validation, then begin only E002 seed 42. Do not start E003/E004.
