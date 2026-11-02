# Image-only ResNet-50 results

One seed 42 experiment on the dataset (provided by the faculty), using the frozen usable-image cohort. 4 complete training epochs and 4 full validations. The registered maximum was four epochs. Selection used full validation Macro-F1, then lower loss, then earlier epoch. Epoch 4 won. One frozen 59,270-row public-test evaluation completed and passed independent saved-CSV verification.

## Results

| Metric | Selected validation | Final public test | Paper validation | Paper test |
|---|---:|---:|---:|---:|
| Accuracy | 80.9339% | 81.1557% | 75.29% | 75.49% |
| Micro-F1 | 0.809339 | 0.811557 | not reported | not reported |
| Macro-F1 | 0.656487 | 0.661796 | not reported | not reported |
| Weighted-F1 | 0.802383 | 0.804935 | not reported | not reported |
| Balanced accuracy | 62.4213% | 62.9919% | not reported | not reported |
| Loss | 0.583574 | 0.584384 | not reported | not reported |

Validation accuracy is numerically +5.6439 percentage points against the paper image-only ResNet-50 value. Public-test accuracy is +5.6657 points. The +1-point aspirations were 76.29% validation / 76.49% test. Validation target met. Test target met.

The paper uses fixed ImageNet features and a different downstream feature/training pipeline. This run fine-tunes ResNet-50 with ImageNet1K V2 weights end-to-end. The approved usable cohort excludes 491 original decoding failures. The paper/release 335-row discrepancy and 3,561 cross-split image-byte duplicate groups remain limitations. This single-seed numerical comparison does not establish controlled superiority, significance or state of the art. [Original paper, Table 4](https://arxiv.org/html/1911.03854v2).

## Training and checkpoint selection

| Epoch | Train loss | Val accuracy | Micro-F1 | Macro-F1 | Weighted-F1 | Balanced accuracy | Val loss | Cumulative updates / AMP skips |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 0.680355 | 78.2155% | 0.782155 | 0.624984 | 0.770977 | 58.9570% | 0.623623 | 17606 / 7 |
| 2 | 0.518336 | 80.6472% | 0.806472 | 0.639919 | 0.795233 | 60.4375% | 0.560817 | 35212 / 14 |
| 3 | 0.445334 | 80.8766% | 0.808766 | 0.653316 | 0.801849 | 62.4476% | 0.550046 | 52817 / 22 |
| 4 | 0.366205 | 80.9339% | 0.809339 | 0.656487 | 0.802383 | 62.4213% | 0.583574 | 70422 / 30 |

Epoch counts are passes within one experiment. Training accuracy/F1 were not exported. Training loss is sample-weighted during optimization. Validation and test loss come from per-row FP32 cross-entropy. A higher accuracy epoch can lose to higher Macro-F1 under the registered rule. Small Macro-F1 gains may win selection without resetting the separate 0.001 patience reference.

## Model and protocol

Pixels → strict RGB decoding → registered 224×224 transform → ImageNet1KV2 ResNet-50 → 2,048 pooled image features → dropout 0.2 → six-logit linear head. All layers fine-tuned. No text encoder, titles, OCR, captions, source metadata, projections or fusion enter the predictor. AdamW 1e-4, weight decay 1e-4 on matrices/convolutions and zero on bias/normalization, clip 1.0, FP16 AMP with FP32 parameters. Effective batch 32, physical batch 32; config is authoritative. Linear warmup 7,046 successful steps, decay over 70,452 planned boundaries; scheduler advances only on successful updates. Early-stop evaluation begins after epoch 3, patience 2, delta 0.001.

Official usable membership remains 563,601 train / 59,299 validation / 59,270 test. Original TSVs, IDs, split assignments and six-class labels are unchanged. The 491 exclusions are 399 train / 43 validation / 49 test, comprising 489 False Connection and 2 Satire/Parody. Image-only starts from ImageNet, without the supervised fusion-trained encoder. The research categories are 0 True, 1 Satire/Parody, 2 Misleading Content, 3 Imposter Content, 4 False Connection and 5 Manipulated Content. A prediction describes a research-defined category and does not independently establish factual truth.

## Per-class evaluation and confusions

### Validation

| Class | Precision | Recall | F1 | Support |
|---|---:|---:|---:|---:|
| True | 0.769295 | 0.874957 | 0.818731 | 23320 |
| Satire/Parody | 0.738237 | 0.561648 | 0.637948 | 3520 |
| Misleading Content | 0.682395 | 0.643788 | 0.662530 | 11277 |
| Imposter Content | 0.375648 | 0.117124 | 0.178571 | 1238 |
| False Connection | 0.969777 | 0.951711 | 0.960659 | 17768 |
| Manipulated Content | 0.792787 | 0.596048 | 0.680483 | 2176 |

Confusion rows are gold labels and columns are predictions, in label order 0–5.

| Gold / Pred | 0 | 1 | 2 | 3 | 4 | 5 |
|---|---:|---:|---:|---:|---:|---:|
| 0 | 20404 | 216 | 2301 | 60 | 201 | 138 |
| 1 | 1082 | 1977 | 235 | 29 | 115 | 82 |
| 2 | 3508 | 148 | 7260 | 121 | 178 | 62 |
| 3 | 596 | 48 | 385 | 145 | 22 | 42 |
| 4 | 403 | 160 | 270 | 10 | 16910 | 15 |
| 5 | 530 | 129 | 188 | 21 | 11 | 1297 |

Row-normalized confusion percentages

| Gold / Pred | 0 | 1 | 2 | 3 | 4 | 5 |
|---|---:|---:|---:|---:|---:|---:|
| 0 | 87.50% | 0.93% | 9.87% | 0.26% | 0.86% | 0.59% |
| 1 | 30.74% | 56.16% | 6.68% | 0.82% | 3.27% | 2.33% |
| 2 | 31.11% | 1.31% | 64.38% | 1.07% | 1.58% | 0.55% |
| 3 | 48.14% | 3.88% | 31.10% | 11.71% | 1.78% | 3.39% |
| 4 | 2.27% | 0.90% | 1.52% | 0.06% | 95.17% | 0.08% |
| 5 | 24.36% | 5.93% | 8.64% | 0.97% | 0.51% | 59.60% |

### Public test

| Class | Precision | Recall | F1 | Support |
|---|---:|---:|---:|---:|
| True | 0.775844 | 0.876079 | 0.822921 | 23507 |
| Satire/Parody | 0.754781 | 0.572851 | 0.651351 | 3514 |
| Misleading Content | 0.678414 | 0.652651 | 0.665283 | 11297 |
| Imposter Content | 0.368984 | 0.112745 | 0.172716 | 1224 |
| False Connection | 0.970931 | 0.950870 | 0.960796 | 17423 |
| Manipulated Content | 0.807298 | 0.614317 | 0.697709 | 2305 |

Confusion rows are gold labels and columns are predictions, in label order 0–5.

| Gold / Pred | 0 | 1 | 2 | 3 | 4 | 5 |
|---|---:|---:|---:|---:|---:|---:|
| 0 | 20594 | 193 | 2305 | 47 | 215 | 153 |
| 1 | 1071 | 2013 | 249 | 16 | 93 | 72 |
| 2 | 3399 | 157 | 7373 | 133 | 164 | 71 |
| 3 | 597 | 26 | 427 | 138 | 8 | 28 |
| 4 | 348 | 159 | 320 | 15 | 16567 | 14 |
| 5 | 535 | 119 | 194 | 25 | 16 | 1416 |

Row-normalized confusion percentages

| Gold / Pred | 0 | 1 | 2 | 3 | 4 | 5 |
|---|---:|---:|---:|---:|---:|---:|
| 0 | 87.61% | 0.82% | 9.81% | 0.20% | 0.91% | 0.65% |
| 1 | 30.48% | 57.29% | 7.09% | 0.46% | 2.65% | 2.05% |
| 2 | 30.09% | 1.39% | 65.27% | 1.18% | 1.45% | 0.63% |
| 3 | 48.77% | 2.12% | 34.89% | 11.27% | 0.65% | 2.29% |
| 4 | 2.00% | 0.91% | 1.84% | 0.09% | 95.09% | 0.08% |
| 5 | 23.21% | 5.16% | 8.42% | 1.08% | 0.69% | 61.43% |

Paper per-class F1, precision, recall, balanced accuracy and loss are not reported. Table 6 error counts are not F1. Lowest test F1 classes are Imposter Content, Satire/Parody. Largest off-diagonal confusions areMisleading Content → True (3399 posts), True → Misleading Content (2305 posts), Satire/Parody → True (1071 posts). Image-only evidence cannot directly establish a headline–image mismatch.

## Other completed modalities

The completed text-only BERT result used the original full released title cohort and selected epoch 4. Its test accuracy is 82.3901% and Macro-F1 0.774566. The completed text+image result uses the same usable-image cohort as this experiment and selected epoch 4. Its test accuracy is 88.1458%, Macro-F1 0.826415. These runs have different optimization and initialization. Fusion also used a supervised text warm start, so the descriptive differences do not isolate the effect of adding text.

## Verification, runtime and artifacts

Independent CPU readback checked all saved manifest members, model/optimizer/scheduler/scaler state, RNG/sampler/cursor, every complete validation export and the complete held-out test export. Exact IDs/golds/order/supports, six normalized probabilities, argmax, per-row CE, all aggregate/class metrics and raw/normalized confusions passed. Selected weights strict-loaded from saved private bytes. The separate evaluator starts in a fresh process after the pre-test freeze receipt and performs a validation-only logit reload check. CUDA recovery was independently exercised before release.

Kaggle job [364917396](https://www.kaggle.com/code/rocky62/urop-image-only-resnet-50?scriptVersionId=364917396). Actual runtime versions are recorded in the resolved protocol. The model usedTesla T4 device 0 from a T4×2 allocation. Controller-measured training/evaluation wall time was 17734.5 seconds, excluding initial notebook startup and final saved-output transfer. Preflight speeds were 143.66 train / 161.82 evaluation images/s, with their measured batch/environment. These are preflight measurements.

Attempt `OFFICIAL-6W-IMAGE-USABLE-v1_seed 42_20261102T145600Z`. Selected epoch 4, weights SHA-256 `5bb54f3bc57d747aeb63e6be9e5f76d2ecbb4cf86e62d6b02c84db132a76ecdf`. Latest recovery SHA-256 `0b1a5846c2d9cf34569cab5ab019cc8b63d4a442b883db790a9ddaa5203c077b`. Private manifest SHA-256 `cd265641e5cb01e9a60ee034df649ca20881ba3d08ca972ddf4044fc844aeae8`. Private archive/readback record `results/experiments/image_only/ARCHIVE_READBACK_20261103.json`. Small numerical evidence `results/experiments/image_only/OFFICIAL-6W-IMAGE-USABLE-v1_seed 42_20261102T145600Z/final_364917396`. Independent verification `results/experiments/image_only/IMAGE_ONLY_SAVED_VERIFIED_20261103.json`. Large predictions, raw images and tensors remain in ignored private storage and the private saved Kaggle version.

GitHub backup is pending until the intended results commit is pushed and independently read back. The completion receipt records the final verified backup. The existing main workflow/progress/comparison pages must use this new receipt when their image-only status is updated.
