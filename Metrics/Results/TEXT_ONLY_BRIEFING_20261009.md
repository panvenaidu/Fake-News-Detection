# Six-class text-only briefing — 9 October 2026

**Completed: training, validation, final testing and verified archiving.** Our validation and test accuracy are higher than the paper’s six-class text-only BERT results.

The [faculty dataset](https://drive.google.com/drive/folders/1DuH0YaEox08ZwzZDpRMOaFpMCeRyxiEF) is the official Fakeddit `multimodal_only_samples` release. We used its three original TSVs, with no resplitting, sampling, exclusions or class rebalancing:

| Original file | Purpose | Rows |
|---|---|---:|
| `multimodal_train.tsv` | Training | 564,000 |
| `multimodal_validate.tsv` | Validation / checkpoint selection | 59,342 |
| `multimodal_test_public.tsv` | Final test | 59,319 |

**Total: 682,661 rows.** Input: `clean_title`; target: `6_way_label`. This completed run uses text from the official multimodal release. The older 75,995-row paired subset is retained as historical evidence and was not this run’s cohort.

**Model and architecture:** `google-bert/bert-base-uncased`, fine-tuned with a six-class classification head. BERT-base has 12 Transformer layers and a 768-dimensional representation. Flow: cleaned title → tokenizer (maximum 128 tokens) → BERT encoder → pooled title representation → dropout and six-output linear classifier → class probabilities. The full BERT model and classification head are trained together.

**Training settings:** seed 42; training batch 32; evaluation batch 128; AdamW learning rate 0.00002; unweighted cross-entropy; fp16 mixed precision. Six epochs finished. Epoch 4 was selected using the highest validation Macro-F1, with the registered loss/earlier-epoch tie rules.

**Workflow:**

1. Verify official files, hashes, split IDs and labels.
2. Train on 564,000 titles, saving recovery checkpoints every 3,000 batches and at epoch boundaries.
3. Validate after each epoch; select the best checkpoint using validation only.
4. Freeze selected weights and evaluate all 59,319 official public test rows.
5. Recompute metrics from exported predictions; verify and save reports, confusion matrices, model weights, tokenizer, checkpoints, provenance and logs.

**Software and cloud:** training began in Google Colab on a Tesla T4 and was recovered/completed in Kaggle on a Tesla T4. Kaggle allocated T4 ×2; the trainer used device 0 only. Final Kaggle environment: Python 3.13.15, PyTorch 2.11.0+cu128 and Hugging Face Transformers 5.18.0. The recovery notebook finished its outputs in about 45 minutes. At completion, no Kaggle jobs were active; the displayed remaining GPU quota was approximately 29h09m.

**Model status:** BERT-base is the completed official text baseline. ModernBERT-base is prepared but untrained. BERT-base + ResNet-50 completed a separate 2,600-row multimodal pilot; it is not a full-cohort benchmark. ResNet-55 was not used.

**All requested metric comparisons:** paper scores below are the six-class text-only BERT row in the [original paper, Table 4](https://arxiv.org/html/1911.03854v2). NR = not reported for that matching experiment.

| Metric | Our validation | Paper validation | Our test | Paper test |
|---|---:|---:|---:|---:|
| Accuracy | 82.7407% | 76.96% | 82.3901% | 76.77% |
| Micro-F1 | 82.7407% | NR | 82.3901% | NR |
| Macro-F1 | 77.8682% | NR | 77.4566% | NR |
| Weighted-F1 | 82.5908% | NR | 82.2430% | NR |
| Balanced accuracy | 75.1522% | NR | 74.9786% | NR |
| Loss | 0.601585 | NR | 0.618080 | NR |

For this single-label six-class task, micro-F1 equals accuracy. The paper does not separately report micro-F1; NR is retained rather than presenting an inferred number as a published score. Loss has no percentage units.

**Accuracy gains:** +5.7807 percentage points on validation; +5.6201 points on test. The registered target of paper test accuracy +1 point (77.77%) was reached.

The paper’s 86.54% / 86.44% BERT accuracy pair belongs to binary classification. We completed six-way classification; no official binary or three-way run is claimed.

**Test classification report:**

| Class | Precision | Recall | F1 | Test examples | Paper text-class F1 |
|---|---:|---:|---:|---:|---|
| True | 85.05% | 88.60% | 86.79% | 23,507 | NR |
| Satire/Parody | 77.94% | 69.29% | 73.37% | 3,514 | NR |
| Misleading Content | 74.18% | 72.59% | 73.38% | 11,297 | NR |
| Imposter Content | 77.90% | 53.84% | 63.67% | 1,224 | NR |
| False Connection | 84.50% | 85.28% | 84.89% | 17,472 | NR |
| Manipulated Content | 85.17% | 80.26% | 82.64% | 2,305 | NR |

These are six separate classes: True plus five misinformation categories. The paper does not publish matching text-only class-wise F1 values. Its Table 6 gives misclassification percentages for the multimodal BERT + ResNet-50 model; those are not text-only F1 scores.

**Comparison limits:** one seed; our BERT-base fine-tuning differs from the paper’s BERT-Large feature-extraction pipeline. The released multimodal files have 335 fewer rows than the paper’s stated total. The measured accuracy improvement is verified; this is not an exact replication or a general state-of-the-art claim.

**Saved and backed up:**

- GitHub: reviewed code/notebooks/configuration, numerical JSON/CSV evidence, full validation/test predictions, classification reports, confusion matrices, provenance, experiment logs, model status and project context.
- Local UROP and private Kaggle output: original data, selected weights, tokenizer and full recovery checkpoint/archives. Large data and weights are deliberately excluded from Git.
- Verification: exact official prediction IDs/labels, recomputed metrics, archive hashes/CRCs, readable model/optimizer/scheduler/AMP/tokenizer, and an idempotent completion check.

[GitHub repository](https://github.com/panvenaidu/Fake-News-Detection) · [Verified final results commit](https://github.com/panvenaidu/Fake-News-Detection/commit/5527824302480de39cafd85a5a9a1c2b8cc68fd7) · [Private saved Kaggle output](https://www.kaggle.com/code/rocky62/urop-official-six-way-text-recovery/output?scriptVersionId=356721456)

Local final report: `results/TEXT_ONLY_FINAL_REPORT_20261009.md`. Numerical evidence: `results/experiments/official_text/OFFICIAL-6W-TEXT-v2_seed42_20261008T095827Z/KAGGLE_RECOVERY_v1_20261009_356721456/raw_evidence/bert-base`. Model/archive storage: `data/cloud_recovery/KAGGLE_RECOVERY_v1_20261009_356721456/`.
