# E002 Seed-42 Canonical Result Preservation

**Run:** `E002-bert-base-uncased-6way-BP6Wv1-s42`  
**Protocol:** `BP-6W-v1`  
**Model:** `bert-base-uncased`  
**Source:** saved `urop.ipynb`, E002 seed-42 completed output (cell 34)

> Preservation note: this file is reconstructed from the saved notebook output. If the original machine-generated run artifacts are later recovered, those remain authoritative.

## Data and environment

- Fakeddit verified paired cohort: 75,995
- Train / validation / test: 62,635 / 6,685 / 6,675
- Manifest SHA-256: `fc74cb42288d366131ac764bf02f9212bacd7cab0af68442a003beaaff9fde20`
- Git commit: `4ff4d996e9b50ad2b005ef4234c62a819e9e5992`
- GPU: Tesla T4, ~14.56 GB VRAM
- AMP: float16
- Total/trainable parameters: 109,486,854 / 109,486,854
- Selected epoch: 4

## Validation

- Accuracy: 0.7801047120
- Macro-F1: 0.7021675464
- Balanced accuracy: 0.6691436187
- Weighted-F1: 0.7767974232
- Loss: 0.7581398568

## Test

- Accuracy: 0.7809737828
- Macro-F1: 0.6965845390
- Balanced accuracy: 0.6693357334
- Weighted-F1: 0.7781740475
- Loss: 0.7508469498

## Compute

- Runtime: 2113.08 s (35.22 min)
- Training time: 1548.38 s (25.81 min)
- Throughput: 242.71 samples/s
- Peak GPU memory: 3238541312 bytes

## Test per-class F1

- True: 0.8365608056
- Satire/Parody: 0.6061452514
- Misleading Content: 0.6717680226
- Imposter Content: 0.4954128440
- False Connection: 0.8258823529
- Manipulated Content: 0.7437379576

## Test confusion matrix

| Actual \\ Predicted | True | Satire/Parody | Misleading Content | Imposter Content | False Connection | Manipulated Content |
|---|---|---|---|---|---|---|
| True | 2160 | 45 | 203 | 9 | 144 | 21 |
| Satire/Parody | 71 | 217 | 20 | 5 | 67 | 10 |
| Misleading Content | 185 | 19 | 834 | 1 | 198 | 7 |
| Imposter Content | 38 | 7 | 15 | 54 | 20 | 6 |
| False Connection | 94 | 28 | 153 | 7 | 1755 | 10 |
| Manipulated Content | 34 | 10 | 14 | 2 | 19 | 193 |

## Current project status

- E002 seed 42: canonical clean run completed.
- E002 seeds 43 and 44: pending GPU access.
- E003 ResNet-50: pending.
- E004 BERT + ResNet-50: pending.
- Advanced candidates after baselines: CLIP / semantic alignment / contrastive learning; other fusion approaches remain candidates.
- HGT/HGAT remains a future graph/social-context direction subject to data availability and terminology confirmation.
