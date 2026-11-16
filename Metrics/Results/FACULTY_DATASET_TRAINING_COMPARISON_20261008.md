# Current faculty data and paper comparison — 8 October 2026

The faculty-provided original TSVs are used unchanged for our six-way text model: **564,000 train / 59,342 validation / 59,319 public test**. Five validation epochs belong to **one BERT-base run**, not five independent experiments. It is interrupted before final testing; selected checkpoint is epoch4 by validation Macro-F1. ModernBERT has not started.

| Full-cohort six-way text | Validation accuracy | Validation Macro-F1 | Test accuracy | Test Macro-F1 |
|---|---:|---:|---:|---:|
| Original paper BERT | 76.96% | Not reported in Table4 | 76.77% | Not reported in Table4 |
| Our BERT-base epoch1 | 81.07% | 75.25% | Pending | Pending |
| Our BERT-base epoch2 | 82.43% | 75.82% | Pending | Pending |
| Our BERT-base epoch3 | 82.89% | 77.75% | Pending | Pending |
| Our BERT-base epoch4 — selected | **82.74%** | **77.87%** | Pending | Pending |
| Our BERT-base epoch5 | 82.80% | 77.84% | Pending | Pending |

Selected validation accuracy is numerically **5.78 percentage points** above the paper. This is provisional: our BERT-base fine-tuning differs from its BERT-large feature pipeline; released TSVs have 335 fewer rows than its stated multimodal count. Final test is pending. The 86.54%/86.44% paper text scores are two-way, not six-way. [Original paper, Table4](https://arxiv.org/pdf/1911.03854).

| Six-way text+image — different cohorts, not a direct benchmark comparison | Training / validation / test rows | Validation accuracy | Validation Macro-F1 | Test accuracy | Test Macro-F1 |
|---|---|---:|---:|---:|---:|
| Original paper BERT+ResNet50 maximum fusion | Original paper multimodal cohort | 86.00% | Not reported in Table4 | 85.88% | Not reported in Table4 |
| Our completed BERT-base+ResNet50 pilot | **2,000 / 300 / 300** | **79.33%** | **59.62%** | **74.33%** | **55.90%** |

One multimodal pilot completed three GPU epochs and final testing on private Kaggle version2. Version1 failed before the first optimizer step and is not a completed model run. The pilot uses original official titles/labels and unchanged split membership from the 75,995 available paired rows. It proves the pipeline works; it does not establish full-cohort performance. Imposter test F1=0 on six examples. Image-only training remains pending.

Original full-precision five-epoch text history: `results/experiments/official_text/OFFICIAL-6W-TEXT-v2_seed42_20261008T095827Z/bert-base/history.json`. Original multimodal metrics/class reports/confusion matrices/environment: `results/experiments/multimodal/MM-PILOT-6W-v1_seed42_20261009/`. Short current status: `results/FACULTY_STATUS_20261009.md`. Earlier observations below are preserved as historical, not current status.

---

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
| Our BERT-base epoch 4 | 82.74% | 77.87% | Pending |
| Paper ResNet-50 image-only | 75.29% | Not reported in Table 4 | 75.49% |
| Paper BERT + ResNet-50 maximum fusion | 86.00% | Not reported in Table 4 | 85.88% |

Source: original paper Table 4, https://arxiv.org/html/1911.03854v2 and https://arxiv.org/pdf/1911.03854. Local epoch observations: results/experiments/official_text/OFFICIAL-6W-TEXT-v2_seed42_20261008T095827Z/bert-base/validation_epoch{1,2,3}_observed.json. These local observations are rounded live-monitor readings, not the original full-precision cloud metric JSON. Current progress proof: results/colab_paper_comparison_status.txt.

Current BERT is checkpointing epoch 4 batch 9,000; recovery metadata reports epoch 4 batch 9,000. Third-epoch validation is 5.93 percentage points higher numerically than the paper's six-way text-only validation accuracy. This is a provisional validation comparison, not a completed test improvement or exact replication. Paper describes BERT-Large embeddings plus classifier, whereas ours fine-tunes BERT-base. Paper counts 682,996 multimodal samples, while the released faculty TSVs total 682,661, a 335-row difference of unknown cause. The paper's six-way multimodal validation result 86.00% remains higher than our current text-only 82.89%; modalities differ. The paper's 86.54% validation / 86.44% test pair refers to TWO-way text-only classification, not six-way.

## Historical smaller subset
Two earlier BERT runs on BP-6W-v1 (75,995 verified pairs: 62,635 train / 6,685 validation / 6,675 test) are preserved as historical. Preliminary scheduler-affected seed-42: validation Macro-F1 0.701184937, test Macro-F1 0.68914922, test accuracy about 77.90%. Clean seed-42: validation Macro-F1 0.702167546, test Macro-F1 0.696584539, test accuracy about 78.10%. These are not results on the full faculty cohort and cannot establish an official-paper benchmark improvement. Both are reconstructed notebook evidence as documented in context/EXPERIMENT_LOG.md. The smaller cohort belongs to the same Fakeddit dataset, not an unrelated dataset.

## User direction
User is considering stopping, but explicitly said NOT right now and to wait a few minutes. No runtime stop, deletion, restart, or new model launch performed for this comparison. BERT continues under its existing protocol; ModernBERT remains queued. A future explicit stop should preserve and verify the most recent durable checkpoint first.


Update 18:37 IST: original cloud history/validation metrics/report/confusion matrix retrieved, with full precision and file hashes in the experiment retrieval manifest. Four completed validation epochs within the same ongoing run; current selected checkpoint epoch 4 by Macro-F1. BERT epoch 5 batch 9000 recovery observed. GPU utilization independently measured at 73%, later 59%. User KeyboardInterrupt interrupted the status monitor; trainer remains alive. Paper comparison remains provisional until selected-checkpoint test.
