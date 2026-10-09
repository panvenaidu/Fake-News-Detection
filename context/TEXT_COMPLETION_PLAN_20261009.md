# Complete official six-class text-only BERT

Plan version: TEXT-COMPLETE-v1, 9 October 2026 (Asia/Kolkata).

Status: **EXECUTION AUTHORIZED on 9 October 2026.** Current progress is recorded in `results/text_completion_execution_20261009.json`. The user requested a concrete plan to hand to GPT-6 Sol. This planning session performs inspection, small CPU diagnostics, documentation and a safe GitHub push. It does not start GPU training or modify the dataset/trainer. A later instruction to execute this plan authorizes its implementation and training steps without repeated routine permission questions.

## 1. Outcome and scope

Finish the existing **BERT-base, seed 42, six-class, full official-cohort text baseline**: finish training, finish validation, select the checkpoint using validation only, evaluate the public test split, verify and archive all results, update project memory and GitHub. Completion is independent of whether the measured accuracy meets the target.

The headline text bar refers to this BERT baseline. ModernBERT is an additional comparison, not already trained and not implicitly included in a BERT 100% claim. Finish and preserve BERT before starting another model. The completed multimodal pilot is retained; do not rerun it. Full multimodal/image-only training, extra seeds, binary/three-way tasks, new model searches and large image downloads are later work.

Working directory: `/Users/panveenaidu/Downloads/SEM7/UROP` only. The ChatGPT project's mirrored `sources/` files are read-only references. Use Chrome for cloud UI; do not use Colab CLI, new OAuth scopes, new account credentials or paid compute. Use the existing private Kaggle account/workspace. No change to raw TSVs, labels, split membership, historical manifests or images.

## 2. Verified starting point

| Item | Evidence-backed state |
|---|---|
| Faculty dataset | Fakeddit official `multimodal_only_samples`, 682,661 rows |
| Original splits | 564,000 train / 59,342 validation / 59,319 public test |
| Inputs and target | `clean_title` only; `6_way_label`, labels 0 through 5 |
| Labels | 0 True; 1 Satire/Parody; 2 Misleading Content; 3 Imposter Content; 4 False Connection; 5 Manipulated Content |
| Original BERT attempt | `OFFICIAL-6W-TEXT-v2_seed42_20261008T095827Z` |
| Observed training/history | Five epochs trained and validated in Colab; interrupted before final test |
| Durable restart point | Epoch 5, batch 15,000 / 17,625; four validation epochs inside the tensor checkpoint |
| Remaining work at maximum budget | 2,625 epoch-5 batches, then epoch 6 unless the existing early-stop rule ends training |
| Selected checkpoint so far | Epoch 4: validation accuracy 0.8274072326514105, Macro-F1 0.7786816742546674 |
| Final test | Pending; no official text test result exists |
| ModernBERT | Prepared; no training |
| Multimodal pilot | Three epochs and final test completed on 2,000/300/300 paired rows; separate scope |
| Cloud state during this review | Kaggle draft off, 0 Active Events; quota displayed 00:06 / 30 hours used (about 29h54m remaining). Recheck at execution. |
| Source control at intake | Local main and remote main at `97b558290ad38844ad3b7fd12b2c5b98e591b1e5` |

The older 75,995-row cohort was the same Fakeddit dataset, sampled within the original splits and reduced by image failures. Its results remain historical. It is not today's full text cohort. The paper lists 682,996 multimodal samples, 335 more than the released files; the reason is unverified.

The three official TSVs were rescanned in this planning session: hashes/counts match the frozen configuration, all titles/labels are valid, IDs are unique and no splits overlap. Saved BERT checkpoint and best-weight byte hashes still match the previous integrity proof. See `results/TEXT_COMPLETION_PLAN_AUDIT_20261009.json`.

## 3. Essential fixes before launch

### A. Correct restart sample order

The original source couples RandomSampler and worker seeding to one generator while using two persistent workers. At a later epoch, an existing iterator resets without consuming a new worker base seed. A fresh iterator after restart consumes a base seed before drawing the permutation. Restoring `sampler_start` and skipping 15,000 batches therefore does not, by itself, recover the original order.

Evidence: a small CPU DataLoader reproduction changed the epoch-2 order and repeated/missed 32 of 128 synthetic IDs around a sample-80 cursor. On the actual saved checkpoint, reconstructing the 564,000-item permutation directly from `sampler_start` matches the saved `loader_rng`; inserting the fresh-worker seed draw does not. This is a resume-path defect; it does not invalidate the recorded uninterrupted Colab epochs. No GPU resume has used this path yet. Details: `results/text_resume_order_diagnostic_20261009.json`.

Implement a separately versioned recovery source, preserving `scripts/train_official_text.py` and its original hash. Separate sampler randomness from worker-start randomness. For this later-epoch checkpoint, reconstruct the order from the saved `sampler_start`, prove its state matches the checkpoint's `loader_rng`, resume at sample 480,000 (batch 15,001), and process the remaining 84,000 samples exactly once. Preserve the random-state progression needed for epoch 6. Store the recovery implementation version and any new sampler/worker state fields in new checkpoints. Do not simply regenerate a permutation from seed 42 or skip batches in a newly shuffled epoch.

Required checks: uninterrupted versus interrupted/resumed order at a later-epoch mid-point, epoch-boundary resume, and a second interruption; same next IDs and next-epoch order; complete coverage with no duplicates or omissions; matching successful optimizer/scheduler counters and AMP skip handling. Run small CPU checks first, then repeat the sampler check in the installed Kaggle Torch version before optimization. Local inspection used Torch 2.8.0; the original cloud run used 2.11.0, whose upstream DataLoader source shows the same worker-seed/reset mechanism. Do not claim identical GPU arithmetic across environments.

### B. Give BERT its own bounded cloud job

The prepared `collab/kaggle_text_recovery_cell.py` currently invokes the original two-model loop, which automatically starts ModernBERT after BERT. Replace this behavior in a separately versioned BERT-only recovery entry point/notebook. Preserve the full original protocol as provenance and record an execution selection of `bert-base`; do not silently edit its model list or hyperparameters. Save BERT evidence and finish the job before a future ModernBERT run.

### C. Complete validation evidence and prevent duplicate work

The recovered model folder lacks the complete validation prediction CSV. The old trainer only exports validation predictions when a new best epoch is selected; if epoch 4 remains best, resuming alone would not restore that CSV. Add a final validation export from the frozen selected weights, with all 59,342 IDs. Preserve the original checkpoint-selection score separately from this restored-checkpoint evaluation, including any tiny environment-related differences. Never reselect the checkpoint from the re-export or test results.

Add an idempotent completion check: if complete results and verified predictions already exist, retrieve them rather than train/test again. If only partial evaluation files exist, inspect them and finish artifact recovery using the same frozen checkpoint, recording any repeated inference. Add a single-run guard, local writable checkpoint paths, and a small evidence bundle even on a handled failure. Retain the original input checkpoint as a durable fallback.

## 4. Fixed scientific settings

Authoritative protocol: `configs/text_official_6way_v2.json`, ID `OFFICIAL-6W-TEXT-v2`.

- Model: `google-bert/bert-base-uncased`, revision `86b5e0934494bd15c9632b12f734a8a67f723594`, six-class head.
- Seed 42; sequence limit 128; dynamic padding; training batch 32; evaluation batch 128.
- AdamW learning rate 2e-5, weight decay 0.01 with original bias/norm exclusions; gradient clip 1; 10% linear warmup/decay; fp16 AMP.
- Maximum six epochs; original minimum three, patience two and Macro-F1 min-delta 0.001 stopping rule.
- Best epoch: highest validation Macro-F1, then lower validation loss, then earlier epoch. Early stopping and best-checkpoint ranking remain the existing separate rules.
- Scheduler advances on successful optimizer steps only. Restore model, optimizer, scheduler, scaler, counters, patience and random state; no weight-only warm start.
- No rebalancing, class weights, new text cleaning, metadata features, resampling or silent exclusions.
- CUDA cloud training only. If Kaggle offers T4 x2, initially expose/use one device as in the Colab run; do not introduce distributed training during recovery.

## 5. Ordered execution checklist after approval

| Stage | Action | Required evidence before moving on |
|---|---|---|
| 1. Read current state | Read this plan, latest resume/status records and raw artifacts; inspect Git and current cloud jobs | No duplicate active BERT job; confirm final test has not already completed elsewhere |
| 2. Repair recovery | Implement A/B/C above in versioned recovery files and do the focused checks | Saved passing diagnostics; original source/config/weights untouched; reviewed diff |
| 3. Preserve and stage | Snapshot original five-epoch Colab history/small metadata; retain the original ZIP; upload checkpoint + proof privately to Kaggle | Correct private dataset and attached official inputs; exact hashes; sufficient disk; original pilot version retained |
| 4. Preflight | Verify all three hashes/counts, checkpoint metadata, sample-order reconstruction, GPU, versions and writable output | GPU identified, epoch5/batch15000/counters restored, correct next sample order; no CPU fallback |
| 5. Submit one saved batch | Save & Run All a clearly named BERT recovery version; record notebook URL, immutable version ID, input versions and source hash | Submission plus actual timestamped optimizer progress; a queued spinner alone is insufficient |
| 6. Finish training | Continue from batch15001, finish epoch5 and epoch6 or legitimate early stop | Fresh advancing steps, finite loss, successful checkpoint saves and epoch validation histories |
| 7. Freeze and evaluate | Fix the validation-selected weight hash; export validation evidence; run final test on all 59,319 official rows | Final metrics/report/confusion matrix/prediction CSV tied to that weight hash |
| 8. Verify and archive | Retrieve small evidence and final weights/checkpoint into UROP; recompute metrics from predictions | IDs/labels/counts exact; recomputed metrics agree; ZIP/hash/readability checks; saved cloud output accessible |
| 9. Synchronize | Update records, faculty comparison and bars; commit/push only approved small files | Remote commit confirmed; complete handoff, no unnecessary GPU session left running |

Training checkpoints: every 3,000 batches and each epoch. A checkpoint in `/kaggle/working` is a runtime recovery file; call it durable cloud output only after saved-version outputs are verified accessible. Keep the original input checkpoint throughout. Prefer a short single-model batch job so the provider can finish and save outputs independently of the chat.

Preserve original history and scores under an immutable historical snapshot before writing the resumed history. Epoch 5 will be recomputed from an older checkpoint, so its new observed values may differ from the historical fifth-epoch values. Record both with their environment and lineage; never replace the historical evidence without retaining it.

If startup fails, inspect the exact error before another submission. Fix a specific cause, run the targeted check, and resume from the latest verified checkpoint. No repeated blind Run All, duplicate jobs, re-downloading already verified input data, or new hyperparameter experiments to hide a failure. If Chrome control is unavailable, save the handoff and request only the browser reconnection needed; do not substitute unapproved CLI authentication.

## 6. Results that make this task complete

Per selected model, archive:

1. `result.json`, `status.json`, full epoch `history.json`, selected checkpoint metadata and frozen weight hash.
2. Validation and test metrics: accuracy, Macro-F1, weighted-F1, balanced accuracy and loss. For single-label six-class evaluation, micro-F1 equals accuracy; calculate/label it clearly if displayed.
3. Validation and test classification reports (precision, recall, F1, support for all six classes), raw and row-normalized 6x6 confusion matrices.
4. Full prediction CSVs: 59,342 validation rows and 59,319 test rows, exactly one row per official split ID with true label, predicted label and confidence. No missing, duplicate, out-of-split or unexpected IDs.
5. Dataset/source/config/pretrained/checkpoint hashes, original and resume environments, package versions, GPU/precision, seed, timing, peak memory, successful updates and skipped updates. Distinguish resume-session wall time from cumulative training time.
6. Best weights, tokenizer/config and usable recovery checkpoint in private cloud output and local ignored storage, plus a retrieval manifest and small portable evidence ZIP.
7. A short faculty table separating our observed scores from paper scores, stating single seed and differing architecture/release count.

Recalculate accuracy and all F1 aggregates from the exported CSVs, reconstruct confusion matrices, verify per-class support and confidence bounds, and compare against JSON at a documented floating-point tolerance. Check loss/history are finite and output files contain actual numbers rather than placeholders. Count only the required verified artifacts, not duplicate snapshots, as completion evidence. No further accuracy tuning or extra training after the test result is seen.

## 7. Paper comparison and expectations

| Six-way reference | Paper validation accuracy | Paper test accuracy | Our current position |
|---|---:|---:|---|
| BERT text | 76.96% | 76.77% | Selected validation 82.7407%; test pending |
| BERT + ResNet-50 maximum fusion | 86.00% | 85.88% | Only a small pilot completed; no direct full-benchmark claim |

The text target of one percentage point above the paper is **test accuracy >=77.77%**. It is a target, not a promised result or a completion condition. The paper's 86.54%/86.44% BERT pair is binary. Table 4 has no matching Macro-F1 score. Our BERT-base fine-tuning differs from the paper's BERT-Large feature pipeline; the current release count differs by 335. State these limitations in the final comparison.

Planning estimate: remaining maximum training is 648,000 sample presentations (84,000 plus 564,000), around 47-54 minutes at the previously observed roughly 200-230 titles/second. Allow roughly 1-2 hours for BERT after inputs and a working GPU are ready, including setup/evaluation/export. Recovery repair, uploading the roughly 1.6 GiB archive, queueing and faults add time. Re-estimate from actual resumed throughput; no promise of completion by a fixed clock time.

## 8. Usage reserve and checkpoints

The user's rule: preserve the last 20% of available assistant usage for safe continuity. Assistant usage and Kaggle GPU quota are separate resources. At the start of this planning review, the tool reported 92% remaining in the five-hour window and 68% in the weekly window; these are timestamped observations, not a current guarantee.

- Check usage before launch, at each major checkpoint and during long work. Read all returned applicable windows; use the most restrictive remaining percentage. If a value is unavailable, record unknown and save proactively.
- Begin syncing early (around 25% remaining), so the reserve is not consumed before checkpoint work starts.
- At 20% or below: start no new model, experiment, large transfer or refactor. Finish the current safe local step. Preserve verified results and the latest readable cloud status/checkpoint; update every record below; commit/push and confirm the remote commit. Use the reserve for this handoff.
- Leave a healthy already-submitted cloud batch running so it can complete without more chat calls. Do not cancel GPU training merely because assistant usage is low. Record the exact job URL/version, whether it is queued/running/failed/completed, last verified timestamp/epoch/batch, and durable checkpoint/output location. If progress cannot be verified, say so.
- Do not claim local/GitHub syncing will occur automatically after the agent stops. Cloud saving continues only through the submitted job's own logic/provider behavior. Provider interruption cannot be ruled out; the verified input checkpoint and later saved outputs make recovery possible.
- No new scheduled task is part of this plan. The user can return or switch to GPT-6 Sol using the saved plan and resume file.

Save milestones after: recovery checks pass; upload/preflight succeeds; actual training begins; each epoch validation completes; final test completes; artifacts verify; usage reaches the reserve. Do useful local work between cloud checks. Avoid rapid unchanged polling and endless monitoring cells; waits should be bounded so new user input can be handled.

At every milestone update `context/RESUME_HERE.md` first, followed by `context/PROJECT_CONTEXT.md`, `context/DECISIONS.md` for actual decisions, `context/EXPERIMENT_LOG.md`, `context/TASK_REPORT.md`, `work_logs/MODEL_STATUS.md`, `collab/COLAB_WORKLOG.md`, `results/official_text_live_status.json`, `results/PROGRESS_TRACKER.json` and `.md`. Update README and the faculty summary when their headline state changes. Troubleshooting receives any new verified failure/fix. Record exactly what is complete, still pending, and the next safe action.

## 9. Storage and GitHub safeguards

- Original data: `data/official_multimodal_v2/`; original recovery files: `data/cloud_recovery/`.
- Original text evidence: `results/experiments/official_text/OFFICIAL-6W-TEXT-v2_seed42_20261008T095827Z/`.
- Store new resume evidence with an explicit timestamped session/subfolder and lineage to that original attempt. Preserve original Colab artifacts and report revised source hashes.
- GitHub receives small code/notebooks/configs, JSON/CSV metrics and predictions, reports, manifests and context. Raw TSVs, images, checkpoint weights, ZIPs, environments, tokens and unreviewed personal screenshots remain excluded.
- Stage an explicit reviewed file list, inspect sizes and staged diff, commit, push normal fast-forward and verify the remote hash. Do not use force push or overwrite unrelated user changes. If remote changes appear, inspect and reconcile safely.
- Existing untracked literature PDF and browser diagnostics are user/reference files; leave them untouched and unstaged.
- A small plan/audit checkpoint is pushed during this planning turn. GPU execution still awaits the user approving this plan.

## 10. Progress reporting

Current verified bars: text-only BERT **73%**, full text+image **40%**, standalone image-only **20%**, overall **44%**. Small multimodal pilot **100%** separately. ModernBERT **40% prepared, 0% trained** separately.

Show each model's data/code readiness, observed training epochs, durable saved training position, validation checks, test rows/evaluation status, saved required artifacts and cloud job state. The text bar's 81% training component is saved progress, while the 83% validation component is five checks out of a six-epoch budget. Neither is accuracy. The resume-path bug adds a prerequisite; it does not erase the saved weights or advance these percentages.

After BERT training legitimately finishes, set its training and validation stages to complete. Set BERT overall to 100% only after test and required archived evidence verify. With the other full modalities unchanged, the overall three-modality bar then becomes about **53%**, not 100%. Do not count the small pilot as full-cohort training. Do not raise bars from elapsed time or the presence of a spinner.

## 11. Exact handoff inputs and source links

| Input | Path / identity |
|---|---|
| Recovered archive | `data/cloud_recovery/bert-base-20261008T133126Z-1-001.zip` |
| Recovery proof to upload | `data/cloud_recovery/recovery_verification.json` |
| Locally verified model folder | `data/cloud_recovery/OFFICIAL-6W-TEXT-v2_seed42_20261008T095827Z/bert-base/` |
| Original combined input archive | `data/cloud_recovery/official_training_inputs.zip` |
| Original trainer | `scripts/train_official_text.py`, SHA256 `a13c0e5d97b2fe7661ce6a228d43d853f1aca703314cfa48688825b7b01701f9` |
| Frozen text configuration | `configs/text_official_6way_v2.json`, SHA256 `b203b3ea15c247c8174bbd67733501e304a31c7b681c720a4ed61bbe05f57689` |
| Prepared helper/notebook | `collab/kaggle_text_recovery_cell.py` and `notebooks/UROP_KAGGLE_TEXT_RECOVERY_20261009.ipynb`; prepared versions require the fixes above before launch |
| Checkpoint hash | `1a89825e3cdc921b800732ac9338008b0c6d82faeddc95427014364ba3bc806b` |
| Best weight hash | `870bea50fa608dddd20421c21fd1786e244b1323e22734093214b87023666753` |
| Archive hash | `369610b47f755e0bda9b09b51d546970da284e51fe245d2c2349e1d95094ff87` |
| Original permutation hash | `a776b65a95c4fd26a8ceb1f2f55b48f30b8adb92bb1b388ed39a0cacb6eec6f6` (564,000 int64 indices, native little-endian bytes) |

- [Faculty dataset](https://drive.google.com/drive/folders/1DuH0YaEox08ZwzZDpRMOaFpMCeRyxiEF)
- [Original paper, Table 4 and experiment methods](https://arxiv.org/html/1911.03854v2)
- [Project GitHub](https://github.com/panvenaidu/Fake-News-Detection)
- [Private official Kaggle input dataset](https://www.kaggle.com/datasets/rocky62/urop-official-six-way-inputs-and-paired-pilot)
- [Existing Kaggle editor](https://www.kaggle.com/code/rocky62/urop-official-six-way-text-recovery/edit); its current draft still contains the multimodal pilot, so never blindly Run All to recover text.
- [Completed pilot version 2](https://www.kaggle.com/code/rocky62/urop-official-six-way-text-recovery/output?scriptVersionId=356486031)
- [Original BERT Drive folder](https://drive.google.com/drive/u/0/folders/15K7CqdsqrZVEdJH1rGNFhlnswNCdMD1j)
- [PyTorch 2.11 DataLoader source](https://github.com/pytorch/pytorch/blob/v2.11.0/torch/utils/data/dataloader.py): iterator initialization/worker base seed versus persistent-worker reset.

Review coverage: current project memory, historical decisions and experiment logs, training/recovery code, source configs, official TSV contents, recovered checkpoint state/hashes, result metadata, relevant literature-survey sections, main Fakeddit paper, live faculty Drive listing and GitHub remote. Bounded histories of the accessible chats `Branch · UROP` and `Implement and run E002 baseline` were consulted. A separate chat titled `UROP` was not found in the available listing. This does not claim that every image or every cited journal full text was opened. Saved raw artifacts take precedence over old chat summaries and historical markdown.
