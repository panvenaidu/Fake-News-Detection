# UROP image-only Vision Transformer 83% experiment

Frozen recipe **full_frame**, epoch 3, seed 42.
Full validation accuracy 83.0199% (49,230/59,299).
Independent full-test accuracy **83.1281%** (49,270/59,270).
Difference from 83.00% +0.1281 percentage points. Additional correct predictions needed 0.

| Cohort | Accuracy | Macro-F1 | Balanced accuracy | Imposter Content recall |
|---|---:|---:|---:|---:|
| Full official test (59,270) | 83.1281% | 0.713128 | 69.1492% | 17.2386% |
| No exact training byte match (56,052) | 82.8160% | 0.711142 | 68.9987% | 17.8571% |

| Baseline | Paired difference (pp) | Correct only for new model | Correct only for baseline |
|---|---:|---:|---:|
| ResNet-50 | +1.9723 | 4,694 | 3,525 |
| DeiT III B/16 | +2.7333 | 4,924 | 3,304 |

The CPU verification JSON includes raw and normalized confusion matrices, per-class metrics, paired bootstrap intervals, and cohort and prediction hashes.
The prior models used this official test as well. No separate holdout was registered.

## Selection and execution

All four recipes used seed 42, effective batch 64, the same 30,000-image training subset, and all 59,299 validation images after each epoch. The best checkpoint per recipe, ranked on unrounded accuracy, was:

| Recipe | Epoch 1 accuracy | Epoch 2 accuracy | Epoch 2 macro-F1 | Epoch 2 cross-entropy |
|---|---:|---:|---:|---:|
| DeiT crop | 72.9422% | 75.9827% | 0.581857 | 0.683843 |
| DeiT full-frame padding | 76.2660% | 77.5696% | 0.621221 | 0.646082 |
| DeiT layer-wise decay | 73.3807% | 74.0164% | 0.556758 | 0.731653 |
| DINOv2 | 75.2104% | 77.5409% | 0.605021 | 0.636570 |

The full-frame recipe won. DINOv2 was within 0.25 percentage points, but a second full run did not fit the registered budget. The four-epoch full-frame run selected epoch 3 using validation only; epoch 4 reached 82.2847%. The selected checkpoint recorded six skipped mixed-precision updates by epoch 3. Its SHA-256 is `97cb89e986c2481d65dd61ff4f2570a907898c885c34ea2e9460385ce01ae300`. The fresh-process fixed-batch reload receipt is `82ac76c8a93f0103decb9de14cc6be7e339849979d99f4516969925bc50d9a50`.

The selected DeiT initialization revision is `b5791d4983082b0c680da556954beb5b1962e85f`, weights SHA-256 `408c1eb6cef049d90ee2615a6df47a879385be42e69763e290ddafc23daeb84b`. DINOv2 base revision is `f9e44c814b77203eaa57a6bdbbd535f21ede1415`, weights SHA-256 `d73036b56966966d07975d696bde331762f37297e2f095de8cea0040c3aa0841`. RGB pixels alone were inputs; each recipe used one six-class Vision Transformer.

Preflight observed 15.2 free GPU hours and protected six hours; its measured per-epoch full-frame estimate was 3,988 seconds. All pilots and one four-epoch full trial fit the planned budget. The optional resolution comparison was not run. Training version runtime was 18,613 seconds; the frozen test ran for 843.8 seconds. The 30-hour ceiling applied to free quota, with 14 h 48 min already used before training and 19 h 59 min before test.

## Verification and cohort

The independent CPU process checked the saved selection and prediction receipts, IDs and labels, probabilities and metrics, the official cohort, exact-byte-match subset, and paired baseline predictions. It produced [the complete verification JSON](VIT83_CPU_VERIFICATION.json), including per-class metrics, raw and row-normalized confusion matrices, and paired bootstrap intervals. The test prediction SHA-256 is `e194780fb370c9fb0da562eee9673afe08cef0fca9250ec4f68f81887e99e154`; its saved receipt SHA-256 is `f027bc7f6b78e5663b3934b6d77f98f39b9abeb3373beca91a66076f110b2f07`. The frozen test was evaluated once.

The original approved cohort has 563,601 train, 59,299 validation, and 59,270 test images, with 491 approved exclusions. Train, validation, and test manifest SHA-256 values respectively are `01f91eacaec0d82c488c6af20b5bb575412cde0065748f47874cb7f16c0351ad`, `58cf89f2fe14d3735318d331ce7e8608d80d48f1a91db40ec337d237d8fbe09f`, and `1f4265585c1caaddcd42f88d3ab3f6faf3f79a0827040aca3e281ef1de3be25e`. Approved exclusion IDs SHA-256 is `e5b32e3dc100460da857da499455c885f522b73059304233eb94b9b7d90fc065`.

Full test confusion matrix (rows are true class, columns predicted class; order: True, Satire/Parody, Misleading Content, Imposter Content, False Connection, Manipulated Content):

```text
20647   300  1746   71    558   185
  596  2637   139   24     70    48
 2994   118  7571  198    314   102
  563    34   327  211     54    35
  519    59   267   24  16523    31
  411    44   105   32     32  1681
```

The low 17.2386% Imposter Content recall (211 of 1,224) remains a material weakness despite meeting the overall accuracy target. The 95% Wilson interval for overall test accuracy is 82.8244%–83.4274%. Paired byte-group bootstrap 95% intervals for the difference are +1.6654 to +2.2649 percentage points against ResNet-50 and +2.3656 to +3.1136 against DeiT. Both prior baselines have also been evaluated on this test, so these results do not replace a fresh independent holdout.

## Saved Kaggle versions

- [Initial preflight 370020449](https://www.kaggle.com/code/rocky62/urop-image-only-vit-83-preflight/log?scriptVersionId=370020449): DeiT checks passed; DINO attention mapping needed correction.
- [Corrected preflight 370024175](https://www.kaggle.com/code/rocky62/urop-image-only-vit-83-preflight/log?scriptVersionId=370024175): all four recipes, cohort, throughput, reload and recovery checks passed.
- [Pilots and full training 370028173](https://www.kaggle.com/code/rocky62/urop-image-only-vit-83-training/log?scriptVersionId=370028173).
- [Single frozen test 370100411](https://www.kaggle.com/code/rocky62/urop-image-only-vit-83-frozen-test/output?scriptVersionId=370100411).
- [Independent CPU verification 370301005](https://www.kaggle.com/code/rocky62/urop-image-only-vit-83-cpu-verification/output?scriptVersionId=370301005).
