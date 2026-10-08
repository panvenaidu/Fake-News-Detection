# COLAB WORKLOG — Multimodal Fake News Detection

> **Purpose:** Chronological record of all verified actions performed in Google Colab.
> **Last Updated:** 2026-09-23
> **Updated By:** Antigravity

---

## Session: 2026-09-22 / 2026-09-23

### 1. Colab T4 GPU Enabled

- **GPU:** Tesla T4
- **VRAM:** ~14.56 GB
- **Status:** Successfully enabled

### 2. Initial Repository Problem and Recovery

- `/content/Fake-News-Detection` was **not present** in the fresh Colab runtime.
- **Fix:** GitHub repository was cloned again successfully:
  ```
  git clone <repo-url> /content/Fake-News-Detection
  ```
- The previously implemented E002 code was recovered from GitHub without loss.
- Git working tree was verified clean after cloning.
- **Important lesson:** Local code deletion in Colab does NOT require rewriting because the code is recoverable from GitHub. This is why all code/context must be committed and pushed.

### 3. Google Drive Mounted

- Google Drive was mounted successfully at `/content/drive/`.
- Verified persistent files:
  - `/content/drive/MyDrive/Colab Notebooks/UROP/data/verified_paired_manifest.csv`
  - `/content/drive/MyDrive/Colab Notebooks/UROP/images.zip`

### 4. Dataset Preparation

1. **Manifest copied** from Google Drive into the Colab project:
   ```
   cp "/content/drive/MyDrive/Colab Notebooks/UROP/data/verified_paired_manifest.csv" \
      /content/Fake-News-Detection/data/
   ```
2. **Manifest verification:**
   - Rows: 75,995
   - Train: 62,635
   - Validation: 6,685
   - Test: 6,675
   - SHA-256: `fc74cb42288d366131ac764bf02f9212bacd7cab0af68442a003beaaff9fde20` — **MATCHED** locked expected hash.

3. **images.zip copied** from Google Drive into Colab project:
   ```
   cp "/content/drive/MyDrive/Colab Notebooks/UROP/images.zip" \
      /content/Fake-News-Detection/
   ```

4. **ZIP structure inspected** before extraction — confirmed it contains `images/` directory with `.jpg` files.

5. **Images extracted successfully:**
   ```
   unzip -q images.zip -d /content/Fake-News-Detection/
   ```

6. **Post-extraction count:** 75,995 JPG images present in `images/`.

### 5. Storage Observations

| Metric | Value |
|--------|-------|
| Initial free Colab disk | ~66 GB |
| `images.zip` size | ~7.9 GB |
| Extracted images size | ~8.0 GB |
| Free space after extraction | ~42 GB |

> **Warning:** Colab local storage (`/content/`) is **temporary**. It is lost when the runtime disconnects or resets. Google Drive is persistent. All results must be committed to Git or copied to Drive before the session ends.

### 6. Full Image Preflight

All 75,995 manifest image paths were checked:

| Metric | Value |
|--------|-------|
| Total images checked | 75,995 |
| All images exist | ✅ Yes |
| RGB | 73,549 |
| RGBA | 196 |
| P (palette) | 2,123 |
| L (grayscale) | 122 |
| CMYK | 5 |
| RGB conversion failures | **0** |

- **Conclusion:** All 75,995 images are usable. Non-RGB images (2,446 total) successfully convert to RGB. They must NOT be removed from the manifest.
- **Warning observed:** One very large image triggered a `PIL.Image.DecompressionBombWarning` but remained readable and convertible. It should not be deleted unless a future validated policy explicitly requires it.

### 7. Environment Verification

| Package | Version |
|---------|---------|
| PyTorch | 2.11.0+cu128 |
| Transformers | 5.16.1 |
| scikit-learn | 1.6.1 |
| CUDA available | True |
| GPU | Tesla T4 |

- **BERT GPU preflight:** PASS — BERT loaded on GPU and produced 6-class logits successfully.

### 8. E002 Seed-42 Execution

- **Runner:** `scripts/run_e002.py --seed 42`
- **Device:** Tesla T4, CUDA AMP enabled
- **Status:** Run completed successfully.

#### 8a. Preliminary Results (PRELIMINARY — scheduler-order issue detected)

**Validation (selected epoch 4):**

| Metric | Value |
|--------|-------|
| Accuracy | 0.7820493642483172 |
| Macro-F1 | 0.7011849373622043 |
| Balanced accuracy | 0.6688611483544041 |
| Weighted-F1 | 0.7784427083189532 |
| Loss | 0.7400053048365671 |

**Test (from validation-selected checkpoint):**

| Metric | Value |
|--------|-------|
| Accuracy | 0.7790262172284644 |
| Macro-F1 | 0.6891492224613445 |
| Balanced accuracy | 0.6597637885595928 |
| Weighted-F1 | 0.7757598886966056 |
| Loss | 0.7398176850808247 |

**Per-class test F1:**

| Class | F1 |
|-------|-----|
| 0 — True | 0.8312138728323699 |
| 1 — Satire/Parody | 0.6097560975609756 |
| 2 — Misleading Content | 0.6707317073170732 |
| 3 — Imposter Content | 0.47342995169082125 |
| 4 — False Connection | 0.8292912644219449 |
| 5 — Manipulated Content | 0.7204724409448819 |

**Runtime:**

| Metric | Value |
|--------|-------|
| Total runtime | 1825.61 seconds (~30.4 min) |
| Training time | 1312.23 seconds (~21.9 min) |
| Throughput | 286.39 samples/sec |
| Peak GPU memory | 3,238,541,312 bytes (~3.02 GB) |

> **⚠️ PRELIMINARY STATUS:** This run produced a `UserWarning: Detected call of lr_scheduler.step() before optimizer.step()`. The run completed but the scheduler-order issue means the learning rate schedule may not have been applied correctly. This result must NOT be treated as the final canonical E002 baseline. A corrected rerun is required.

#### 8b. Machine-Generated Artifacts

The raw machine-generated result artifacts from this run were produced in the Colab runtime. **No machine-generated seed-42 result artifact currently exists in the local Git repository** — the Colab results were not synced back before the runtime ended. The values above are from the observed Colab output.

**Action required:** If machine-generated JSON artifacts exist in Google Drive or a future Colab session, they should be copied to:
```
results/experiments/e002_text/E002-bert-base-uncased-6way-BP6Wv1-s42/
```
and treated as the authoritative source. If those artifacts contain values that differ from the Colab output above, the machine-generated artifacts take precedence.

### 9. Warnings and Errors Observed

| Warning/Error | Severity | Impact |
|---------------|----------|--------|
| `lr_scheduler.step() before optimizer.step()` | ⚠️ Affects LR schedule | Preliminary result; rerun required |
| Palette image transparency warning | ℹ️ Info | No conversion failure |
| `PIL.Image.DecompressionBombWarning` | ℹ️ Info | Image remained readable |
| DataLoader worker-count warning | ℹ️ Performance | Not a model failure |
| HuggingFace unauthenticated Hub warning | ℹ️ Info | Model downloaded successfully |
| BERT pre-training head UNEXPECTED keys | ℹ️ Expected | Normal when loading for downstream task |
| NameError for `PY` (shell/heredoc) | ❌ Notebook format | Use Python cells, not shell heredoc |
| SyntaxError (nested `python -c` quoting) | ❌ Notebook format | Use Python cells, not nested shell |

### 10. Faculty Direction (2026-09-22)

- BERT and ResNet-50 remain baselines.
- Faculty wants broader comparison with modern multimodal approaches.
- Candidate families include: CLIP/semantic alignment, contrastive learning, cross-attention/co-attention, adaptive/correlation-based fusion, modality-decoupled/multi-expert methods, and HGAT where appropriate.
- HGAT requires social/context graph data — later candidate only.
- Final research contribution remains undecided.
- Faculty requested "initial values" from actual training runs.

---

## Current Colab Working Layout

```
Google Drive (persistent):
  /content/drive/MyDrive/Colab Notebooks/UROP/
    data/verified_paired_manifest.csv    ← manifest backup
    images.zip                           ← image archive backup

GitHub (persistent):
  Code, configs, context files, result artifacts
  Must be committed and pushed before Colab runtime ends

/content/ (TEMPORARY — lost on runtime reset):
  /content/Fake-News-Detection/          ← cloned GitHub repo
    data/verified_paired_manifest.csv    ← copied from Drive
    images/                              ← extracted from images.zip
    images.zip                           ← copied from Drive
    results/experiments/                 ← training outputs (MUST SYNC)
```

### Workflow for Each Colab Session

1. Clone GitHub repository into `/content/`
2. Copy manifest from Google Drive → `data/`
3. Copy and extract `images.zip` from Google Drive → `images/`
4. Verify manifest hash and image count
5. Run training
6. **Before session ends:** Commit and push results to Git, or copy to Google Drive

### Performance Note

Training should use local `/content/` image storage, **not** file-by-file Google Drive access. Google Drive I/O is significantly slower than local Colab disk I/O, which would severely impact training throughput.


## 2026-10-08 — Official release migration (current)

User authorized full official six-way text training on Google Colab. BERT-base and ModernBERT-base are prepared under `OFFICIAL-6W-TEXT-v2`; training is NOT yet verified as started. Chrome controls timed out after existing Google Drive sign-in. New metrics are not available. Official data: 564,000 train / 59,342 validation / 59,319 public test. Old E002 results remain historical BP-6W-v1 subset results. See `context/AUDIT_20261008.md`, `results/official_dataset_audit.json`, `configs/text_official_6way_v2.json` and `notebooks/UROP_OFFICIAL_6WAY_TEXT_20261008.ipynb`.


## 2026-10-08 14:50 IST — Setup/recovery checkpoint (current)

- User authorized local and GitHub checkpoint updates for every model, and confirmed Chrome-only training; Colab CLI fallback declined. No Colab CLI credentials were granted.
- Official dataset files and their hashes/counts are saved locally; full six-way cohort remains unchanged.
- BERT-base and ModernBERT-base trainer/notebook now save recoverable state every 3,000 batches and at epoch boundaries, including optimizer, scheduler, scaler, random generators, sampler position, history and selected checkpoint. `--resume-attempt` restores a named attempt and preserves completed models.
- Recovery batch ordering passed a CPU sampler check; script and notebook syntax checks passed. Cloud GPU execution/recovery has NOT been tested.
- Chrome application control continues to time out, and the direct Chrome browser provider is unavailable. Training is NOT verified as started; no official-v2 validation/test metrics exist. The prior cloud preflight verified Tesla T4 only.
- Account usage query: 34% remains in five-hour Codex window; reset 2026-10-08 17:35 IST. This is separate from Colab runtime lifetime and GPU limits.
- Next action: restore Chrome automation or upload `notebooks/UROP_OFFICIAL_6WAY_TEXT_20261008.ipynb` in Chrome Colab, select T4 and Run all; verify Drive mount, dataset hashes and the first actual optimizer steps. Preserve exact cloud ATTEMPT path.
- Then sync each model's small JSON/CSV/log evidence under `results/experiments/official_text/`, update these context/log/status files and push milestone documentation. Large TSVs, images and weights remain excluded from Git. Local/GitHub syncing requires a connected agent; cloud checkpoints write independently.


## 2026-10-08T09:33:11.547672+00:00 — Cloud startup checkpoint

Chrome recovered; Drive mounted on T4. Observed Python 3.13.15 / transformers 5.18.0 / torch 2.11.0+cu130. Official file/source verification succeeded. Three cloud initialization attempts (20261008T092708Z, 20261008T092745Z, 20261008T092810Z) failed with `AttributeError: Tee object has no attribute isatty` before optimizer steps. Cloud evidence is preserved under `/content/drive/MyDrive/Colab Notebooks/UROP/official_text_runs/`. Fixed stream-method delegation; isatty/encoding/fileno checks and notebook syntax passed locally. Clean relaunch pending; no new validation/test metrics. Chrome-only preference honored. Setup commit 09876a88d70747cae62e6fac55946a547532e9e8 is pushed.


## 2026-10-08T09:39:18.215639+00:00 — Corrected cloud process launched

Pinned fixed source SHA256 `a13c0e5d97b2fe7661ce6a228d43d853f1aca703314cfa48688825b7b01701f9` loaded from pushed commit `9c7abf1`. Colab cell [16] visibly entered Executing state on Tesla T4. This verifies process launch only; first optimizer steps, current attempt folder, and metrics have not yet been observed. BERT runs first; ModernBERT remains queued. Live Chrome controls subsequently became unavailable. Do not rerun launch cells or replace data blindly: inspect current process/output and cloud status before deciding whether a recovery is needed. Latest machine-readable local status: `results/official_text_live_status.json`. Checkpoints write to Drive independently; local and GitHub synchronization needs a connected agent.


## 2026-10-08T09:45:49.174071+00:00 — Usage/recovery checkpoint

Last usage check: 6% remains; five-hour window resets 2026-10-08 17:35 IST. This supersedes the earlier 34% preflight reading. Latest source logging fix and recovery code are pushed. Current cloud training progress is unverified: cell 16 entered execution, but a later accessibility view showed 4 seconds elapsed without readable subprocess output. Do not claim active optimizer steps or metrics. Native Chrome controls/screenshots are unreliable/unavailable and the Chrome terminal has no usable prompt. User was asked to keep the Mac awake/unlocked with Chrome visible; Colab CLI fallback was explicitly declined. Preserve existing cloud attempts; inspect latest model status/error/checkpoint before any rerun. All scientific settings and dataset files remain unchanged.


## 2026-10-08T09:49:32.158683+00:00 — Final continuity checkpoint

All code/config/notebook, dataset provenance, audit, startup errors and current unverified launch state are saved. Checkpoint cadence is implemented (every 3,000 batches and each epoch), but no successful cloud weight checkpoint or optimizer updates have yet been verified. The last available Colab setup screenshot is `results/colab_setup_last_available.png`; it is not live training-progress proof. Attempts to create a continuation heartbeat failed schedule validation, so no automatic follow-up is active. Resume only after checking the existing cloud attempt; do not assume chat usage reset automatically resumes an agent. Chrome-only preference remains in force.


## 2026-10-08T10:03:25.864123+00:00 — Official BERT optimizer steps verified

Chrome Colab runtime recovered. A guarded notebook launch started PID 23054 with verified fixed source SHA256 a13c0e5d97b2fe7661ce6a228d43d853f1aca703314cfa48688825b7b01701f9. Active attempt: `OFFICIAL-6W-TEXT-v2_seed42_20261008T095827Z` in `/content/drive/MyDrive/Colab Notebooks/UROP/official_text_runs/`. Notebook: https://colab.research.google.com/drive/11JK1wLLVPH8G7_oThnb0YkLMSR4URafF. BERT epoch 1 reached batch 1,000/17,625, with 997 successful optimizer updates and 3 mixed-precision skipped updates, approximately 229.78 titles/second. Checkpoint not yet present at this observation; first is due at batch 3,000. ModernBERT remains queued. No official-v2 validation/test metrics exist yet. Prior cell 16 was interrupted; it is superseded by this verified active attempt. Browser editing produced malformed launch code before this guarded launch; those cells did not train. A repeated execution was blocked by the active-process guard, preventing duplicate training. Keep official splits and scientific settings unchanged; monitor status/checkpoints before any restart. Chrome-only requirement honored.


## 2026-10-08T10:08:03.557939+00:00 — First durable training checkpoint verified

Live Colab monitor observed BERT epoch 1 batch 3,500 / 3,497 optimizer updates, with recovery metadata saved for epoch 1 batch 3,000. Source writes recovery metadata only after the full model/optimizer/scheduler/scaler/RNG checkpoint replaces its temporary file. Active attempt remains OFFICIAL-6W-TEXT-v2_seed42_20261008T095827Z. ModernBERT queued; no validation or test metrics yet. Continuous read-only monitor installed in notebook cell 11; do not rerun this monitor or launch while it is executing.


### 2026-10-08T10:16:40.078Z — Recovery checkpoint observed

OFFICIAL-6W-TEXT-v2_seed42_20261008T095827Z
bert-base training epoch 1 batch 6500 updates 6496
Saved recovery: 1 6000
modernbert-base queued
Process: None UTC: 10:15:46


### 2026-10-08T10:22:41.633Z — Recovery checkpoint observed

OFFICIAL-6W-TEXT-v2_seed42_20261008T095827Z
bert-base checkpointing epoch 1 batch 9000 updates None
Saved recovery: 1 9000
modernbert-base queued
Process: None UTC: 10:21:45


## 2026-10-08T10:24:48.790731+00:00 — Automatic continuation and restart safeguards

An hourly thread follow-up is now ACTIVE (automation id `complete-urop-text-training`), superseding earlier failed scheduling attempts. It inspects this existing cloud attempt, finishes authorized BERT/ModernBERT evaluations, recovers from checkpoints if needed, and synchronizes small evidence/context/GitHub milestones. It remains quiet when nothing meaningful changes. No paid compute authorization or Colab CLI access is granted. The local notebook and launch helper now inspect real cloud process arguments before starting, preserving the same scientific protocol and trainer source. Launch metadata and logs persist in Drive; a separate monitor displays checkpoint/validation/test progress. These local launch-cell changes have not been deployed over the currently running trainer and do not alter its source or results. Colab's resource panel reported zero purchased compute units and up to three hours of runtime at the observed usage level; continuation depends on actual GPU availability.


### 2026-10-08T10:41:09.172Z — Recovery checkpoint observed

OFFICIAL-6W-TEXT-v2_seed42_20261008T095827Z
bert-base training epoch 1 batch 6500 updates 6496
Saved recovery: 1 6000
modernbert-base queued
Process: None UTC: 10:15:16


### 2026-10-08T10:42:25.373784+00:00 — Verified 15,000-batch recovery; ignore replayed output

A refreshed Colab snapshot verified BERT epoch 1 batch 16,500 with 16,492 optimizer updates and saved recovery at batch 15,000 (cloud reading 10:38:37 UTC). Chrome Drive separately verified resume_checkpoint.pt at 1.22 GB, checkpoint history, recovery metadata, tokenizer, source and config in the exact BERT folder linked in live status. Reconnection replayed an older 6,500-batch reading; that is historical cached display, not current progress. Do not let such replayed outputs regress live status. Validation and test metrics remain unverified.


## 2026-10-08T10:46:10.624380+00:00 — First official full-cohort validation result

BERT epoch 1 validation: **81.07% accuracy**, **75.25% Macro-F1**, read from the Colab monitor's four-decimal rounded output at 10:43:43 UTC. This is an intermediate validation observation, not a final result. Epoch 2 batch 500 / 18,117 optimizer updates is running; recovery saved at the epoch-1 boundary (batch 17,625). ModernBERT is queued. Test has not been evaluated; full-precision original JSON/report/predictions must still be synchronized from Drive. Rounded observation saved at `results/experiments/official_text/OFFICIAL-6W-TEXT-v2_seed42_20261008T095827Z/bert-base/validation_epoch1_observed.json`. The experiment continues unchanged under the original validation-selection/early-stop protocol. Hourly automatic continuation is active; no paid compute or Colab CLI fallback authorized.


### 2026-10-08T11:08:23.431218+00:00 — Connection label stale; training progress verified

Chrome still displays Connecting/Resuming execution, while fresh output confirms BERT epoch 2 batch 10,000, 27,615 optimizer updates, recovery saved at epoch 2 batch 9,000. Cloud reading 2026-10-08 11:05:58 UTC (16:35:58 IST), approximately one minute before inspection. This advanced from the user screenshot showing batch 5,500 at 16:24:38 IST. No runtime reset or duplicate training launch was performed. First validation remains 81.07% accuracy / 75.25% Macro-F1 (rounded); final test pending, ModernBERT queued. Stale startup/usage fields in live status were moved under historical_startup_observations so they do not contradict current verified progress.


### Colab quota check — 2026-10-08 16:43:59 IST
Chrome Resources panel: not subscribed, zero purchased compute units, free resources not guaranteed, runtime may last up to 2 hours. This is not proof that free GPU quota is exhausted or a promised remaining duration. Panel says Not connected while timestamped monitor advances to BERT epoch 2 batch 13500, 31112 optimizer updates, recovery epoch 2 batch 12000. ModernBERT queued; latest validation remains intermediate 0.8107 accuracy/0.7525 Macro-F1, no final test yet. Raw Chrome evidence: results/colab_gpu_quota_check.txt. Do not restart or delete this runtime based solely on Connecting.


### Kaggle access and second BERT validation — 2026-10-08 16:57 IST
User authorized Kaggle as an additional compute provider. Existing Kaggle account rocky62 signed in through panvee62 Google sign-in. Settings show GPU 00:00 / 30 hrs, but account is phone-unverified. Phone/CAPTCHA/SMS form is open for user; no training, uploads, API credentials, or changed sharing. Evidence: results/kaggle_setup_status.json and results/kaggle_quota_verification_observed.txt. Alternate Google email is panvee58@gmail.com (50 was a typo); no migration authorized/performed. Chrome extension now exposes browser id 3, profile Rocky: use browser controls rather than stale native AX; current Kaggle handoff tab 719302181. Existing Colab tab 719302027 live reading 11:27:15 UTC verifies BERT epoch 3 batch 1500, 36735 updates, recovery epoch 2 boundary batch 17625. Second intermediate validation accuracy 0.8243, Macro-F1 0.7582 (rounded). Original JSON and final test pending; ModernBERT remains queued. Do not duplicate BERT or ModernBERT across providers. Kaggle checkpoints need saved notebook outputs or another verified durable backup before relying on session disk for recovery; no Kaggle persistence strategy deployed yet.


### Mobile status check — 2026-10-08 17:48 IST
Fresh Chrome monitor at 12:18:12 UTC verifies BERT epoch 4 batch 5500, 58351 optimizer updates, recovery epoch 4 batch 3000. Third intermediate validation accuracy 82.89%, Macro-F1 77.75%, rounded; final test still pending, ModernBERT queued. Connection UI says Runtime disconnected/Connecting, but monitor timestamp and optimizer progress advanced; do not infer stopped training solely from this label. Kaggle settings now explicitly say Phone verification: Verified. Quota remains 00:00 / 30 hrs. This supersedes earlier phone-verification blocker. No Kaggle GPU assigned, notebook or model run launched yet. Preserve BERT Colab process and avoid duplicate ModernBERT across the pending Colab queue and Kaggle. Evidence: results/colab_epoch3_validation_observed.txt, results/kaggle_setup_status.json.


### Faculty cohort vs paper comparison — 2026-10-08 17:56 IST
Verified one full-cohort BERT optimization run in progress, three completed epoch validation checks, no final test yet. Epochs 1/2/3 validation accuracy 81.07/82.43/82.89%, Macro-F1 75.25/75.82/77.75% (rounded). Paper Table 4 rechecked: six-way text BERT 76.96% validation/76.77% test; six-way BERT+ResNet50 86.00/85.88%; binary text BERT 86.54/86.44%. Current six-way text validation is numerically +5.93 percentage points over paper text validation, not a confirmed test improvement or exact replication. Architecture and 335-row release discrepancy remain caveats. Full comparison saved results/FACULTY_DATASET_TRAINING_COMPARISON_20261008.md. Latest live output 12:26:02 UTC verifies epoch 4 checkpointing batch 9000 and recovery at 9000; optimizer counts not exposed in that state. User is considering stopping but explicitly NOT right now; no runtime stop or reset performed.


### Monitor interruption repaired; original metrics retrieved — 2026-10-08 18:37 IST
User stopped/restarted only the continuous status monitor. Chrome health check independently verifies trainer PID 23054 alive (poll None), Tesla T4 73% utilization with 3641 MiB allocated, epoch 5 batch 7500 / 77970 updates at 13:04:21 UTC. Finite refreshed status at 13:07:44 UTC shows epoch 5 checkpointing batch 9000, recovery saved 13:07:43 UTC. No model crash observed. Replaced notebook cell 11 with a finite status display that returns immediately; only monitor behavior changed. Trainer source hash unchanged. A Colab editor fill initially inserted before old code, causing a status-cell SyntaxError before execution; cleared the editor properly and verified successful completed cell. BERT process unaffected. Old cell 9/10 status snapshots and raw cell 12 export collapsed to avoid stale-display confusion.

Original small cloud evidence (protocol, environment, pip freeze, dataset hashes/counts, model config, status, history, best checkpoint, recovery metadata/history, validation metric/report/confusion CSV) faithfully exported through Chrome and saved under results/experiments/official_text/OFFICIAL-6W-TEXT-v2_seed42_20261008T095827Z/. Retrieval hashes recorded in retrieval_manifest.json. Predictions and model weights remain in Drive; not yet synced. Four original validation observations: epoch 1 accuracy .8106737218159146/Macro-F1 .7524517476142621; epoch 2 .8243234134339927/.7582002314752563; epoch 3 .8289070135822857/.7774830561247422; epoch 4 .8274072326514105/.7786816742546674. Current selected checkpoint epoch 4 by Macro-F1, even though epoch 3 accuracy is higher. Test still pending; ModernBERT queued. Previous statement only rounded metrics available is superseded. Full faculty cohort/splits/source unchanged. Continue BERT up to original early-stop/max6 and test selected checkpoint once; Kaggle fallback authorized if Colab cannot continue, phone verified/30h unused as last checked. Do not launch duplicate training. Status cell 11 is now finite: rerun once to refresh. Health/export cell 12 is finite and can resync small evidence. Local notebook and helper now use finite monitor too.
