# MODEL STATUS — Multimodal Fake News Detection

> **Purpose:** Single easy-to-read current status of all experiment models.
> **Last Updated:** 2026-09-23
> **Updated By:** Antigravity

---

## Current Model Status

| Experiment | Model | Implementation | Smoke Test | Training | Results | Current Status |
|---|---|---|---|---|---|---|
| E002 | BERT text-only (`bert-base-uncased`, 109.5M params) | ✅ Complete | ✅ Passed | ✅ Clean seed-42 | ✅ Clean seed-42 | Clean seed-42 complete; seeds 43/44 pending |
| E003 | ResNet-50 image-only (~26M params) | ❌ Not started | ❌ N/A | ❌ Not started | ❌ None | Pending implementation |
| E004 | BERT + ResNet-50 multimodal (~136M params) | ❌ Not started | ❌ N/A | ❌ Not started | ❌ None | Pending implementation |
| E005 | CLIP-based multimodal | ❌ Not started | ❌ N/A | ❌ Not started | ❌ None | Planned; architecture not frozen |
| E006 | HGAT social-context | ❌ Not started | ❌ N/A | ❌ Not started | ❌ None | Future; blocked on data verification |

---

### E002 BERT
- implemented
- smoke-tested
- preliminary seed-42 preserved
- scheduler-order bug corrected
- clean canonical seed-42 completed
- seeds 43/44 pending

**Clean seed-42 test metrics:**
- Accuracy: 0.7810
- Macro-F1: 0.6966
- Balanced accuracy: 0.6693
- Weighted-F1: 0.7782
- Loss: 0.7508

---

## E003 ResNet-50
- not implemented
- not trained

---

## E004 BERT + ResNet-50
- not implemented
- not trained

------

## E005 CLIP / semantic alignment
- candidate
- architecture not frozen
- not implemented
- not trained

---

## Contrastive learning
- candidate training/method direction
- not implemented
- not trained

---

## Cross-attention/co-attention
- candidate
- not implemented
- not trained

---

## Adaptive/correlation fusion
- candidate
- not implemented
- not trained

---

## Modality-decoupled/multi-expert
- candidate
- not implemented
- not trained

---

## E006 HGAT
- future investigation
- blocked on verification of required graph/social-context data

---

## Candidate Research Model Families

> **Status: CANDIDATE METHODS — NOT YET IMPLEMENTED.**

The following model families are research options identified from faculty feedback and literature. They are NOT committed architecture choices. The final research direction will be selected only after observing baseline failures and comparing feasible methods.

| # | Family | Description | Feasibility on Current Cohort |
|---|--------|-------------|-------------------------------|
| 1 | CLIP / semantically aligned embeddings | Jointly pre-trained text-image encoder; contrastive learning aligns text and image in shared embedding space | ✅ Feasible — requires only paired text + image |
| 2 | Contrastive learning for text-image alignment | Broader family including CLIP; train text/image encoders with contrastive objectives | ✅ Feasible — requires only paired text + image |
| 3 | Cross-attention / co-attention fusion | Attention between text and image features (e.g., ViLT, VisualBERT) | ✅ Feasible — requires only paired text + image |
| 4 | Adaptive / correlation-based fusion | Learn fusion weights or correlation between modalities | ✅ Feasible — requires only paired text + image |
| 5 | Multi-expert / modality-decoupled fusion | Separate expert networks per modality with learned routing | ✅ Feasible — requires only paired text + image |
| 6 | HGAT / graph-based social-context modelling | Model user/comment/propagation graphs | ⚠️ Requires social graph data not currently verified |

**Current practical priority:** CLIP (family 1) is the most direct candidate for the next multimodal experiment because our cohort contains paired text and images and does not require additional data.

**HGAT (family 6)** requires social/context graph information (users, comments, propagation) that is not currently available in our canonical paired cohort (`clean_title` + local image + `6_way_label`). It remains a later candidate pending data verification.

---

## Results Storage Rule

| Location | Purpose | Authority |
|----------|---------|-----------|
| `results/experiments/` | Raw machine-generated experiment outputs (JSON/CSV) | **Source of truth** for numerical results |
| `context/EXPERIMENT_LOG.md` | Human-readable experiment history and observations | References `results/experiments/` |
| `work_logs/MODEL_STATUS.md` (this file) | Current model status summary | References `results/experiments/` |
| `collab/COLAB_WORKLOG.md` | Colab operational history | Chronological record |
| `work_logs/TROUBLESHOOTING.md` | Error/fix knowledge base | Reusable solutions |

Raw machine-generated artifacts are authoritative. Markdown summaries must reference those artifacts. If markdown summaries and raw artifacts disagree, the raw artifacts are correct.


## 2026-10-08 — Official release migration (current)

User authorized full official six-way text training on Google Colab. BERT-base and ModernBERT-base are prepared under `OFFICIAL-6W-TEXT-v2`; training is NOT yet verified as started. Chrome controls timed out after existing Google Drive sign-in. New metrics are not available. Official data: 564,000 train / 59,342 validation / 59,319 public test. Old E002 results remain historical BP-6W-v1 subset results. See `context/AUDIT_20261008.md`, `results/official_dataset_audit.json`, `configs/text_official_6way_v2.json` and `notebooks/UROP_OFFICIAL_6WAY_TEXT_20261008.ipynb`.


## 2026-10-08 14:50 IST — Setup/recovery checkpoint (current)

- User authorized local and GitHub checkpoint updates for every model, and confirmed Chrome-only training; Colab CLI fallback declined. No Colab CLI credentials were granted.
- Official dataset files and their hashes/counts are saved locally; full six-way cohort remains unchanged.
- BERT-base and ModernBERT-base trainer/notebook now save recoverable state every 3,000 batches and at epoch boundaries, including optimizer, scheduler, scaler, random generators, sampler position, history and selected checkpoint. `--resume-attempt` restores a named attempt and preserves completed models.
- Recovery batch ordering passed a CPU sampler check; script and notebook syntax checks passed. Cloud GPU execution/recovery has NOT been tested.
- Chrome application control continues to time out, and the direct Chrome browser provider is unavailable. Training is NOT verified as started; no official-v2 validation/test metrics exist. The prior cloud preflight verified Tesla T4 only.
- Account usage query: 34% remains in five-hour Codex window; reset 2026-10-08 17:35 IST. This is separate from Colab runtime lifetime and GPU limits.
- Next action: restore Chrome automation or upload `notebooks/UROP_OFFICIAL_6WAY_TEXT_20261008.ipynb` in Chrome Colab, select T4 and Run all; verify Drive mount, dataset hashes and the first actual optimizer steps. Preserve exact cloud ATTEMPT path.
- Then sync each model's small JSON/CSV/log evidence under `results/experiments/official_text/`, update these context/log/status files and push milestone documentation. Large TSVs, images and weights remain excluded from Git. Local/GitHub syncing requires a connected agent; cloud checkpoints write independently.


## 2026-10-08T09:33:11.547672+00:00 — Cloud startup checkpoint

Chrome recovered; Drive mounted on T4. Observed Python 3.13.15 / transformers 5.18.0 / torch 2.11.0+cu130. Official file/source verification succeeded. Three cloud initialization attempts (20261008T092708Z, 20261008T092745Z, 20261008T092810Z) failed with `AttributeError: Tee object has no attribute isatty` before optimizer steps. Cloud evidence is preserved under `/content/drive/MyDrive/Colab Notebooks/UROP/official_text_runs/`. Fixed stream-method delegation; isatty/encoding/fileno checks and notebook syntax passed locally. Clean relaunch pending; no new validation/test metrics. Chrome-only preference honored. Setup commit 09876a88d70747cae62e6fac55946a547532e9e8 is pushed.


## 2026-10-08T09:39:18.215639+00:00 — Corrected cloud process launched

Pinned fixed source SHA256 `a13c0e5d97b2fe7661ce6a228d43d853f1aca703314cfa48688825b7b01701f9` loaded from pushed commit `9c7abf1`. Colab cell [16] visibly entered Executing state on Tesla T4. This verifies process launch only; first optimizer steps, current attempt folder, and metrics have not yet been observed. BERT runs first; ModernBERT remains queued. Live Chrome controls subsequently became unavailable. Do not rerun launch cells or replace data blindly: inspect current process/output and cloud status before deciding whether a recovery is needed. Latest machine-readable local status: `results/official_text_live_status.json`. Checkpoints write to Drive independently; local and GitHub synchronization needs a connected agent.


## 2026-10-08T09:45:49.174071+00:00 — Usage/recovery checkpoint

Last usage check: 6% remains; five-hour window resets 2026-10-08 17:35 IST. This supersedes the earlier 34% preflight reading. Latest source logging fix and recovery code are pushed. Current cloud training progress is unverified: cell 16 entered execution, but a later accessibility view showed 4 seconds elapsed without readable subprocess output. Do not claim active optimizer steps or metrics. Native Chrome controls/screenshots are unreliable/unavailable and the Chrome terminal has no usable prompt. User was asked to keep the Mac awake/unlocked with Chrome visible; Colab CLI fallback was explicitly declined. Preserve existing cloud attempts; inspect latest model status/error/checkpoint before any rerun. All scientific settings and dataset files remain unchanged.


## 2026-10-08T09:49:32.158683+00:00 — Final continuity checkpoint

All code/config/notebook, dataset provenance, audit, startup errors and current unverified launch state are saved. Checkpoint cadence is implemented (every 3,000 batches and each epoch), but no successful cloud weight checkpoint or optimizer updates have yet been verified. The last available Colab setup screenshot is `results/colab_setup_last_available.png`; it is not live training-progress proof. Attempts to create a continuation heartbeat failed schedule validation, so no automatic follow-up is active. Resume only after checking the existing cloud attempt; do not assume chat usage reset automatically resumes an agent. Chrome-only preference remains in force.
