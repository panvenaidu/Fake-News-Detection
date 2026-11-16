# Completed six-class text-only BERT — 9 October 2026

**Train, validate, test and archive: complete and independently verified.**

Faculty dataset: official Fakeddit `multimodal_only_samples`; 564,000 train / 59,342 validation / 59,319 public test (682,661 total). `clean_title` only, original `6_way_label`, all six labels. No new splits, exclusions or class rebalancing.

Model: BERT-base-uncased, seed42, fine-tuned for six epochs. Epoch4 selected by validation Macro-F1; epoch6 did not improve selection. This continued the original interrupted BERT attempt. ModernBERT remains prepared and untrained.

| Metric | Validation | Test |
|---|---:|---:|
| Accuracy | 82.7407% | 82.3901% |
| Micro-F1 | 82.7407% | 82.3901% |
| Macro-F1 | 77.8682% | 77.4566% |
| Weighted-F1 | 82.5908% | 82.2430% |
| Balanced accuracy | 75.1522% | 74.9786% |
| Loss | 0.601585 | 0.618080 |

| Six-class text comparison | Paper | Our BERT | Difference |
|---|---:|---:|---:|
| Validation accuracy | 76.96% | 82.7407% | +5.7807 percentage points |
| Test accuracy | 76.77% | 82.3901% | +5.6201 percentage points |

**The target of test accuracy >=77.77% (paper +1 percentage point) was reached.** [Paper Table4](https://arxiv.org/html/1911.03854v2) does not report a comparable Macro-F1 score. The 86.54%/86.44% text pair in the paper is binary. This is a single-seed numerical comparison: our BERT-base fine-tuning differs from their BERT-Large feature pipeline; released multimodal files have335 fewer rows than the paper statistic. Do not call this an exact replication or a general state-of-the-art claim.

| Test class | F1 | Support |
|---|---:|---:|
| True | 86.79% | 23,507 |
| Satire/Parody | 73.37% | 3,514 |
| Misleading Content | 73.38% | 11,297 |
| Imposter Content | 63.67% | 1,224 |
| False Connection | 84.89% | 17,472 |
| Manipulated Content | 82.64% | 2,305 |

Cloud: Kaggle saved version3, scriptVersionId356721456; TeslaT4×2 allocated, trainer used device0. Python3.13.15 / Torch2.11.0+cu128 / Transformers5.18.0. Successful updates105,710; AMP skips40. Peak allocated GPU memory3.05GiB.
Resumed trainer session: 42.22 minutes including setup/evaluations; notebook logs finish outputs at2705.5s (~45.09min) including bootstrap/archive. Cumulative recorded training-loop time across Colab/recovery: 237.44 minutes; not today's wall time. Six-way recovery reprocessed the last84,000 epoch5 titles from the older checkpoint; original fifth-epoch history was preserved.
No active Kaggle jobs; draft off. Fresh quota display:00:51 /30h used, approximately29h09m remaining. Colab quota was not rechecked. Assistant usage at the final synchronization check: 24% five-hour / 42% weekly remaining. This prompted final saving and Git synchronization, with no new training. No new scheduled task was created.

Recovery correction: separate worker RNG and exact original sampler order, including its exhausted-iterator RNG draw. Checks passed locally and on installed Kaggle Torch. Completed-result guard tested with actual artifacts and returned without training or inference. Full raw prediction IDs/labels/supports and metrics verified; both archive hashes/CRCs and69 numerical manifest members verified; model/optimizer/scheduler/AMP/tokenizer strict load passed. SDPA warn-only determinism was retained; no bitwise reproducibility guarantee.

Progress (workflow checkpoints, not model accuracy):

```text
Text-only BERT   [██████████] 100%
Full text+image  [████░░░░░░]  40%
Image-only      [██░░░░░░░░]  20%
Overall         [█████░░░░░]  53%
```

Text: dataset/code/train/validate/test+archive are all complete. Six trained/validated epochs, full59,342 validation and59,319 test predictions. The completed2,600-row multimodal pilot remains100% separately; full multimodal training and image-only training remain later work. ModernBERT comparison remains40% prepared,0% trained. Four model training experiments remain documented overall (two historical sampled BERT runs, this official BERT attempt, one multimodal pilot); recovery is a continuation of the official attempt, not an extra independent model.

Original data: `data/official_multimodal_v2/`. Original Colab results and checkpoint ZIP remain preserved. Current numerical evidence: `results/experiments/official_text/OFFICIAL-6W-TEXT-v2_seed42_20261008T095827Z/KAGGLE_RECOVERY_v1_20261009_356721456/raw_evidence`. Verification: `results/experiments/official_text/OFFICIAL-6W-TEXT-v2_seed42_20261008T095827Z/KAGGLE_RECOVERY_v1_20261009_356721456/completion_verification.json`. Weight/archive storage: `data/cloud_recovery/KAGGLE_RECOVERY_v1_20261009_356721456/`. Raw TSVs, images, weights and ZIPs remain excluded from Git. [Private saved cloud output](https://www.kaggle.com/code/rocky62/urop-official-six-way-text-recovery/output?scriptVersionId=356721456).

Next task: review this completed baseline and register a separate ModernBERT comparison or a shared-cohort multimodal protocol. Do not rerun or tune this BERT against its observed test scores. Full image coverage remains an unresolved prerequisite for a full-cohort text+image benchmark.

GitHub: [verified results/documentation commit](https://github.com/panvenaidu/Fake-News-Detection/commit/5527824302480de39cafd85a5a9a1c2b8cc68fd7). Remote `main` matched this hash after the push. Numerical results, predictions, source and reports are backed up; weights and raw data remain local/private cloud.
