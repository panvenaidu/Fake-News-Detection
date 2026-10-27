# Verified Part1 pipeline checkpoint

2026-10-27T08:16:24.069796+00:00 — Verified Part1 epoch1 training validation and recovery

Completed full scientific training 1/2; full validation 1/2. No final test. This is one four-epoch experiment, stopped after epoch2.

Evidence: `results/MM_PART1_EPOCH1_VERIFIED_20261027.json`. Private immutable output: rocky62/urop-mm-part1-science-usable-20261027/1. Recovery next epoch 2, cursor0. No final test.

Bounded controller: `collab/run_verified_part1_pipeline_v1.py`; live journal `data/cloud_recovery/part1_verified_pipeline_20261027/status.json`. A STOP_PIPELINE file in that folder prevents the next job. Verify saved launch receipts before recovery; never duplicate a submitted notebook.
