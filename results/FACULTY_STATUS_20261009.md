# UROP faculty update — 9 October 2026

Task: six-class Fakeddit classification, text-only followed by text + image.

| Model / cohort | Validation accuracy | Validation Macro-F1 | Test accuracy | Test Macro-F1 | Status |
|---|---:|---:|---:|---:|---|
| BERT-base text-only — official 564,000/59,342/59,319 rows | **82.74%** | **77.87%** | Pending | Pending | Five epochs validated; epoch4 selected; interrupted, recovery needed |
| BERT-base + ResNet-50 — 2,000/300/300 paired pilot | **79.33%** | **59.62%** | **74.33%** | **55.90%** | Completed three GPU epochs and final test; small pilot |
| ModernBERT-base text-only | — | — | — | — | Implemented; training not started |

The text+image architecture, image processing, GPU training, validation-based checkpoint selection, final testing and recovery are implemented and demonstrated. This meets an implementation milestone; it does not mean half the official dataset was trained. Pilot test imposter-class F1 is zero (six examples), so rare-class performance needs more work. Pilot results cannot establish an improvement over the full official benchmark.

| Original paper, Table4 | Validation accuracy | Test accuracy |
|---|---:|---:|
| Six-way BERT text | 76.96% | 76.77% |
| Six-way BERT+ResNet-50 maximum fusion | 86.00% | 85.88% |

Our official BERT selected validation accuracy is numerically higher; final test remains pending. Our BERT-base fine-tuning differs from the paper's BERT-large feature pipeline, and the released cohort differs slightly from its counts. The paper does not supply matching Macro-F1 values in Table4. Its 86.54%/86.44% text numbers belong to binary classification. [Original paper](https://arxiv.org/pdf/1911.03854).

Current blocker: Colab GPU usage limits and an epoch-boundary recovery-metadata write error. The original saved tensor checkpoint must be placed inside `data/cloud_recovery/`, verified, and privately transferred to Kaggle to finish the unchanged BERT protocol and final test. No text GPU job is currently running. The multimodal Kaggle pilot is finished, not still training.

Original multimodal evidence: [private saved Kaggle version2](https://www.kaggle.com/code/rocky62/urop-official-six-way-text-recovery?scriptVersionId=356486031), local `results/experiments/multimodal/MM-PILOT-6W-v1_seed42_20261009/`. Original text history: `results/experiments/official_text/OFFICIAL-6W-TEXT-v2_seed42_20261008T095827Z/bert-base/history.json`. Detailed audit: `context/RENEWED_AUDIT_20261009.md`. Historical 75,995-row results remain preserved separately.
