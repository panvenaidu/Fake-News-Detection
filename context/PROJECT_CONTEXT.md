<!-- TEXT-COMPLETE-v1 LIVE -->
## BERT completion execution — 9 October 2026

Saved Kaggle version356721456 is actively processing the recovered BERT training. Installed Torch2.11.0+cu128 passed the persistent-worker, exact suffix/next-epoch and CPU optimizer/AMP gates. Input hashes passed; original epoch5/batch15000 and counter state restored. Next IDs84p7pu/3nue2v/2nfbs2 verified; finite resumed loss0.1882; training advanced through batches15001,15500 and16000. GPU TeslaT4, Python3.13.15; one trainer device exposed despite T4x2 allocation. Original selected epoch4 remains unchanged until new validation. Final test pending; ModernBERT not launched.

Continue observing this exact saved job. Finish remaining epoch5, then epoch6 or the registered early-stop rule. Keep original input checkpoint as durable fallback; new Kaggle working checkpoints become durable only after saved outputs are verified. Freeze validation-selected weight hash, export full validation/test evidence, retrieve weights and independently verify metrics/IDs before claiming completion.

Evidence: `results/text_completion_execution_20261009.json`; plan `context/TEXT_COMPLETION_PLAN_20261009.md`. The user has authorized execution. Historical entries below retain earlier observations.
<!-- /TEXT-COMPLETE-v1 LIVE -->

## Latest handoff - 9 October 2026: text completion plan ready

Read `context/TEXT_COMPLETION_PLAN_20261009.md` first. User requested a detailed GPT-6 Sol handoff and will approve execution next. This session audited data/code/evidence and saved a plan; no GPU training or final test was run. All official TSVs were rescanned and saved weight hashes reverified. Kaggle inspection: no active jobs, draft off, quota 00:06 / 30h used (about 29h54m remaining at observation).

**New prerequisite:** original mid-epoch resume changes sample order when fresh workers consume the sampler generator. CPU reproduction and actual checkpoint RNG inspection confirmed the mismatch. Saved weights are intact; repair and verify resume ordering before running the prepared recovery notebook. Also make a BERT-only job and export the missing full validation prediction CSV. Preserve original source/config/history; record versioned recovery changes. See `results/text_resume_order_diagnostic_20261009.json` and `results/TEXT_COMPLETION_PLAN_AUDIT_20261009.json`.

**Usage reserve:** start syncing around 25% remaining; at 20% start no new experiment and use the reserve to update all context/log/status files and safely commit/push. Leave a healthy submitted cloud job running independently; record its exact state and durable outputs. Do not imply local/GitHub updates happen while the agent is inactive. Latest planning check: 24% five-hour / 57% weekly remaining; finish documentation and handoff now.

Progress unchanged: BERT73%, full text+image40%, image-only20%, overall44%; multimodal pilot100% separately. BERT has five observed training/validation epochs, saved epoch5 batch15000, final test pending. A later approval to execute the saved plan authorizes its implementation and training sequence. Earlier entries below are historical where they conflict with this note.

**Progress-display preference:** When the user asks how much is completed, show loading bars and the five checkpoint states from `results/PROGRESS_TRACKER.json` / `results/PROGRESS_TRACKER.md`. Refresh using verified artifacts. These are equally weighted workflow stages, not accuracy or elapsed-time percentages. Keep the completed small multimodal pilot separate from the full benchmark. Current bars: BERT73%, full text+image40%, standalone image-only20%, overall44%; ModernBERT comparison40% prepared. Recovery files are stored in data/cloud_recovery/. Original BERT tensor verified at epoch5 batch15000/17625 (epoch unfinished); replay remaining epoch5 batches before proceeding. Full multimodal prediction CSVs/original archive now synced and verified. No GPU job currently running.

## Current state — 8 October 2026, completed multimodal pilot

**Text-only, official full cohort:** BERT-base completed five training/validation epochs. Selected epoch4 has validation accuracy **82.7407%** and Macro-F1 **77.8682%**. Epoch5 accuracy **82.8031%**, Macro-F1 **77.8388%** did not replace the selected checkpoint. The trainer failed writing recovery metadata at the end of epoch5; Colab GPU allocation is blocked by usage limits. **Final test pending. ModernBERT not started.** Original five-epoch history is retrieved. Original tensor integrity is verified at epoch5 batch15000/17625, before epoch completion; resume will replay the remaining2625 batches of epoch5. Verification: `results/bert_recovery_verification.json`. No BERT recovery job is currently running.

**Text+image, engineering pilot:** BERT-base + ResNet-50 maximum fusion **completed three GPU epochs and a final test** on Kaggle version2, scriptVersionId356486031. Pilot: **2,000 train / 300 validation / 300 test**, all six classes, unchanged official split membership. Selected epoch3: validation **79.33% accuracy / 59.62% Macro-F1**; test **74.33% accuracy / 55.90% Macro-F1**. 188 optimizer updates, one AMP skip; 297.9-second notebook run. Original metrics, history, class reports, confusion matrices and GPU environment are synced to `results/experiments/multimodal/MM-PILOT-6W-v1_seed42_20261009/`; weights/checkpoints remain preserved in the private saved Kaggle output. All300 validation and300 test original predictions are now synced locally and verified against the official pilot IDs/labels. This is **not an official full-cohort benchmark**, not “50% of training”, and not evidence of outperforming the paper. Imposter test F1 is zero on six examples.

**Next:** privately attach the verified recovery archive and `data/cloud_recovery/recovery_verification.json` to Kaggle, then use `notebooks/UROP_KAGGLE_TEXT_RECOVERY_20261009.ipynb` to resume the unchanged original text protocol. It finishes BERT before ModernBERT; preserve the original Colab environment plus Kaggle resume environment. Do not rerun the completed multimodal pilot. `results/FACULTY_STATUS_20261009.md` is the short faculty summary. The earlier entries below describe historical observations and are superseded by this current section.

# PROJECT CONTEXT — Multimodal Fake News Detection

> **Last Updated:** 2026-09-22
> **Updated By:** Antigravity

---

## Project Overview

**Title:** Multimodal Fake News Detection Using Text + Image

**Team:**
- **Panvee** — Coding, implementation, model development, training, experiments
- **Karthik** — Literature review and research paper
- **Third Member** — Weekly reports, documentation, presentations, meeting records

**Duration:** 3–5 months (minimum core work in 3 months)

**Reference Paper:** "Fake News Detection: It's All in the Data!" (Applied Sciences, 2026)

**Primary Dataset:** Fakeddit (https://fakeddit.netlify.app/)

**Modality Scope:** TEXT + IMAGE only (no video, no AI-generated content in initial scop## Current Phase

**Phase 1 — UNDERSTAND** (In Progress)

- [x] Inspect official Fakeddit repository
- [x] Inspect official Fakeddit website
- [x] Determine data download structure
- [x] Create project directory structure
- [x] Create initial context files
- [x] Download TSV metadata files
- [x] Inspect TSV columns and sample counts
- [x] Determine multimodal sample counts (`hasImage == True`)
- [x] Estimate image storage requirements
- [x] Decide on practical baseline dataset size
- [x] Create reproducible stratified baseline sample manifest (80,000 samples)
- [x] Download and verify 80,000 baseline images (75,995 verified paired samples)
- [ ] Read reference paper in detail
- [x] Focused baseline-architecture decision review (primary sources plus relevant 2023–2026 work)
- [ ] Broader literature review (recent multimodal fake news work)

---

## Dataset: Fakeddit

### Source
- **Paper:** Nakamura, Levy, Wang (LREC 2020). "r/Fakeddit: A New Multimodal Benchmark Dataset for Fine-grained Fake News Detection"
- **ArXiv:** https://arxiv.org/abs/1911.03854
- **Website:** https://fakeddit.netlify.app/
- **Repository:** https://github.com/entitize/Fakeddit

### Key Facts (from official sources)
- Over 1 million samples from Reddit
- Supports **2-way**, **3-way**, and **6-way** classification
- Contains: text (clean_title), metadata, comments (coming soon), images
- TSV format with tab-separated columns
- `hasImage` column distinguishes multimodal (text+image) from unimodal (text-only) samples
- Original paper experiments used **multimodal-only** samples (`hasImage == True`)
- `image_url` column contains URLs for downloading images
- Images also available as a single archive from Google Drive

### Classification Labels

**2-way:** True, Fake

**3-way:** Completely true, Not enough info (satire/misleading), Definitely false/fake

**6-way:** True, Satire/Parody, Misleading Content, Imposter Content, False Connection, Manipulated Content

### Data Download Links
- **TSV/Metadata (v2.0):** https://drive.google.com/drive/folders/1jU7qgDqU1je9Y0PMKJ_f31yXRo5uWGFm?usp=sharing
- **Images (recommended, single archive):** https://drive.google.com/file/d/1cjY6HsHaSZuLVHywIxD5xQqng33J5S2b/view?usp=sharing
- **Images (alternative):** Use `image_url` column in TSVs with the provided `image_downloader.py` script
- **Private test set (text):** https://drive.google.com/file/d/1ExPiA_v2Dq_rG6afY4rvgUV-Jh9ByiTI/view?usp=sharing (DO NOT USE for our research — no labels)
- **Private test set (images):** https://drive.google.com/file/d/1YtvM2Muf4hT0SCALI7FaILaGPJdW7lW1/view?usp=sharing (DO NOT USE)

### Official Usage Guidelines (from Fakeddit website — Challenge section)
1. Only use the `6_way_label` and the `clean_title` columns from the public dataset.
2. Do not use additional paired text/image data.
3. Do not attempt to extract ground truth labels from the Internet.
4. Disregarding these guidelines is unethical and will not help future research.

> **Note:** The challenge guidelines restrict feature columns for the competition leaderboard. For our research (not the competition), we may use other public metadata columns (e.g., `hasImage`, `image_url`, `2_way_label`, `3_way_label`), but we must NOT use private test labels or scrape extra labels.

### Verified TSV Columns
- `clean_title` — missing values exist (dropped 90,900 missing title samples across splits)
- `2_way_label`, `3_way_label`, `6_way_label` — all 0 missing values
- `hasImage` — boolean/int (`True`/`1`), 0 missing
- `image_url` — missing values exist (filtered out)
- `id` — unique identifier (0 duplicates across all splits)
- Additional metadata columns (`author`, `domain`, `score`, `subreddit`, `upvote_ratio`, etc.)

### Train/Validation/Test Structure & Baseline Manifest
- Files: `all_train.tsv`, `all_validate.tsv`, `all_test_public.tsv` located in `data/Fakeddit datasetv2.0/all_samples (also includes non multimodal)/`
- Baseline Manifest: `data/baseline_sample_manifest.csv` generated by `scripts/create_baseline_sample.py` (seed=42)
- **Sample Distribution:**
  - **Train:** 66,000 samples
  - **Validation:** 7,000 samples
  - **Test:** 7,000 samples
  - **Total Baseline Subset:** **80,000 samples**

### Image Download Status (Completed 2026-09-07)
- **Baseline manifest:** `data/baseline_sample_manifest.csv` — 80,000 samples (unchanged)
- **Verified paired manifest:** `data/verified_paired_manifest.csv` — **75,995 samples** with confirmed valid images
- **Images directory:** `images/` — 75,995 verified `{id}.jpg` files (gitignored)
- **Download success rate:** 94.99% (4,005 failures, primarily HTTP 404 on expired Reddit CDN links)
- **Actual storage used:** **7.822 GB** (8,398,948,245 bytes)
- **Actual average image size:** **107.93 KB / image** (higher than 100-sample test due to full-dataset variance)
- **Failure log:** `results/download_failures.json` (4,005 entries)
- **Final report:** `results/download_final_report.json`
- Note: Original download was interrupted at 26,837 images; resumed successfully without data loss.

### Storage Estimates
- TSV files: ~276 MB total
- Baseline 80K verified images (actual): **7.822 GB**
- Full 771k image set (projected at ~108 KB/image): **~80 GB**

---

## Working Hypothesis


> **Improve multimodal fake-news detection so that it is more robust to unseen/different data while remaining computationally efficient.**

This is a working hypothesis only. The final research contribution will be decided after baseline experiments and failure analysis (Phase 4).

---

## Hardware

| Machine | OS | GPU | RAM | Storage |
|---|---|---|---|---|
| MacBook Air M3 | macOS | Apple Silicon (MPS) | 16 GB | 512 GB |
| Windows laptop | Windows | NVIDIA RTX 3050 | TBD | TBD |
| Cloud | Colab / CoCalc | T4/A100 (Colab) | Varies | Varies |

## Baseline Architecture Decision (2026-09-08)

The following initial baselines have been selected. E002 is implemented and
smoke-tested only; no baseline has been canonically trained.

| Setting | Selected baseline | Rationale |
|---|---|---|
| Text-only | `bert-base-uncased` (110M parameters) with a linear classifier | Standard open English encoder; practical for repeated runs and directly isolates `clean_title`. |
| Image-only | ImageNet-pretrained ResNet-50 (about 26M parameters) with a linear classifier | Mature, compute-efficient vision backbone. The original Fakeddit study found it stronger than its tested VGG16 and EfficientNet image alternatives. |
| Text + image | BERT-base + ImageNet-pretrained ResNet-50; project representations to equal width, take an element-wise maximum, then use a small MLP classifier | Mirrors the strongest simple fusion family reported in the original Fakeddit paper while remaining transparent and reproducible. |

**Initial task:** 6-way Fakeddit classification. Select checkpoints by validation macro-F1 and report macro-F1, per-class precision/recall/F1, confusion matrix, and accuracy/micro-F1 as supplementary metrics. Use only the fixed official split membership in `data/verified_paired_manifest.csv` (75,995 paired items).

**Compute expectation (not benchmarked):** BERT-base + ResNet-50 is about 136M backbone parameters. It is practical on a Colab T4/A100 with mixed precision and conservative batches (roughly 8–16 as a starting range), suitable for M3/MPS debugging, and likely feasible on the RTX 3050 with small batches plus gradient accumulation. Exact VRAM and throughput must be measured in the first approved run.

**Evaluation caveat:** Fakeddit's labels are distant/subreddit-level and its released split is not a robustness test. Later work should add a temporal or held-out subgroup/domain-shift evaluation without replacing this initial benchmark.

## Baseline Experimental Protocol (2026-09-08)

**Protocol ID:** `BP-6W-v1`. This is a pre-registered baseline protocol, not an implementation or result.

### Common cohort and task

- Use `data/verified_paired_manifest.csv` only, for **all** E002/E003/E004, preserving its `split` column: **62,635 train / 6,685 validation / 6,675 test** (75,995 total). Do not resample, reshuffle split membership, or admit items outside the verified manifest.
- Use `clean_title`, the local `image_path`, and `6_way_label` only. Lock the official mapping: 0 True, 1 Satire/Parody, 2 Misleading Content, 3 Imposter Content, 4 False Connection, 5 Manipulated Content.
- The manifest already has no blank titles or duplicate IDs. Before every run, validate that every listed image exists and decodes as RGB. A failure aborts the run; samples must never be silently skipped or removed for one model only.
- Use unweighted cross-entropy loss and no resampling. Report macro-F1 rather than attempting to hide the class imbalance through accuracy alone.

### Shared training and evaluation rules

- Fine-tune all selected pretrained encoders end-to-end from epoch 1; do not freeze them. Use AdamW, betas `(0.9, 0.999)`, epsilon `1e-8`, gradient-norm clipping at 1.0, and no weight decay on bias or normalization parameters.
- Maximum 10 epochs. Evaluate validation data after every epoch. After at least 3 epochs, stop after two consecutive epochs without a validation macro-F1 gain of at least 0.001.
- Use a linear schedule with 10% warm-up of the planned optimizer-update steps and linear decay to zero. The test split is evaluated only from the validation-selected checkpoint.
- Run exactly three seeds: **42, 43, 44**. Select the best epoch per seed by validation macro-F1; ties use lower validation loss, then the earlier epoch. Report mean and standard deviation over the three test runs, never the best test seed alone.
- Primary metric: test macro-F1. Also report accuracy, balanced accuracy, weighted-F1, per-class precision/recall/F1/support (with `zero_division=0`), and raw plus row-normalized 6x6 confusion matrices.
- CUDA canonical runs use `torch.amp.autocast("cuda", float16)` plus `torch.amp.GradScaler("cuda")`. The M3/MPS machine is for development/smoke checks unless a CUDA device is unavailable; canonical numbers must state device and precision.

### Fixed model settings

| Experiment | Input/model-specific settings | AdamW learning rates | Weight decay | T4/A100 micro-batch and accumulation |
|---|---|---|---|---|
| E002 | `BertTokenizerFast`/`bert-base-uncased`; stored `clean_title`; truncation at 128 tokens including special tokens; dynamic batch padding; BERT classifier dropout 0.2 | BERT and head `2e-5` | 0.01 | 32 × 1 |
| E003 | RGB image; train `RandomResizedCrop(224, scale=(0.8,1.0), ratio=(0.75,1.333), bilinear, antialias=True)`, no horizontal flip or colour augmentation; validation/test `Resize(232, bilinear, antialias=True)` then `CenterCrop(224)`; ImageNet V2 mean/std; ResNet-50 IMAGENET1K_V2; classifier dropout 0.2 | ResNet and head `1e-4` | `1e-4` | 32 × 1 |
| E004 | The identical text/image pipelines; BERT CLS 768→512 and ResNet pooled 2048→512 linear projections, each LayerNorm; element-wise maximum; `512→256→6` MLP with GELU and dropout 0.2 | BERT `2e-5`; ResNet `1e-4`; new projection/MLP `1e-3` | BERT/new layers 0.01; ResNet `1e-4` | 8 × 4 |

The target effective batch size is **32** for every optimizer update. On the RTX 3050, begin with E002 `8×4`, E003 `16×2`, E004 `4×8`; if memory requires a smaller micro-batch, increase accumulation to preserve 32 and record the change. This is a hardware adaptation, not a hyperparameter search.

### Fairness, reproducibility and logging

- `BP-6W-v1` permits no per-model hyperparameter sweep. Any future tuning requires a protocol amendment, validation-only selection and the same documented search budget for every baseline.
- Seed Python, NumPy and PyTorch; use deterministic algorithms where supported, deterministic cuDNN, `benchmark=False`, seeded DataLoader generator and seeded workers. Exact replication is only claimed within the recorded software/hardware environment.
- Save an immutable resolved config, code commit, manifest SHA-256 and split/class counts, package versions/`pip freeze`, model and weights revisions, preprocessing, seed, device/VRAM/driver, AMP state, trainable/total parameter counts, epoch metrics, selected checkpoint, wall time, samples/sec, peak GPU memory and any OOM/non-finite event.
- Name runs `E00X-<model>-6way-BP6Wv1-s<seed>`; keep test predictions and confusion matrices tied to that run ID.

**2-way control:** after all 6-way E002/E003/E004 runs are complete and recorded, a requested control round may retrain the same three models on `2_way_label` with the same manifest, split, preprocessing, seeds, update budget and per-model optimizer groups; only the output dimension and label column change. It is not used to choose the research gap or replace the primary six-way analysis.

## E002 Implementation Status (2026-09-08)

- **Implemented:** reusable verified-manifest validation, deterministic text datasets/DataLoaders, the end-to-end `bert-base-uncased` pooled/CLS classifier with 0.2 dropout, AdamW parameter groups, linear warm-up/decay, gradient clipping, validation checkpoint ranking, BP-6W-v1 early stopping, required metrics/confusion-matrix artifacts, per-run metadata/error logging, and canonical CUDA-only training entry point.
- **Frozen configuration:** `configs/e002_text_bp6w_v1.json` locks the verified manifest SHA-256 (`fc74cb42288d366131ac764bf02f9212bacd7cab0af68442a003beaaff9fde20`), split counts, all BP-6W-v1 E002 values, approved seeds, and the resolved public `bert-base-uncased` revision `86b5e0934494bd15c9632b12f734a8a67f723594`.
- **Smoke test:** passed on CPU as a non-canonical implementation check only. It loaded the fixed manifest, validated two paired images, used a two-item dynamic-padded batch (shape `[2, 34]`), completed forward/loss/backward/optimizer/checkpoint-write steps, and removed the 438,028,532-byte smoke checkpoint after verification. It produced no training, validation, or test metric.
- **Environment:** the Mac reports PyTorch 2.8.0 with CUDA unavailable and MPS unavailable. Missing local `transformers` and `scikit-learn` dependencies were installed only in `/private/tmp/e002-deps` for smoke verification; project requirements now declare the E002 deep-learning dependencies. Canonical E002 execution remains blocked pending CUDA.
- **Scope guard:** E003 and E004 have not been implemented or run. The 80,000 source manifest and 75,995-row verified paired manifest were not modified.

## E002 Colab Training Status (2026-09-22/23)

- **Colab T4 setup:** Successfully configured. Tesla T4, ~14.56 GB VRAM, CUDA AMP enabled.
- **Dataset preparation:** Manifest and images copied from Google Drive, verified (75,995 images, SHA-256 match, all images convert to RGB).
- **Full image preflight:** Passed. Image modes: RGB=73,549, RGBA=196, P=2,123, L=122, CMYK=5. Zero RGB conversion failures.
- **BERT GPU preflight:** Passed on Tesla T4.
- **Preliminary seed-42 run:** Completed on Colab T4. **⚠️ PRELIMINARY — scheduler-order issue detected.**
  - Warning: `lr_scheduler.step()` called before `optimizer.step()`.
  - The learning rate schedule may not have been applied correctly.
  - Test Macro-F1: 0.6891 (preliminary), Test accuracy: 0.7790 (preliminary).
  - Full preliminary metrics preserved in `results/experiments/e002_text/E002-bert-base-uncased-6way-BP6Wv1-s42-preliminary/preliminary_result.json`.
  - This result must be **rerun after correcting the scheduler order** before being treated as the final canonical E002 baseline.
- **Seeds 43/44:** Not yet run.
- **Machine-generated artifact:** No raw JSON artifact was synced from Colab to the local Git repository. The preserved preliminary result file was reconstructed from observed Colab output.

---

## Advanced Model Research Direction

Baseline:
- BERT (E002)
- ResNet-50 (E003)
- BERT+ResNet-50 (E004)

Advanced candidates after baseline:
- CLIP / semantic alignment
- Contrastive learning
- Cross-attention/co-attention
- Adaptive/correlation fusion
- Modality-decoupled/multi-expert fusion

Later candidate:
- HGAT (if required graph/social data is verified)

We will not choose the final advanced method before observing baseline behaviour. No advanced method has been implemented or tested yet.

### Current Model Status Summary

| Experiment | Model | Role | Status |
|---|---|---|---|
| E002 | BERT text-only | Baseline | ✅ Implemented, ✅ smoke-tested, ⚠️ preliminary seed-42 (scheduler issue, rerun needed) |
| E003 | ResNet-50 image-only | Baseline | ❌ Not implemented |
| E004 | BERT + ResNet-50 multimodal | Baseline | ❌ Not implemented |
| E005 | CLIP-based multimodal | Stronger comparison | ❌ Not implemented, architecture not frozen |
| E006 | HGAT social-context | Future investigation | ❌ Blocked pending data verification |

---

## Initial Metrics Goal

The faculty has requested initial experimental values. These are the metrics that must be collected from **actual canonical CUDA training runs** under protocol `BP-6W-v1`:

**Per model (E002, E003, E004), per seed (42, 43, 44):**
- Validation loss (per epoch)
- Validation Macro-F1 (per epoch, used for checkpoint selection)
- Test Macro-F1 (from validation-selected checkpoint only)
- Accuracy
- Balanced accuracy
- Weighted-F1
- Per-class precision / recall / F1 / support
- Raw 6×6 confusion matrix
- Row-normalized 6×6 confusion matrix
- Training wall time
- Throughput (samples/sec)
- Peak GPU memory
- Total / trainable parameter count

**Aggregation:** three-seed mean ± standard deviation. No best-test-seed reporting.

**Guardrails:**
- Do NOT report the E002 CPU smoke-test loss (`2.6260`) as a performance result
- Do NOT import literature-reported accuracy into our results tables
- Do NOT fabricate any metric value
- Do NOT mix paper-reported numbers with our experimental results as though they are directly comparable

---

## Experimental Priority

### Phase A — Baselines (Immediate)

Run in this order:

1. **E002 — BERT text-only canonical training** (seeds 42, 43, 44)
   - Implementation: ✅ complete
   - Config: `configs/e002_text_bp6w_v1.json`
   - Runner: `scripts/run_e002.py`
   - Status: ⚠️ preliminary seed-42 complete with scheduler-order issue; **fix scheduler then rerun seed 42, then run 43/44**

2. **E003 — ResNet-50 image-only** (seeds 42, 43, 44)
   - Implementation: ❌ pending
   - Protocol settings: fixed in BP-6W-v1 (see protocol section above)
   - Status: pending implementation then training

3. **E004 — BERT + ResNet-50 multimodal** (seeds 42, 43, 44)
   - Implementation: ❌ pending
   - Protocol settings: fixed in BP-6W-v1 (see protocol section above)
   - Status: pending implementation then training

### Phase B — Stronger Multimodal Comparison

4. **E005 — CLIP-based multimodal experiment**
   - Architecture: not yet frozen; requires design review
   - Working reference: OpenAI CLIP (exact advisor terminology to be confirmed)
   - Cohort: same `data/verified_paired_manifest.csv` (75,995 paired samples)
   - Protocol: BP-6W-v1 evaluation rules apply; model-specific training settings TBD
   - Status: ❌ planned, not implemented

### Phase C — Future Investigation

5. **E006 — HGAT social-context model**
   - Prerequisite: verify that Fakeddit provides user/comment/propagation graph data compatible with our cohort
   - If data is unavailable, HGAT cannot be implemented on the current setup
   - Status: ❌ future, blocked pending data availability verification

---

## Repository Structure

```
project/
├── context/              # Shared project memory
│   ├── PROJECT_CONTEXT.md
│   ├── DECISIONS.md
│   ├── EXPERIMENT_LOG.md
│   └── TASK_REPORT.md
├── collab/               # Colab operational history
│   └── COLAB_WORKLOG.md
├── work_logs/            # Troubleshooting and model status
│   ├── TROUBLESHOOTING.md
│   └── MODEL_STATUS.md
├── src/                  # Source code
├── scripts/              # Utility scripts
│   ├── dataset_analysis.py
│   ├── create_baseline_sample.py
│   ├── download_images.py
│   └── sync_results_to_git.sh
├── configs/              # Training/model configs
├── experiments/          # Experiment-specific files
├── results/              # Results, figures, tables (source of truth)
│   ├── dataset_analysis.json
│   ├── sampling_report.json
│   ├── download_final_report.json
│   ├── download_failures.json
│   └── experiments/      # Machine-generated experiment outputs
├── data/                 # Ignored by Git
│   ├── baseline_sample_manifest.csv
│   └── verified_paired_manifest.csv
├── images/               # Ignored by Git (75,995 verified images)
├── notebooks/            # Jupyter notebooks
├── docs/                 # Documentation
├── README.md
└── requirements.txt
```

---

## Blockers

- ~~The verified paired dataset is ready, but canonical E002 training is blocked on this Mac because neither CUDA nor MPS is available.~~ **Resolved:** A Colab T4 environment has been successfully enabled and used for a preliminary E002 seed-42 run. Google Drive is used for persistent data storage. The large image archive should be copied/extracted into the local Colab runtime for training (rather than reading file-by-file from slow Google Drive access). Exact Colab dataset paths must be verified before each training run.
- **⚠️ E002 scheduler-order issue:** The preliminary seed-42 run detected `lr_scheduler.step()` before `optimizer.step()`. This must be fixed in `e002_text.py` before final canonical E002 training.
- E003 and E004 are blocked on implementation (not yet written).
- E005 (CLIP) is blocked on architecture design review and implementation.
- E006 (HGAT) is blocked on verifying social/context graph data availability in Fakeddit.

---

## Next Steps

1. **Immediate:** The E002 scheduler-order bug has been corrected. No full retraining was performed during the fix task. The preliminary seed-42 result remains preliminary. A clean canonical seed-42 rerun is required. Then run seeds 43 and 44.
2. **Phase A — Baselines:** After E002 is complete, implement and run E003 (ResNet-50), then E004 (BERT+ResNet-50).
3. **Phase B — CLIP:** After baseline results are recorded, design and implement E005 CLIP-based multimodal experiment. Architecture must be reviewed and frozen before training.
4. **Phase C — HGAT:** Investigate whether Fakeddit provides the required user/comment/propagation graph data. Only proceed with E006 if data is verified.
5. Use observed class-wise and cross-model failures to select, rather than assume, a final research contribution. The contribution is NOT decided at this stage.


## 2026-10-08 14:50 IST — Setup/recovery checkpoint (current)

- User authorized local and GitHub checkpoint updates for every model, and confirmed Chrome-only training; Colab CLI fallback declined. No Colab CLI credentials were granted.
- Official dataset files and their hashes/counts are saved locally; full six-way cohort remains unchanged.
- BERT-base and ModernBERT-base trainer/notebook now save recoverable state every 3,000 batches and at epoch boundaries, including optimizer, scheduler, scaler, random generators, sampler position, history and selected checkpoint. `--resume-attempt` restores a named attempt and preserves completed models.
- Recovery batch ordering passed a CPU sampler check; script and notebook syntax checks passed. Cloud GPU execution/recovery has NOT been tested.
- Chrome application control continues to time out, and the direct Chrome browser provider is unavailable. Training is NOT verified as started; no official-v2 validation/test metrics exist. The prior cloud preflight verified Tesla T4 only.
- Account usage query: 34% remains in five-hour Codex window; reset 2026-10-08 17:35 IST. This is separate from Colab runtime lifetime and GPU limits.
- Next action: restore Chrome automation or upload `notebooks/UROP_OFFICIAL_6WAY_TEXT_20261008.ipynb` in Chrome Colab, select T4 and Run all; verify Drive mount, dataset hashes and the first actual optimizer steps. Preserve exact cloud ATTEMPT path.
- Then sync each model's small JSON/CSV/log evidence under `results/experiments/official_text/`, update these context/log/status files and push milestone documentation. Large TSVs, images and weights remain excluded from Git. Local/GitHub syncing requires a connected agent; cloud checkpoints write independently.


## 2026-10-08T09:39:18.215639+00:00 — Corrected cloud process launched

Pinned fixed source SHA256 `a13c0e5d97b2fe7661ce6a228d43d853f1aca703314cfa48688825b7b01701f9` loaded from pushed commit `9c7abf1`. Colab cell [16] visibly entered Executing state on Tesla T4. This verifies process launch only; first optimizer steps, current attempt folder, and metrics have not yet been observed. BERT runs first; ModernBERT remains queued. Live Chrome controls subsequently became unavailable. Do not rerun launch cells or replace data blindly: inspect current process/output and cloud status before deciding whether a recovery is needed. Latest machine-readable local status: `results/official_text_live_status.json`. Checkpoints write to Drive independently; local and GitHub synchronization needs a connected agent.


## 2026-10-08T09:45:49.174071+00:00 — Usage/recovery checkpoint

Last usage check: 6% remains; five-hour window resets 2026-10-08 17:35 IST. This supersedes the earlier 34% preflight reading. Latest source logging fix and recovery code are pushed. Current cloud training progress is unverified: cell 16 entered execution, but a later accessibility view showed 4 seconds elapsed without readable subprocess output. Do not claim active optimizer steps or metrics. Native Chrome controls/screenshots are unreliable/unavailable and the Chrome terminal has no usable prompt. User was asked to keep the Mac awake/unlocked with Chrome visible; Colab CLI fallback was explicitly declined. Preserve existing cloud attempts; inspect latest model status/error/checkpoint before any rerun. All scientific settings and dataset files remain unchanged.


## 2026-10-08T09:49:32.158683+00:00 — Final continuity checkpoint

All code/config/notebook, dataset provenance, audit, startup errors and current unverified launch state are saved. Checkpoint cadence is implemented (every 3,000 batches and each epoch), but no successful cloud weight checkpoint or optimizer updates have yet been verified. The last available Colab setup screenshot is `results/colab_setup_last_available.png`; it is not live training-progress proof. Attempts to create a continuation heartbeat failed schedule validation, so no automatic follow-up is active. Resume only after checking the existing cloud attempt; do not assume chat usage reset automatically resumes an agent. Chrome-only preference remains in force.


## 2026-10-08T10:03:25.864123+00:00 — Official BERT optimizer steps verified

Chrome Colab runtime recovered. A guarded notebook launch started PID 23054 with verified fixed source SHA256 a13c0e5d97b2fe7661ce6a228d43d853f1aca703314cfa48688825b7b01701f9. Active attempt: `OFFICIAL-6W-TEXT-v2_seed42_20261008T095827Z` in `/content/drive/MyDrive/Colab Notebooks/UROP/official_text_runs/`. Notebook: https://colab.research.google.com/drive/11JK1wLLVPH8G7_oThnb0YkLMSR4URafF. BERT epoch 1 reached batch 1,000/17,625, with 997 successful optimizer updates and 3 mixed-precision skipped updates, approximately 229.78 titles/second. Checkpoint not yet present at this observation; first is due at batch 3,000. ModernBERT remains queued. No official-v2 validation/test metrics exist yet. Prior cell 16 was interrupted; it is superseded by this verified active attempt. Browser editing produced malformed launch code before this guarded launch; those cells did not train. A repeated execution was blocked by the active-process guard, preventing duplicate training. Keep official splits and scientific settings unchanged; monitor status/checkpoints before any restart. Chrome-only requirement honored.


## 2026-10-08T10:24:48.790731+00:00 — Automatic continuation and restart safeguards

An hourly thread follow-up is now ACTIVE (automation id `complete-urop-text-training`), superseding earlier failed scheduling attempts. It inspects this existing cloud attempt, finishes authorized BERT/ModernBERT evaluations, recovers from checkpoints if needed, and synchronizes small evidence/context/GitHub milestones. It remains quiet when nothing meaningful changes. No paid compute authorization or Colab CLI access is granted. The local notebook and launch helper now inspect real cloud process arguments before starting, preserving the same scientific protocol and trainer source. Launch metadata and logs persist in Drive; a separate monitor displays checkpoint/validation/test progress. These local launch-cell changes have not been deployed over the currently running trainer and do not alter its source or results. Colab's resource panel reported zero purchased compute units and up to three hours of runtime at the observed usage level; continuation depends on actual GPU availability.


## 2026-10-08T10:46:10.624380+00:00 — First official full-cohort validation result

BERT epoch 1 validation: **81.07% accuracy**, **75.25% Macro-F1**, read from the Colab monitor's four-decimal rounded output at 10:43:43 UTC. This is an intermediate validation observation, not a final result. Epoch 2 batch 500 / 18,117 optimizer updates is running; recovery saved at the epoch-1 boundary (batch 17,625). ModernBERT is queued. Test has not been evaluated; full-precision original JSON/report/predictions must still be synchronized from Drive. Rounded observation saved at `results/experiments/official_text/OFFICIAL-6W-TEXT-v2_seed42_20261008T095827Z/bert-base/validation_epoch1_observed.json`. The experiment continues unchanged under the original validation-selection/early-stop protocol. Hourly automatic continuation is active; no paid compute or Colab CLI fallback authorized.


### Kaggle access and second BERT validation — 2026-10-08 16:57 IST
User authorized Kaggle as an additional compute provider. Existing Kaggle account rocky62 signed in through panvee62 Google sign-in. Settings show GPU 00:00 / 30 hrs, but account is phone-unverified. Phone/CAPTCHA/SMS form is open for user; no training, uploads, API credentials, or changed sharing. Evidence: results/kaggle_setup_status.json and results/kaggle_quota_verification_observed.txt. Alternate Google email is panvee58@gmail.com (50 was a typo); no migration authorized/performed. Chrome extension now exposes browser id 3, profile Rocky: use browser controls rather than stale native AX; current Kaggle handoff tab 719302181. Existing Colab tab 719302027 live reading 11:27:15 UTC verifies BERT epoch 3 batch 1500, 36735 updates, recovery epoch 2 boundary batch 17625. Second intermediate validation accuracy 0.8243, Macro-F1 0.7582 (rounded). Original JSON and final test pending; ModernBERT remains queued. Do not duplicate BERT or ModernBERT across providers. Kaggle checkpoints need saved notebook outputs or another verified durable backup before relying on session disk for recovery; no Kaggle persistence strategy deployed yet.


### Mobile status check — 2026-10-08 17:48 IST
Fresh Chrome monitor at 12:18:12 UTC verifies BERT epoch 4 batch 5500, 58351 optimizer updates, recovery epoch 4 batch 3000. Third intermediate validation accuracy 82.89%, Macro-F1 77.75%, rounded; final test still pending, ModernBERT queued. Connection UI says Runtime disconnected/Connecting, but monitor timestamp and optimizer progress advanced; do not infer stopped training solely from this label. Kaggle settings now explicitly say Phone verification: Verified. Quota remains 00:00 / 30 hrs. This supersedes earlier phone-verification blocker. No Kaggle GPU assigned, notebook or model run launched yet. Preserve BERT Colab process and avoid duplicate ModernBERT across the pending Colab queue and Kaggle. Evidence: results/colab_epoch3_validation_observed.txt, results/kaggle_setup_status.json.


### Monitor interruption repaired; original metrics retrieved — 2026-10-08 18:37 IST
User stopped/restarted only the continuous status monitor. Chrome health check independently verifies trainer PID 23054 alive (poll None), Tesla T4 73% utilization with 3641 MiB allocated, epoch 5 batch 7500 / 77970 updates at 13:04:21 UTC. Finite refreshed status at 13:07:44 UTC shows epoch 5 checkpointing batch 9000, recovery saved 13:07:43 UTC. No model crash observed. Replaced notebook cell 11 with a finite status display that returns immediately; only monitor behavior changed. Trainer source hash unchanged. A Colab editor fill initially inserted before old code, causing a status-cell SyntaxError before execution; cleared the editor properly and verified successful completed cell. BERT process unaffected. Old cell 9/10 status snapshots and raw cell 12 export collapsed to avoid stale-display confusion.

Original small cloud evidence (protocol, environment, pip freeze, dataset hashes/counts, model config, status, history, best checkpoint, recovery metadata/history, validation metric/report/confusion CSV) faithfully exported through Chrome and saved under results/experiments/official_text/OFFICIAL-6W-TEXT-v2_seed42_20261008T095827Z/. Retrieval hashes recorded in retrieval_manifest.json. Predictions and model weights remain in Drive; not yet synced. Four original validation observations: epoch 1 accuracy .8106737218159146/Macro-F1 .7524517476142621; epoch 2 .8243234134339927/.7582002314752563; epoch 3 .8289070135822857/.7774830561247422; epoch 4 .8274072326514105/.7786816742546674. Current selected checkpoint epoch 4 by Macro-F1, even though epoch 3 accuracy is higher. Test still pending; ModernBERT queued. Previous statement only rounded metrics available is superseded. Full faculty cohort/splits/source unchanged. Continue BERT up to original early-stop/max6 and test selected checkpoint once; Kaggle fallback authorized if Colab cannot continue, phone verified/30h unused as last checked. Do not launch duplicate training. Status cell 11 is now finite: rerun once to refresh. Health/export cell 12 is finite and can resync small evidence. Local notebook and helper now use finite monitor too.
