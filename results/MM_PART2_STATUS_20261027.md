# Multimodal Part2 status

2026-10-27T20:01:48.584573+00:00

PARTIAL Part2: final registered training and/or held-out testing remains unfinished.

## Protocol and completion
- Same seed42 experiment; accepted Part1 plus continuation. Validated epochs:3; next epoch4, consumed cursor515296, phasetrain.
- Selected epoch:3; validation Macro-F1, then lower loss, then earlier epoch. Weights SHA256 `360a436a1af6d5a9a6375dc26b2e8e8a0fa30e9cf3bafb157d027d39472d960d`.
- [Faculty dataset](https://drive.google.com/drive/folders/1DuH0YaEox08ZwzZDpRMOaFpMCeRyxiEF): usable563601train/59299validation/59270test; exactly491approved strict decode exclusions; official splits/labels unchanged.
- BERT-base selected text epoch4 warm start + ImageNetV2 ResNet50; both fine-tuned; independent512projections+LayerNorm; elementwise max;256GELU/dropout.2;6logits.
- Kaggle TeslaT4 device0, original frozen source/config/environment; same four-epoch schedule; no new seed/model/data.

## Validation and test metrics
| Metric | Selected validation | Held-out public test | Paper validation | Paper test |
|---|---:|---:|---:|---:|
| Accuracy | 88.5344% | Pending | 86.00% | 85.88% |
| Micro-F1 | 0.885344 | Pending | Not reported | Not reported |
| Macro-F1 | 0.827924 | Pending | Not reported | Not reported |
| Weighted-F1 | 0.884944 | Pending | Not reported | Not reported |
| Balanced accuracy | 80.8381% | Pending | Not reported | Not reported |
| Cross-entropy loss | 0.587545 | Pending | Not reported | Not reported |

Selected validation is +2.5344 percentage points versus the paper’s86.00% reference. Final multimodal test is pending; no test improvement is claimed.

## Class results: validation
| Class | Precision | Recall | F1 | Support |
|---|---:|---:|---:|---:|
| True | 0.873281 | 0.909305 | 0.890929 | 23320 |
| Satire/Parody | 0.815478 | 0.763352 | 0.788555 | 3520 |
| Misleading Content | 0.808995 | 0.832668 | 0.820661 | 11277 |
| Imposter Content | 0.829891 | 0.551696 | 0.662785 | 1238 |
| False Connection | 0.976345 | 0.938485 | 0.957041 | 17768 |
| Manipulated Content | 0.840488 | 0.854779 | 0.847573 | 2176 |

## Class results: held-out test
Pending full held-out evaluation.

## Interpretation and limitations
This is a numerical reference comparison, not a controlled paper reproduction or statistical superiority claim. The paper uses another feature/fine-tuning pipeline; one seed and extra text warm-start compute;335paper/release-row discrepancy;491class-skewed exclusions;3561cross-split image-byte hash groups. Dataset labels are weak supervision, not independent factual-truth verification. Paper Table6 error proportions are not class F1.

Original source exports/private weights: `data/cloud_recovery/part2_saved_output_20261027_362859423/extracted/urop_mm_part2_20261027/OFFICIAL-6W-MM-USABLE-v2_seed42_20261027`. Independent readback: `results/MM_PART2_SAVED_PARTIAL_VERIFIED_20261027.json`. Recovery proof: `{"loaded": {"file": "796d18b295fe4fd4b355417c98c04039.pt", "sha256": "6c7747e08f482d6e504e05fb6c7e1a8c4e1fe3bce7154961f9380ed7e3e6f68e", "bytes": 1608464758, "cursor": 515296}, "fallback_errors": []}`.

Paper: [https://arxiv.org/html/1911.03854v2](https://arxiv.org/html/1911.03854v2). Current cloud run/version and Git acceptance must be read from the latest Part2 receipts. No public/raw-data/weight publication is implied.

## Architecture size
133977414 parameters, all 133977414 trainable, verified by strict checkpoint key/shape metadata; no local forward pass. Evidence: `results/MM_PART2_PARAMETER_METADATA_20261027.json`.

## Independently accepted partial Part 2 — 2026-10-27T20:03:16.185634+00:00

Same scientific run; **Part 2 remains incomplete**. Three full epochs and three full59,299-row validations accepted; epoch4 stopped safely at cursor515296/563601. Recovery:68,913 successful optimizer updates +29 AMP skips. No final held-out test or image-only training. Current provisional selected epoch3 VALIDATION accuracy88.5343766%, Macro-F1.8279239414; selection not yet frozen for final test.

CPU-only independent readback passed exact validation IDs/golds/probabilities/loss/metrics, original protocol hashes, generation SHA, optimizer/scheduler/scaler/RNG/history/sampler position and strict actual model-state load (527keys, no inference). Private ZIP CRC/member safety passed;53archive members,37run artifact hashes recorded. Source of truth: `results/MM_PART2_SAVED_PARTIAL_VERIFIED_20261027.json`, `results/MM_PART2_MANUAL_DOWNLOAD_READBACK_20261027.json`, `results/MM_PART2_STATUS_20261027.md`. The earlier Chrome-block/pending-readback notes below are historical; the user's normal download resolved that blocker.

Workflow bars: text100 / text+image74.57 (display75) / image20 / overall64.86 (display65). Equal20% stages: dataset100%,implementation100%,recoverable training97.8573%,full validations75%,test+final archive0%. This measures checkpoints, not model accuracy or remaining time.

Private job: https://www.kaggle.com/code/rocky62/urop-mm-part2-continuation-20261027?scriptVersionId=362859423. Saved batchSuccessful, zeroActiveEvents. Fresh quota19:42UTC11:40/30hours used (~18h20remaining, rounded). Actual model used TeslaT4 device0 from allocatedT4x2. No trainer is still running. No new account/OAuth/token/schedule/goal or scientific input changes.

Next: resume **this exact current generation**, complete remaining48,305 training rows and full epoch4 validation, then freeze Macro-F1/loss/earlier-epoch selection and perform one full59,270-row test. Never rerun the old epoch2-guarded launcher or revive Part1 STOP_PIPELINE. Follow the exact handoff below. Training-budget estimate is not a completion promise.

## Exact private recovery

Local attempt: `data/cloud_recovery/part2_saved_output_20261027_362859423/extracted/urop_mm_part2_20261027/OFFICIAL-6W-MM-USABLE-v2_seed42_20261027`
Cloud attempt: `/kaggle/working/urop_mm_part2_20261027/OFFICIAL-6W-MM-USABLE-v2_seed42_20261027`

- `recovery/796d18b295fe4fd4b355417c98c04039.pt` —1,608,464,758bytes; SHA256 `6c7747e08f482d6e504e05fb6c7e1a8c4e1fe3bce7154961f9380ed7e3e6f68e`.
- `selected_epoch3_f009f3c47f6e49eab7652f2823e3eb80.pt` —SHA256 `360a436a1af6d5a9a6375dc26b2e8e8a0fa30e9cf3bafb157d027d39472d960d`.
- Epoch3 predictions SHA256 `afb34b1f34f300c74c77309047e2e497846478d3a13863b56a904b8a96c3a3ca`.
- ZIP `data/cloud_recovery/part2_saved_output_20261027_362859423/results_362859423.zip` —5045725092bytes; SHA256 `dbabb68d61f643cb53ed5b646aec072de386e30376c3a3c7909d4348bc4b768d`.
- All private artifact sizes/hashes: `results/MM_PART2_SAVED_PARTIAL_VERIFIED_20261027.json`.
- Reviewable metrics/class report/confusions: `results/experiments/multimodal/OFFICIAL-6W-MM-USABLE-v2_seed42_20261027/part2_362859423/`.

## Safe future continuation

1. Inspect current usage, existing jobs, fresh Kaggle quota/environment and accepted protocol; no duplicate trainer.
2. Attach saved private version362859423 alongside unchanged approved packed input/gate/source. Verify exact current generation/hash, source/config/data/dependency contract, epoch4/cursor515296, updates68913/skips29, full RNG/sampler/crop/history/BatchNorm state. This task's original epoch2-guarded wrapper is intentionally NOT reusable unchanged.
3. Prepare a new bounded continuation wrapper that copies this current accepted output to a NEW working location without resetting state. Acknowledge the old STOP_REQUESTED sentinel only in that NEW continuation output after recovery validation; keep completed Part1 STOP_PIPELINE protected. Resume unchanged scientific trainer, same four-epoch schedule/seed/effective batch/weights and all state.
4. Finish residual48,305rows, full validation; freeze selected weights using declared validation-only rule. Then one complete59,270-row test, independent metric/ID/probability/loss/confusion verification, selected-model round trip, durable private outputs, final report/HTML/context and Git readback. No tuning on test or early final test.
5. Existing CSV/evaluation/report helpers are saved but their final-test runtime path has not yet been exercised on a completed model. Strictly inspect actual outputs and report any failure; code preparation is not final evaluation.

Six-hour window began14:08:54UTC and ends20:08:54UTC. Graceful stop19:35, runtime terminal19:36:42, private/local verification20:01–20:02. Task deliberately preserves partial work within budget. At ~63trainingpairs/sec residualtraining alone~13minutes, excluding setup/cache/checkpoints, full validation/test, export/download/verification. No completed-finish guarantee.

## Comparison and caution

Epoch3 improves validation accuracy and Macro-F1 versus epoch2 but loss worsens(.564860→.587545), compatible with more confident mistakes. Macro-F1 is the registered primary criterion. Numerical validation difference+2.5344points versus paper86.00%; final test pending (paper85.88%). Different fine-tuning/feature pipeline, additional text warm start,491skewed exclusions,335paper/release-row discrepancy,3561cross-split byte-identical image groups and one seed prevent a controlled-superiority claim. F1/loss paper values are not reported. Original text-only and Part1 results remain intact.

Final partial handoff receipt: `results/MM_PART2_VERIFIED_PARTIAL_HANDOFF_20261027.json`. Results/documentation commit `f2488f3c4f2f3b53572721bdedff07d76063ec44` matched remote main by git ls-remote at 2026-10-27T20:04:13.095829+00:00. This receipt is committed as a child; Part2 and final test remain incomplete.
