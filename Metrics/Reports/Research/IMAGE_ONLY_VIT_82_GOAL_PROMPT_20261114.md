# Goal: fine-tune an image-only Vision Transformer and pursue 82% test accuracy

## Objective and authority

Implement, train, validate, test and independently verify an **image-only, six-class Vision Transformer** on our existing faculty Fakeddit cohort. Pursue at least **82.00% full-test accuracy**, exceeding the historical image-only ResNet-50 result of **81.1557%**.

This is an execution task. Carry the work through saved, reopened and verified results, not just code or a proposed plan. Use available tools, connectors, CLI and computer use as appropriate. Use computer use for Kaggle operations when necessary; prefer a reliable purpose-built tool when available. Inspect existing sessions and saved outputs before launching anything, avoid duplicate jobs, monitor submitted jobs through completion, and recover from checkpoints after interruptions.

You are authorized to implement separate experiments and run them within the existing available Kaggle quota. Make routine implementation decisions autonomously. Ask only for genuinely missing access, credentials, material scientific ambiguity, or additional paid resources. Do not purchase compute or change paid plans. Do not commit or push without a separate instruction.

**Scope is strictly image-only ViT.** Do not implement multimodal fusion, BERT, text encoders, explicit OCR, captions, metadata predictors, Swin, ensembles or a new ResNet training run. The existing ResNet results are comparison references. A single pretrained ViT plus a six-class head is the intended model. Image-only pretrained ViT variants are allowed as separate registered candidates.

## 1. Read the project and establish the starting state

Work in `/Users/panveenaidu/Downloads/SEM7/UROP`.

Read these files before changes:

- `/Users/panveenaidu/Downloads/SEM7/UROP/AGENTS.md`
- `/Users/panveenaidu/Downloads/SEM7/UROP/FOLDER_GUIDE.md`
- `/Users/panveenaidu/Downloads/SEM7/UROP/Metrics/Results/IMAGE_ONLY_VIT_RESNET_REPORT.md`
- `/Users/panveenaidu/Downloads/SEM7/UROP/Metrics/Results/IMAGE_ONLY_FINAL_REPORT_20261102.md`
- `/Users/panveenaidu/Downloads/SEM7/UROP/Metrics/Reports/Research/VIT_82_AND_FUSION_RESEARCH_20261114.md` — use its image-only sections; its multimodal stages are out of scope.
- `/Users/panveenaidu/Downloads/SEM7/UROP/Configuration/Image Only/image_only_usable_6way_v1.json`
- `/Users/panveenaidu/Downloads/SEM7/UROP/Configuration/Image Only/image_only_vit_resnet_frozen_v1.json`
- `/Users/panveenaidu/Downloads/SEM7/UROP/Model/Image Only/frozen_image_pair_v1.py`

Inspect reusable components:

- `/Users/panveenaidu/Downloads/SEM7/UROP/Training/Text + Image/Scripts/packed_image_io_v3.py`
- `/Users/panveenaidu/Downloads/SEM7/UROP/Training/Text + Image/Scripts/usable_cohort_v2.py`
- `/Users/panveenaidu/Downloads/SEM7/UROP/Testing/Image Only/verify_frozen_image_pair_v1.py`
- `/Users/panveenaidu/Downloads/SEM7/UROP/Model/Image Only/train_image_only_v1.py`

Some reusable loaders live in a folder named Text + Image; importing a loader does not authorize using text as input. Trainers moved into `Model/`; check imports, dependencies and paths before reuse. Do not blindly execute old launch commands. Preserve all existing work and completed baseline evidence.

Verified starting results:

| Model | Regime | Test accuracy | Macro-F1 |
|---|---|---:|---:|
| ViT-B/16 | Frozen encoder, trained head | 65.6487% | 0.481237 |
| ResNet-50 | Matched frozen encoder, trained head | 71.9082% | 0.527292 |
| ResNet-50 | Historical end-to-end fine-tuning | 81.1557% | 0.661796 |

The 71.9% result belongs to frozen ResNet, not ViT. Full ViT fine-tuning remains untested. The historical ResNet recipe and pretraining differ, so numerical comparisons do not isolate architecture alone.

Useful existing private Kaggle references:

- Packed data: https://www.kaggle.com/datasets/rocky62/urop-faculty-usable-packed-input-v3
- Image quality output: https://www.kaggle.com/code/rocky62/urop-images-quality-check
- Frozen comparison: https://www.kaggle.com/code/rocky62/urop-image-only-vit-vs-resnet-50?scriptVersionId=369302248
- Independent readback: https://www.kaggle.com/code/rocky62/urop-image-only-vit-comparison-readback/output?scriptVersionId=369460396
- Historical ResNet: https://www.kaggle.com/code/rocky62/urop-image-only-resnet-50?scriptVersionId=364917396

If the local checkout is unavailable, inspect the private repository `panvenaidu/Fake-News-Detection` and saved artifacts. Do not substitute a different public dataset silently.

## 2. Freeze data scope and evaluation rules

Use the existing approved usable-image cohort:

- Training: **563,601** posts.
- Validation: **59,299** posts.
- Test: **59,270** posts.

Preserve split membership, IDs, labels and approved exclusions. Verify mounted dataset/output versions and manifest/index hashes against existing evidence. Decode RGB pixels strictly; do not introduce new silent decode exclusions or label corrections.

Class mapping: 0 True; 1 Satire/Parody; 2 Misleading Content; 3 Imposter Content; 4 False Connection; 5 Manipulated Content.

For this **new accuracy-focused experiment**, register checkpoint selection before training:

1. Highest unrounded validation accuracy.
2. Higher validation macro-F1 on an exact accuracy tie.
3. Lower validation cross-entropy.
4. Earlier epoch.

Apply the same rule to every candidate. Document that prior runs selected macro-F1 first; do not rewrite their results. Report macro-F1, balanced accuracy and all class recalls throughout so the accuracy target does not hide class collapse.

Do not use test images, labels, predictions or errors for tuning. Historical aggregate scores are comparison references only. Inspect training/validation examples for diagnosis. The test benchmark has been used by previous models; acknowledge that history rather than calling it newly untouched.

## 3. Preflight and register an affordable run budget

Check current Kaggle jobs, live GPU quota, hardware, session limits, writable disk and input availability. An earlier observation of 30 GPU hours is not current evidence.

Create a separate private notebook, configuration, source snapshot and output directory for this fine-tuning study. Pin software versions and pretrained weight hashes. Keep all data, per-post predictions and weights private.

Run a small real-image train/validation smoke test. Verify input shapes, six logits, finite loss, nonzero encoder gradients, changed encoder/head parameters, optimizer updates and saved-checkpoint reload agreement in evaluation mode. Exercise resumable state and verify continuation agrees with an uninterrupted short run within documented numerical tolerances.

Benchmark a few hundred representative training updates, including loading and accumulation, after startup. Measure validation throughput and storage requirements. Estimate pilot, full training, test, checkpointing and independent verification costs. Reserve about 20% of the available compute window for recovery and verification. Reduce the number of trials before sacrificing final full-cohort evaluation.

Register the maximum trials, epoch caps and available GPU-hour budget. Do not start jobs that cannot finish or save recovery state before session/quota expiry. If multiple devices are used, verify distributed sample coverage and actual quota accounting; do not assume automatic multi-GPU use.

## 4. Implement the first end-to-end ViT

Start with TorchVision `vit_b_16` and `ViT_B_16_Weights.IMAGENET1K_V1` for continuity with the frozen result. Replace the ImageNet classifier with dropout 0.2 and a six-logit linear head. Make the entire encoder trainable.

Feed images through the encoder on every training step. Cached frozen final embeddings cannot support end-to-end fine-tuning. Use training mode during training and evaluation mode during validation/testing.

Starting recipe:

| Setting | Initial proposal |
|---|---|
| Input | RGB, 224 × 224, checkpoint-compatible normalization |
| Training transform | Mild random resized crop, scale 0.8–1.0, bilinear antialiasing; no flips initially |
| Evaluation transform | Deterministic shorter-side resize to 256, center crop 224 |
| Optimizer | AdamW |
| Encoder learning rate | 3e-5 |
| Head learning rate | 3e-4 |
| Weight decay | 0.05 for matrix weights; zero for bias/norm parameters |
| Effective batch | 64; choose microbatch 8 or 16 plus accumulation based on memory |
| Schedule | 10% successful-update warmup, then cosine decay |
| Loss | Ordinary six-class cross-entropy |
| Precision | FP16 AMP with FP32 parameters; gradient clipping 1.0 |
| Initial seed | 42 |

Handle skipped AMP updates correctly. Record effective batch and successful optimizer updates. These are proposed starting values, not guaranteed optimal settings.

## 5. Run bounded validation-only experiments

### Stage A — learning-rate screening

Create one fixed, class-stratified 30,000-row subset from training only. Save its ID manifest. Compare encoder learning rates `1e-5`, `3e-5`, `1e-4`, keeping the head LR 10 times the encoder LR. Use equal data exposure, seed and order, initially two complete pilot epochs per trial, with full validation when affordable. Mark all pilot results as pilots.

Use pilots to detect unstable/ineffective settings, not to claim final accuracy. Preserve at least two plausible candidates when curves are close; short-run rankings may reverse at scale.

### Stage B — first full-cohort fine-tuning run

Promote a stable original ViT configuration to full training and full validation. Register up to eight epochs if the measured budget permits. Set the complete learning-rate schedule in advance. Validate after every epoch; select checkpoints using the registered rule.

Allow early stopping after at least four epochs, with patience three full validation checks without an accuracy improvement. Save the best checkpoint even if the final epoch is worse. Stop at the registered cap, not when a desired score happens to appear. Do not evaluate the test set yet.

If the measured budget permits fewer epochs, declare the limitation before launching. Do not call an incomplete run fully converged.

### Stage C — targeted improvements

Use training/validation evidence to prioritize a small number of changes, one at a time:

1. **Stronger pretrained ViT:** screen one supervised DeiT III/ImageNet-21k ViT-B/16, or an accessible MAE-B/16 or DINOv3-B/16 checkpoint. Preserve the ViT-B/16 focus and pin its exact architecture/weights/preprocessing. If weights require unavailable access, use an accessible candidate; do not let an optional model block the main run. No Swin or language-pretrained CLIP branch in this study.
2. **Full-frame preprocessing:** compare aspect-preserving resize/padding with the crop recipe. Inspect training/validation screenshots and memes for lost content. Register matching deterministic evaluation transforms.
3. **Layer-wise LR decay:** test factor 0.75, with smaller learning rates in earlier blocks.
4. **Regularization:** test label smoothing 0.05 or weight decay 0.01 separately if learning curves justify it.
5. **Class imbalance:** if rare-class collapse persists, test one mild weighting/logit-adjustment setting using training frequencies and validation selection. Do not assume improved macro-F1 also improves accuracy.

Avoid a large Cartesian sweep. Do not stack several unverified changes and claim one caused a gain. Give a strong candidate enough training before discarding it. If validation is still improving near the cap, an additional run with a prospectively registered schedule of up to 12 epochs is allowed only within the registered compute budget and before test evaluation.

Higher resolution is a later option only when validation error analysis and budget justify it. Verify positional-embedding interpolation/input-size support; changing the resize alone is insufficient. Do not add aggressive CutMix, erasing or rotations without a specific label-preservation justification.

### Stage D — select and confirm

Use the full validation split to choose the final recipe. Where budget permits, run fixed seeds 42, 43 and 44 for that recipe and report all results. Do not choose the luckiest test seed. Seed 42 is the primary single-model result; additional seeds assess repeatability, not an ensemble.

Prefer completing and verifying one valid full-cohort result over leaving many unfinished pilots. Record all unsuccessful and abandoned trials with their reasons.

## 6. Recovery and experiment records

Save model, optimizer, scheduler, AMP scaler, RNG states, sampler/data cursor, epoch and update counts. Checkpoint periodically and before session expiry. Reopen persistent saved checkpoints before relying on them for continuation. Never restart an expensive finished stage merely because a local file is missing; inspect saved Kaggle outputs first.

For every run record hypothesis, parent config, changed settings, source/config hashes, checkpoint hash, seed, split hashes, preprocessing, trainable parameters, memory, GPU time, validation history, class recalls and selection decision. Log crashes as failures with missing metrics, not zero-valued accuracy results.

Use the controlled experiment discipline from `/Users/panveenaidu/.codex/skills/autoresearch/SKILL.md` if useful. Its literal LM `val_bpb` evaluation, five-minute convergence assumption, destructive reset workflow and indefinite loop do not apply to this project. Do not launch that separate language-model workflow.

## 7. Freeze, test once and independently verify

Before accessing test inputs for inference, freeze the final recipe, selection receipt, selected checkpoint hashes and any preregistered seed replications. Do not evaluate every exploratory candidate on test.

Evaluate the selected model on all 59,270 test IDs. Also report the exact-byte no-training-overlap subset; for the full approved training cohort it contains 56,052 posts. Confirm membership from the actual manifests. Byte hashes detect exact repeats, not all near duplicates or external pretraining overlap.

Independently recompute from saved predictions:

- Accuracy, macro-F1, weighted-F1, balanced accuracy and cross-entropy.
- Per-class precision, recall, F1 and support.
- Raw and normalized confusion matrices.
- Unique/exact ID coverage and unchanged labels.
- Six finite probabilities per row, sums near one, and argmax/predicted-class agreement.

Reload selected weights in a fresh process and reproduce a fixed validation batch. Reopen the saved private Kaggle version and independently verify its saved outputs, not just transient live notebook output. Provide accuracy uncertainty and paired comparison intervals when compatible baseline predictions are available; distinguish sampling uncertainty from seed variability.

Compare the new result with frozen ViT 65.6487% and historical fine-tuned ResNet 81.1557%. Report percentage-point differences and limitations of the different pretraining, optimization and selection protocols. Do not portray this as a matched ResNet retraining experiment.

After test evaluation, do not continue tuning against that test score. If the target is missed, report the gap; any further adaptive development needs a separately justified evaluation plan.

## 8. Deliverables and stopping conditions

Deliver the separate trainer/configuration, private saved Kaggle version, pinned environment/weights, scope/budget registration, complete experiment log, resumable checkpoints, selected model, validation/test predictions and metrics, confusion matrices, independent verification receipt and final report. Use the existing seven-folder project organization and update the single handoff in `AGENTS.md`. Preserve historical artifacts.

The final answer must clearly state:

1. Whether training and saved-output verification completed.
2. The actual full-test accuracy and whether it reached 82.00%.
3. The difference from historical ResNet's 81.1557%.
4. Macro-F1, balanced accuracy, rare-class results and overlap-subset accuracy.
5. Selected model, initialization, epoch, seed, runtime and exact saved-version/report links.
6. Any remaining limitations or access/quota blocker and the exact recoverable state.

Claim the **82% accuracy target achieved only after independently verified full-test accuracy is at least 82.00%**. Completing the experiment below 82% is a valid measured outcome, but does not fulfill the accuracy target. Never manufacture success, change labels/splits, drop difficult samples or quietly introduce text. If available resources prevent completion, preserve recovery state and report the concrete blocker; do not promise an unobserved score.
