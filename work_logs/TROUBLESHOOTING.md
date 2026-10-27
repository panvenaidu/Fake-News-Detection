<!-- PART2_READBACK_LAYOUT_20261027 -->
## Part2 readback layout and browser preparation — 27 October 2026

- Raw saved cloud output need not contain `selected_checkpoint.json`; that small aggregate selection record was synthesized after independent verification. Resolve the selected tensor name/hash from the accepted Part1 receipt or the recovery payload's `state.best`, and resolve the private root from the large-artifact manifest. A local metadata inspection initially assumed the aggregate file existed in raw output, raised FileNotFoundError, then used those authoritative receipts. The verified model has133,977,414trainable parameters; no forward pass or local training occurred.
- Kaggle file import did not accept the native file selection. The new private copied notebook's code cell was replaced using its normal editor paste; frozen source hashes, exact Python/dependency contract and accepted recovery were subsequently checked inside the committed GPU runtime before any continuation. No browser security bypass, new API token, account migration or Colab OAuth was used.
- Startup heartbeats contained fresh parent UTC but copied epoch2 nested status. Do not call it epoch2 replay or advancing epoch3. Genuine new epoch3 samples first appeared with fresh trainerUTC14:37:31; sustained sample/update counters established training, separately from the process heartbeat.
<!-- /PART2_READBACK_LAYOUT_20261027 -->

<!-- CURRENT RESUMED GOAL BLOCKED -->
2026-10-25T04:09:26.752532+00:00: Supported Goal status **BLOCKED**, after3consecutive observations in this resumed sequence. Short94% / weekly19%; registered20%weeklyreserve applies and explicit override question remains unanswered. No newjob/scientificprogress; packing319820/18,scientific0/2epochs/0/2validations,test0. Recovery and original data preserved. Resume the SAME Goal only after allowance recovers above20% or the user explicitly changes the reserve rule; do not repeat polling/commit cycles or create another Goal. Audit `results/MM_PART1_USAGE_RESERVE_AUDIT_20261025.json`; exact recovery `results/MM_PART1_RECOVERY_PROGRESS_20261025.json`. Older active/blocked counts below are historical.
<!-- /CURRENT RESUMED GOAL BLOCKED -->

<!-- FRESH RESUMED RESERVE AUDIT -->
2026-10-25T04:07:11.569856+00:00: Goal API is ACTIVE after resume; fresh blocked audit count1 (prior3count is historical). Five-hour allowance100%, weekly19%; the registered smaller-balance20%reserve still applies. User clarification requested: keep weeklyreserve, or explicitly authorize using it this run down to10%handoff/5%hardstop. No answer/override applied yet, no newlongjob, no scientific progress. Recovery `results/MM_PART1_RECOVERY_PROGRESS_20261025.json`; audit `results/MM_PART1_USAGE_RESERVE_AUDIT_20261025.json`. Do not reuse the old blocked count or create another Goal. Part1 remains0/2epochs,0/2validations,test0; durablepacking319820/18unchanged.
<!-- /FRESH RESUMED RESERVE AUDIT -->

<!-- GOAL BLOCKED USAGE RESERVE -->
2026-10-24T20:36:43.467016+00:00: Existing Goal tool returned **BLOCKED**, after the same20%weeklyreserve condition across3consecutiveGoalturns. Short allowance64% does not override weekly20%; user requires the smaller applicable balance. No newtransfer/major implementation/training is permitted at this reserve, and the recovery handoff is already verified. Previous Goalturn and this turn are no-progress revalidations, not waits on a live computation. Eight artifact hashes and remote Git `68f78346c7a571d7e2aa51cc57f5461bd94f16ad` matched. Original data,18packs/319820images, API metadata index and text-only results preserved. Scientific0/2epochs,0/2validations,test0; Part1 incomplete, Part2 not started. Resume the SAME existing Goal after applicable allowance recovers above20% (or explicit user changes the reserve constraint); do not create a duplicate Goal. Follow `results/MM_PART1_RECOVERY_PROGRESS_20261025.json`; exact blocked audit `results/MM_PART1_USAGE_RESERVE_AUDIT_20261025.json`. No inactive-agent monitoring promised. Older active/paused status below is historical. The phrase 'no test' means no final model-test inference in Part1; required engineering/recovery checks remain authorized.
<!-- /GOAL BLOCKED USAGE RESERVE -->

<!-- API RECOVERY RESERVE -->
2026-10-24T20:33:14.771734+00:00: Weekly allowance20% (short69%) => user checkpoint reserve. All new API probe/inventory cells are terminal; no packing/training job is running. API receipt identity,150source metadata receipts/682170IDs, privateindexwrite/readback and4KiB originalTAR range checks passed. Packing remains319820/18; scientific0/2epochs,0/2validations,test0. Recovery `results/MM_PART1_RECOVERY_PROGRESS_20261025.json`; verified checkpoint Git `4b069d769593f63f7f48965ffb844aebb4f71dba`. Do not start long transfer/debugging/training while applicable allowance<=20%. Existing Goal remains incomplete; no unsupported pause/completion claim. No monitoring after this stop is promised. At10% follow the user's pause/handoff instruction; hardstop5%.
<!-- /API RECOVERY RESERVE -->

<!-- API RECOVERY 20261025 -->
## Current Part 1 recovery — 2026-10-24T20:28:30.121784+00:00

Existing Goal verified **active**. Still Part 1: **0/2 scientific epochs, 0/2 full validations, no final test**. Durable packing remains **319,820 images / 18 archives** of the approved 682,170 original faculty pairs. Text-only results and the 491 approved exclusions remain unchanged.

New verified evidence: original and copied receipt are byte-identical (SHA `92008e69c84c7485965def2c5a7c2d29663d9c18feb587d1bcf9fef5d69108c4`); no replacement applied. Full DriveFS inventory failed at receipt 5. Kernel logs prove cloud Drive process PID36308 was OOM-killed at20:16:52UTC with11281852KiB anonymous RSS. The exact trigger for this memory growth is not proven; root-cgroup zero counters do not negate the child-cgroup kernel OOM evidence. This is cloud RAM, not laptop RAM. Do not loop resets/remounts or repeat source extraction.

User explicitly approved new notebook Drive+Cloud API access. Standard Colab authorization finished, and the bounded 1.7MB Drive API specimen passed exact size/SHA and membership verification without DriveFS. Seven offline rejection checks passed. The metadata-only API inventory PASSED all150source receipts /682170IDs with exact approved split/class counts in86seconds. A115527byte private index was created and byte-readback verified (SHA `291a2c5b27aa39f1b1b16b3726655609927a08cee03a34e35d9fe7e47670a87a`). Colab displayed1.06GB RAM at terminal observation. This is NOT image-byte verification, original-TSV title joining, packing or training. The bounded4KiB originalTAR range check PASSED HTTP206/exactContentRange/TARmagic in cell `xNddVqfSmtsV`. It does not verify the full archive hash. All new cells are terminal; no packing/training is running. Source checkpoint `7530a33` was pushed and remote-verified before launch. Kaggle draft remains session off / accelerator None / no input attached / release unset at this run's observation.

Authoritative run receipt: `results/MM_PART1_RECOVERY_PROGRESS_20261025.json`; new evidence files are listed there. No other new cloud job was launched. Next: implement and fault-test bounded original-byte API transport using the durable private index (privateID in ignored `data/official_paired_v2/API_METADATA_INDEX_RECEIPT_20261025.json`); preserve all source shards and18closedpacks. The prepared DriveFS recovery script was NOT executed and must not bypass its failed inventory gate. Full immutable input/runtime hash+decode, actual CUDA/preflight and epochs1–2 validations remain required. Bars unchanged: text100/MM40/image20/overall53. At20% enter checkpoint reserve; handoff10%, hardstop5%. Older active/paused and fault-cause notes below are historical.
<!-- /API RECOVERY 20261025 -->

## Approved reset reproduced same Drive read failure

<!-- APPROVED RESET RESERVE HANDOFF -->
## Current recovery handoff — 2026-10-24T15:55:24.809235+00:00

**User approved Option1 CPU reset after backup verification. RESET COMPLETED; no unsaved project data was deleted.** Pre-reset runtime inventory found only one empty project lockfile outside standardfolders; originalDrive not reset. Fresh CPU notebook JSON backed up locally(546373bytes,SHAe3f7a69e72849158a8268f9ef6e893acf654395ce6b555c5964da707b28bee54), all33cells/terminal/inventory evidence retained. Original3TSVs and438031077byte selectedtextweightsSHA verified; all31existing engineering/recoveryartifact hashes passed; Git9c526ed verified before reset. DriveUI confirmed18TARs+18receipts; originalarchive/shards and fullTSVs preserved. Exactreceipt `results/MM_PART1_APPROVED_RESET_BACKUP_20261024.json`.

**The reset did NOT resolve the Drive issue.** FreshCPU PID6223, bootIDae273ba2-88f2-4c3a-bf05-e8481a0895be, mountedsameapprovedDrive. Boundedread-onlyinventory ended15:49:16UTC after31seconds at exactsame source receipt4 (`images_0784678d477441dd9378373cf7830aad.receipt.json`),OSError107. No newcopyjob/trainer/GPU allocation. Last genuinely durable point remains319820images/18transportTARs, successfulpriorflush11:35:10UTC. Originalmetadata/labels/splits/exact491approvedexclusions unchanged. Do not loop CPU resets or source extraction.

Small derived diagnosis: via normalDriveUI made ONE copy of the failing1.7MB receipt, then moved ONLY that newcopy outoforiginalshards intoofficial_images_v1root as `Copy of images_0784678d477441dd9378373cf7830aad.receipt.json`. Creation andmove success observed; originalfile remains untouched. Copy has NOT been read/hash-verified, is NOT an authorized/appliedreplacement, and does not pass any imagegate. Sourcefolder temporarycopy was removed bymove; no originalfile was moved/deleted. Screenshots saved locally. Fullbytes/semantic/sourcehash reconciliation required before any alternative metadata path.

Failure-reporting runner`collab/run_usable_transport_job_v4.py` (SHA6f416ccd7878ed59377787ba8ec5fb232b237c6e787a7b11c100d5b6b0027152) preserves original error ifDrivefailurewritesfail;5faultinjectioncasespassed,scratchnevercalleddurable. This is engineeringonly; not cloudlaunched. Sameone-hourpackingcap/sharedpacker/model/cohort. New diagnosticsource`collab/post_reset_image_inventory_20261024.py`. Git sourcecheckpoint e1f02fa saved/pushed; verify currentbackupreceipt for latesthead.

Usage19%short/28%weekly => checkpointreserve: no newlongjob/largetransfer/major debugging. ExistingGoalAPI STILLreportsPAUSED evenafteruseranswer“Existing Goal resumed”; do not fabricateactive status/createanotherGoal. Manualauthorizedwork above was performed; supportedGoalresume must bechecked afterallowance recovers. No independentcloudjob or inactive-agentmonitoring claimed.

NEXT afterallowancerecovery: inspectexistingGoalactualstatus; boundedread of newlycopiedreceipt throughsameapprovedDrive only; do not rerunthefailedloop. Comparefullcopybytes/hashes or explicit source/packedrowevidence before any metadata alternative. Ifcopyalsounreadable, inspectsupportedprivatecloudtransfer/service route; no repeatedreset,scopeexpansion,accountmigration or publicexposure. Then completeoriginal-bytepacking/metadata/privateimmutablefullKaggleinput, runtime682170imagehash+decode, actualCUDArecovery/measuredpreflight, registeredepochs1–2/fullvalidations. NoPart1finaltest. V2scientificsourcepin5aa5c87 unchanged;Kaggledraftprivateguardedv2saved/readbackverified,Version1imageinputstill640images. Freshquotaearlier00:00/30GPUhours; recheckbeforelaunch.

Scientificepochs0/2,fullvalidations0/2,test0. Barsunchanged:text100/MM40/image20/overall53. Authoritativecurrentreceipt`results/MM_PART1_POST_RESET_HANDOFF_20261024.json` and`results/MM_PART1_USABLE_RECEIPT_20261024.json`; raw notebook/output/weights/dataremainprivate/ignored. UserHTML/literature/unrelatedfilespreserved.
<!-- /APPROVED RESET RESERVE HANDOFF -->

## 2026-10-24: CPU Drive connection abort during source receipt reads


## Current CPU recovery boundary — 2026-10-24T15:32:18.793134+00:00

**No cloud training or CPU copy job is currently running.** Usable-cohort continuation8091318e and its recovered job4239db2e both terminated with Drive endpoint errors before any new images. Same150source receipts diagnostic failed on receipt4 (`images_0784678d477441dd9378373cf7830aad.receipt.json`,1778013bytes) with connection-aborted103. Its normal Drive web preview is accessible; this does NOT prove the full receipt byte hash or a data corruption cause. A single browser download attempt has no completed file observation; do not claim success/retry blindly. AmpleRAM/no recordedOOM; Drive daemon restarts/cancelled writes seen, exact underlying cause unproven. Failure receipt writes and flush also failed; exact notebook outputs saved privately and hashed in `results/MM_PART1_CPU_DRIVE_FAILURE_20261024.json`.

**Last verified durable image preparation remains319,820images/18archives**, job3bcc65e9 with successful11:35:10UTC flush. Failed guard is4239db2e; notebookkernel1568 was not a trainer. Source archive/shards/originalTSVs/approved682170cohort unchanged. No extra exclusion, alternate image, weaker decoder, extraction repeat or GPU allocation.

Supported Colab "Disconnect and delete runtime" dialog is open in the CPU notebook; **confirmation is pending**, not accepted. Browser policy requires action-time permission for permanent scratch reset. All needed original data,18closedpacks, ownedsource and diagnostic evidence are in Drive/local/Git. If approved: reset this idle CPU runtime, reconnect one CPU instance with existing approved Drive scope, bounded-read all150source receipts/18pack receipts, then explicitly retire4239guard only after actual terminal/lock checks and resume same pinned one-hour runner. Do NOT rerun either one-shot recovery cell or old extraction cells. If reads still fail, preserve exact evidence and inspect transport/service route rather than cycling launches.

Independent progress: existing PRIVATE Kaggle draft updated to approved usable v2 template; full code-cell source readback equals local template afterCRLFnormalization, no execution counts/outputs. Draft saved, sessionoff, acceleratorNone, RELEASE_PATH=None. Receipt `results/MM_PART1_USABLE_KAGGLE_DRAFT_20261024.json`. Kagglequota fresh UI00:00/30GPUhours used and2.31GB/214.75GBprivate storage; workspace remains previouslyauthorizedRocky62. Privateimageinput Version1 is still640images, full immutable staging/runtimebytegate pending. New notebook is guarded preparation, not a result.

Scientific epochs0/2, fullvalidations0/2, test0. Bars unchanged text100/MM40/image20/overall53. Existing GoalACTIVE. Next dependent action needs reset confirmation; independent evidence/docs/source backup can continue. At20%reserve no new long jobs; handoff10%,hardstop5%.


##24October2026: official image staging scratch limit

The prior CPU job stopped at505573 committed images because the8GiB scratch guard triggered. Source/shards are in Drive, but mounted Drive reads/writes use runtime cache; Drive quota does not increase VM disk. The error itself is verified; exact cache-byte attribution was not separately profiled. A replacement streamed reader uses the same original public author file, verifies HTTP ranges, total length, original head/tail bytes and final CRC/SHA, and avoids storing the full compressed source on VM. Committed shards are hash-revalidated and reused; orphans preserved. The active job is recorded in results/MM_PART1_STREAM_JOB_20261024.json. No scientific cohort/model/protocol change, no paid resources or extra permissions. Do not bypass disk safety or blindly restart old code.

Primary references: https://research.google.com/colaboratory/faq.html ; https://github.com/googlecolab/colabtools/blob/main/google/colab/drive.py .

## Verified recovery outcome — 9 October 2026

Versioned recovery passed locally and in KaggleTorch2.11. Original epoch5 validation was reproduced; epoch6 completed and epoch4 selected. Both downloaded archives passed checksums/CRC; full prediction verification and strict model/optimizer/scheduler/AMP/tokenizer loads passed. Completion guard returned without training/inference. Native Chrome AX toggling did not refresh the download toast; the visible toolbar coordinate opened the current download panel and confirmed completion. No duplicate download/training was launched from observation timeouts.

## Recovery correction — 9 October 2026

The original restart coupled worker seeding with the sample-order generator. Versioned recovery separates the worker generator, replays the installed RandomSampler through exhaustion (including its unused final permutation), verifies the saved epoch5 order and resumes at sample480000. Focused checks pass on local Torch2.8.0; repeat in installed Kaggle Torch before optimization. The original source is preserved. Artifact verifier rejects duplicate IDs, wrong labels, confidence outside0–1 and incorrect metrics. Evidence: `results/text_recovery_v1_checks_20261009.json` and `results/text_evidence_verifier_checks_20261009.json`.

## TSH-010 - 2026-10-09 - Mid-epoch restart sample-order mismatch

Status: diagnosed; fix planned, not implemented. Original `train_official_text.py` uses one generator for shuffle and worker base seeds, with persistent workers. A fresh iterator after restart consumes an extra worker seed compared with later-epoch persistent-worker resets. Restoring sampler_start and skipping batches therefore changes the sample order.

Verified locally with a 128-item two-worker DataLoader: epoch2 order changed, 32 already-seen items repeated and 32 unseen items missed after an 80-item cursor. Actual checkpoint: direct randperm(564000) from sampler_start matches saved loader_rng; adding the fresh worker seed does not. Torch2.8 CPU inspection; upstream Torch2.11 DataLoader has the same mechanism. No GPU resume was launched; historical uninterrupted training is preserved.

Required next action: versioned sampler/worker RNG separation with exact current-suffix and next-epoch order checks, including actual installed Kaggle runtime, before optimization. Preserve old weights/source/config and original observed history. Details: `context/TEXT_COMPLETION_PLAN_20261009.md`, `results/text_resume_order_diagnostic_20261009.json`.

# TROUBLESHOOTING — Multimodal Fake News Detection

> **Purpose:** Reusable knowledge base of verified problems and fixes encountered during the project.
> **Last Updated:** 2026-09-23
> **Updated By:** Antigravity

---

## TSH-001 — E002 Scheduler Warning: `lr_scheduler.step()` before `optimizer.step()`

### Problem
The E002 BERT training run produced a scheduler-order warning during canonical CUDA training on Colab T4.

### Symptom / Error
```
UserWarning: Detected call of lr_scheduler.step() before optimizer.step()
```

### Cause
When using PyTorch AMP (`GradScaler`), the `scaler.step(optimizer)` method may skip the optimizer step if it detects NaN/inf gradients. If the optimizer step is skipped but `scheduler.step()` is called unconditionally, the PyTorch scheduler detects that `optimizer._step_count` hasn't incremented and raises this warning.

### Fix
Moved scheduler stepping after the optimizer update at the correct optimizer-step boundary and wrapped it in a scale check (the standard PyTorch AMP pattern) in `src/fakenews_baselines/e002_text.py`:

```python
scale_before = scaler.get_scale()
scaler.step(optimizer)
scaler.update()
optimizer.zero_grad(set_to_none=True)
if scaler.get_scale() == scale_before:
    scheduler.step()
```

### Verification
Checked `src/fakenews_baselines/e002_text.py` statically. Verified no unintended protocol changes. Verified syntax passed.

### Future prevention
Keep `optimizer.step()` (or `scaler.step(optimizer)` with a scale check) before `scheduler.step()` in the training loop.

### Result
The preliminary seed-42 run produced metrics, but the learning rate schedule may not have been applied correctly. **The scheduler-order bug has been corrected in the code. No full retraining was performed during the fix task. The preliminary seed-42 result remains preliminary. A clean canonical seed-42 rerun is required.**

### Notes
- The preliminary metrics are preserved for reference but are not final.
- Seeds 43 and 44 must NOT be run until this is corrected.
- The fix is a code change in the training loop, not a protocol change.

---

## TSH-002 — Non-RGB Images in Manifest

### Problem
2,446 of 75,995 images in the verified paired manifest are not in RGB mode.

### Symptom / Error
Image preflight reported mode distribution:
- RGB: 73,549
- RGBA: 196
- P (palette): 2,123
- L (grayscale): 122
- CMYK: 5

### Cause
Reddit images come in various formats. Some are palette-indexed PNGs, grayscale images, RGBA with alpha channels, or CMYK color space images.

### Fix
Convert all images to RGB mode during the image loading pipeline using `image.convert("RGB")`. This handles all observed modes:
- RGBA → RGB (alpha channel dropped)
- P → RGB (palette expanded)
- L → RGB (grayscale expanded to 3 channels)
- CMYK → RGB (color space converted)

### Result
All 75,995 images successfully converted to RGB. **Zero conversion failures.** Non-RGB images must NOT be removed from the manifest.

### Safe to repeat?
Yes — `image.convert("RGB")` is safe and idempotent. Already-RGB images pass through unchanged.

### Notes
- The image loading code should always apply `.convert("RGB")` regardless of the source mode.
- Do not create a separate "RGB-only" manifest — that would break the locked cohort.

---

## TSH-003 — PIL DecompressionBombWarning

### Problem
One very large image triggered a PIL security warning during image preflight.

### Symptom / Error
```
PIL.Image.DecompressionBombWarning: Image size (XXX pixels) exceeds limit of 89,478,485 pixels
```

### Cause
PIL has a default pixel limit to prevent memory exhaustion from decompression bombs (malicious or very large images). One image in the dataset exceeds this threshold.

### Fix
No fix required for now. The warning did not prevent the image from being read or converted. If this becomes a memory issue during training, either:
1. Increase PIL's limit: `PIL.Image.MAX_IMAGE_PIXELS = None` (use cautiously)
2. Or resize the image during loading (the ResNet pipeline already resizes to 224×224)

### Result
The image remained readable and convertible to RGB. No data loss.

### Safe to repeat?
Yes — it is a warning, not an error.

### Notes
- Do not delete the image from the manifest unless a future validated policy explicitly requires it.
- The ResNet/CLIP image pipeline will resize all images anyway, so the raw pixel count is irrelevant after preprocessing.

---

## TSH-004 — DataLoader Worker Count Warning

### Problem
Colab recommended fewer DataLoader workers than configured.

### Symptom / Error
```
UserWarning: This DataLoader will create X worker processes in total. Our suggested max number of worker in current system is Y.
```

### Cause
Colab environments have limited CPU cores. The configured `num_workers=4` in `e002_text_bp6w_v1.json` may exceed the available cores.

### Fix
Reduce `num_workers` in the config or pass it as a runtime override. Alternatively, ignore the warning — it is a performance hint, not a correctness issue.

### Result
Training ran successfully despite the warning. No data corruption or model failure.

### Safe to repeat?
Yes — this is a performance/environment warning, not a model failure.

### Notes
- Adjusting `num_workers` to match Colab's available cores may improve throughput.
- This is a hardware adaptation, not a protocol change.

---

## TSH-005 — Hugging Face Unauthenticated Request Warning

### Problem
Hugging Face Hub warned about unauthenticated model/tokenizer downloads.

### Symptom / Error
```
UserWarning: ...unauthenticated request...rate limit...
```

### Cause
The `bert-base-uncased` model and tokenizer were downloaded without a Hugging Face authentication token.

### Fix
No fix required unless rate limits become an actual issue. If needed:
1. Generate a HF token at https://huggingface.co/settings/tokens
2. Set `HF_TOKEN` environment variable or use `huggingface-cli login`

### Result
The model and tokenizer downloaded successfully. No training impact.

### Safe to repeat?
Yes — public models like `bert-base-uncased` are accessible without authentication.

### Notes
- Do not require `HF_TOKEN` as a hard dependency unless rate limiting actually blocks downloads.
- The frozen BERT revision `86b5e0934494bd15c9632b12f734a8a67f723594` is a specific commit, so it will always download the same model.

---

## TSH-006 — Incorrect Colab Shell/Heredoc Commands

### Problem
Nested shell commands and heredoc syntax caused errors in Colab notebook cells.

### Symptom / Error
```
NameError: name 'PY' is not defined
```
or
```
SyntaxError: invalid syntax
```

### Cause
1. Shell heredoc syntax (`<<'PY' ... PY`) is not supported in Colab notebook cells that expect Python.
2. Nested `python -c '...'` commands with complex quoting cause syntax errors when the outer shell interprets the inner quotes incorrectly.

### Fix
Use normal Python code in Colab notebook cells instead of shell commands for preflight checks. For example:
```python
# In a Colab cell (Python):
import torch
print(torch.cuda.is_available())
```
instead of:
```bash
# In a Colab cell (shell — error-prone):
!python -c 'import torch; print(torch.cuda.is_available())'
```

### Result
Preflight checks ran successfully when rewritten as normal Python cells.

### Safe to repeat?
Yes — always use Python cells for Python code in Colab.

### Notes
- These were notebook-command formatting errors, not project/data/model failures.
- Shell (`!command`) cells in Colab are fine for simple commands like `ls`, `pip install`, etc.

---

## TSH-007 — GitHub Repository Missing from Fresh Colab Runtime

### Problem
A fresh Colab runtime did not contain the project directory `/content/Fake-News-Detection`.

### Symptom / Error
```
FileNotFoundError: /content/Fake-News-Detection does not exist
```

### Cause
Colab's `/content/` directory is **temporary**. When a runtime disconnects or resets, all local files are lost. The GitHub repository must be cloned again in each new session.

### Fix
Clone the repository at the start of every Colab session:
```bash
!git clone <repo-url> /content/Fake-News-Detection
```
Then copy the manifest and extract images from Google Drive.

### Result
Repository recovered successfully. All code, configs, and context files were intact from GitHub.

### Safe to repeat?
Yes — this is the standard Colab workflow.

### Notes
- **Always commit and push results before ending a Colab session.**
- Google Drive persists across sessions; `/content/` does not.
- The dataset (manifest + images) must be re-prepared each session from Drive.

---

## TSH-008 — BERT Pre-training Head Unexpected Keys Warning

### Problem
Loading `bert-base-uncased` for downstream classification produced a warning about unexpected keys.

### Symptom / Error
```
Some weights of the model checkpoint at bert-base-uncased were not used when initializing BertModel: ['cls.predictions.bias', 'cls.predictions.transform.dense.weight', ...]
```

### Cause
The pre-trained BERT checkpoint includes the masked language model (MLM) head weights. When loading BERT for classification (without the MLM head), these weights are unused and PyTorch reports them.

### Fix
No fix required. This is expected and correct behavior. The MLM head is intentionally not used for downstream classification.

### Result
BERT loaded correctly. The classification head is initialized from scratch (as intended by the fine-tuning protocol).

### Safe to repeat?
Yes — this warning always appears when loading pre-trained BERT for downstream tasks.

### Notes
- Do not suppress this warning unless it clutters output unacceptably.
- This is NOT a model failure or data corruption issue.

---

## TSH-009 — Palette Image Transparency Warning

### Problem
Some palette-mode (P) images triggered a transparency-related warning during conversion.

### Symptom / Error
```
UserWarning: Palette images with Transparency expressed in bytes should be converted to RGBA images
```

### Cause
Some PNG images use palette mode with transparency information stored as byte values. PIL warns that converting directly to RGB may lose transparency information.

### Fix
The `.convert("RGB")` call handles this correctly — transparency is dropped (replaced with a background color, typically white or black). Since we do not need transparency for CNN/transformer image classification, this is acceptable.

### Result
All palette images converted to RGB successfully. No data loss relevant to the classification task.

### Safe to repeat?
Yes — the warning is informational.

### Notes
- If exact transparency preservation is ever needed (unlikely for fake-news detection), convert to RGBA first, then composite onto a white background, then convert to RGB.

## 2026-10-23 CPU remount and Kaggle editor

CPU runtime had disconnected due to inactivity/duration. Reconnect plus routine previously-approved Google Drive sign-in restored mount; original source and script survived. Do not redownload the113623359224-byte archive. A new Kaggle engineering notebook and old text editor both stay at Editor Loading, with reCAPTCHA-service error visible. Reload/new dedicated notebook did not expose code cells; no GPU allocated. User verification requested; no security setting changed.

### 2026-10-23 browser observation recovery

An unhandled download-wait rejection reset the CUA bindings; cloud CPU/GPU jobs were unaffected. Catch event promises immediately before triggering UI actions. Download was actually complete in Chrome history; reveal exact file in Finder, then move only that owned artifact into UROP. Never repeat a download solely because its event observation timed out. Colab output JavaScript errors recurred after an intentionally interrupted historical cell; a view reload/old-output cleanup does not establish a stopped process. Colab Active sessions and new Drive shard receipts showed the CPU runtime/job remained active. No cookie/security setting was weakened.
