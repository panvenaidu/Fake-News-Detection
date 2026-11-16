# Image-only ViT-B/16 fine-tuning execution record

**Complete.** The independently verified full-test accuracy is **80.3948%** on 59,270 posts, **1.6052 percentage points short** of the 82.00% target. The selected DeiT III B/16 checkpoint scored 0.7609 percentage points below historical end-to-end ResNet-50 and 14.7461 above frozen ViT-B/16. [Verified report](VIT_FINETUNE_REOPENED_REPORT_369953825.md) · [Verification receipt](VIT_FINETUNE_REOPENED_VERIFICATION_369953825.json)

The target is **82.00% full-test accuracy** on the approved six-class faculty Fakeddit cohort. The accuracy-first checkpoint rule is registered in `Configuration/Image Only/image_only_vit_finetune_v1.json`: compare full-validation accuracy, macro-F1, lower cross-entropy, then earlier epoch. Historical baselines selected by macro-F1 first.

| Stage | Evidence |
|---|---|
| Private notebook and pinned inputs | [GPU preflight version 369547836](https://www.kaggle.com/code/rocky62/urop-image-only-vit-b16-fine-tuning/log?scriptVersionId=369547836). The UI showed private access, no other active jobs, and 00:00 usage of 30 hours. Kaggle detected two Tesla T4s and verified the 563,601 / 59,299 / 59,270 registered counts. |
| Training and validation | Three two-epoch pilots and both six-epoch full trials completed. The accuracy-first rule selected DeiT III B/16 epoch 3, seed 42, at 80.2577% full-validation accuracy. The fresh-process validation comparison verified the released weight. [Training and frozen validation output](https://www.kaggle.com/code/rocky62/urop-image-only-vit-b16-continuation/output?scriptVersionId=369827269) |
| Frozen test and independent readback | Both completed. The saved full test, byte-overlap subset and both historical baseline comparisons passed independent CPU readback. [Frozen test output](https://www.kaggle.com/code/rocky62/urop-image-only-vit-b16-frozen-test/output?scriptVersionId=369892645) · [Independent CPU output](https://www.kaggle.com/code/rocky62/urop-image-only-vit-b16-cpu-readback/output?scriptVersionId=369953825) |

Compute is restricted to existing quota, with a 20% quota reserve. [Kaggle documents](https://www.kaggle.com/docs/notebooks) a 12-hour CPU/GPU session limit and 20 GB of saved workspace. The controller stops scientific training before session expiry and leaves a resumable saved version. The smoke and timings use train/validation rows only. CPU regression passed on full-size train-order partition and reconstruction, deterministic pilot sampling, checkpoint selection, metric readback, and rejecting a changed label.

Both trials used strictly decoded RGB pixels, full encoder fine-tuning, and a six-logit dropout/linear head. TorchVision used ImageNet-1K V1 weights. DeiT III used supervised ImageNet-22k weights fine-tuned on ImageNet-1k. Both initializations were pinned by SHA-256.


## Preflight and trial log

- [Version 369547836](https://www.kaggle.com/code/rocky62/urop-image-only-vit-b16-fine-tuning/log?scriptVersionId=369547836), 14 Nov 2026, status: failed smoke. All source input gates and weight initialization passed; the first update changed both encoder and head, and the direct validation reload matched exactly. The subsequent FP16 continuation comparison exceeded the 0.0002 absolute probability tolerance on one of 288 values (observed 0.00026062). No benchmark metrics or scientific scores are attributed to that attempt. GPU usage after termination: 00:10 / 30h for about 10m20s of T4 ×2 wall time, consistent with charging session time rather than two device-hours.
- [Version 369551317](https://www.kaggle.com/code/rocky62/urop-image-only-vit-b16-fine-tuning/log?scriptVersionId=369551317), retry: allow DDP bucket setup to settle before the saved cursor and compare continued outputs in FP32. Preserve exact initial reload; separately bound loss, weight and gradient changes and record measured continuation error.
- Local authoritative audit checked the original TSVs, exact 491 approved exclusions and pinned index. Identical-byte groups with conflicting labels: 1,164 train (2,379 incompatible rows) and 33 validation (158 incompatible rows). Majority-per-image ceilings within these splits are 99.5779% and 99.7336%; this is a descriptive diagnostic rather than a generalization bound. The fixed 30,000-row pilot has class counts [11,820, 1,783, 5,707, 628, 8,913, 1,149] in label order. No test error analysis was performed.

Recovery and exact-version mounting steps are in [the private execution runbook](../../Training/Image%20Only/Cloud/VIT_FINETUNE_RUNBOOK.md).

## Corrected preflight and scientific launch

- [Reopened timing receipt, 369551317](https://www.kaggle.com/code/rocky62/urop-image-only-vit-b16-fine-tuning/output?scriptVersionId=369551317&select=urop_vit_finetune%2Fpreflight%2Ftiming.json). The visible output matched the printed contents. The mirrored 1,214-byte JSON has SHA-256 `83383346284efaa8df13fbae423397844a507c4a702c8b7df9c42400594fc723`; the training controller checks those exact mounted bytes before staging.
- 85,803,270 trainable parameters; microbatch 16 per GPU, effective batch 64, 240 successful warmup/benchmark updates, zero AMP skips. The benchmark measured 181.15 training RGBs/s over 220 timed updates and 176.61 validation RGBs/s over 4,096 rows. Peak allocated GPU memory 3.12 GB; a 1.03 GB recovery checkpoint took 3.79s to write and hash. Exact validation reload passed; resumed-vs-uninterrupted FP32 probability and CE maximum differences were 3.8743e-07 and 1.0729e-06.
- [Private scientific version 369555528](https://www.kaggle.com/code/rocky62/urop-image-only-vit-b16-training/log?scriptVersionId=369555528) submitted on T4 ×2. Launch uses a conservative 30 minutes of prior usage, above the two preflights' observed combined session times, and preserves 6 hours of the 30 GPU-hour total. Benchmarked costs with padding are 1.104 hours/full epoch and 0.165 hours/pilot epoch, plus scheduled staging/recovery/test overhead. The controller writes the definitive registration before science and uses the pinned preflight environment. The worker registered three two-epoch learning-rate pilots, eight epochs each for TorchVision ViT-B/16 and the DeiT III challenger, a six-hour reserve, and no seed replications. The budget record appeared at 467.1 seconds, before the first validation. Separately, the optional DeiT III public checkpoint passed full SHA-256, strict loading and finite six-logit evaluation on the local CPU with timm 1.0.22; this is an engineering check, not a scientific result.
- Selected model, held-out accuracy, Baseline differences, macro-F1, balanced accuracy, rare-class results and no-training-overlap accuracy are pending; these cannot be inferred from the smoke or throughput.

The frozen-test and continuation builders now reuse the exact embedded training source. The independent readback accepts both historical prediction files by their verified SHA-256 hashes and computes paired confidence intervals after checking IDs and gold labels.


## Live scientific observations — 15 November 2026 IST

Kaggle version 369555528 verified the registered cohort counts on two T4 GPUs. These are pilot metrics from the worker logs, pending independent readback from persisted output.

| Encoder learning rate | Epoch | Accuracy | Macro-F1 | Balanced accuracy | Cross-entropy | Optimizer updates | AMP skips |
|---|---:|---:|---:|---:|---:|---:|---:|
| 1e-5 | 1 | 69.1496% | 0.499656 | 48.1633% | 0.858643 | 469 | 0 |
| 1e-5 | 2 | 69.8005% | 0.516314 | 48.9927% | 0.834445 | 938 | 0 |
| 3e-5 | 1 | 71.7381% | 0.534123 | 51.0797% | 0.785201 | 469 | 0 |
| 3e-5 | 2 | 71.7854% | 0.544012 | 51.6680% | 0.782394 | 938 | 0 |
| 1e-4 | 1 | 70.9692% | 0.515422 | 48.9789% | 0.804005 | 469 | 0 |
| 1e-4 | 2 | 71.7348% | 0.546216 | 52.1889% | 0.792614 | 938 | 0 |

Imposter Content recall was zero in five of six pilot epochs and 0.1616% at the second epoch for 1e-4. At 3,630.4 seconds, the worker promoted the 3e-5 encoder rate to the 563,601-row TorchVision run (seed 42, eight-epoch cap). The 1e-4 pilot ranked second. The lead was 0.0506 percentage points under the registered accuracy-first rule. Full-cohort validation remains pending. The final test will follow validation selection and a fresh-process checkpoint reload.

At 4,029.7 seconds the first full-cohort epoch logged a checkpoint after 64,000 training rows and 1,000 successful optimizer updates with zero AMP skips. At 4,423.3 seconds the worker logged 128,000 training rows and 2,000 successful optimizer updates, still with zero AMP skips. At 4,814.9 seconds the worker reached 192,000 rows and 3,000 successful updates, with zero AMP skips. At 5,205.9 seconds the worker logged 256,000 rows and 4,000 successful updates with zero AMP skips. Recent checkpoint intervals imply about 163 training rows/s, compared with the short preflight benchmark of 181.15 rows/s. These checkpoint writes were observed in the active worker log. Kaggle will finalize the version output after the session exits.

The continuation builder can pin the finalized paused session receipt by SHA-256. A local fixture verified it accepts the paused checkpoint directory and rejects a preflight-only input while preserving the original scientific source.

For independent readback, both historical test prediction CSVs were located in their exact saved Kaggle versions. The CPU notebook builder now includes the specified science version and historical baseline version IDs in the importable notebook metadata.

At 5,596.5 seconds the worker logged 320,000 training rows and 5,000 successful updates in epoch 1 with zero AMP skips. The independent verifier passed a synthetic end-to-end readback covering the frozen selection, resumable checkpoint, full and overlap-subset prediction exports, uncertainty, and report. It rejected an altered test label. The test also confirmed that digit-only SHA-256 strings retain leading zeros and that bootstrap intervals remain finite for small fixtures. No real test inference was run.

## Finalized first scientific session and continuation

[Scientific version 369555528](https://www.kaggle.com/code/rocky62/urop-image-only-vit-b16-training/log?scriptVersionId=369555528) exited at its planned recovery deadline and Kaggle finalized 8.21 GB of output. The [saved session receipt](https://www.kaggle.com/code/rocky62/urop-image-only-vit-b16-training/output?scriptVersionId=369555528&select=urop_vit_finetune%2Fsessions.json) records the paused run. The 1,980-byte [local receipt](VIT_FINETUNE_SESSIONS_369555528.json) has SHA-256 `6438d30a6aa07c4d9edf45495292dce75b5c562708834ee4f8afc455475875c0`. At the deadline, DeiT III had consumed all 563,601 epoch 4 training rows and saved 35,219 successful optimizer updates and nine AMP skips cumulatively. Its epoch 4 validation was still pending. The reopened recovery manifest records a 1,030,092,845-byte `resume.pt` with SHA-256 `021b50e22e3aa861d36f57dc532883a3a14d51e478dbcd8dfa6c06568fb86ea0` and lists a previous generation as fallback.

| Model | Epoch | Full validation accuracy | Macro-F1 | Balanced accuracy | Imposter recall | Manipulated recall |
|---|---:|---:|---:|---:|---:|---:|
| TorchVision ViT-B/16 | 1 | 75.1783% | 0.574589 | 55.3691% | 1.6155% | 44.9908% |
| TorchVision ViT-B/16 | 2 | 76.6202% | 0.600853 | 55.7868% | 6.9467% | 44.2555% |
| TorchVision ViT-B/16 | 3 | 77.6995% | 0.628731 | 59.1923% | 11.0662% | 56.1121% |
| TorchVision ViT-B/16 | 4 | 77.0688% | 0.627500 | 59.8108% | 10.0162% | 53.6765% |
| TorchVision ViT-B/16 | 5 | 74.9810% | 0.612945 | 58.3622% | 9.0468% | 54.0441% |
| TorchVision ViT-B/16 | 6 | 76.8462% | 0.629862 | 60.7396% | 13.1664% | 56.9853% |
| DeiT III B/16 | 1 | 78.2796% | 0.602979 | 57.6387% | 1.6155% | 44.3934% |
| DeiT III B/16 | 2 | 80.1261% | 0.639022 | 58.8696% | 11.7124% | 45.1746% |
| DeiT III B/16 | 3 | 80.2577% | 0.655443 | 62.1527% | 12.6010% | 61.6728% |

These values are from the finalized worker log and cover all 59,299 validation rows per epoch. TorchVision early-stopped after epoch 6 under the registered patience of three and selected epoch 3 within its arm. DeiT III uses encoder learning rate 3e-5 and seed 42. Final checkpoint selection is pending.

The reopened [registration.json](https://www.kaggle.com/code/rocky62/urop-image-only-vit-b16-training/output?scriptVersionId=369555528) is 10,830 bytes with SHA-256 `39e31ee93d73ea740c3f1f36400036e124cecd84c7dab6e9e7fce3d46ab9f67f`. All nine embedded file bodies in the local training and continuation notebooks match the saved registration hashes. The registration records three two-epoch pilots, two eight-epoch full-trial caps, seed 42 with zero seed replications, and a six-hour reserve. It pins the train, validation, and pilot manifests to SHA-256 `01f91eacaec0d82c488c6af20b5bb575412cde0065748f47874cb7f16c0351ad`, `58cf89f2fe14d3735318d331ce7e8608d80d48f1a91db40ec337d237d8fbe09d`, and `531a834a15b11233ca7d4565d516880ef830d95c7ee6cb474d2c5fbb7b767d92`, respectively.

The Kaggle editor showed 11h52m of 30h GPU quota used, leaving 18h08m, including the protected 6h reserve. [Private continuation version 369827269](https://www.kaggle.com/code/rocky62/urop-image-only-vit-b16-continuation/log?scriptVersionId=369827269) was submitted on T4 ×2 and was queued at first inspection. It embeds the original scientific source and requires the mounted recovery session receipt to match the exact saved SHA-256 before loading the checkpoint. Frozen test inference and independent readback are pending.

### Class recall on completed validation epochs

All values are percentages. Epochs through DeiT III epoch 3 come from the finalized first worker log. DeiT III epochs 4–6 come from the finalized continuation log. The class labels are in the registered order.

| Run | Epoch | True | Satire/Parody | Misleading Content | Imposter Content | False Connection | Manipulated Content |
|---|---:|---:|---:|---:|---:|---:|---:|
| Pilot 1e-5 | 1 | 89.43 | 32.13 | 38.77 | 0.00 | 75.98 | 52.67 |
| Pilot 1e-5 | 2 | 84.85 | 34.38 | 50.85 | 0.00 | 76.73 | 47.15 |
| Pilot 3e-5 | 1 | 86.96 | 39.83 | 44.23 | 0.00 | 82.88 | 52.57 |
| Pilot 3e-5 | 2 | 84.57 | 43.04 | 55.30 | 0.00 | 79.07 | 48.02 |
| Pilot 1e-4 | 1 | 83.83 | 35.63 | 43.28 | 0.00 | 86.88 | 44.26 |
| Pilot 1e-4 | 2 | 82.92 | 44.74 | 56.54 | 0.16 | 79.83 | 48.94 |
| TorchVision ViT-B/16 | 1 | 80.64 | 52.64 | 63.82 | 1.62 | 88.51 | 44.99 |
| TorchVision ViT-B/16 | 2 | 90.74 | 52.07 | 55.58 | 6.95 | 85.12 | 44.26 |
| TorchVision ViT-B/16 | 3 | 87.02 | 51.31 | 61.19 | 11.07 | 88.46 | 56.11 |
| TorchVision ViT-B/16 | 4 | 83.80 | 57.84 | 68.54 | 10.02 | 84.99 | 53.68 |
| TorchVision ViT-B/16 | 5 | 77.42 | 51.88 | 73.04 | 9.05 | 84.74 | 54.04 |
| TorchVision ViT-B/16 | 6 | 79.53 | 56.68 | 68.76 | 13.17 | 89.32 | 56.99 |
| DeiT III B/16 | 1 | 81.81 | 53.32 | 73.71 | 1.62 | 90.98 | 44.39 |
| DeiT III B/16 | 2 | 93.99 | 53.95 | 58.51 | 11.71 | 89.88 | 45.17 |
| DeiT III B/16 | 3 | 87.80 | 51.59 | 69.21 | 12.60 | 90.04 | 61.67 |
| DeiT III B/16 | 4 | 82.92 | 58.84 | 72.92 | 15.35 | 87.65 | 59.28 |
| DeiT III B/16 | 5 | 81.73 | 55.97 | 72.32 | 15.83 | 89.73 | 55.65 |
| DeiT III B/16 | 6 | 80.50 | 58.69 | 71.84 | 17.77 | 88.91 | 58.04 |

## Continuation startup and resumed epoch 4 validation

[Version 369827269](https://www.kaggle.com/code/rocky62/urop-image-only-vit-b16-continuation/log?scriptVersionId=369827269) started on two Tesla T4s and reverified the registered cohort at 118.5 seconds. The worker passed the registered source, configuration, environment, and saved-checkpoint gates before resuming directly at epoch 4 validation. At 940.6 seconds it logged 59,299 validation rows, accuracy **78.7265%**, macro-F1 **0.649430**, balanced accuracy **62.8253%**, and cross-entropy **0.693523**. Validation prediction SHA-256 is `cb88dae02c152ed6ab54ea9617861f13dc2888ad23331f13905d7ed9a39d3889`. The validation-only recovery kept the epoch 4 totals at 35,219 successful updates and nine AMP skips, and at 944.6 seconds the worker checkpointed the start of epoch 5. Epoch 3 remains the leading validated checkpoint at 80.2577%. The continuation output will be reopened once Kaggle finalizes it.

## Frozen validation selection and test submission

[Kaggle continuation 369827269](https://www.kaggle.com/code/rocky62/urop-image-only-vit-b16-continuation/log?scriptVersionId=369827269) completed in 7,969.0 seconds. In epoch 5, DeiT III recorded 78.4769% validation accuracy, 0.639940 macro-F1, and 61.8729% balanced accuracy. In epoch 6 it recorded 77.9440% accuracy, 0.640199 macro-F1, and 62.6252% balanced accuracy. The arm then stopped under the registered accuracy patience rule, with 52,826 successful updates and 16 AMP skips.

The reopened [selection and fixed validation receipt](https://www.kaggle.com/code/rocky62/urop-image-only-vit-b16-continuation/output?scriptVersionId=369827269) verify that DeiT III B/16 epoch 3, seed 42, won with **80.2577%** accuracy, **0.655443** macro-F1, and **62.1527%** balanced accuracy. Selection SHA-256 `1b562e241faf49918bbba404d9f1a4de7acb40bf3db7cd100418a93903ee1e66` matches the fresh-process [receipt](VIT_FINETUNE_FIXED_VALIDATION_369827269.json), which has SHA-256 `de80df50822492120c5b958f3d7bf93b699607bc921fec7c3a0e01dbc5be20ef`. On 40 fixed validation images, maximum absolute differences were `1.1102230246251565e-16` for class probabilities and `8.881784197001252e-16` for cross-entropy. Selected weight SHA-256 is `295ef963b57cb0db64182100887f05954a8c4cb09ebad9f8a80b021ac6051cf2`.

The Kaggle editor showed 14h04m of 30h consumed before the single test submission. [Private frozen test version 369892645](https://www.kaggle.com/code/rocky62/urop-image-only-vit-b16-frozen-test/log?scriptVersionId=369892645) was queued at first inspection. It mounts the exact frozen validation release alongside the two approved inputs and checks the fresh validation receipt hash. The test uses one worker on the pinned T4 session. It will evaluate 59,270 approved IDs once and derive the exact-byte no-training-overlap metrics from the same predictions. The independent CPU readback and test scores are pending.

The [separate private CPU readback draft](https://www.kaggle.com/code/rocky62/urop-image-only-vit-b16-cpu-readback/edit) has the two approved cohort inputs and both saved baseline outputs mounted. Its accelerator is None and internet is off. The draft is unsubmitted and awaits the completed test output and receipt SHA-256.

At 2026-11-15 13:20:32 UTC, Kaggle still showed private frozen-test version 369892645 as queued, 24 minutes after submission. Monitoring was paused at the owner's request. The Kaggle job was left in its existing state.

## Saved frozen test and independent CPU submission

[Private frozen test 369892645](https://www.kaggle.com/code/rocky62/urop-image-only-vit-b16-frozen-test/log?scriptVersionId=369892645) completed successfully in 862.1 seconds of Kaggle wall time. Its [saved output](https://www.kaggle.com/code/rocky62/urop-image-only-vit-b16-frozen-test/output?scriptVersionId=369892645) contains full and no-training-exact-byte-overlap predictions, metrics, reports and confusions. The reopened completion receipt lists full prediction SHA-256 `57a5848380c26f9446e949297af8acf51b01d81c3c3aef4b99c9c1a94de2c6b0`. Its 335-byte [local mirror](VIT_FINETUNE_TEST_SAVED_369892645.json) has SHA-256 `ede9f3882b1d8cba8302ad06a6d54c86b20faf0435e38f89b611cdc84aec3174`.

The saved test metrics show **80.3948%** accuracy, **0.660470** macro-F1 and **62.5296%** balanced accuracy on **59,270** rows. The no-training-exact-byte-overlap subset contains **56,052** rows and reports **80.3664%** accuracy. These are the GPU pipeline's saved metrics pending independent recomputation from prediction files.

[Private CPU readback 369953825](https://www.kaggle.com/code/rocky62/urop-image-only-vit-b16-cpu-readback/log?scriptVersionId=369953825) was submitted and started. It checks the exact test receipt hash and mounts the two approved cohort inputs and both historical prediction sources. Internet is off and no GPU was requested. Readback source cell SHA-256 is `6c7df18b088856c69fff8f25b0dc421f757193682c98003c9b747b3042d4f199`.

## Final independent verification

The [CPU readback version 369953825](https://www.kaggle.com/code/rocky62/urop-image-only-vit-b16-cpu-readback/output?scriptVersionId=369953825) completed in 138.4 seconds and verified the saved test output from version 369892645. The local [report](VIT_FINETUNE_REOPENED_REPORT_369953825.md) and [receipt](VIT_FINETUNE_REOPENED_VERIFICATION_369953825.json) match the reopened Kaggle files byte for byte. Their SHA-256 hashes are `6a95c609bc47558b24a54f1579347808a08bff772e23060dc2c8e173be989f0c` and `49c0c071c916367c3b66188127888ff3e5b6452cd4ad58fe528167c6f36bdcc8`.

The readback verified all 18 validation exports across five trials, all 59,270 test rows and the 56,052-row exact-byte overlap exclusion. Both test exports include six-class metrics and raw and row-normalized confusion matrices. The verifier checked checkpoint hashes and loaded the saved optimizer recovery state for every trial on CPU. It reconciled the validation-only promotion and winner, official split IDs, original labels and image hashes, prediction probabilities, paired baseline IDs and labels, and the fresh-process validation receipt. Training and test predictions, per-trial completion records, source snapshots and large weights are in the pinned private Kaggle outputs.

The selected DeiT III trial used **6.13 hours** of measured training and validation. Kaggle wall time was **41,441.7 s** for the initial scientific version, **7,969.0 s** for the continuation and **862.1 s** for the frozen test. The quota display showed 14h04m consumed before the test. The registered design used one seed and limited full trials to TorchVision ViT-B/16 and DeiT III. Both reached the registered early-stop criterion, with no sustained late accuracy improvement. The optional later-stage variants and seed replications were outside the registered run count. Intervals quantify test-sample uncertainty for the fixed seed, and historical comparisons also reflect differences in pretraining, optimization and checkpoint selection. The training-overlap check covers exact byte matches.
