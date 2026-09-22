# Task Report — Current Project Handoff (2026-09-23)

> **Purpose:** This is a handoff document for the next AI agent or team member. It contains the complete current project state so that work can continue without re-explaining the history.

---

## What Has Been Completed

### Dataset
- **Primary dataset:** Fakeddit (LREC 2020)
- **Canonical verified paired manifest:** `data/verified_paired_manifest.csv`
- **75,995 verified paired samples** with confirmed valid images in `images/`
- **Splits:** 62,635 train / 6,685 validation / 6,675 test
- **Manifest SHA-256:** `fc74cb42288d366131ac764bf02f9212bacd7cab0af68442a003beaaff9fde20`
- **Task:** 6-way classification (`6_way_label`): 0 True, 1 Satire/Parody, 2 Misleading Content, 3 Imposter Content, 4 False Connection, 5 Manipulated Content
- **Inputs:** `clean_title` + local verified image
- The manifest is hash-locked and must NOT be changed without an explicitly approved protocol amendment.

### Baseline Protocol
- **Protocol ID:** `BP-6W-v1` — pre-registered in `context/PROJECT_CONTEXT.md` and `context/DECISIONS.md` (D012)
- Seeds: 42, 43, 44
- Primary metric: Macro-F1 (validation for checkpoint selection, test for reporting)
- Three-seed mean ± standard deviation reporting
- Full protocol details in `context/PROJECT_CONTEXT.md` § "Baseline Experimental Protocol"

### E002 — BERT Text-Only Baseline
- **Implementation:** ✅ Complete
  - Source: `src/fakenews_baselines/e002_text.py`
  - Config: `configs/e002_text_bp6w_v1.json`
  - Runner: `scripts/run_e002.py`
- **Smoke test:** ✅ Passed (2026-09-08, CPU, non-canonical)
- **Preliminary seed-42 run:** ⚠️ Completed on Colab T4 (2026-09-22/23)
  - **PRELIMINARY — scheduler-order issue detected — rerun required**
  - Warning: `lr_scheduler.step()` before `optimizer.step()`
  - Preliminary test Macro-F1: 0.6891, test accuracy: 0.7790
  - Full metrics in `results/experiments/e002_text/E002-bert-base-uncased-6way-BP6Wv1-s42-preliminary/preliminary_result.json`
  - Seeds 43/44: NOT run
- **Canonical status:** ❌ NOT complete — scheduler fix and rerun required

### Colab T4 Environment
- **GPU:** Tesla T4, ~14.56 GB VRAM
- **Status:** Successfully configured and used for preliminary E002 run
- **Dataset:** Verified in Colab — manifest SHA-256 match, 75,995 images, all convert to RGB
- **Image preflight:** RGB=73,549, RGBA=196, P=2,123, L=122, CMYK=5, zero conversion failures
- **Storage layout:** See `collab/COLAB_WORKLOG.md` for persistent-vs-temporary setup

### Project Documentation
- `collab/COLAB_WORKLOG.md` — chronological Colab operational history
- `work_logs/TROUBLESHOOTING.md` — reusable error/fix knowledge base (9 entries)
- `work_logs/MODEL_STATUS.md` — current model status with preliminary metrics
- `scripts/sync_results_to_git.sh` — result sync helper (no auto-commit)

### Team
- **Panvee** — Coding, implementation, model development, training, experiments
- **Karthik** — Literature review and research paper
- **Yogesh** — Documentation, weekly reports, presentations, meeting records

---

## Faculty Feedback (2026-09-22)

1. BERT and ResNet-50 remain baselines but are insufficient alone.
2. Broaden model comparison with modern multimodal approaches.
3. Candidate families (NOT YET IMPLEMENTED):
   - CLIP / semantically aligned text-image embeddings
   - Contrastive learning for text-image alignment
   - Cross-attention / co-attention fusion
   - Adaptive / correlation-based fusion
   - Multi-expert / modality-decoupled fusion
   - HGAT / graph-based social-context modelling
4. CLIP is the most direct next candidate (requires only paired text + image).
5. HGAT is later — requires social/context graph data not yet verified.
6. Faculty wants "initial values" from actual training runs.
7. CLIP/LIP terminology from advisor screenshot to be confirmed.

**Recorded in:** D013 in `context/DECISIONS.md`

---

## What Has NOT Been Done

| Item | Status |
|---|---|
| E002 final canonical training (scheduler fixed) | ❌ Not done |
| E002 seeds 43/44 | ❌ Not run |
| E003 ResNet-50 image-only | ❌ Not implemented |
| E004 BERT + ResNet-50 multimodal | ❌ Not implemented |
| E005 CLIP-based multimodal | ❌ Not implemented, architecture not frozen |
| E006 HGAT social-context | ❌ Future, blocked on data verification |
| Three-seed mean ± std for any model | ❌ None |
| Final research contribution selection | ❌ Not decided |

---

## ⚠️ Most Important Immediate Next Step

**The E002 scheduler-order bug has been corrected. No full retraining was performed during the fix task. The preliminary seed-42 result remains preliminary. A clean canonical seed-42 rerun is required.**

Do NOT run seeds 43/44 or start E003 until the scheduler fix is verified.

### Full Priority Order

1. preserve documentation on GitHub
2. fix E002 scheduler ordering
3. verify scheduler fix without full training
4. commit/push scheduler fix
5. return to Colab
6. rerun E002 seed 42 cleanly
7. after successful clean seed 42, run E002 seeds 43 and 44
8. aggregate E002 three-seed results
9. implement E003
10. implement E004
11. analyze all three baseline models
12. select appropriate advanced multimodal candidate(s)
13. investigate CLIP/semantic alignment/contrastive learning first among the advanced directions
14. investigate HGAT only if data requirements are verified

---

## Metrics Required Per Model

Per seed (42, 43, 44), per model (E002, E003, E004):
- Validation loss, Macro-F1, accuracy, balanced accuracy, weighted-F1 (per epoch)
- Test Macro-F1, accuracy, balanced accuracy, weighted-F1, loss
- Per-class precision / recall / F1 / support
- Raw and row-normalized 6×6 confusion matrices
- Training time, throughput, peak GPU memory, parameter count

Aggregation: three-seed mean ± standard deviation.

---

## Scientific Guardrails

- No fabricated metrics
- No protocol changes to BP-6W-v1
- No manifest changes
- No mixing literature numbers with our results
- No calling the smoke-test loss or preliminary scheduler-affected metrics "final canonical results"
- No silent architecture swaps
- No claiming novelty without verification
- No claiming CLIP/HGAT is implemented

---

## Results Storage Rules

| Location | Purpose | Authority |
|----------|---------|-----------|
| `results/experiments/` | Raw machine-generated experiment outputs | **Source of truth** |
| `context/EXPERIMENT_LOG.md` | Experiment history | References raw artifacts |
| `work_logs/MODEL_STATUS.md` | Current model summary | References raw artifacts |
| `collab/COLAB_WORKLOG.md` | Colab operational history | Chronological record |
| `work_logs/TROUBLESHOOTING.md` | Error/fix knowledge base | Reusable solutions |

Raw artifacts are authoritative. If markdown and raw artifacts disagree, raw artifacts are correct.

---

## Result Sync Workflow

```
Colab training → result artifacts created → verify artifacts
→ copy into GitHub working tree → bash scripts/sync_results_to_git.sh
→ git diff/status → git commit → git push
```

Do not auto-commit. Do not include images, data, ZIP archives, or model caches.
