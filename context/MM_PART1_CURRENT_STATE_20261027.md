## Usage handoff — 2026-10-27T03:57:28.070385+00:00

Primary allowance reached the user’s 5% hard stop (95% used; reset Unix 1793074294). Last live Kaggle observation: Version 4 GPU preflight 362691302 running at 932.5 seconds, actual Tesla T4/CUDA recovery fixture passed, final timing receipt not yet observed. This is a committed bounded 7,200-second Kaggle job; it can finish and save outputs independently. No assistant monitoring continues after this handoff. Scientific train 0/2 and validation 0/2. Next: inspect Version 4, run prepared `data/cloud_recovery/kaggle_api_requests/preflight_release_readback.json` through the FIFO credential controller, independently verify saved summary/fixture/throughput, and use `collab/build_kaggle_science_job_v1.py` plus `collab/kaggle_part1_epoch_job_20261027.py` to submit epoch 1 with its measured budget. Refresh the API quota/job audit immediately before submission; the bundle requires that timestamp to be fresh. Pin actual GPU Docker digest from successful preflight metadata. No image-gate rerun, no Part 1 test.

# Part 1 live checkpoint — 27 October 2026

## Verified complete

- Private faculty packed input v3, Version 1: https://www.kaggle.com/datasets/rocky62/urop-faculty-usable-packed-input-v3 . All original official TSV split assignments, IDs, titles and six labels remain; the approved 491 strict decoding exclusions define 682,170 pairs (563,601 train / 59,299 validation / 59,270 integrity-only public test).
- Full image verification **saved successfully** in private Kaggle notebook Version 2, ID **362643633**, after 5,845.4 seconds: https://www.kaggle.com/code/rocky62/urop-mm-packed-faculty-image-gate-20261026/output?scriptVersionId=362643633 . No more acquisition, extraction, transfer or image-gate rerun is needed.
- Downloaded the eight-file saved output into ignored `data/cloud_recovery/KAGGLE_PACKED_GATE_v2_362643633/`. The 108,064,768-byte SQLite index SHA is `fc8dc03a4f773da5762891c8392375add5fb8087251b527f3b37a880308e6018`; coverage receipt SHA is `afe8c723f91fe74f791908e0c16fab94d919af64c7cb7c9b5a37e676361d95e5`.
- Independent local readback checked SQLite integrity, every approved ID against the original TSVs/exclusion registration, all 39 archive proofs and 79,687,306,914 image bytes. Result: `results/MM_PART1_SAVED_GATE_READBACK_20261027.json`. Source: `scripts/verify_saved_packed_gate_v3.py`.

## GPU engineering job — inspect before changing anything

Private notebook: https://www.kaggle.com/code/rocky62/urop-mm-part1-packed-gpu-20261026/logs?scriptVersionId=362691302 . This is **Version 4**, the current measured preflight, submitted with a 7,200-second bound. It is not a scientific training experiment. Actual logs show two allocated Tesla T4 15,360 MiB GPUs, one visible/used device 0, Torch 2.11.0+cu128, CUDA 12.8. The actual CUDA recovery fixture **passed** at about 131 seconds. The 600-second train-only throughput measurement follows; await its saved summary/fixture before scientific release. Do not duplicate this run.

Versions 2 and 3 stopped before scientific training: the notebook inherited its original CPU Docker image, yielding Torch 2.11.0+cpu and no CUDA driver. Version 4 removed that CPU image pin and selected Kaggle's current GPU environment. Use the **actual successful GPU Docker digest** from Version 4 metadata for later jobs; never reuse the old CPU digest. Keep fixture/preflight sources pinned, scientific numeric trainer/config unchanged.

The browser editor repeatedly stalled. The approved Kaggle API credential was used with official `kaggle==2.2.5` from an ignored project venv. Credential passes through a mode-600 FIFO to the API process and stays in RAM; no token file, printed token, notebook credential, or Git credential. `collab/kaggle_api_task_v1.py` performs bounded actions. Existing CUA variable `packedToken` currently holds the approved credential; do not print it. API requests and any local package state remain under ignored `data/cloud_recovery/`.

## Exact next actions

1. Read current Version 4 status/logs. Its output must show `gpu_preflight_verified` and saved `GPU_PREFLIGHT_SUMMARY.json`, actual CUDA fixture and measured preflight receipt. Retrieve small JSON/log evidence using the API, verify hashes and actual timing; pin its GPU Docker image digest and notebook version. Do not call setup checks validation metrics.
2. Use prepared `collab/kaggle_part1_epoch_job_20261027.py` for **epoch 1 only**, with a fresh actual API quota/job check, measured preflight summary checksum and bounded session timeout. It uses scientific source `b4378dd4213dec255a82f5400fb26bb4426f59d7`, launcher `406cf546b23cdef55ed66b1c513434d10ea98478` / SHA `100f12659a0400e93139e14ee44b451c76c8d054219b08ea95a37a86a545b050`, and requires at least one hour of session/export reserve plus measured timing margin. Run the bootstrap in a fresh cloud Python process with CUDA_VISIBLE_DEVICES=0.
3. Submit scientific code privately as Save & Run All through the official API, attaching immutable packed input v3/1, saved gate/2, completed BERT output and successful measured preflight output. Freeze the verified GPU environment. Do not use an unattended interactive draft for long jobs. Save the launch receipt and immutable attempt ID.
4. After epoch 1 and full validation complete, retrieve and independently check saved predictions/metrics/recovery and verify private output survives session loss. Only then resume the same attempt for epoch 2, retaining the four-epoch LR budget and RNG/order state. The prepared bootstrap supports this with the prior result checksum; inspect it before use.
5. Accept Part 1 only after **2/2 full training epochs, 2/2 complete validations, verified epoch-3 recovery, local/private artifacts and Git backup**. No final test in Part 1. Part 2 and image-only remain unstarted.

## Current scientific progress and safeguards

Train **0/2**, full validation **0/2**, Part 1 final test prohibited. Workflow bars remain text 100 / multimodal 40 / image-only 20 / overall 53. No new accuracy or F1 result exists. Preparation and engineering successes do not increase these scientific fractions. The +1 percentage-point paper target remains an aspiration, never a guaranteed outcome.

At 03:37 UTC the API showed 30 GPU hours total and about 21 seconds used; refresh before launch. Primary allowance may be used to the user's 5% hard stop; prepare verified handoff before that boundary. Goal tool currently returns null; do not create a duplicate. Preserve unrelated user edits, including `results/UROP_Text_Only.html`. Keep raw data, images, weights, archive/index files and credentials out of Git. This document supersedes stale transfer/image-gate pending notes dated October 26 and the earlier interactive gate observation.
