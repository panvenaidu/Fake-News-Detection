# UROP image-only Vision Transformer 83% experiment

## Run status

All four two-epoch pilots and the four-epoch full-frame trial completed. The frozen checkpoint is full-frame epoch 3, with 83.0199497462% validation accuracy (49,230 / 59,299). The private official test version has been submitted once; its results and independent CPU verification remain pending. Validation accuracy is not test accuracy.

| Phase | Exact saved Kaggle version | Status |
|---|---|---|
| Initial GPU preflight | [370020449](https://www.kaggle.com/code/rocky62/urop-image-only-vit-83-preflight/log?scriptVersionId=370020449) | DeiT checks passed, DINOv2 attention-key mismatch |
| Corrected GPU preflight | [370024175](https://www.kaggle.com/code/rocky62/urop-image-only-vit-83-preflight/log?scriptVersionId=370024175) | All four recipes passed reload and recovery checks |
| Pilots and full trial | [370028173](https://www.kaggle.com/code/rocky62/urop-image-only-vit-83-training/log?scriptVersionId=370028173) | Completed; epoch 3 selected and frozen |
| Frozen official test | [370100411](https://www.kaggle.com/code/rocky62/urop-image-only-vit-83-frozen-test?scriptVersionId=370100411) | Running; outcome pending |
| Independent CPU readback | Pending | Requires saved test output |

Pilot validation accuracy after epochs 1 and 2, respectively: crop 72.9422%, 75.9827%; full-frame 76.2660%, 77.5696%; layer decay 73.3807%, 74.0164%; DINOv2 75.2104%, 77.5409%. Full-frame won on unrounded accuracy. DINOv2 was within 0.25 percentage points, but a second full run was not budgeted while preserving the six-hour reserve. The full-frame epoch 3 checkpoint SHA-256 is `97cb89e986c2481d65dd61ff4f2570a907898c885c34ea2e9460385ce01ae300`; its independent reload receipt SHA-256 is `82ac76c8a93f0103decb9de14cc6be7e339849979d99f4516969925bc50d9a50`. Epoch 4 scored 82.2847%.

Kaggle showed 14 h 48 min used before the training run and 19 h 59 min used before the test. The training version ran for 18,613 seconds. No resolution comparison was performed; the selected validation score exceeded 83%. No fresh faculty holdout was registered.

## Cohort audit

The pinned Kaggle inputs are packed dataset version 1 (21277535) and quality-check output 362643633. The loader compared the mounted pinned manifest, coverage report and SQLite index hashes and reconciled the retained IDs, six-class labels and split membership against the hashed original faculty TSVs and approved 491 exclusions. These checks passed on Kaggle. The separately audited local historical ResNet prediction export matches the 59,270 official test IDs and labels and records 48,101 correct predictions (81.1557%). The local pinned index agrees exactly with all 682,170 approved IDs. Its image SHA-256 field identifies 56,052 official test images with no exact training bytes.

| Artifact | SHA-256 |
|---|---|
| Faculty cohort registration | `3fe0b622958a1eee6732789d4f7acf6b450c0e3bda87312e5cbb6500fb405ce5` |
| Approved exclusion IDs | `e5b32e3dc100460da857da499455c885f522b73059304233eb94b9b7d90fc065` |
| Faculty packed manifest | `96c84e9453401cc4a24999c41cdbeb182dafd08771383cf1c75feea9c3001caf` |
| Packed coverage receipt | `afe8c723f91fe74f791908e0c16fab94d919af64c7cb7c9b5a37e676361d95e5` |
| Packed index | `fc8dc03a4f773da5762891c8392375add5fb8087251b527f3b37a880308e6018` |
| Historical ResNet-50 test predictions | `ca2c8afb877146b2ae892e60a03f114acd8cb184d2d6e1cd861c2f65b5eb41d3` |

Historical DeiT III B/16 remains the verified ViT baseline at 80.3948% test accuracy until the new test predictions are independently verified.

## Implementation checks

The original training engine and baseline reports were preserved. Local checks verified that extreme aspect ratios produce a centered 224 × 224 RGB tensor, the first and last DeiT encoder blocks and head receive the specified relative learning rates, and the DINOv2 base tensor keys and shapes match the pinned checkpoint header. The separate GPU preflight is responsible for verifying runtime compatibility, model updates, throughput and checkpoint recovery on actual faculty images.

The [experiment source and runbook](../../Training/Image%20Only/ViT%2083/README.md) are in the current local project checkout.

