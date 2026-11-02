# UROP validation and test metrics

Open `index.html` for the readable comparison; `all_metrics.csv` for a spreadsheet; `all_metrics.json` for exact machine-readable values. Original results remain intact.

Five score metrics are displayed as percentages. Loss is unscaled (lower is better). Accuracy equals Micro-F1 for this single-label six-class task. Macro-F1 weights classes equally; weighted-F1 weights by support; balanced accuracy averages class recall.

## Text-only · BERT-base

Independent saved-artifact verification passed

| Split | Accuracy | Micro-F1 | Macro-F1 | Weighted-F1 | Balanced accuracy | Cross-entropy loss | Samples |
|---|---:|---:|---:|---:|---:|---:|---:|
| Validation | 82.7407% | 82.7407% | 77.8682% | 82.5908% | 75.1522% | 0.601584592 | 59,342 |
| Test | 82.3901% | 82.3901% | 77.4566% | 82.2430% | 74.9786% | 0.618080115 | 59,319 |

Evidence: [validation](../../results/experiments/official_text/OFFICIAL-6W-TEXT-v2_seed42_20261008T095827Z/KAGGLE_RECOVERY_v1_20261009_356721456/raw_evidence/bert-base/validation_metrics.json), [test](../../results/experiments/official_text/OFFICIAL-6W-TEXT-v2_seed42_20261008T095827Z/KAGGLE_RECOVERY_v1_20261009_356721456/raw_evidence/bert-base/test_metrics.json)

## Text + image · BERT-base + ResNet-50

Independent saved-artifact verification passed

| Split | Accuracy | Micro-F1 | Macro-F1 | Weighted-F1 | Balanced accuracy | Cross-entropy loss | Samples |
|---|---:|---:|---:|---:|---:|---:|---:|
| Validation | 88.5074% | 88.5074% | 82.9303% | 88.4814% | 80.8302% | 0.694794647 | 59,299 |
| Test | 88.1458% | 88.1458% | 82.6415% | 88.1317% | 80.8249% | 0.723865879 | 59,270 |

Evidence: [validation](../../results/experiments/multimodal/OFFICIAL-6W-MM-USABLE-v2_seed42_20261027/final_362955511/validation_metrics.json), [test](../../results/experiments/multimodal/OFFICIAL-6W-MM-USABLE-v2_seed42_20261027/final_362955511/test_metrics.json)

## Image-only · ResNet-50

Cloud-reported; independent local artifact verification pending

| Split | Accuracy | Micro-F1 | Macro-F1 | Weighted-F1 | Balanced accuracy | Cross-entropy loss | Samples |
|---|---:|---:|---:|---:|---:|---:|---:|
| Validation | 80.9339% | 80.9339% | 65.6487% | 80.2383% | 62.4213% | 0.583574318 | 59,299 |
| Test | 81.1557% | 81.1557% | 66.1796% | 80.4935% | 62.9919% | 0.584383827 | 59,270 |

Evidence: [validation](../../results/experiments/image_only/CLOUD_COMPLETION_OBSERVED_20261103.json), [test](../../results/experiments/image_only/CLOUD_COMPLETION_OBSERVED_20261103.json)

## Accuracy compared with the paper

| Model | Split | Ours | Paper | Difference | Numerically higher |
|---|---|---:|---:|---:|---|
| Text-only · BERT-base | Validation | 82.7407% | 76.96% | +5.7807 pp | 🟢 Ours ↑ |
| Text-only · BERT-base | Test | 82.3901% | 76.77% | +5.6201 pp | 🟢 Ours ↑ |
| Text + image · BERT-base + ResNet-50 | Validation | 88.5074% | 86.00% | +2.5074 pp | 🟢 Ours ↑ |
| Text + image · BERT-base + ResNet-50 | Test | 88.1458% | 85.88% | +2.2658 pp | 🟢 Ours ↑ |
| Image-only · ResNet-50 | Validation | 80.9339% | 75.29% | +5.6439 pp | 🟢 Ours ↑ |
| Image-only · ResNet-50 | Test | 81.1557% | 75.49% | +5.6657 pp | 🟢 Ours ↑ |

Paper Micro-F1, Macro-F1, weighted-F1, balanced accuracy, cross-entropy loss and per-class precision/recall/F1: **not reported** for these matching comparisons. Do not invent a winner for those metrics.

[Paper Table 4](https://arxiv.org/html/1911.03854v2) was checked against the original six-way columns.

These are numerical reference comparisons, not controlled improvements. Our fine-tuning and checkpoint selection differ from the paper. Text-only uses 682,661 released rows; image branches use 682,170 pairs after 491 approved image decoding exclusions. The paper/release count discrepancy and documented cross-split image duplicates remain limitations. One seed per baseline; no significance or state-of-the-art claim. Image-only values remain cloud-reported pending local verification.

## Detailed results

Each model folder contains validation/test JSON. Text-only and text + image also contain the available class reports and raw/normalized confusion matrices. Image-only missing details are explicitly listed in `image_only/PENDING.md`.

Highest recorded validation and test accuracy among our models: text + image. Text-only and image branches use different cohorts, so this is descriptive rather than a controlled ablation.

Full source paths and SHA-256 values: `source_manifest.json`. This consolidation changes no data, models, experiment state or acceptance status.
