# Task Report

## Task
Create a reproducible stratified sampling pipeline for the FIRST BASELINE DATASET from the official local Fakeddit TSV files (`all_train.tsv`, `all_validate.tsv`, `all_test_public.tsv`).

## Status
Completed

## Files Changed / Created
- `scripts/create_baseline_sample.py` (Created — reproducible sampling script, seed=42)
- `data/baseline_sample_manifest.csv` (Created — sample manifest containing 80,000 multimodal entries)
- `results/sampling_report.json` (Created — detailed JSON report of before/after class distributions and filter metrics)
- `context/PROJECT_CONTEXT.md` (Updated — documented manifest details, sample size, and repository structure)
- `context/DECISIONS.md` (Updated — recorded Decision D008 for 80k stratified sampling parameters)
- `context/EXPERIMENT_LOG.md` (Updated — logged Experiment E001B data sampling metrics)
- `context/TASK_REPORT.md` (Updated — current task status and results)

## Sample Size
- **Total Baseline Sample Size:** **80,000 samples**
  - **Train:** 66,000 samples (82.5%)
  - **Validation:** 7,000 samples (8.75%)
  - **Test:** 7,000 samples (8.75%)
- **Reproducibility:** Seed=42 via `scripts/create_baseline_sample.py`

## Missing-Data Handling
- **`clean_title` Missingness:** Across the 771,698 raw multimodal samples (`hasImage == True` & valid `image_url`), exactly **90,900 samples** had missing, null, or empty `clean_title` text:
  - **Train split:** 75,098 missing titles dropped
  - **Validation split:** 7,866 missing titles dropped
  - **Test split:** 7,936 missing titles dropped
- **Resolution:** All 90,900 missing-title samples were filtered out, leaving a clean usable pool of **680,798** multimodal samples. 100% of samples in `data/baseline_sample_manifest.csv` have valid `clean_title` text.

## Class Distributions (Before vs After Sampling)

### Overall 6-Way Label Distribution
| Label Index & Description | Before Sampling Count (680,798 Usable) | Before % | After Sampling Count (80,000 Sampled) | After % |
|---|---|---|---|---|
| **0 — True** | 267,601 | 39.31% | 31,446 | 39.31% |
| **1 — Satire / Parody** | 40,423 | 5.94% | 4,750 | 5.94% |
| **2 — Misleading Content** | 129,384 | 19.01% | 15,203 | 19.00% |
| **3 — Imposter Content** | 14,234 | 2.09% | 1,673 | 2.09% |
| **4 — False Connection** | 203,139 | 29.84% | 23,871 | 29.84% |
| **5 — Manipulated Content** | 26,017 | 3.82% | 3,057 | 3.82% |

### Per-Split 6-Way Label Counts (After Sampling)
- **Train (66,000):** Class 0: 25,933 | Class 1: 3,920 | Class 2: 12,541 | Class 3: 1,382 | Class 4: 19,696 | Class 5: 2,528
- **Validation (7,000):** Class 0: 2,744 | Class 1: 416 | Class 2: 1,330 | Class 3: 146 | Class 4: 2,107 | Class 5: 257
- **Test (7,000):** Class 0: 2,769 | Class 1: 414 | Class 2: 1,332 | Class 3: 145 | Class 4: 2,068 | Class 5: 272

## Storage Estimate
- **Estimated Image Storage:** **~3.05 GB** (calculated using ~40 KB/image reference estimate for 80,000 images).
- *Note:* This figure is treated as an estimate until images are downloaded and verified.

## What Was NOT Done
- Did NOT download the 80,000 images or the full ~30 GB image archive yet.
- Did NOT train any baseline model.
- Did NOT select final model architecture or research gap.
- Did NOT upload dataset files or manifests to GitHub (protected by `.gitignore`).

## Current Project State
The baseline dataset manifest (`data/baseline_sample_manifest.csv`) is fully constructed, validated, and reproducible. All context memory files are updated. The repository is cleanly tracked on GitHub while dataset files remain excluded.

## Recommended Next Step
Formulate the image download pipeline script to download the ~80,000 images specified in `data/baseline_sample_manifest.csv` and verify exact image storage requirements.

## Agent
Antigravity

## Date
2026-09-07



