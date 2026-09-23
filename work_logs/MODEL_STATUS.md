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
