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

## Independently accepted partial Part 2 — 2026-10-27T20:03:16.185634+00:00

Same scientific run; **Part 2 remains incomplete**. Three full epochs and three full59,299-row validations accepted; epoch4 stopped safely at cursor515296/563601. Recovery:68,913 successful optimizer updates +29 AMP skips. No final held-out test or image-only training. Current provisional selected epoch3 VALIDATION accuracy88.5343766%, Macro-F1.8279239414; selection not yet frozen for final test.

CPU-only independent readback passed exact validation IDs/golds/probabilities/loss/metrics, original protocol hashes, generation SHA, optimizer/scheduler/scaler/RNG/history/sampler position and strict actual model-state load (527keys, no inference). Private ZIP CRC/member safety passed;53archive members,37run artifact hashes recorded. Source of truth: `results/MM_PART2_SAVED_PARTIAL_VERIFIED_20261027.json`, `results/MM_PART2_MANUAL_DOWNLOAD_READBACK_20261027.json`, `results/MM_PART2_STATUS_20261027.md`. The earlier Chrome-block/pending-readback notes below are historical; the user's normal download resolved that blocker.

Workflow bars: text100 / text+image74.57 (display75) / image20 / overall64.86 (display65). Equal20% stages: dataset100%,implementation100%,recoverable training97.8573%,full validations75%,test+final archive0%. This measures checkpoints, not model accuracy or remaining time.

Private job: https://www.kaggle.com/code/rocky62/urop-mm-part2-continuation-20261027?scriptVersionId=362859423. Saved batchSuccessful, zeroActiveEvents. Fresh quota19:42UTC11:40/30hours used (~18h20remaining, rounded). Actual model used TeslaT4 device0 from allocatedT4x2. No trainer is still running. No new account/OAuth/token/schedule/goal or scientific input changes.

Next: resume **this exact current generation**, complete remaining48,305 training rows and full epoch4 validation, then freeze Macro-F1/loss/earlier-epoch selection and perform one full59,270-row test. Never rerun the old epoch2-guarded launcher or revive Part1 STOP_PIPELINE. Follow the exact handoff below. Training-budget estimate is not a completion promise.

```text
Text-only       ██████████ 100%
Text + image    ███████▌░░  75% (exact 74.57%)
Image-only      ██░░░░░░░░  20%
Overall         ██████▌░░░  65% (exact 64.86%)
```

Historical progress records below are superseded by this verified checkpoint.

## Part2 terminal handoff — 2026-10-27T19:42:11.943303+00:00

Same experiment safely stopped epoch4/cursor515296; cloud reports epoch3 full validation88.5344% accuracy /0.827924 Macro-F1, selected provisionally by Macro-F1. No final test; Part2 incomplete. Output version362859423 saved privately; local independent readback blocked by Chrome ERR_BLOCKED_BY_CLIENT and awaiting human normal download. Current source of truth: `context/MM_PART2_CURRENT_20261027.md`, `results/MM_PART2_STATUS_20261027.md`, terminal observation receipt. Older launch/Part1 observations below are historical, not current activity. Accepted workflow bars remain text100/MM60/image20/overall60 until independent local readback.

<!-- PART2_LAUNCH_20261027 -->
## Part 2 continuation submitted — 2026-10-27T14:30:41.173922+00:00

Same accepted experiment `OFFICIAL-6W-MM-USABLE-v2_seed42_20261027` resumes epoch3/cursor0 in private Kaggle version1/scriptVersion362859423. Actual runtime resume/source/dependency/T4 guards passed14:25:43UTC. No new full epoch/validation/test has been accepted yet; copied epoch2 status during startup is not fresh training evidence. Frozen source/config/data/schedule unchanged. Read `context/MM_PART2_CURRENT_20261027.md` and launch/live receipts before any action; never duplicate a live trainer or restart the completed Part1 controller. Current verified workflow remains text100/MM60/image20/overall60; latest verified score is epoch2 VALIDATION88.358994%, Macro-F1.82266654, not test.

Training safe-stop19:35UTC; runtime return19:43UTC; six-hour task deadline20:08:54UTC. Final test only after registered training and frozen validation selection; otherwise save verified partial recovery and handoff. No image-only/new seed/model/account/purchase/schedule. Existing Rocky Chrome UI used without new API credentials.
<!-- /PART2_LAUNCH_20261027 -->

# UROP workflow checkpoint progress

2026-10-27T11:23:19.331947+00:00

```text
Text-only       ██████████ 100%
Text + image    ██████░░░░  60%
Image-only      ██░░░░░░░░  20%
Overall         ██████░░░░  60%
```

Part1 package100%: train2/2, full validation2/2, verified recovery/private/local artifacts and final backup. Full multimodal budget: training2/4, validation2/4, final test0. Percentages are workflow checkpoints, not accuracy or elapsed time. See `results/MM_PART1_REPORT_20261027.md` and final Git proof.
