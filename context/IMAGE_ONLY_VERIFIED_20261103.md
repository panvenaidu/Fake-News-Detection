# Image-only independently verified

The owner-downloaded archive was moved into `data/cloud_recovery/image_only_saved_364917396/results_364917396.zip` and extracted there. All 65 ZIP members passed CRC, duplicate-name, traversal and symlink checks. Archive SHA-256: `25eb12b554ae2e600f4cc8a4e65bac9ceb3aff133d337b5f94608673ccb8584d`.

Independent CPU saved-artifact verification passed for all four complete validations and the complete 59,270-row public test, all private manifest hashes, selected weights, model/optimizer/scheduler/scaler, saved RNG/sampler state and recovery counters. Epoch 4 selected; 70,422 successful updates + 30 AMP skips. Recovery is epoch 5 / cursor 0, representing completed budget; do not train epoch 5 or rerun the test.

Validation accuracy 80.9339112%, Macro-F1 0.6564868851. Test accuracy 81.1557280%, Macro-F1 0.6617958357. All aggregate/class metrics and confusion matrices are saved.

Authoritative verification: `results/experiments/image_only/IMAGE_ONLY_SAVED_VERIFIED_20261103.json`. Final report: `results/IMAGE_ONLY_FINAL_REPORT_20261102.md` (UTC verification date). Completion receipt: `results/IMAGE_ONLY_FINAL_COMPLETION_RECEIPT_20261102.json`. Metrics dashboard: `results/metrics_summary/index.html`. Prior pending-download notes are historical and superseded. GitHub backup is recorded separately after actual remote readback. No training, test inference or new cloud allocation occurred during this verification.
