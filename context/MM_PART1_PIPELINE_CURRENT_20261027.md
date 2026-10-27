## Final remote backup verified

2026-10-27T11:26:25.532854+00:00 — scientific release `4aa051710930d31b82cdee63cd836aac9921ed6a` matches origin/main;21 report/aggregate/independent-receipt files matched their committed bytes. Final proof: `results/MM_PART1_FINAL_GIT_BACKUP_20261027.json`. Acceptance receipt is now `verified_part1_complete`; all steps4–7 passed. Part2/test remain unstarted.

# Part 1 complete — verified handoff, 27 October 2026

Updated 2026-10-27T11:23:19.331947+00:00. Both full training epochs and both full validations are independently verified. **Part 1 package: 100%.** The whole text+image workflow is60%; Part2 and final test have not started.

- Faculty usable cohort:563601 train /59299 validation /59270 integrity-only test, with the exact approved491 decoding exclusions (489FalseConnection,2Satire/Parody). Original three TSVs and official splits/labels are unchanged. All682170 usable image IDs and raw bytes passed the saved full gate.
- Model: BERT-base selected text epoch4 warmstart + ImageNetV2 ResNet-50; maximum fusion; six classes; seed42; same four-epoch schedule. One scientific experiment, two bounded private Kaggle jobs.
- Epoch1 validation: accuracy87.706369%, Macro-F1 .81318290. Epoch2: accuracy88.358994%, Micro-F1 .88358994, Macro-F1 .82266654, weighted-F1 .88287401, balanced accuracy .80194161, loss .56486012. Epoch2 selected by the registered Macro-F1 rule. Loss increased versus epoch1; all metrics are retained.
- Matching paper validation accuracy86.00%; numerical difference+2.358994points meets the+1-point validation aspiration. Different usable cohort and fine-tuning protocol limit direct benchmark equivalence. No test win is claimed; final test remainsPart2.
- Actual cloud GPU: Kaggle TeslaT4, one used device0 (T4x2 allocation). All registered jobs are COMPLETE; quota observed11:10:56UTC:6.4453/30h used,0reserved,23.5547h remaining.
- Latest recovery: **epoch3, cursor0**, phase train,35211successfulupdates+15AMPskips=35226boundaries; model/BatchNorm, optimizer, four-epoch scheduler, scaler, RNG, history and contracts verified. Recovery SHA `357c0707a80ef97f485cfe1824b537327aeb6810b89890055e6d18866e1f1819`. Selected weights and latest recovery are distinct required artifacts; both are retained.

## Evidence and exact Part2 next action

Read `results/MM_PART1_REPORT_20261027.md`, `results/MM_PART1_RECEIPT_20261027.json`, `results/MM_PART1_EPOCH2_VERIFIED_20261027.json` and `results/MM_PART1_FINAL_GIT_BACKUP_20261027.json` first. Aggregate metrics, per-class reports and labelled raw/normalized confusion matrices are under `results/experiments/multimodal/OFFICIAL-6W-MM-USABLE-v2_seed42_20261027/`.

Immutable saved cloud output: `rocky62/urop-mm-part1-science-epoch2-20261027/1`. Local private output: `data/cloud_recovery/part1_verified_pipeline_20261027/epoch2_saved_output/urop_mm_science_20261027/OFFICIAL-6W-MM-USABLE-v2_seed42_20261027/`. Seventeen required tensor/prediction/metric artifacts were hash/readback verified;31files retrieved. Large data/weights/predictions remain ignored and private, not in Git.

**Part2:** read `context/MULTIMODAL_PART2_EXECUTION_PLAN_20261023.md` with its approved usable-cohort amendment. Resume this SAME attempt from epoch3/cursor0, same configSHA `ad8f86f86b1fef453ae3bccda0aeb13cc50b298dc0d5d502f87c9ac4b041b483`, numerical trainerSHA `7f7fb90deb08a5901d1ca8343b780f6d82dd42b3e278d51f333568435becee0e`, source release `342d287007b7cbe795031228bdb4c2c5b4ee70b6`, readerSHA `a29e66d9c2962eb5bdfdce9abab02866fc77ad44aa5711ec8009a09dda7bb60d`, actual GPU Docker digest in final receipt. Keep the four-epoch LR budget, selection history and RNG/order. Do not rerun Part1, reacquire images, re-split, exclude more IDs, replace models, or reset the schedule. New cloud sessions may copy the same SHA-verified39raw packs into bounded cloud scratch; that is lossless caching, not dataset re-preparation. Final public test is authorized only in Part2 under the frozen selection protocol.

The finite Part1 controller60613/PID22245 has finished successfully; do not restart it. Its STOP_PIPELINE marker prevents accidental additional launches. Temporary idle-sleep assertion ends with the controller. All current scientific cloud jobs are terminal. Text-only results and unrelated user edits remain preserved. Current workflow bars: text100 / text+image60 / image-only20 / overall60.

Primary allowance was checkpointed before the5%hard stop; the same committed epoch2 continued through the reserve pause without a training restart. Actual primary reset was verified09:14UTC. Follow the latest5%primary hard-stop rule and the weekly availability ceiling for future work.
