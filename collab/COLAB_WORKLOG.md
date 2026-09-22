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
