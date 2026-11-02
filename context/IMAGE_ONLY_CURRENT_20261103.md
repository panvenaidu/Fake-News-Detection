# Image-only saved job completed; artifact download pending

The authenticated Kaggle saved version 364917396 finished successfully in 4h 55m 59s and exposes 64 output files. Its rendered `IMAGE_JOB_RESULT.json` reports four completed epochs, four full validations, epoch 4 selected, and full test complete with its cloud CSV verification passed. This supersedes the previous live epoch-2 handoff. No trainer was restarted or new runtime allocated.

Observed receipt values (pending independent local saved-byte verification): validation accuracy 80.9339112%, Macro-F1 0.6564868851 on 59,299 rows; test accuracy 81.1557280%, Macro-F1 0.6617958357 on 59,270 rows. All six metrics and the exact selected weights hash are transcribed with evidence qualifications in `results/experiments/image_only/CLOUD_COMPLETION_OBSERVED_20261103.json`. These are cloud-reported values, not yet final local acceptance.

Chrome blocked the normal Output actions → Download output at https://www.kaggle.com/code/svzip/364917396 with ERR_BLOCKED_BY_CLIENT. A human must complete the normal download; the agent must not bypass the browser security block. Save the ZIP in Downloads or `data/cloud_recovery/`. Do not rerun training.

Next: verify ZIP paths/CRC and hashes; extract privately into a new ignored folder; run `scripts/verify_image_only_saved_v1.py` against the actual attempt folder; independently verify all four validation CSVs, test CSV, weights and recovery. Only after accepted_complete, generate the final report, update existing dashboards/workflow/context, then verify the GitHub backup. Full scientific completion remains pending those acceptance steps. Existing accepted progress remains unchanged until verification.
