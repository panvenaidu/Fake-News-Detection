# EXPERIMENT LOG — Multimodal Fake News Detection

> Record actual experiments, configurations, results, observations, and conclusions here.
> Do NOT record invented or hypothetical results.
> Format: Experiment ID, Date, Description, Configuration, Results, Observations

---

## Status

No experiments have been run yet. The project is in Phase 1 (Understanding).

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

### E001 — Data Exploration
- **Date:** 2026-09-07
- **Goal:** Inspect TSV files, count samples, analyze label distribution, identify multimodal samples
- **Configuration:** Python script (`scripts/dataset_analysis.py`) analyzing `all_train.tsv`, `all_validate.tsv`, `all_test_public.tsv`
- **Results & Observations:**
  - **Sample counts:** 878,218 train / 92,444 val / 92,444 test (total ~1.06M).
  - **Multimodal (`hasImage=True` and valid URL):** 637,564 train / 67,035 val / 67,099 test (Total: 771,698 usable multimodal samples).
  - **Missing Values:** `clean_title` has 75,429 missing values in train. This must be handled (likely filtered out) during dataset creation.
  - **Labels:** 2-way, 3-way, 6-way labels have 0 missing values.
  - **Imbalance:** 6-way label is highly imbalanced (e.g. class 4 is 242k, class 3 is 11k in train).
  - **Storage:** ~29.44 GB estimated for the full multimodal image subset. Recommend using a balanced subset of 50k-100k for initial baseline.
