# Frozen image-only ViT-B/16 versus ResNet-50

ResNet-50 scored 71.9082% accuracy and 0.527292 macro-F1, compared with 65.6487% and 0.481237 for ViT-B/16. ResNet-50 led on all three aggregate metrics on both test cohorts. Both models completed four head-training epochs with full validation. Independent CPU readback reproduced the metrics from the saved predictions on November 14, 2026. [Private science run](https://www.kaggle.com/code/rocky62/urop-image-only-vit-vs-resnet-50?scriptVersionId=369302248) · [Verified per-class report](https://www.kaggle.com/code/rocky62/urop-image-only-vit-comparison-readback/output?scriptVersionId=369460396&select=REOPENED_REPORT.md) · [Independent verification receipt](https://www.kaggle.com/code/rocky62/urop-image-only-vit-comparison-readback/output?scriptVersionId=369460396&select=REOPENED_VERIFICATION.json)

| Held-out cohort | Model | Accuracy | Macro-F1 | Balanced accuracy |
|---|---|---:|---:|---:|
| All 59,270 test posts | ViT-B/16 | 65.6487% | 0.481237 | 46.1886% |
| | ResNet-50 | 71.9082% | 0.527292 | 50.4909% |
| | ViT − ResNet-50 | −6.2595 pp | −0.046056 | −4.3023 pp |
| 56,052 test posts with no training byte hash | ViT-B/16 | 65.4053% | 0.482825 | 46.3123% |
| | ResNet-50 | 71.5817% | 0.525616 | 50.3841% |
| | ViT − ResNet-50 | −6.1764 pp | −0.042791 | −4.0718 pp |

## Per-class results

The table covers the full test set. The verified Kaggle report also includes every class on the 56,052-post subset. Both models had very low recall on Imposter Content. The largest full-test F1 gap was in False Connection.

| Class | Support | ViT precision | ViT recall | ViT F1 | ResNet precision | ResNet recall | ResNet F1 |
|---|---:|---:|---:|---:|---:|---:|---:|
| True | 23,507 | 0.627798 | 0.791084 | 0.700045 | 0.679377 | 0.842090 | 0.752033 |
| Satire/Parody | 3,514 | 0.519807 | 0.306204 | 0.385387 | 0.624571 | 0.311042 | 0.415274 |
| Misleading Content | 11,297 | 0.586856 | 0.372311 | 0.455589 | 0.604015 | 0.463397 | 0.524444 |
| Imposter Content | 1,224 | 0.666667 | 0.001634 | 0.003260 | 0.263158 | 0.004085 | 0.008045 |
| False Connection | 17,423 | 0.742796 | 0.795959 | 0.768459 | 0.852356 | 0.876083 | 0.864057 |
| Manipulated Content | 2,305 | 0.668200 | 0.504121 | 0.574679 | 0.686417 | 0.532755 | 0.599902 |

## Cohort, training and runtime

The full faculty cohort was 563,601 training, 59,299 validation and 59,270 held-out posts, with the approved split membership, IDs and labels. A local join of the registered IDs and verified SQLite index independently found 3,218 test posts whose exact image bytes also occur in training. Byte hashes detect exact repeats. ResNet-50's lead persisted after excluding those posts. Kaggle mounted packed dataset version 1 (ID 21277535) and quality check version 2 (script version 362643633). It verified the manifest, coverage and index SHA-256 values against the prior verified baseline records, then checked archive and image bytes using the packed loader.

Both models used RGB pixels resized on the shorter side to 256 with antialiased bilinear interpolation, center cropped to 224 × 224, and normalized for ImageNet. The frozen encoders ran in evaluation mode with FP16 autocast and cached float32 features. Both six-output heads used dropout 0.2, AdamW (learning rate 0.001, weight decay 0.0001), cross-entropy, seed 42, and batches of 256 in the same training order. The real-image smoke used 48 training and 48 validation posts. Each model produced 48 × 6 logits, updated its head, and reproduced fixed validation logits after reloading.

| Model | Validation macro-F1 over epochs 1–4 | Selected epoch | Selected validation loss |
|---|---|---:|---:|
| ViT-B/16 | 0.478156, 0.480408, 0.476105, 0.475856 | 2 | 0.938778 |
| ResNet-50 | 0.517046, 0.515871, 0.522037, 0.524482 | 4 | 0.792661 |

Checkpoint selection used highest unrounded validation macro-F1, then lower loss, then earlier epoch. Both checkpoint hashes were frozen before test features were extracted. The CPU readback recomputed every validation and test metric, checked exact ID coverage and order, preserved labels, normalized finite probabilities, argmax, per-row cross-entropy, confusion matrices, the selection rule, and the selected head hashes. The science output retains the resolved config, manifests, preflight receipt, feature shards, weights and recovery state, predictions, metrics, and training histories. Kaggle retains the session logs under the same version. [Saved science artifacts](https://www.kaggle.com/code/rocky62/urop-image-only-vit-vs-resnet-50/output?scriptVersionId=369302248) · [Run logs](https://www.kaggle.com/code/rocky62/urop-image-only-vit-vs-resnet-50/log?scriptVersionId=369302248)

Kaggle reported 4,674.0 seconds (77.9 minutes) for the GPU version. The in-notebook run recorded 77.2 minutes. It used GPU 0 from a Tesla T4 ×2 allocation with Python 3.13.16, Torch 2.11.0+cu130 and TorchVision 0.26.0+cu130. Before staging, Kaggle reported 30 GPU hours available and 19.5 GiB of writable output space. Staging and checking 39 packed archives took 435.75 seconds. A 2,048-post benchmark measured 161.35 posts/s for both encoders together, which supported the full cohort.

| Backbone | Pretrained weight SHA-256 | Selected head SHA-256 |
|---|---|---|
| ViT-B/16 ImageNet1K V1 | `c867db91d3e12c6cbadabb610d73c24a546bf82d8c03a9fea34f43a712ddb0e9` | `29740a2f964a169827f130fe5e03936efc2cf44fcb79e72662a13b0e4442e5bf` |
| ResNet-50 ImageNet1K V2 | `11ad3fa62ca79e40addfd354a8ec4b7c75143b3038b8d2a807fbc68deab379ca` | `ba1a57ea9e91ba8b511f20fd7b4579c84dfd90844f5e3cd7556551efeab85eaa` |

The matched frozen ResNet-50 is the main comparison. The historical end-to-end ResNet-50 scored 81.1557% accuracy and 0.661796 macro-F1 under its original protocol. The two pretrained backbones use different ImageNet recipes, so this comparison measures the frozen pretrained models as supplied. One seed gives no estimate of variability across runs. [Historical report](IMAGE_ONLY_FINAL_REPORT_20261102.md)
