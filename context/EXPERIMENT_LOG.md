# EXPERIMENT LOG — Multimodal Fake News Detection

> Record actual experiments, configurations, results, observations, and conclusions here.
> Do NOT record invented or hypothetical results.
> Format: Experiment ID, Date, Description, Configuration, Results, Observations

---

## Status

Preliminary E002 seed-42 metrics exist, but no final canonical three-seed baseline metrics exist yet. A preliminary E002 seed-42 run was completed on Colab T4 (2026-09-22/23) but produced a scheduler-order warning (`lr_scheduler.step()` before `optimizer.step()`); this result is PRELIMINARY and must be rerun after correction. E002 implementation and a non-canonical CPU smoke test are complete. On 2026-09-22, the faculty directed broadening the model comparison to include CLIP-based multimodal experiments beyond the BERT/ResNet-50 baselines, and HGAT as a later candidate.

---

## Planned Experiments

### E001 — Data Exploration (Pending)
- **Goal:** Inspect TSV files, count samples, analyze label distribution, identify multimodal samples
- **Status:** Not started — TSV files not yet downloaded

### E002 — Text-Only Baseline (Planned)
- **Goal:** Establish text-only classification performance
- **Status:** Implementation and smoke test complete. Preliminary seed-42 run completed on Colab T4 (2026-09-22/23) with scheduler-order warning; rerun required. Seeds 43/44 pending. No final canonical validation/test performance result exists.

### E003 — Image-Only Baseline (Planned)
- **Goal:** Establish image-only classification performance
- **Status:** Not started — architecture and `BP-6W-v1` protocol are fixed; pending implementation approval

### E004 — Text+Image Baseline (Planned)
- **Goal:** Establish multimodal baseline performance
- **Status:** Not started — architecture and `BP-6W-v1` protocol are fixed; pending implementation approval

### E005 — CLIP-Based Multimodal (Planned — Added 2026-09-22)
- **Goal:** Explore semantically aligned text-image representations (CLIP) for multimodal fake-news classification as a stronger comparison model beyond the BERT + ResNet-50 baseline
- **Status:** Planned, not implemented. Architecture not yet frozen. Requires design review before implementation. Added per advisor feedback on 2026-09-22.
- **Cohort:** Same `data/verified_paired_manifest.csv` (75,995 paired samples)
- **Terminology note:** Working reference is CLIP (Contrastive Language-Image Pre-training, OpenAI); exact advisor terminology to be confirmed before implementation.

### E006 — HGAT Social-Context Model (Future Investigation — Added 2026-09-22)
- **Goal:** Model social/context graph relationships (users, comments, propagation) for fake-news detection
- **Status:** Future investigation only. **NOT an immediate experiment.** HGAT requires social/context graph data that is not currently available in our canonical Fakeddit paired cohort (`clean_title` + local image + `6_way_label`). Implementation is blocked until the availability of user/comment/propagation graph data is verified for our Fakeddit setup. Added per advisor feedback on 2026-09-22.

---

## Advisor-Requested Experiments / Upcoming (2026-09-22)

Faculty requested initial experimental values/metrics on 2026-09-22. The following table summarizes all current and planned experiments with their status:

| Experiment | Model | Status | Has Results? |
|---|---|---|---|
| E002 | BERT text-only | ✅ Implemented, ✅ smoke-tested, ⚠️ preliminary seed-42 (scheduler issue) | **Preliminary only** |
| E003 | ResNet-50 image-only | ❌ Not implemented | **No** |
| E004 | BERT + ResNet-50 multimodal | ❌ Not implemented | **No** |
| E005 | CLIP-based multimodal | ❌ Planned, architecture not frozen | **No** |
| E006 | HGAT social-context | ❌ Future, blocked on data verification | **No** |

**Preliminary E002 seed-42 metrics exist, but no final canonical three-seed baseline metrics exist yet.** All final canonical metrics must come from actual canonical CUDA training runs under protocol `BP-6W-v1`, not smoke-test losses or literature-reported values. Literature-reported results must never be placed into our experiment-results sections or mixed with our own experimental metrics.

---

## Completed Experiments

### E002 — Preliminary Seed-42 Colab Training — 2026-09-22/23 (PRELIMINARY)
- **Goal:** First canonical CUDA training run for E002 BERT text-only baseline.
- **Configuration:** `configs/e002_text_bp6w_v1.json`; seed 42; Tesla T4 GPU; CUDA AMP enabled; `data/verified_paired_manifest.csv` SHA-256 verified; 75,995 paired samples (62,635 train / 6,685 validation / 6,675 test).
- **⚠️ STATUS: PRELIMINARY.** The run produced `UserWarning: Detected call of lr_scheduler.step() before optimizer.step()`. The learning rate schedule may not have been applied correctly. The E002 scheduler-order bug has been corrected. No full retraining was performed during the fix task. The preliminary seed-42 result remains preliminary. A clean canonical seed-42 rerun is required.
- **Preliminary results (validation, selected epoch 4):** accuracy 0.7820, Macro-F1 0.7012, balanced accuracy 0.6689, weighted-F1 0.7784, loss 0.7400.
- **Preliminary results (test):** accuracy 0.7790, Macro-F1 0.6891, balanced accuracy 0.6598, weighted-F1 0.7758, loss 0.7398.
- **Per-class test F1:** True 0.8312, Satire/Parody 0.6098, Misleading Content 0.6707, Imposter Content 0.4734, False Connection 0.8293, Manipulated Content 0.7205.
- **Runtime:** total 1825.6s (~30.4 min), training 1312.2s, throughput 286.4 samples/sec, peak GPU memory 3,238,541,312 bytes (~3.02 GB).
- **Environment:** PyTorch 2.11.0+cu128, Transformers 5.16.1, scikit-learn 1.6.1, Tesla T4.
- **Artifact:** `results/experiments/e002_text/E002-bert-base-uncased-6way-BP6Wv1-s42-preliminary/preliminary_result.json` (reconstructed from Colab output; original machine-generated JSON was not synced from Colab).
- **Observations:** Lowest per-class F1 is Imposter Content (0.4734), the smallest class (140 test samples). Highest F1 are True (0.8312) and False Connection (0.8293). Additional warnings: palette image transparency, DecompressionBombWarning, DataLoader worker count, HuggingFace unauthenticated hub, BERT unexpected keys (all non-critical).
- **Scope:** Seed 42 only. Seeds 43/44 not run. Scheduler-order issue means this is not the final canonical result. No E003/E004/E005/E006 was run.

### E002 — Text-Only Implementation Smoke Test — 2026-09-08 (Non-canonical)
- **Goal:** Verify the complete E002 implementation path before any canonical training.
- **Configuration:** `configs/e002_text_bp6w_v1.json`; fixed `data/verified_paired_manifest.csv` SHA-256 `fc74cb42288d366131ac764bf02f9212bacd7cab0af68442a003beaaff9fde20`; resolved `bert-base-uncased` revision `86b5e0934494bd15c9632b12f734a8a67f723594`; seed 42; CPU; AMP disabled; two train rows; zero DataLoader workers for the smoke-only local check. This was not a BP-6W-v1 training run and did not substitute for CUDA.
- **Verified results:** imports, `BertTokenizerFast`, fixed-manifest loading, two paired-image RGB decodes, one dynamic-padded batch (`input_ids` and attention mask `[2, 34]`), BERT forward pass (`[2, 6]` logits), unweighted cross-entropy loss (`2.625950574874878`), backward pass, gradient clipping, optimizer step, and checkpoint writing all passed. The checkpoint was 438,028,532 bytes and was immediately removed after verification. The model contained 109,486,854 total/trainable parameters.
- **Observations:** the first smoke invocation exposed a macOS multiprocessing pickling error in a nested collator. The collator was moved to a top-level class; the final rerun passed. No failed checkpoint, training checkpoint, validation metric, test metric, or prediction was retained.
- **Scope:** no canonical training, E003, E004, resampling, manifest change, image download, or protocol change occurred.

### Baseline Protocol Decision — 2026-09-08 (Non-experimental)
- **Goal:** Pre-register a fair, reproducible and compute-adaptable protocol for E002/E003/E004 before implementation.
- **Verified cohort:** `data/verified_paired_manifest.csv`: 75,995 rows; 62,635 train / 6,685 validation / 6,675 test; zero empty `clean_title` values and zero duplicate IDs. No file was changed.
- **Decision:** `BP-6W-v1` uses the same paired cohort and fixed split for every baseline; 6-way labels; three seeds (42/43/44); unweighted cross-entropy; validation macro-F1 checkpoint selection; 10-epoch cap; shared effective batch 32; and macro/per-class/confusion-matrix reporting. E002, E003 and E004 model-specific settings are recorded in PROJECT_CONTEXT and D012.
- **Evidence:** Original Fakeddit benchmark; GenBench 2023 temporal Fakeddit evaluation; official PyTorch/TorchVision/Hugging Face documentation for reproducibility, AMP, ResNet V2 preprocessing, and token padding/truncation.
- **Results:** No model, training, inference, metric, resource measurement, or checkpoint exists. The local manifest-count inspection was read-only.
- **Required future log fields:** run ID; protocol/config and code hashes; manifest hash and class counts; device/VRAM/software; parameter counts; micro/effective batch and AMP; epoch-level losses/metrics; selected checkpoint; test metrics/predictions/confusion matrix; runtime, throughput, peak memory; and exceptions/OOMs.
- **Unresolved:** exact RTX 3050 VRAM; no resulting model configuration may be changed to accommodate it except micro-batch/accumulation while preserving effective batch.

### Architecture Decision Review — 2026-09-08 (Non-experimental)
- **Goal:** Select scientifically defensible, reproducible and compute-feasible text-only, image-only and text+image baselines before implementation.
- **Configuration:** Research/decision review only. Consulted the original Fakeddit paper and repository, the supplied 2026 data-centric review, and selected 2023–2025 primary literature on generalization, temporal shift and stronger multimodal encoders. No code or model was run.
- **Decision:** Use BERT-base for text-only, ImageNet-pretrained ResNet-50 for image-only, and BERT-base + ResNet-50 with equal-dimension projection and element-wise maximum fusion for text+image. Use 6-way labels initially and validation macro-F1 as the principal selection metric.
- **Observations:** The original Fakeddit paper found the BERT + ResNet-50 maximum-fusion family its strongest simple multimodal combination. Later studies show that standard in-domain scores and scores from different subsets/splits are not directly comparable, and that temporal/content shifts can substantially reduce performance. The 3-way setting has a very small intermediate class and published Fakeddit analysis found it behaved similarly to 2-way; 6-way exposes more diagnostic errors but is imbalanced.
- **Results:** No experimental metrics, runtime, memory use, checkpoint, or benchmark result exists yet.
- **Next prerequisite:** Team approval of the fixed experimental protocol before E002/E003/E004 are implemented or run.

### E001B — Baseline Stratified Dataset Sampling
- **Date:** 2026-09-07
- **Goal:** Create reproducible stratified sample of 80,000 multimodal items for first baseline experiment.
- **Configuration:** Python script (`scripts/create_baseline_sample.py`), seed=42, filtering `hasImage==True`, valid `image_url`, non-empty `clean_title`.
- **Results & Observations:**
  - **Raw Multimodal Count:** 771,698
  - **Missing `clean_title` Filtered:** 90,900 missing titles dropped (75,098 train, 7,866 val, 7,936 test).
  - **Usable Multimodal Pool:** 680,798 samples (562,466 train, 59,169 val, 59,163 test).
  - **Final Sample Size:** **80,000 samples** (66,000 train, 7,000 val, 7,000 test).
  - **Output Manifest:** `data/baseline_sample_manifest.csv` containing standard metadata columns.
  - **Detailed Distributions:** Recorded in `results/sampling_report.json`. Stratification strictly preserved exact 6-way label ratios.
  - **Estimated Storage:** ~3.05 GB (preliminary reference estimate).

### E001C — Image Downloader Pipeline 100-Sample Validation
- **Date:** 2026-09-07
- **Goal:** Test reliability, PIL validation, resumability, and storage metrics on a 100-image sample from `data/baseline_sample_manifest.csv`.
- **Configuration:** Python script (`scripts/download_images.py --limit 100`), 8 workers, 10s timeout, 2 retries.
- **Results & Observations:**
  - **Attempted:** 100 images
  - **Successful & Decodable:** 95 images (95.0%)
  - **Failed / Unavailable:** 5 images (5.0%, all HTTP 404 Not Found on Reddit CDN)
  - **Corrupt / Unreadable:** 0 images (100% of downloaded files verified with PIL)
  - **Actual Storage Used:** 1.56 MB (1,635,552 bytes)
  - **Measured Average Image Size:** 16.81 KB / image
  - **Projected Storage for Full 80K Baseline:** **~1.28 GB** (at ~16.81 KB/image)
  - **Resumability Verification:** Second run validated in 0.31s with all 95 files detected as `already_exists`.
  - **ID Mapping:** Verified 95/95 filenames directly match `{id}.jpg`.



### E001D — Full 80K Baseline Image Download (Resumed After Interruption)
- **Date:** 2026-09-07
- **Goal:** Download and verify all 80,000 images from `data/baseline_sample_manifest.csv`.
- **Configuration:** `scripts/download_images.py`, 8 workers, 10s timeout, 2 retries, PIL validation, resumable.
- **Interruption:** Original run stopped at 26,837 valid images. Resumed without restart — existing files skipped via PIL check.
- **Results & Observations:**
  - **Total Attempted:** 80,000
  - **Images Present Before Resume:** 26,837 (all PIL-valid, all in manifest)
  - **Newly Downloaded After Interruption:** 49,158
  - **Total Successful & Verified:** **75,995 (94.99%)**
  - **Failed / Missing:** 4,005 (5.01%)
  - **Corrupt / Unreadable:** 31
  - **Actual Storage Used:** 7.822 GB (8,398,948,245 bytes)
  - **Average Image Size:** 107.93 KB / image
  - **Primary Failure Cause:** HTTP 404 (3,863 / 4,005 failures = 96.5%)
  - **Verified Manifest:** `data/verified_paired_manifest.csv` — 75,995 rows, matches disk exactly
  - **Failure Log:** `results/download_failures.json` — 4,005 entries with ID, URL, status, error
  - **ID Mapping:** Verified 75,995/75,995 filenames match `{id}.jpg`, all map to unique manifest IDs
  - **Original Manifest:** `data/baseline_sample_manifest.csv` unchanged (80,000 rows)
