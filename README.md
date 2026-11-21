# Multimodal Fake News Detection

A six-class research study using the provided Fakeddit data. It compares post-title, image-only, and fused title-plus-image models, with a later vision-transformer follow-up. **These are research-category predictions, not fact-checks:** a model score does not establish whether a claim is true.

![Validation and held-out test accuracy across five model runs](accuracy-chart.svg)

## Results

| Model | Input | Validation accuracy | Test accuracy | Test Macro-F1 | Test rows |
|---|---|---:|---:|---:|---:|
| BERT-base | Title | 82.74% | 82.39% | 0.7746 | 59,319 |
| ResNet-50 | Image | 80.93% | 81.16% | 0.6618 | 59,270 |
| BERT-base + ResNet-50 | Title + image | 88.51% | **88.15%** | **0.8264** | 59,270 |
| DeiT III B/16 fine-tuned | Image follow-up | 83.02% | 83.13% | 0.7131 | 59,270 |
| BERT-base + DeiT III B/16 | Title + image | **90.89698%** | **90.72887%** | 0.8616 | 59,270 |

The first three rows are the completed baseline comparison. The DeiT III image-only result and the BERT + DeiT III multimodal result are later follow-up experiments. For BERT + DeiT III, Epoch 4 was selected by validation accuracy; one evaluation of the frozen checkpoint produced a held-out test accuracy **0.16811 percentage points lower** than validation. The training receipt records four completed epochs and `no_test: true`; the separate held-out evaluation passed independent CSV verification. See the [final result record](results/experiments/bert_deit3/final_results.json) and [post-run audit](results/experiments/bert_deit3/POSTRUN_AUDIT.md). Accuracy is the share of correctly classified posts; Macro-F1 weights the six categories equally and helps expose uneven class performance.

## Data and evaluation

The project uses six Fakeddit categories: **True, Satire/Parody, Misleading Content, Imposter Content, False Connection,** and **Manipulated Content**. Original split assignments are retained.

| Cohort | Train | Validation | Held-out test | Total |
|---|---:|---:|---:|---:|
| Text (all released titles) | 564,000 | 59,342 | 59,319 | 682,661 |
| Image and multimodal (usable pairs) | 563,601 | 59,299 | 59,270 | 682,170 |

Image-based runs exclude 491 records whose image files could not be decoded. The image-only, multimodal, and DeiT III runs share the usable image cohort; the text-only run retains all released titles, so its test set has 49 more rows. Treat cross-cohort comparisons as descriptive rather than perfectly paired.

For the three baselines, the checkpoint was selected on validation Macro-F1, with lower validation loss and then the earlier epoch as tie-breakers; the selected checkpoint was frozen before held-out testing. The DeiT III image-only path uses validation accuracy, then Macro-F1, lower loss, and earlier epoch. BERT + DeiT III selected Epoch 4 by validation accuracy. Test scores did not select checkpoints. The fixed seed is 42.

## Models

- **Text-only:** BERT-base reads the cleaned post title (`clean_title`).
- **Image-only baseline:** ResNet-50 classifies RGB pixels.
- **Multimodal baseline:** BERT-base and ResNet-50 features are projected and combined with maximum fusion before a classifier head.
- **Image follow-up:** a fine-tuned DeiT III B/16 model; reported separately from the original three-baseline comparison.
- **Multimodal follow-up:** BERT-base + DeiT III B/16, with Epoch 4 validation-selected and independently verified once on the held-out test split.

## Repository map

| Path | Purpose |
|---|---|
| `model/` | Modality-specific model definitions and training modules |
| `preprocessing/` | Shared preparation code and data manifests |
| `training/` | Cloud scripts, notebooks, and training support |
| `testing/`, `validation/` | Checks and evaluation support |
| `configs/` | Modality-specific experiment settings |
| `results/` | Result receipts, verification records, and experiment outputs |
| `metrics/` | Reporting and metric utilities |
| `archives/` | Historical and superseded material |

Key saved evidence: [text result record](results/text_only_bert_results.json), [ResNet-50 result record](results/image_only_resnet50_results.json), the [multimodal completion receipt](results/MM_FINAL_COMPLETION_RECEIPT_20261028.json), and the [image follow-up summary](results/image_only_vit_results.json) with its [DeiT III test verification](results/VIT83_VERIFICATION_370301005/VIT83_CPU_VERIFICATION.json).

## Reproducibility status

This working tree is not yet a turnkey run guide. The root `requirements.txt` is absent, and `configs/requirements.txt` does not list `torchvision`. The recent reorganization has made the three trainer symlinks target the lowercase `model/` sources, but helper paths still need alignment: the paired-pilot builder resolves `configs/` and `data/` beneath `preprocessing/shared/`, and the multimodal validation check expects `configs/multimodal_usable_6way_v2.json` instead of the current `configs/text_plus_image/` location. Until these paths are corrected and smoke-tested, this README intentionally avoids copy-paste training commands. Next steps are to fix the remaining helper paths, publish one dependency manifest, identify one canonical entry point per modality, and separate active results from archived experiments.

The dataset is faculty-provided; use only authorized copies and keep private data out of public commits. See the [Fakeddit release](https://github.com/entitize/fakeddit), the [original paper](https://arxiv.org/abs/1911.03854), and the [project website](https://urop-project.upliftingibis2.chatgpt.site/).
