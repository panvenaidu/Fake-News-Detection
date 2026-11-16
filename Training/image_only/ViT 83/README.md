# UROP image-only Vision Transformer 83% study

The experiment uses RGB pixels and a single six-class Vision Transformer. The four recipe slots are DeiT III crop control, DeiT III full-frame resize and center padding, DeiT III crop with layer-wise learning-rate decay, and DINOv2 B/14. All pilot trials start from their original pretrained checkpoint. The full trials also start from their respective original checkpoint. Each uses seed 42 and effective batch 64. Full-frame uses bilinear downsampling and RGB padding (124, 116, 104), close to the normalization mean. DINOv2 uses its normalized class token and a six-class head. Its unused masked-image-training token is held fixed.

## Inputs and phase gates

- Faculty cohort `FACULTY-6W-USABLE-682170-v1`. Private packed input dataset version 1 (21277535), quality gate version 362643633. These pin the original tables, exact approved exclusions, paired manifest, coverage receipt, packed archive index and archive hashes.
- Use the free GPU quota display before starting every version. Keep six GPU hours protected from exploration. Use two T4 GPUs for preflight and training, and one GPU for the single frozen test.
- Use the pinned Kaggle environment from the successful preflight. Enable Internet for public weight downloads during preflight and training.
- Preflight verifies the inputs, times every available recipe and exercises a real-image optimizer continuation from a saved engineering checkpoint. It exports verified timings. Training registers quota and sources before scientific updates. The engineering images come from training and validation. The initial optional 336 comparison is omitted from this allocation given the observed free quota.
- Both required pilots evaluate all 59,299 validation rows after each of their two epochs. The pilot cohort is the same fixed, stratified 30,000 training IDs. The promotion decision uses unrounded validation accuracy, macro-F1, lower cross-entropy, earlier epoch, and recipe order for exact ties. The crop control supplies a reference. The highest-ranked alternative advances. A second alternative requires the same affordable cap and a pilot difference within 0.25 percentage points.
- In a clean training continuation mount only the exact predecessor and the two cohort inputs. Keep matching source files and the receipt SHA. The checkpoint stores the model, optimizer, scaler, scheduler, per-rank RNG, cursor, and prior validation results.
- If the winning full checkpoint exceeds 47,592 correct on the validation split, the training version freezes it and checks reload in a fresh validation process. The frozen test uses that exact saved version. CPU readback takes the exact frozen-test version and both saved baseline prediction versions (ResNet-50 364917396 and DeiT 369892645) and recomputes all requested metrics.
- No separate faculty holdout was registered at experiment launch.

## Saved runs

- [Initial preflight 370020449](https://www.kaggle.com/code/rocky62/urop-image-only-vit-83-preflight/log?scriptVersionId=370020449) passed the three DeiT recipes and stopped on the DINOv2 attention projection names.
- [Corrected preflight 370024175](https://www.kaggle.com/code/rocky62/urop-image-only-vit-83-preflight/log?scriptVersionId=370024175) uses the unchanged pinned tensors with the installed Transformers projection names and isolates the optional challenger process.

Use `build.py <phase> <output.ipynb>` from this directory. Pass `--quota-used-minutes` for GPU phases, and `--recovery-version` and `--recovery-sha` for every downstream phase. The training recovery SHA is the predecessor's `sessions.json` hash. The frozen test takes the predecessor's `fixed_validation_receipt.json` hash. The CPU verifier takes the saved test's `test_saved.json` hash. The notebook metadata lists the exact input versions. If transferring the generated code cell into an existing private editor, also check the actual input versions visible there.
