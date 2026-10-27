# Multimodal verified scientific results

2026-10-28T03:08:18.467384+05:30

Scientific train/validation/test verified; final documentation/remote-backup acceptance must be checked separately.

## Protocol and completion
- Same seed42 experiment; accepted Part1 plus continuation. Validated epochs:4; next epoch5, consumed cursor0, phasetrain.
- Selected epoch:4; validation Macro-F1, then lower loss, then earlier epoch. Weights SHA256 `1c5c7bd312405589776776a1ea7aca33f1a18f5bb8a45d80652b022dc2b835a4`.
- [Faculty dataset](https://drive.google.com/drive/folders/1DuH0YaEox08ZwzZDpRMOaFpMCeRyxiEF): usable563601train/59299validation/59270test; exactly491approved strict decode exclusions; official splits/labels unchanged.
- BERT-base selected text epoch4 warm start + ImageNetV2 ResNet50; both fine-tuned; independent512projections+LayerNorm; elementwise max;256GELU/dropout.2;6logits.
- Kaggle TeslaT4 device0, original frozen source/config/environment; same four-epoch schedule; no new seed/model/data.

## Validation and test metrics
| Metric | Selected validation | Held-out public test | Paper validation | Paper test |
|---|---:|---:|---:|---:|
| Accuracy | 88.5074% | 88.1458% | 86.00% | 85.88% |
| Micro-F1 | 0.885074 | 0.881458 | Not reported | Not reported |
| Macro-F1 | 0.829303 | 0.826415 | Not reported | Not reported |
| Weighted-F1 | 0.884814 | 0.881317 | Not reported | Not reported |
| Balanced accuracy | 80.8302% | 80.8249% | Not reported | Not reported |
| Cross-entropy loss | 0.694795 | 0.723866 | Not reported | Not reported |

Selected validation is +2.5074 percentage points versus the paper’s86.00% reference. Final test is +2.2658 points versus85.88%; the +1-point test aspiration was met.

## Class results: validation
| Class | Precision | Recall | F1 | Support |
|---|---:|---:|---:|---:|
| True | 0.875725 | 0.905918 | 0.890566 | 23320 |
| Satire/Parody | 0.829276 | 0.764489 | 0.795565 | 3520 |
| Misleading Content | 0.798045 | 0.839940 | 0.818457 | 11277 |
| Imposter Content | 0.833536 | 0.554120 | 0.665696 | 1238 |
| False Connection | 0.976331 | 0.937922 | 0.956741 | 17768 |
| Manipulated Content | 0.850161 | 0.847426 | 0.848792 | 2176 |

## Class results: held-out test
| Class | Precision | Recall | F1 | Support |
|---|---:|---:|---:|---:|
| True | 0.875192 | 0.899094 | 0.886982 | 23507 |
| Satire/Parody | 0.820831 | 0.753557 | 0.785757 | 3514 |
| Misleading Content | 0.791851 | 0.837833 | 0.814194 | 11297 |
| Imposter Content | 0.802326 | 0.563725 | 0.662188 | 1224 |
| False Connection | 0.974573 | 0.937152 | 0.955496 | 17423 |
| Manipulated Content | 0.849656 | 0.858134 | 0.853874 | 2305 |

## Interpretation and limitations
This is a numerical reference comparison, not a controlled paper reproduction or statistical superiority claim. The paper uses another feature/fine-tuning pipeline; one seed and extra text warm-start compute;335paper/release-row discrepancy;491class-skewed exclusions;3561cross-split image-byte hash groups. Dataset labels are weak supervision, not independent factual-truth verification. Paper Table6 error proportions are not class F1.

Original source exports/private weights: `data/cloud_recovery/final_saved_output_20261028_362955511/extracted/urop_mm_final_20261028/OFFICIAL-6W-MM-USABLE-v2_seed42_20261027`. Independent readback: `results/MM_FINAL_SAVED_VERIFIED_20261028.json`. Recovery proof: `{"loaded": {"file": "e7d74710ee1f498e9511e63f9db4783e.pt", "sha256": "0ebd4b001603802d26c2c48a03bccfa94afd95a6484536c2d14eb6bc5ecb7e26", "bytes": 1608465078, "cursor": 0}, "fallback_errors": []}`.

Paper: [https://arxiv.org/html/1911.03854v2](https://arxiv.org/html/1911.03854v2). Current cloud run/version and Git acceptance must be read from the latest Part2 receipts. No public/raw-data/weight publication is implied.

## Architecture size
133977414 parameters, all 133977414 trainable, verified by strict checkpoint key/shape metadata; no local forward pass. Evidence: `results/MM_PART2_PARAMETER_METADATA_20261027.json`.

## VERIFIED text + image completion — 28 October2026

Four full epochs and four full59,299-row validations completed in the SAME seed42 experiment. Epoch4 selected by validation Macro-F1, selection frozen BEFORE the single full59,270-row public test. Independent saved-byte verification passed: exact IDs/golds/probabilities/per-row CE, all six metrics, class reports, raw/normalized confusions, strict selected-model load, validation-only GPU reload/logit roundtrip, full recovery state and all artifact hashes. ZIP75members passed CRC/safe paths. No test-driven tuning, new seed/model/cohort or image-only training.

Selected validation: accuracy88.5073947%,micro-F1.8850739473,Macro-F1.8293028761,weighted-F1.8848143053,balancedaccuracy80.8302355%,loss.6947946472. Test: accuracy88.1457736%,micro-F1.8814577358,Macro-F1.8264151321,weighted-F1.8813174384,balancedaccuracy80.8249360%,loss.7238658786. Epoch4 had slightly lower accuracy and worse loss than epoch3 but higher Macro-F1, so selection follows the registered rule. One experiment, not four independent replications.

Paper matching accuracy86.00%validation/85.88%test: numerical deltas+2.5074/+2.2658percentagepoints, exceeding the+1-point aspiration on both splits. Different feature/fine-tuning pipeline, extra text warm start,491class-skewed exclusions,335paper/release discrepancy,3561cross-split image-byte groups and one seed prevent a controlled-superiority claim. Paper F1/loss values not reported.

Authoritative report: results/MULTIMODAL_FINAL_REPORT_20261028.md. Faculty HTML: results/UROP_Multimodal_Final_20261028.html. Verification: results/MM_FINAL_SAVED_VERIFIED_20261028.json. Small numerical artifacts: results/experiments/multimodal/OFFICIAL-6W-MM-USABLE-v2_seed42_20261027/final_362955511/. Private archive manifest: results/MM_FINAL_DOWNLOAD_READBACK_20261028.json; tensors/per-ID outputs stay ignored/private. Recoveryepoch5/cursor0,70422successfulupdates+30AMPskips=70452registeredboundaries. Do not train epoch5 or rerun test.

Kaggle https://www.kaggle.com/code/rocky62/urop-mm-final-continuation-20261028?scriptVersionId=362955511 : Successful,2929.7s batch, TeslaT4device0. Test inference410.813s; measured test peak allocated783636992bytes (not training peak). Fresh quota12:28/30h used, approximately17h32left. Original source/config/data/environment preserved. Current Goal API returnednull; no duplicate Goal/task/schedule created. Legacy automation view rendered a card but no local automation record was found; disabling it is NOT verified. This completion receipt must prevent duplicate work if an old heartbeat arrives.

```text
Text-only       ██████████ 100%
Text + image    ██████████ 100%
Image-only      ██░░░░░░░░  20%
Overall         ███████▎░░  73%
```

Five equally weighted workflow stages, all complete for multimodal; overall=(100+100+20)/3=73.333%. These are workflow percentages, not accuracy. Next research task is image-only; it has NOT started. Older partial/running/pending records below are historical and superseded by this verified completion.

Private attempt: `data/cloud_recovery/final_saved_output_20261028_362955511/extracted/urop_mm_final_20261028/OFFICIAL-6W-MM-USABLE-v2_seed42_20261027`. All sizes/SHA256: results/MM_FINAL_SAVED_VERIFIED_20261028.json.
