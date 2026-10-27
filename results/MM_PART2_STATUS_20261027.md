# Part 2 — saved partial continuation, independent readback pending

As of 2026-10-27T19:42:11.943303+00:00 (UTC; local calendar date 28 October).

**Part 2 is incomplete.** Same seed-42 experiment, unchanged registered source/config/cohort. Kaggle version 1/scriptVersion362859423 finished successfully after the bounded wrapper requested a safe stop at 19:35 UTC. No final multimodal test was performed.

## Completion boundary and evidence levels

- Accepted before this task: epochs 1–2, both full validations, locally verified tensors and predictions.
- Cloud terminal result: epoch 3 trained and fully validated on 59,299 IDs; epoch 4 stopped at consumed-row cursor **515,296/563,601 (91.43%)**, phase train. This is **97.86% of the four-epoch training budget by consumed rows**, NOT completion of Part 2.
- Three of four full validations are reported by the cloud controller; epoch 4 validation remains undone.
- Runtime loaded and checked its saved recovery generation without fallback; private output tree exposes recovery, selected epoch-3 weights and validation exports. Local strict tensor/prediction verification is pending the output download.
- The Kaggle UI showed Successful and **0 Active Events** at approximately 19:41 UTC. No additional trainer/session was allocated.
- Chrome blocked the normal output ZIP URL with ERR_BLOCKED_BY_CLIENT. Human download handoff requested; do not bypass this browser block.

## Cloud-reported validation — provisional until independent local readback

| Metric | Epoch 2 (previously accepted) | Epoch 3 (cloud reported) | Matching paper validation |
|---|---:|---:|---:|
| Accuracy | 88.358994% | 88.534377% | 86.00% |
| Micro-F1 | 0.8835899425 | 0.8853437663 | Not reported |
| Macro-F1 | 0.8226665390 | 0.8279239414 | Not reported |
| Weighted-F1 | 0.8828740126 | 0.8849443480 | Not reported |
| Balanced accuracy | 80.194161% | 80.838108% | Not reported |
| Loss | 0.5648601171 | 0.5875453333 | Not reported |

Epoch 3 currently wins on validation Macro-F1 despite worse cross-entropy loss; this follows the declared primary selection rule. It is not the final frozen selection until epoch 4 and full validation finish. The numerical validation difference is +2.5344 percentage points versus the paper, with different cohort/feature/fine-tuning pipeline, extra text warm-start training, one seed, 491 class-skewed exclusions, unresolved 335-row release/paper discrepancy and 3,561 cross-split image-byte groups. No controlled-superiority or test-improvement claim. Final test accuracy/Micro-F1/Macro-F1/weighted-F1/balanced accuracy/loss/class report/confusions are **pending**; the paper's matching test accuracy is 85.88%.

## Private artifacts (runtime hashes; not yet independently read back locally)

Job: [https://www.kaggle.com/code/rocky62/urop-mm-part2-continuation-20261027?scriptVersionId=362859423](https://www.kaggle.com/code/rocky62/urop-mm-part2-continuation-20261027?scriptVersionId=362859423)

Runtime attempt: `/kaggle/working/urop_mm_part2_20261027/OFFICIAL-6W-MM-USABLE-v2_seed42_20261027`

- Recovery: `recovery/796d18b295fe4fd4b355417c98c04039.pt`, 1,608,464,758 bytes, SHA-256 `6c7747e08f482d6e504e05fb6c7e1a8c4e1fe3bce7154961f9380ed7e3e6f68e`.
- Current selected weights: `selected_epoch3_f009f3c47f6e49eab7652f2823e3eb80.pt`, SHA-256 `360a436a1af6d5a9a6375dc26b2e8e8a0fa30e9cf3bafb157d027d39472d960d`.
- Epoch-3 predictions: `validation_epoch3_predictions.csv`, SHA-256 `afb34b1f34f300c74c77309047e2e497846478d3a13863b56a904b8a96c3a3ca`.
- Saved receipt: `part2_runtime_result.json`; runtime strict load and three CSV validations returned successfully. Parsed terminal observation: `results/MM_PART2_CLOUD_TERMINAL_OBSERVATION_20261027.json`.

## Quota, timing and unchanged protocol

Task started 14:08:54 UTC; training release 14:25:43; runtime result 19:36:42. Runtime controller elapsed 18,771.97 seconds (~5h13m); total task elapsed at runtime result ~5h28m. Hard task deadline20:08:54 UTC. Tesla T4 device0 used; Kaggle allocated T4x2 but the model used one. Starting live UI quota was06:26/30hours used; later editor retained that number and is not a fresh final balance. Fresh reloaded editor Session options at 2026-10-27T19:42:40.171301+00:00 displayed **11:40/30 hours used**, approximately **18h20 remaining** (UI rounded minutes). Receipt: `results/MM_PART2_CAPACITY_END_OBSERVATION_20261027.json`. Platform cap was not independently exposed; own UTC bounds were enforced. Source/config/data hashes are preserved in `results/MM_PART2_LAUNCH_RECORD_20261027.json`, original `protocol.json`, and Part1 accepted receipt.

## Exact next safe actions

1. Human completes the normal private output ZIP download in Rocky Chrome: `https://www.kaggle.com/code/svzip/362859423`. Save in Downloads or project `data/cloud_recovery/`. Do not run/restart training to obtain it.
2. Move only this owned archive into a NEW ignored Part2 recovery directory, verify safe archive members/CRC, extract without overwriting Part1, hash the archive and inventory.
3. CPU-only readback from UROP: `.venv-urop/bin/python scripts/verify_saved_mm_part2_v1.py --project /Users/panveenaidu/Downloads/SEM7/UROP --run <retrieved attempt directory> --output <new verification receipt>`. This verifies all three validation exports, exact cohort/labels/probabilities/metrics, recovery tensors/optimizer/scheduler/scaler/RNG/sampler/crop/history and current selection. It performs no model inference/training.
4. Only after successful readback, accept the new progress and generate the partial status/report HTML with `scripts/build_multimodal_final_report_v1.py`. Never pass the cloud-observation receipt to a verifier-dependent report builder as though it were a local acceptance receipt.
5. A future authorized bounded continuation must use this SAME generation at epoch4/cursor515296, not the old epoch3/cursor0 launch guard. Preserve original state/schedule. Review the copied STOP_REQUESTED sentinel in the NEW continuation output; do not revive the protected Part1 STOP_PIPELINE. Never blindly rerun the existing Part2 launch notebook, which intentionally requires the original epoch2 recovery and would not resume the current cursor.
6. Finish remaining **48,305** training rows, full59,299-row validation; freeze selection using all registered validation history, then run the single59,270-row held-out test. Independently verify predictions/weights, archive private evidence, final report/HTML/context and remote Git backup. No image-only/new seed/model/data changes.

At the observed ~63 training pairs/second, residual training alone is roughly13 minutes, excluding environment/cache/checkpoint setup, validation/test/export, downloads and verification. No complete-finish promise follows from that estimate.

## Progress bars — accepted evidence versus observed work

Accepted workflow remains text100 / text+image60 / image20 / overall60 pending local readback. This is intentionally conservative, not a claim training did nothing. Cloud-reported training fraction is97.86%, validation75%, test0%. If independent readback accepts the current partial recovery, the existing five-equal-stage method yields text+image about74.6% (40 setup +19.57 training +15 validation), overall64.9%; do not label that100%.

Documentation backup verified against remote main: `51a85424c03a2ce9ae0f3bb4e0e3cc256c0fe60d`; receipt `results/MM_PART2_PARTIAL_GIT_BACKUP_20261027.json`. This verifies code/documentation backup, not pending private tensor/prediction readback.
