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
  - **Estimated Storage:** ~3.05 GB (reference estimate based on 40KB/image).

