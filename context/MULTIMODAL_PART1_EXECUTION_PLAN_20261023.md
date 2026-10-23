# UROP · Text + image · Part 1

Execution handoff · MM-PART1-v2 · 23 October 2026

Status: PLAN PREPARED. No full multimodal training has started. Execute this plan when the user gives the handoff prompt to the execution agent. This revision supersedes the October 9 Part 1 instructions for the accuracy target, usage thresholds and execution safeguards. Historical protocols and completed results stay intact.

## 01 · What Part 1 must achieve

Use **GPT-6.1 Sol, High reasoning effort** for execution. This is a practical recommendation, not a measured ranking or a guarantee. Extra High is optional for a specific unresolved recovery or numerical bug; it does not improve the trained classifier merely by being selected. The assistant writes and operates the experiment; **BERT-base + ResNet-50** is the research model being trained. Astra is not required to execute this saved plan.

Part 1 delivers a complete, verified image cohort, a full-cohort trainer, and **epochs 1 and 2 of one four-epoch experiment**, each followed by full validation. It ends with a usable checkpoint for epoch 3, evidence saved locally/private cloud, updated project records, and a verified GitHub backup. Part 2 finishes training, selects the checkpoint and performs the final public test. Image-only is a separate later task using the same audited images.

| Workflow | Current recorded completion | After accepted Part 1 |
|---|---:|---:|
| Text-only | 100% | 100% |
| Full text + image | 40% | 60% |
| Image-only | 20% | 20% |
| Three-modality overall | 53% | 60% |

These are the existing five-stage workflow bars, not accuracy or elapsed time. The 40% multimodal starting value credits the schema audit and pilot architecture; it does **not** mean full images or the full trainer are ready. The 2,600-row pilot is complete separately. Preparation alone does not increase these bars.

The revised minimum performance aspiration is **+1 percentage point** over the matching six-way multimodal paper result: **87.00% validation accuracy and 86.88% test accuracy**. The previous +2–3-point goal is a stretch goal. Part 1 cannot establish a final test win because it does not run the test. No expected score is promised.

Timing: allow **2–4 hours for implementation and checks**, plus **roughly 8–12+ GPU hours for two epochs and validation**, conditional on measured throughput. Full-image acquisition and verification may add several hours or longer and currently has no reliable upper bound. This is not a two-hour total task. Recalculate the estimate before launching; do not promise completion today.

## 02 · What to read and verify first

All local project work must stay inside `/Users/panveenaidu/Downloads/SEM7/UROP`. Paths below are relative to that root. Synced ChatGPT project `sources/` files are read-only references. Preserve unrelated work, especially the existing modification to `results/UROP_Text_Only.html` and untracked literature/screenshots.

Read in this order; newest verified evidence takes precedence over old status paragraphs:

1. This plan, `context/RESUME_HERE.md`, `context/PROJECT_CONTEXT.md`, `results/PROGRESS_TRACKER.json` and `work_logs/MODEL_STATUS.md`.
2. `context/DECISIONS.md`, `context/EXPERIMENT_LOG.md`, `context/TASK_REPORT.md`, `collab/COLAB_WORKLOG.md`, `work_logs/TROUBLESHOOTING.md` and `README.md`. Older notes saying text is unfinished, usage is exhausted, or 29h09m GPU remains are dated history.
3. `results/TEXT_ONLY_FINAL_REPORT_20261009.md`, `results/text_completion_execution_20261009.json`, and the completion verification in the official text recovery directory. Preserve the completed six-epoch text run; do not retrain it.
4. `results/official_dataset_provenance.json`, `results/official_dataset_audit.json`, the three original TSVs, `data/verified_paired_manifest.csv`, `results/MULTIMODAL_PLAN_AUDIT_20261009.json` and the new Part 1 audit receipt.
5. `context/MULTIMODAL_COMPLETION_PLAN_20261009.md`, `scripts/train_multimodal_pilot.py`, `scripts/build_paired_pilot.py`, `configs/multimodal_pilot_6way_v1.json`, the pilot notebook/bootstrap and pilot verification/result files. Read `scripts/train_official_text_recovery_v1.py` for recovery lessons, not as a multimodal trainer.
6. The [faculty dataset](https://drive.google.com/drive/folders/1DuH0YaEox08ZwzZDpRMOaFpMCeRyxiEF), [paper](https://arxiv.org/html/1911.03854v2), [authors' dataset instructions](https://github.com/entitize/Fakeddit), and local `LITERATURE_SURVEY_REPORT_UPDATED_FINAL.pdf`. Focus on paper Tables 4–6, dataset eligibility, experiment settings and minority-class errors.
7. Compare local branch/commit with [GitHub](https://github.com/panvenaidu/Fake-News-Detection). Inspect working changes before editing or staging. Check live assistant allowance, signed-in cloud access, running jobs, GPU allowance, session duration and storage.

Do not reread every image or tensor as prose. Inventory files, read relevant source/context/results, then perform explicit integrity and decode checks where required. A file inventory is not a claim that every file was substantively reviewed.

At execution, create or reuse one explicitly user-requested Goal with the Part 1 acceptance criteria. A Goal does not provide extra assistant credits, GPU time, authentication or guaranteed unattended monitoring. Do not create a scheduled task.

## 03 · Gate A: the exact faculty dataset and all images

Use the released `multimodal_only_samples` in the [faculty dataset](https://drive.google.com/drive/folders/1DuH0YaEox08ZwzZDpRMOaFpMCeRyxiEF). Original files remain in `data/official_multimodal_v2/`.

| File | Official rows | Images currently present locally | Missing or unverified locally |
|---|---:|---:|---:|
| multimodal_train.tsv | 564,000 | 62,635 | 501,365 |
| multimodal_validate.tsv | 59,342 | 6,685 | 52,657 |
| multimodal_test_public.tsv | 59,319 | 6,675 | 52,644 |
| Total | 682,661 | 75,995 | 606,666 |

Inputs are `clean_title` and the image with the same `id`; target is `6_way_label`. Classes: **0 True; 1 Satire/Parody; 2 Misleading Content; 3 Imposter Content; 4 False Connection; 5 Manipulated Content**. Keep the original split membership. Normalize the old manifest's split spelling `validate` to `validation` only in the new derived manifest, with a recorded mapping.

1. Recheck TSV hashes, row counts, label range/class counts, nonempty titles, unique IDs and no cross-split ID overlap. The current TSV hashes matched the saved provenance on October 23.
2. Use a **45–90-minute feasibility checkpoint** to establish access, actual archive size, transfer speed, local/cloud scratch capacity, private input limits and persistence. Current local free space was about 120.3 GB decimal; this must be rechecked. `images.zip` is the existing subset, not the full collection.
3. Prefer the authors' [public_images.tar.bz2](https://drive.google.com/file/d/1cjY6HsHaSZuLVHywIxD5xQqng33J5S2b/view). Verify metadata and a feasible storage route before a large transfer. Use CPU preparation before allocating a GPU. Account for compressed source, extraction, temporary shards and retained checkpoints together.
4. Acquire required IDs into bounded, versioned shards with hashes and a restart log. A compressed TAR stream is not automatically resumable at an arbitrary member: prove transfer/extraction recovery and ensure discarded progress cannot force repeated full downloads. Preserve original bytes and existing images. Detect and log byte conflicts before reuse.
5. Decode **every required image**, record missing/corrupt/duplicate IDs and content duplicates across splits, and verify exact split/title/label joins. Audit all three splits for integrity only; test labels/images must not drive model selection. No placeholders, silent exclusions, new split, rebalancing or unrelated image source.
6. Save `data/official_paired_v1/paired_manifest.csv`, per-image/shard provenance and `results/official_image_coverage_v1.json`. Publish only to the existing private cloud workspace, verify its saved version, and recheck hashes inside the future training runtime.

**Gate passes only with 564,000 / 59,342 / 59,319 usable pairs.** If access, capacity or coverage fails, save exact failed IDs/reasons and a feasible next action. Continue independent code checks, but stop dependent full-cohort training. A reduced cohort needs a separate protocol and the user's scope decision; it cannot silently replace this plan or be called comparable full-cohort completion.

## 04 · Gate B: architecture and frozen protocol

Reuse the pilot architecture in a new full-cohort implementation. ResNet is **50**, not 55. This is a proven project baseline, not a claim to use the newest research model. ModernBERT, CLIP, SigLIP 2, image-only and extra seeds are outside Part 1.

```text
clean_title -> BERT tokenizer (max 128) -> BERT-base -> CLS 768
                                                    |
                                       Linear 768->512 + LayerNorm
                                                    |
                                               MAXIMUM -> 512->256
                                                    |      GELU + dropout 0.2
                                       Linear 2048->512 + LayerNorm
                                                    |      256->6 logits
paired image -> RGB / 224 crop -> ResNet-50 -> pooled 2048   -> six probabilities
```

Both encoders, projection layers and classifier train end to end. Apply unweighted cross-entropy to logits; softmax is for reporting probabilities.

| Setting | Freeze before the registered run |
|---|---|
| Protocol and seed | OFFICIAL-6W-MM-v1; seed 42; immutable attempt ID |
| Planned budget | Four epochs total; Part 1 stops after epoch 2 validation |
| Text initialization | Verified validation-selected text epoch 4 encoder only |
| Vision / head initialization | ResNet50 ImageNet1K_V2; fresh projections/classifier |
| Batch / tokens | Microbatch 8; accumulation 4; effective batch 32; eval batch 32; max 128 tokens, dynamic padding |
| AdamW learning rates | BERT 1e-5; image 1e-4; head 1e-3 |
| Weight decay | Text/head .01; image .0001; zero for bias/norm; betas (.9,.999), epsilon 1e-8 |
| Schedule | 10% warm-up then linear decay over the entire four-epoch budget; preserve across parts |
| Numerical settings | CUDA fp16 AMP + GradScaler; clip gradient norm 1.0; log skipped updates |
| Train image transform | RGB; RandomResizedCrop 224, scale (.8,1), ratio (.75,4/3), bilinear antialias; ImageNet normalization; no flips or colour augmentation |
| Validation transform | RGB; Resize 232 then CenterCrop 224; ImageNet normalization |
| Selection | Highest full-validation Macro-F1; ties lower loss, then earlier epoch |
| Early stopping | Earliest stop after epoch 3; patience 2, Macro-F1 improvement threshold .001; define and persist counter semantics before launch |

The text warm start is **transfer initialization**, with fresh optimizer/scheduler/scaler. Use explicit `BertModel(add_pooling_layer=False)`. Strip `bert.` and strictly map all 197 encoder keys; exclude only the two pooler and two classifier keys. Verify every target shape/dtype/key and save a mapping receipt. The old saved config says `BertForMaskedLM`; the verified tensors are from the classifier. Do not instantiate from that misleading architecture field or silently use non-strict loading.

For the full train count, 70,500 microbatches form 17,625 planned optimizer boundaries per epoch, 70,500 over four epochs; warm-up is 7,050 successful updates. Track consumed batches and successful updates separately when AMP skips. Report prior text training cost as part of the warm-start method. This is not an exact replication of the paper's feature pipeline.

## 05 · Gate C: implementation and meaningful checks

Create a separate `scripts/train_official_multimodal_v1.py`, `configs/multimodal_official_6way_v1.json`, dedicated private Kaggle notebook/bootstrap, and an independent evidence verifier. Keep the completed pilot source and artifacts unchanged. Freeze source/config/dependency/model revisions in the run directory before actual training.

Required trainer behavior:

- Accept full paired manifest, dataset root and output root; validate exact data hashes and split counts. Fail if CUDA is unavailable for training. CPU-only integrity/synthetic checks are allowed locally.
- Separate total budget (four epochs) from the current job stop boundary (epoch 1 or 2). Part 1 must not construct/run a test evaluator accidentally. The pilot automatically tests at its end; do not copy that behavior.
- Pretokenize text, load images efficiently and use deterministic sampler order. Seed each crop using a stable algorithm from seed/epoch/ID, independent of worker count. Do not use process-randomized Python hash. Keep worker RNG separate from sampler/model RNG and persist algorithm version.
- Save after cleared-gradient optimizer boundaries, normally every 1,000 successful updates plus every completed epoch. Add a time-triggered safe boundary and a graceful stop/export request so reserve handling does not wait an entire epoch.
- Save epoch-end training state before validation; if validation is interrupted, rerun only that deterministic validation, not the epoch. Mark validation complete separately. Keep last committed consumed-batch position for mid-epoch recovery.
- Enforce one active trainer per attempt, explicit launch/resume/finish states, and an idempotent guard for a verified completed Part 1. A status cell performs one bounded check and exits.

Tests before full launch:

1. Exact joins, split normalization and six-label mapping; missing or corrupt image fails with its ID. No access path can escape the input root.
2. Six finite logits and nonzero gradients through both encoders and fusion/head; RGB, grayscale, palette and RGBA input handling.
3. Correct accumulation/sample weighting including a synthetic partial tail; AMP skipped steps do not advance scheduler; train/eval mode and BatchNorm behavior are correct.
4. Warm-start key mapping and weight checksum; checkpoint round-trip; selection ties and early-stop counter behavior.
5. Interrupt/resume a tiny training-only run mid-epoch, at epoch end, after an AMP skip and after a second interruption. Compare resumed suffix AND next-epoch IDs, crop parameters, LR, optimizer/scaler counters, RNG and BatchNorm buffers on the installed cloud Torch. Account for sampler exhaustion draws if using RandomSampler. Check numerical agreement within a declared tolerance; do not promise cross-device bitwise reproducibility.
6. Corrupt/incomplete newest checkpoint falls back to the preceding verified generation; double launch and repeated completed-Part-1 invocation do no extra training/test.
7. Validation exports exact IDs, all six probabilities, per-row cross-entropy, labels and predictions. Recompute all requested metrics and check confusion-matrix/support totals independently.

Use synthetic or train-only examples for engineering/throughput tests. Mark them as disposable checks; restore the original initialization and RNG before the registered experiment. Record any config change before seeing full validation results.

## 06 · Gate D: cloud preflight and the two epochs

Operate **Chrome profile Rocky, signed in as panvee62@gmail.com**, and the existing private Kaggle workspace. Verify the actual Google account and Kaggle workspace before uploads or launching a job; the profile name alone is not identity proof. Native computer/desktop control may open or focus the dedicated Chrome application/profile; then prefer the enabled Chrome extension/browser controls for page actions. If a browser tool opens an unrelated signed-out session, return to Rocky rather than silently migrating accounts. If extension control disconnects, preserve progress and reconnect; never claim a click or launch succeeded without evidence. Genuine private login/consent may require the user. Prefer the proven single-T4 training path if available. Record actual allocated and used devices. Colab through Chrome is fallback only. No Colab CLI/new OAuth, paid compute, account migration or scheduled task is included.

1. Verify signed-in access, active jobs, current GPU allowance, actual session cap, input/output/storage limits and persistence. Historical 29h09m remaining is not current. The Chrome session used for this plan could view public Drive but was signed out; it did not verify Kaggle access or quota.
2. Stage immutable private inputs on CPU. Verify full manifest/shards/weights inside the runtime. Reserve enough disk for two recovery generations, selected weights, predictions, logs and temporary writes. Do not duplicate large image inputs into saved model outputs.
3. Run a **10–15-minute train-only throughput preflight** after warm-up. Measure train/evaluation-path throughput, peak VRAM, loader waits, checkpoint duration and export time. Keep microbatch 8 unless a preregistered change is necessary; changing it changes ResNet BatchNorm behavior even with identical effective batch size.
4. Estimate one epoch as `564000 / train_examples_per_second + 59342 / eval_examples_per_second + checkpoint_seconds`. Validation-path speed measured on train examples is provisional; refine it after the first actual full validation. Add 20% timing margin and at least one hour for saving/export before the current session limit.
5. Use one-epoch cloud jobs if two epochs do not comfortably fit. Both jobs resume the same four-epoch schedule and attempt. Two user work packages need not equal two cloud sessions. Never shrink the cohort or reset the LR schedule to fit a timer.
6. Train epoch 1 on all 564,000 pairs, validate all 59,342, export full metrics/predictions and verify a durable checkpoint. Refresh quota and timing. Only then launch/resume epoch 2 if the reserve and cloud gates permit.
7. Finish epoch 2 and full validation. Save latest recovery for epoch 3 **and** the best validation-selected weights so far; these can differ. Stop further training automatically at the Part 1 boundary. The public test remains pending.

The old pilot took about 200.5 seconds for its small training/evaluation loop. Scaling it suggests roughly 10.5 GPU hours for two full epochs, but tiny-cohort scaling can misestimate full image I/O and validation overhead. Replace the 8–12+ hour planning range with measured values; preparation and transfers are additional. If quotas are inadequate, give the exact remaining work and reset observation instead of repeatedly reconnecting or launching doomed runs.

Live status must include UTC timestamp, epoch, consumed batch, successful optimizer updates, recent loss, GPU utilization and last verified durable checkpoint. Advancing timestamps/counters plus process/device evidence support “running.” A spinner, green tick, old output or `Process None` alone does not establish whether a trainer is running, finished or stopped.

## 07 · Recovery and assistant-usage reserve

Check the applicable assistant allowance before work, before every large transfer/job, after each major checkpoint and periodically during active work. Use the smaller remaining percentage of applicable short/weekly limits. Recheck at roughly ten-minute active-work intervals when available. GPU quota and assistant quota are separate. If usage is unavailable, report that limitation and work in conservative bounded stages; do not invent a percentage or promise automatic threshold detection while inactive.

| Remaining assistant allowance | Mandatory behavior |
|---|---|
| Around 25% | Refresh all records and prepare the handoff early. Ensure a live job has a bounded stop and durable export route. |
| At or below 20% | Enter reserve. Start no new training job, large transfer, experiment or major refactor. Request the next safe checkpoint/stop boundary, retrieve and verify evidence, update all context/log/status files and sync reviewed Git changes. |
| At or below 10% | Substantive work has stopped. Perform only essential checkpoint verification, Git receipt and final handoff. No further model debugging or tuning. |
| At or below 5% | Hard stop of assistant work. The checkpoint/handoff should already be complete. Emit the saved location, exact last durable point, job state and next action; if anything is unverified, say so immediately. Do not begin saving a huge checkpoint here. |

If allowance jumps across a threshold, apply the most conservative crossed state immediately. Do not plan to consume the 5% reserve. Continuous small records and bounded jobs provide protection even if the agent is abruptly rate-limited.

Checkpoint contents: model parameters and BatchNorm buffers; optimizer; four-epoch scheduler; AMP scaler; Python/NumPy/Torch/each-CUDA-device RNG; sampler order/consumed position; crop algorithm/state; epoch and validation-complete flags; successful/skipped updates; best-checkpoint identity and selection/early-stop history; data/config/source/environment hashes.

Write on session-local disk using generation IDs, validate the tensor and metadata, then advance the pointer atomically and retain the preceding valid generation. The verified tensor's consumed position outranks newer log/JSON observations; replay only the work after the last valid saved position, recording the replay. A file in notebook scratch space is only a **local runtime checkpoint**. Call it durable only after verifying a saved private cloud output/version or retrieved local artifact survives session loss. Persist at least at every completed bounded cloud job; record the possible replay window if emergency runtime loss predates export.

Before stopping a cloud runtime, verify its durable output. Prefer graceful stop/export over killing a process mid-write. A job may continue after the assistant stops only if it is already submitted, has a bounded end and verified persistence behavior, and its unsupervised state is explicitly disclosed. Never claim ongoing monitoring without an active mechanism. A verified save makes work recoverable; no plan can promise zero cloud failures.

## 08 · Deliverables and acceptance checklist

Use `results/experiments/multimodal/OFFICIAL-6W-MM-v1_seed42_<UTC>/` for this run's small evidence. Keep large images, weights and archives under ignored `data/` and verified private cloud storage. Save an artifact manifest with bytes, hashes, roles, timestamps and storage locations.

Required outputs include:

- Full image coverage/provenance and immutable private input version; frozen protocol, source, environment and warm-start mapping receipts.
- Epoch 1 and epoch 2 training history, counts, timing, successful/skipped updates and error log; every evaluation must cover the complete official validation ID set exactly once.
- Validation accuracy, micro-F1, Macro-F1, weighted-F1, balanced accuracy and sample-mean cross-entropy loss; six-class precision/recall/F1/support; raw and normalized 6x6 confusion matrices; full probabilities and per-item loss for independent recomputation.
- Latest recovery checkpoint and current selected weights, tokenizer/config, integrity/load verification, private saved cloud version/job URL, local retrieval hashes and explicit next epoch/batch.
- `results/MM_PART1_RECEIPT_<date>.json` and `results/MM_PART1_REPORT_<date>.md`, with each gate's status, exact completed stages, failures, live quota observation and next action. Include a file count and manifest, not an unsupported “everything saved.”

At data readiness, preflight, each durable epoch boundary and final handoff, update `context/PROJECT_CONTEXT.md`, `context/RESUME_HERE.md`, `context/DECISIONS.md`, `context/EXPERIMENT_LOG.md`, `context/TASK_REPORT.md`, `collab/COLAB_WORKLOG.md`, `work_logs/MODEL_STATUS.md`, `README.md` and `results/PROGRESS_TRACKER.json` / `.md`. Update troubleshooting when a new failure is understood. Preserve history and clearly mark superseded observations.

GitHub: review exact staged changes; commit/push source, config, notebooks with sanitized outputs, small metrics, reports and receipts. Keep raw TSVs, images, checkpoints, secrets, oversized prediction files and unrelated user edits out. If a prediction export is too large, retain it privately and commit its manifest/hash. Verify the remote commit and save its receipt. A failed push must be reported as pending, never as backed up. The local context files are the next agent's durable memory; do not depend on hidden chat memory.

Part 1 is accepted only when **all** are true: full image gate passed; registered full trainer/checks passed; two complete training epochs; two full validations; usable next-epoch recovery; verified local/private artifacts; updated records and verified Git backup; no final test performed. Then report full multimodal 60%, train 50% (2/4), validation 50% (2/4), final test 0%. The Part 1 package itself is 100% complete; the whole multimodal model is not.

After one completed registered epoch plus validation, the existing tracker can show 50% multimodal. Code/image staging alone stays 40%. If any acceptance gate fails, report partial completion and the exact blocker. Do not mark a Goal complete just because usage is low. Part 2 continues the same run from epoch 3; image-only and later improvements remain separate.

## 09 · Comparison rules and evidence anchors

| Matching six-way result | Validation accuracy | Test accuracy |
|---|---:|---:|
| Paper: BERT + ResNet-50 maximum fusion | 86.00% | 85.88% |
| Current minimum target: +1 percentage point | 87.00% | 86.88% |
| Our full multimodal | Pending | Pending; Part 2 only |
| Our completed text-only baseline | 82.7407% | 82.3901% |

Source: [paper Tables 4–5](https://arxiv.org/html/1911.03854v2). The paper's six-way text row is 76.96% / 76.77%; binary text scores are a different task. It does not report comparable Macro-F1, weighted-F1, balanced accuracy or loss: write “not reported.” Table 6 gives class error proportions, not F1. Keep paper-derived comparisons limited to the matching metric/task.

Our text accuracy is numerically higher than the paper's text row. That does not predict a multimodal win. The paper uses a different feature pipeline; its multimodal count is 682,996 versus 682,661 released rows (335-row difference unresolved). The first full run is single-seed; do not describe a one-run difference as statistically established superiority.

Select by validation Macro-F1, report the accuracy of that same checkpoint, and never select or redesign using test performance. If the +1-point target is missed, retain the run, review validation errors, then register a separate improvement experiment. Possible later work includes aligned pretrained vision-language features and controlled fusion comparisons; none is automatically authorized by Part 1. No honest agent can guarantee the target in advance.

Data SHA-256 anchors (verified October 23; compare full strings):

```text
multimodal_train.tsv
9894cb4aa2f901c6f29b61ac3d95ce9f7e78c43be8062ae5deb1c219c82497bb
multimodal_validate.tsv
c70140ec376e083e3780b5b488c96c8933678ca5800139bfb78c92e95df6946e
multimodal_test_public.tsv
bc92378e070ca7b1a7497053d1c34cdc3f550be6232a76791a2c722d6d9bbf94
selected text epoch-4 weights
870bea50fa608dddd20421c21fd1786e244b1323e22734093214b87023666753
```

Warm-start file: `data/cloud_recovery/KAGGLE_RECOVERY_v1_20261009_356721456/weights/best_weights.pt` (438,031,077 bytes). Pinned BERT source is `google-bert/bert-base-uncased`, revision `86b5e0934494bd15c9632b12f734a8a67f723594`. The completed text receipt is under `results/experiments/official_text/OFFICIAL-6W-TEXT-v2_seed42_20261008T095827Z/KAGGLE_RECOVERY_v1_20261009_356721456/completion_verification.json`.

## 10 · Paste this to the execution agent

Use the following as an ordinary prompt with this PDF/Markdown attached. It does not depend on an installed `/call` or other slash command.

> Execute UROP full text+image Part 1 using MM-PART1-v2 at `/Users/panveenaidu/Downloads/SEM7/UROP/context/MULTIMODAL_PART1_EXECUTION_PLAN_20261023.md`. Use GPT-6.1 Sol High. Read the plan and its required evidence before acting. Create or reuse a Goal specifically for this Part 1, with its acceptance checklist; do not create a recurring scheduled task. Work locally only inside UROP and use Chrome with the existing authorized private Kaggle workspace. Preserve completed text results, original data, historical protocols and unrelated edits.
>
> Complete the full-image feasibility/coverage gate, implement and freeze the full-cohort BERT-base + ResNet-50 maximum-fusion protocol, verify warm start and recovery, measure cloud capacity/throughput, then train and fully validate epochs 1–2 only of the registered four-epoch run. The final target is at least 87.00% validation and 86.88% test accuracy, with honest reporting and no test-driven tuning. Do not promise those scores or evaluate the final test in Part 1.
>
> Save durable checkpoints and all required evidence, update the named context/experiment/cloud/model/progress files, push only reviewed appropriate files, and verify the remote GitHub commit. At 20% allowance enter checkpoint-and-handoff reserve; at 10% stop substantive work; at 5% stop assistant work after reporting the saved state. Pause the Goal after a verified usage-reserve handoff if incomplete. Do not mark it complete until every acceptance criterion is verified.
>
> Continue independent work if a gate is blocked, but do not silently change dataset, scope, architecture or budget. If full images or durable cloud capacity cannot be secured, report the concrete blocker and remaining work. Finish with the workflow bars, epoch/validation counts, all obtained validation metrics, recovery location/hash, cloud job/version, Git receipt and exact Part 2 resume action. No image-only/modern-model expansion, paid compute, account migration or Colab CLI in this task.

This handoff is sufficient to begin the authorized part; genuine private login/consent or a scientific scope change may still need the user's input. The plan provides safe checkpoints and bounded work, not a guarantee that quota, storage or the complete image collection will be available.
