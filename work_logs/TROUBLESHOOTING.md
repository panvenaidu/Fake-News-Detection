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
The learning rate scheduler's `.step()` method is called before the optimizer's `.step()` method in the training loop. PyTorch expects the optimizer step to happen first so the scheduler adjusts the LR for the *next* step, not the current one.

### Fix
Reorder the training loop so that `optimizer.step()` is called before `scheduler.step()`. The fix must be applied in `src/fakenews_baselines/e002_text.py` in the training loop.

### Result
The preliminary seed-42 run completed and produced metrics, but the learning rate schedule may not have been applied correctly. **This result is PRELIMINARY and must be rerun after the fix before being treated as the final canonical E002 baseline.**

### Safe to repeat?
No — the scheduler issue should be fixed before any further canonical training.

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
