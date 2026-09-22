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

---

## D012 — 2026-09-08 — Reproducible Baseline Experimental Protocol (`BP-6W-v1`)

**Decision:** Use the pre-registered protocol in `PROJECT_CONTEXT.md` for E002/E003/E004. It fixes the paired cohort, task, preprocessing, end-to-end fine-tuning, optimizer groups, training budget, evaluation, seed policy and logging before any model is implemented or trained.

**Core protocol decisions:**
- All three baselines use the identical verified paired cohort: `data/verified_paired_manifest.csv`, preserving **62,635 train / 6,685 validation / 6,675 test** rows. Text-only is deliberately restricted to this cohort for direct modality comparison.
- Primary task is 6-way, with official integer mapping 0 True, 1 Satire/Parody, 2 Misleading Content, 3 Imposter Content, 4 False Connection, 5 Manipulated Content. Loss is unweighted cross-entropy; primary selection and reporting metric is macro-F1.
- Stored `clean_title` is tokenized by `BertTokenizerFast` for `bert-base-uncased`, with a 128-token limit and dynamic padding. ResNet inputs are RGB ImageNet-normalized 224-pixel crops; no flip/colour augmentation is used because images may contain textual evidence.
- All encoders are fine-tuned from epoch 1. Training uses AdamW, fixed model-specific parameter groups, a target effective batch of 32, 10 maximum epochs, 10% linear warm-up/decay, gradient clipping, and early stopping by validation macro-F1.
- Three matched seeds (42, 43, 44) are required. Checkpoints are selected on validation macro-F1 only, then tested once per seed. Results are reported as three-seed mean ± standard deviation, not best-seed test performance.
- Canonical results should be run with CUDA AMP on cloud/T4/A100. RTX 3050 memory differences may alter only micro-batch and gradient accumulation while preserving effective batch 32; all such changes are logged.
- A later 2-way control is permitted only after the six-way baseline round. It retrains the same protocol on `2_way_label`; it cannot replace the primary task or be selected using test results.

**Rationale:**
- Fixed paired rows and split membership prevent differing image availability or text-only sample volume from confounding modality comparisons.
- Macro-F1, per-class scores and confusion matrices are necessary because Fakeddit's fine-grained labels are imbalanced. The original Fakeddit benchmark established 6-way multimodal evaluation; later temporal Fakeddit analysis shows fine-grained class behavior and distribution shifts require more than aggregate accuracy.
- TorchVision documents the selected ResNet-50 V2 weights, 224 crop, ImageNet normalization and approximately 25.6M parameters. Hugging Face documents dynamic padding/truncation behavior. PyTorch documents worker seeding and CUDA autocast/GradScaler for reproducible data loading and AMP.
- Model-specific encoder learning rates and decay preserve each encoder's fixed, pre-registered transfer-learning scale; equal effective batch, epochs, scheduler, early stopping, seeds and no-sweep rule preserve the shared comparison budget.

**Evidence:**
- Nakamura, Levy and Wang, *r/Fakeddit* (LREC 2020): benchmark precedent for 2-/3-/6-way paired text-image modelling and BERT + ResNet-50 maximum fusion.
- Stepanova and Ross, *Temporal Generalizability in Multimodal Misinformation Detection* (GenBench 2023): fine-grained imbalance and temporal degradation require macro and class-wise analysis.
- PyTorch reproducibility and AMP documentation; TorchVision ResNet-50 V2 documentation; Hugging Face padding/truncation documentation.

**Decided By:** Team-approved protocol research (Codex)

---

## D013 — 2026-09-22 — Advisor Feedback: Broaden Model Comparison Beyond BERT/ResNet-50

**Decision:** Expand the model comparison to include a CLIP-based multimodal experiment (E005) alongside the existing BERT and ResNet-50 baselines (E002/E003/E004). Keep HGAT as a later candidate (E006) pending verification that the required social/context graph data is available. No final research contribution is selected at this stage.

**Faculty directive:**
- BERT and ResNet-50 are common/popular models. They remain as baseline/control models but should not be the **only** models considered.
- Faculty pointed to semantically aligned text-image embeddings and HGAT from the discussed literature (including the SARD paper).
- Faculty specifically requested initial experimental values/metrics from actual training runs.

**Key constraints:**
1. **BERT and ResNet-50 are not discarded.** They remain essential baselines for controlled comparison.
2. **CLIP-based multimodal experiment is the immediate next practical model direction** after E002/E003/E004 baselines are trained.
3. **HGAT is a later candidate, NOT an immediate experiment.** HGAT requires social/context graph information (user networks, comment threads, propagation patterns) that is not currently present in our canonical Fakeddit paired cohort (`clean_title` + local image + `6_way_label`). Implementation is blocked until data availability is verified.
4. **No CLIP or HGAT implementation exists yet.** No code, configuration, or results have been produced for either model.
5. **Faculty-requested "initial values" must come from actual canonical CUDA runs**, not smoke-test losses, literature-reported numbers, or fabricated metrics.
6. **Final research contribution is NOT decided.** We are in the baseline/comparison stage.

**Terminology note:** The advisor referenced semantically aligned text-image embeddings in the discussed literature. The SARD paper uses the term "CLIP" (Contrastive Language-Image Pre-training, OpenAI). However, the exact wording from the faculty's screenshot/discussion has not been independently verified — it may say "CLIP", "LIP", or another exact term. **Working reference: CLIP.** The exact terminology must be confirmed with the advisor before implementation begins.

**Literature motivation (separated from our experimental results):**
- **CLIP** is used in recent multimodal fake-news work for semantic alignment between text and image representations. It produces jointly trained text-image embeddings via contrastive pre-training, unlike separately trained BERT + ResNet-50 encoders.
- **HGAT** is used in approaches such as SARD to model social/context relationships (users, comments, propagation). This is a fundamentally different capability from text-image fusion and requires graph-structured social data.
- These are literature descriptions only. They do not imply that either model has been tested on our Fakeddit cohort or that our results are comparable to published SARD numbers.

**What this decision does NOT authorize:**
- No protocol amendment to BP-6W-v1
- No change to the verified paired manifest or its 75,995-row cohort
- No silent replacement of ResNet-50 with another image encoder
- No change to the 6-way classification task
- No hyperparameter sweep beyond the pre-registered protocol
- No claim that CLIP or HGAT has already been implemented or tested

**Decided By:** Faculty/Advisor direction (2026-09-22)

---

## D014 — 2026-09-22/23 — Colab T4 Validation and Preliminary E002 Seed-42 Run

**Decision:** Record the successful Colab T4 environment setup, dataset verification, and preliminary E002 seed-42 training run. The preliminary result is NOT treated as the final canonical E002 baseline due to a detected scheduler-order issue.

**What was verified:**
1. Colab T4 GPU (Tesla T4, ~14.56 GB VRAM) successfully enabled.
2. Google Drive mounted; manifest and images.zip located and copied.
3. Manifest SHA-256 matched the locked expected hash.
4. 75,995 images extracted and verified (all convert to RGB; zero failures).
5. BERT GPU preflight passed on Tesla T4.
6. E002 seed-42 training completed successfully with CUDA AMP.

**Preliminary E002 seed-42 result (PRELIMINARY — scheduler issue):**
- Test Macro-F1: 0.6891, Test accuracy: 0.7790
- Validation Macro-F1: 0.7012 (selected epoch 4)
- Runtime: ~30.4 min, throughput: 286.4 samples/sec, peak memory: ~3.02 GB
- Full metrics in `results/experiments/e002_text/E002-bert-base-uncased-6way-BP6Wv1-s42-preliminary/preliminary_result.json`

**Scheduler-order issue:**
- Warning: `lr_scheduler.step()` called before `optimizer.step()`
- Impact: Learning rate schedule may not have been applied correctly
- **Required action:** Fix the ordering in `e002_text.py`, then rerun seed 42 before treating it as canonical
- Seeds 43/44 must not be run until the fix is verified

**What this does NOT authorize:**
- Treating the preliminary result as the final canonical E002 baseline
- Running seeds 43/44 before the scheduler fix
- Starting E003/E004/E005/E006
- Any protocol, manifest, or architecture change

**Decided By:** Verified from Colab session evidence (Antigravity)

---

## D015 — 2026-09-23 — Advanced Multimodal Model Directions After Baseline Round

**Decision:** The team will investigate stronger multimodal approaches after completing the baseline round (E002, E003, E004). The baseline/control model family remains BERT, ResNet-50, and BERT+ResNet-50, and they are not being discarded.

**Advanced Candidate Directions:**
1. CLIP / semantically aligned text-image representation
2. Contrastive learning for cross-modal alignment
3. Cross-attention / co-attention fusion
4. Adaptive / correlation-based fusion
5. Modality-decoupled or multi-expert fusion

**Terminology Note:**
- The current project uses "CLIP" as the working reference for the semantically aligned text-image direction. (Do NOT replace with "CLAP" without explicit verification).
- CLIP represents a concrete model family, semantic alignment represents a strategy, and contrastive learning represents a training objective. They should not automatically be treated as entirely separate implementations.
- HGAT remains a separate future investigation because it requires social/context graph data that is not currently verified for our canonical paired cohort.

**Research Strategy:**
- We do NOT commit to implementing every candidate.
- We will complete the baseline round first: E002 → E003 → E004.
- Then analyze overall Macro-F1, per-class F1, confusion matrices, modality-specific failures, computational cost, and robustness.
- Based on this analysis, we will select one or more advanced directions for deeper experimentation.
- The final research contribution is NOT yet decided.

**Decided By:** Team discussion / Faculty alignment (2026-09-23)
