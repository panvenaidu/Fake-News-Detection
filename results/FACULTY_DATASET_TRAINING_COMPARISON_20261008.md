# Faculty dataset training and original-paper comparison

Checked 2026-10-08; latest cloud monitor 12:26:02 UTC / 17:56:02 IST.

## Dataset actually used
Faculty folder: https://drive.google.com/drive/folders/1DuH0YaEox08ZwzZDpRMOaFpMCeRyxiEF
Official released multimodal TSVs: train 564,000, validation 59,342, public test 59,319. File hashes verified; existing official splits preserved; no resampling or exclusions. Text input clean_title; six_way_label target. Evidence: results/official_dataset_audit.json, results/official_dataset_provenance.json, configs/text_official_6way_v2.json.

## Number of runs
One verified BERT-base seed-42 optimization run is in progress: OFFICIAL-6W-TEXT-v2_seed42_20261008T095827Z. Three completed epochs have three validation checks; they are checkpoints of ONE run, not three independent runs. Zero completed full-cohort model runs, zero final public-test evaluations yet. ModernBERT is queued and has not trained. No official-cohort image-only or text+image training has run. Three recorded initialization failures before optimizer steps are not completed training experiments. Earlier interrupted launches and duplicate-guard errors are not independent completed results.

## Recorded six-way results
| Model/checkpoint | Validation accuracy | Validation Macro-F1 | Test accuracy |
|---|---:|---:|---:|
| Paper BERT text-only | 76.96% | Not reported in Table 4 | 76.77% |
| Our BERT-base epoch 1 | 81.07% | 75.25% | Pending |
| Our BERT-base epoch 2 | 82.43% | 75.82% | Pending |
| Our BERT-base epoch 3 | 82.89% | 77.75% | Pending |
| Paper ResNet-50 image-only | 75.29% | Not reported in Table 4 | 75.49% |
| Paper BERT + ResNet-50 maximum fusion | 86.00% | Not reported in Table 4 | 85.88% |

Source: original paper Table 4, https://arxiv.org/html/1911.03854v2 and https://arxiv.org/pdf/1911.03854. Local epoch observations: results/experiments/official_text/OFFICIAL-6W-TEXT-v2_seed42_20261008T095827Z/bert-base/validation_epoch{1,2,3}_observed.json. These local observations are rounded live-monitor readings, not the original full-precision cloud metric JSON. Current progress proof: results/colab_paper_comparison_status.txt.

Current BERT is checkpointing epoch 4 batch 9,000; recovery metadata reports epoch 4 batch 9,000. Third-epoch validation is 5.93 percentage points higher numerically than the paper's six-way text-only validation accuracy. This is a provisional validation comparison, not a completed test improvement or exact replication. Paper describes BERT-Large embeddings plus classifier, whereas ours fine-tunes BERT-base. Paper counts 682,996 multimodal samples, while the released faculty TSVs total 682,661, a 335-row difference of unknown cause. The paper's six-way multimodal validation result 86.00% remains higher than our current text-only 82.89%; modalities differ. The paper's 86.54% validation / 86.44% test pair refers to TWO-way text-only classification, not six-way.

## Historical smaller subset
Two earlier BERT runs on BP-6W-v1 (75,995 verified pairs: 62,635 train / 6,685 validation / 6,675 test) are preserved as historical. Preliminary scheduler-affected seed-42: validation Macro-F1 0.701184937, test Macro-F1 0.68914922, test accuracy about 77.90%. Clean seed-42: validation Macro-F1 0.702167546, test Macro-F1 0.696584539, test accuracy about 78.10%. These are not results on the full faculty cohort and cannot establish an official-paper benchmark improvement. Both are reconstructed notebook evidence as documented in context/EXPERIMENT_LOG.md. The smaller cohort belongs to the same Fakeddit dataset, not an unrelated dataset.

## User direction
User is considering stopping, but explicitly said NOT right now and to wait a few minutes. No runtime stop, deletion, restart, or new model launch performed for this comparison. BERT continues under its existing protocol; ModernBERT remains queued. A future explicit stop should preserve and verify the most recent durable checkpoint first.
