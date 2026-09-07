# EXPERIMENT LOG — Multimodal Fake News Detection

> Record actual experiments, configurations, results, observations, and conclusions here.
> Do NOT record invented or hypothetical results.
> Format: Experiment ID, Date, Description, Configuration, Results, Observations

---

## Status

No model-training experiments have been run yet. Dataset sampling/download validation and a non-experimental architecture decision review are complete; the project remains in Phase 1 (Understanding).

---

## Planned Experiments

### E001 — Data Exploration (Pending)
- **Goal:** Inspect TSV files, count samples, analyze label distribution, identify multimodal samples
- **Status:** Not started — TSV files not yet downloaded

### E002 — Text-Only Baseline (Planned)
- **Goal:** Establish text-only classification performance
- **Status:** Not started — depends on architecture choice

### E003 — Image-Only Baseline (Planned)
- **Goal:** Establish image-only classification performance
- **Status:** Not started — depends on image subset download

### E004 — Text+Image Baseline (Planned)
- **Goal:** Establish multimodal baseline performance
- **Status:** Not started — depends on E002, E003

---

## Completed Experiments

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
