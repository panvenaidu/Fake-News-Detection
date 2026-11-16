# Image-only six-class ViT fine-tuning

Verified full-test accuracy was **80.3948%** on **59,270** posts. The model missed the 82.00% target (-1.6052 pp). It scored -0.7609 pp relative to historical fine-tuned ResNet-50 and +14.7461 pp relative to frozen ViT-B/16.

The selected deit3_base_patch16_224.fb_in22k_ft_in1k used deit3_base_patch16_224.fb_in22k_ft_in1k (initialization SHA-256 `408c1eb6cef049d90ee2615a6df47a879385be42e69763e290ddafc23daeb84b`). Selected epoch 3, seed 42, encoder LR 3.0e-05. Full trial used 6.13 h of measured training/validation time across sessions. The saved test version is 369892645.

| Test cohort | Accuracy | Macro-F1 | Weighted-F1 | Balanced accuracy | Cross-entropy |
|---|---:|---:|---:|---:|---:|
| Full test (59,270) | 80.3948% | 0.660470 | 0.799002 | 62.5296% | 0.575887 |
| No exact training byte match (56,052) | 80.3664% | 0.662357 | 0.798778 | 62.7103% | 0.580113 |

Full accuracy 95% intervals: Wilson 80.0732%–80.7124%; exact-byte grouped Poisson bootstrap 79.6961%–81.0274%. These intervals describe evaluation-sample uncertainty, not variation across seeds.

Paired Historical ResNet-50: -0.7609 pp (row bootstrap 95% interval -1.0494 to -0.4674 pp). Exact-byte grouped interval: -1.1558 to -0.4167 pp.

Paired Frozen ViT-B/16: +14.7461 pp (row bootstrap 95% interval +14.3496 to +15.1308 pp). Exact-byte grouped interval: +14.0858 to +15.3036 pp.

## Full-cohort validation

| Trial | Epoch | Accuracy | Macro-F1 | Balanced accuracy | CE | Imposter recall |
|---|---:|---:|---:|---:|---:|---:|
| full_seed42 | 1 | 75.1783% | 0.574589 | 55.3691% | 0.694963 | 1.6155% |
| full_seed42 | 2 | 76.6202% | 0.600853 | 55.7868% | 0.659228 | 6.9467% |
| full_seed42 | 3 | 77.6995% | 0.628731 | 59.1923% | 0.637818 | 11.0662% |
| full_seed42 | 4 | 77.0688% | 0.627500 | 59.8108% | 0.665318 | 10.0162% |
| full_seed42 | 5 | 74.9810% | 0.612945 | 58.3622% | 0.747386 | 9.0468% |
| full_seed42 | 6 | 76.8462% | 0.629862 | 60.7396% | 0.803091 | 13.1664% |
| deit3_seed42 | 1 | 78.2796% | 0.602979 | 57.6387% | 0.609571 | 1.6155% |
| deit3_seed42 | 2 | 80.1261% | 0.639022 | 58.8696% | 0.577035 | 11.7124% |
| deit3_seed42 | 3 | 80.2577% | 0.655443 | 62.1527% | 0.582247 | 12.6010% |
| deit3_seed42 | 4 | 78.7265% | 0.649430 | 62.8253% | 0.693523 | 15.3473% |
| deit3_seed42 | 5 | 78.4769% | 0.639940 | 61.8729% | 0.766084 | 15.8320% |
| deit3_seed42 | 6 | 77.9440% | 0.640199 | 62.6252% | 1.130615 | 17.7706% |

The independent receipt includes each pilot epoch and recall for all six classes.

## Full test: per-class metrics

| Label | Precision | Recall | F1 | Support |
|---|---:|---:|---:|---:|
| True | 0.760733 | 0.878887 | 0.815553 | 23,507 |
| Satire/Parody | 0.837506 | 0.523620 | 0.644371 | 3,514 |
| Misleading Content | 0.674540 | 0.687616 | 0.681015 | 11,297 |
| Imposter Content | 0.407035 | 0.132353 | 0.199753 | 1,224 |
| False Connection | 0.981591 | 0.905872 | 0.942212 | 17,423 |
| Manipulated Content | 0.747659 | 0.623427 | 0.679915 | 2,305 |

## No exact training byte match: per-class metrics

| Label | Precision | Recall | F1 | Support |
|---|---:|---:|---:|---:|
| True | 0.759486 | 0.882094 | 0.816211 | 22,238 |
| Satire/Parody | 0.834653 | 0.531278 | 0.649275 | 3,373 |
| Misleading Content | 0.681919 | 0.686151 | 0.684028 | 10,795 |
| Imposter Content | 0.409326 | 0.137631 | 0.205997 | 1,148 |
| False Connection | 0.980796 | 0.901895 | 0.939692 | 16,309 |
| Manipulated Content | 0.745087 | 0.623572 | 0.678936 | 2,189 |

Independent readback checked full split IDs and labels, probability rows, per-row loss, confusion matrices, exact-byte subset membership, optimizer update counts and validation-only selection. The selected checkpoint reproduced a fixed validation batch in a fresh process. The full and row-normalized confusion matrices are in the saved verification JSON.

The benchmark was used by earlier models. Exact byte hashes do not detect near duplicates or overlap with external pretraining. The ResNet recipe, pretraining, and macro-F1-first selection differ; this is a descriptive comparison, not a matched architecture ablation.
