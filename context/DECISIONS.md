# DECISIONS LOG — Multimodal Fake News Detection

> Record important project decisions and rationale here.
> Format: Date, Decision, Rationale, Decided By

---

## D001 — 2026-09-07 — Dataset Selection: Fakeddit

**Decision:** Use Fakeddit as the primary dataset.

**Rationale:**
- Over 1 million multimodal samples (text + image)
- Supports 2-way, 3-way, and 6-way classification
- Publicly available with clear usage guidelines
- Established benchmark with published baselines (LREC 2020)
- Includes `has_image` column for filtering multimodal samples
- Active research community using this dataset

**Decided By:** Team (project specification)

---

## D002 — 2026-09-07 — Initial Modality Scope: Text + Image Only

**Decision:** Restrict initial implementation to text + image modality only.

**Rationale:**
- Aligns with Fakeddit's core multimodal design
- Keeps the project manageable within 3–5 months
- Video, AI-generated content, and other modalities are future extensions only
- The original Fakeddit paper's experiments used text + image

**Decided By:** Team (project specification)

---

## D003 — 2026-09-07 — Baseline-First Approach

**Decision:** Establish text-only, image-only, and text+image baselines before attempting any improvement.

**Rationale:**
- Cannot identify genuine research gaps without understanding baseline performance
- Need to analyze where the baseline fails before proposing improvements
- Prevents premature optimization or unfounded claims
- Standard scientific methodology

**Decided By:** Team (project specification)

---

## D004 — 2026-09-07 — Project Structure and Shared Context System

**Decision:** Use `context/` directory with PROJECT_CONTEXT.md, DECISIONS.md, and EXPERIMENT_LOG.md as shared memory across all AI agents and team members.

**Rationale:**
- Multiple AI tools (Claude Code, Codex, Antigravity, etc.) may be used
- Need a single source of truth that any agent can read
- Prevents conflicting information or duplicated work
- Standard practice for multi-agent collaboration

**Decided By:** Team (project specification)

---

## D005 — 2026-09-07 — Do Not Download Full Images Immediately

**Decision:** First inspect TSV metadata to determine multimodal sample counts and storage requirements before downloading the full image archive.

**Rationale:**
- Full image archive could be very large (tens of GB)
- MacBook Air has only 512 GB total storage
- May only need a subset for initial baselines
- Need to understand data characteristics before committing storage

**Decided By:** Team (project specification)

---

## D006 — 2026-09-07 — Use Public Dataset Only

**Decision:** Use only the public train/validate/test splits. Do NOT use private test sets.

**Rationale:**
- Private test sets have no labels — useless for our experiments
- Following official dataset guidelines
- Academic integrity requirement

**Decided By:** Team (project specification)

## D007 — 2026-09-07 — First Baseline Image Subset

**Decision:** We will use a smaller subset (e.g. 50k-100k samples) of the multimodal dataset for the initial baseline rather than the full ~771k usable samples.

**Rationale:**
- The full image dataset for multimodal samples is estimated to be ~29.44 GB.
- While manageable on a 512 GB MacBook Air, training on ~771k images for initial baselines would be slow and computationally expensive.
- A balanced subset allows for faster iteration and debugging of the text+image pipeline.
- We will download only the required images for the chosen subset using the `image_url` column, or extract them from the archive later if needed.

**Decided By:** Antigravity (Data Strategy)

---

## D008 — 2026-09-07 — Baseline Stratified Sample Specification (80,000 Samples)

**Decision:** Formulate an 80,000-sample reproducible baseline manifest (`data/baseline_sample_manifest.csv`) split into 66,000 Train, 7,000 Validation, and 7,000 Test samples using `scripts/create_baseline_sample.py` with seed=42.

**Rationale:**
- 80,000 samples provide a highly representative sample size for training transformer + vision backbone baselines while drastically reducing image storage requirement to ~3.05 GB (estimated).
- Filtering strictly drops all 90,900 samples missing `clean_title` across splits, ensuring zero missing text features.
- Stratification on `6_way_label` preserves class distribution while maintaining split integrity across Train, Validation, and Test sets.
- Fixed seed (42) ensures 100% experiment reproducibility.

**Decided By:** Antigravity (Data Strategy)

---

## D009 — 2026-09-07 — Image Download Architecture and Validation Strategy

**Decision:** Use a multi-threaded, resumable download pipeline (`scripts/download_images.py`) restricted exclusively to the 80,000-sample baseline manifest. Each downloaded image is validated via PIL (`Image.open().verify()`) before saving as `{id}.jpg`.

**Rationale:**
- Directly maps file names to Fakeddit item `id` with zero naming conflicts.
- Atomic writes (`.tmp` -> `.jpg`) ensure interrupted downloads never leave corrupt image fragments.
- PIL decoding validation ensures unreadable/corrupt files or error web pages are not treated as valid images.
- Verification test on 100 images yielded 95% availability (95/100 HTTP 200, 5/100 HTTP 404, 0 corrupt).
- Actual average image size measured at **16.81 KB / image**, yielding an updated storage footprint of only **~1.28 GB** for all 80,000 images.

**Decided By:** Antigravity (Implementation)

---



## D010 — 2026-09-07 — Full 80K Image Download Completed (Resumed After Interruption)

**Decision:** Use the verified paired manifest (`data/verified_paired_manifest.csv`, 75,995 samples) as the canonical dataset for all baseline experiments. The original 80K manifest remains unchanged for reference.

**Rationale:**
- Full download was interrupted at 26,837 images; resumable pipeline successfully recovered without data loss or re-downloading valid files.
- Final success rate: 94.99% (75,995 / 80,000). Failures are primarily expired Reddit CDN links (HTTP 404, 96.5% of failures).
- All 75,995 images verified with PIL; 1:1 ID mapping confirmed.
- Actual storage: 7.822 GB (significantly higher than 100-sample test estimate of ~1.28 GB due to full-dataset size variance).
- 4,005 failed samples documented individually in `results/download_failures.json` — not silently discarded.

**Decided By:** Cursor (Composer)

---

## D011 — 2026-09-08 — Initial Baseline Architecture and Evaluation Setting

**Decision:** Establish the following initial baselines on the canonical verified paired manifest (75,995 samples), without implementation or training yet:

1. **Text-only:** fine-tuned `bert-base-uncased` with a linear classification head.
2. **Image-only:** fine-tuned ImageNet-pretrained ResNet-50 with a linear classification head.
3. **Text+image:** the same BERT-base and ResNet-50 encoders; project their representations to a common dimensionality, apply element-wise maximum fusion, then use a small MLP classifier.
4. **Initial label setting:** 6-way classification. Choose checkpoints by validation macro-F1 and report macro-F1, per-class metrics and a confusion matrix; accuracy/micro-F1 are supplementary.

**Rationale:**
- The original Fakeddit paper reported BERT + ResNet-50 with maximum fusion as its best simple multimodal combination, and ResNet-50 as the strongest of its tested image encoders.
- BERT-base (110M parameters) is a strong, standard open encoder but is more feasible than BERT-large for repeated 80K-subset experiments. ResNet-50 is about 26M parameters. Their combined size is feasible on a T4/A100 with mixed precision and conservative batches, while retaining a lower-compute path on MPS/RTX 3050.
- Maximum fusion is deliberately simple and documented; it does not prematurely treat a cross-modal interaction mechanism as the proposed contribution. More complex CLIP/ViT/attention models remain later comparison or improvement candidates.
- Six-way classification preserves Fakeddit's fine-grained task and exposes minority-class and modality-specific failures. The manifest is already stratified on this label. Published Fakeddit analysis found that the small 3-way intermediate class behaved similarly to 2-way; 6-way is more diagnostic but imbalanced.

**Constraints and safeguards:**
- Do not alter the 80K manifest, download more data, or use metadata/comments/private labels.
- Keep the official split membership fixed; use only `clean_title`, the local paired image, and the chosen label.
- Do not compare numerical results with papers unless split, subset, label setting, paired-image availability, and metric all match.
- Treat the released/random Fakeddit split as in-domain performance only. A temporal or held-out-subgroup test is later robustness evaluation, not a replacement for this baseline.

**Evidence:**
- Nakamura, Levy and Wang, *r/Fakeddit* (LREC 2020), official paper: BERT + ResNet-50 with maximum fusion was its best simple multimodal combination across 2-, 3- and 6-way tasks; it excluded items lacking text or image.
- Stepanova and Ross, *Temporal Generalizability in Multimodal Misinformation Detection* (GenBench 2023): Fakeddit is increasingly imbalanced at finer granularity, 3-way behaved similarly to 2-way in their analysis, and temporally out-of-domain evaluation materially reduced F1.
- Tahmasebi et al., *Improving Generalization for Multimodal Fake News Detection* (ICMR 2023): high standard-test performance did not ensure robustness under realistic content manipulations.
- Kuntur et al., *Fake News Detection: It's All in the Data!* (Applied Sciences 2026): dataset design, labeling and bias shape reported fake-news performance and comparability.

**Decided By:** Team-approved research decision analysis (Codex)
