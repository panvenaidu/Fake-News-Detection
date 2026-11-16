# Multimodal misinformation classification

This project evaluates six-category classification using text, images, and text with images from the [Fakeddit dataset (provided by the faculty)](https://github.com/entitize/fakeddit). The models predict research-defined categories; a prediction alone does not establish whether a claim is true.

| Input | Model | Validation accuracy | Test accuracy |
|---|---|---:|---:|
| Text | BERT-base | 82.74% | 82.39% |
| Image | ResNet-50 | 80.93% | 81.16% |
| Text + image | BERT-base + ResNet-50 | 88.51% | 88.15% |

The reported results use one seed per model and the original split assignments. Image-based models use the approved cohort after excluding 491 images that could not be decoded. Text-only uses the full released title cohort, so comparisons across modalities are descriptive. Different training methods and cohorts also limit direct comparison with the [original paper](https://arxiv.org/abs/1911.03854).

## Results

- [Text-only final report](Metrics/Results/TEXT_ONLY_FINAL_REPORT_20261009.md)
- [Image-only final report](Metrics/Results/IMAGE_ONLY_FINAL_REPORT_20261102.md)
- [Text + image final report](Metrics/Results/MULTIMODAL_FINAL_REPORT_20261028.md)

## Project folders

- Model: model source and architecture references
- Configuration: registered settings and dependencies
- Pre-processing: private data and preparation tools
- Training: training notebooks and scripts by modality
- Validation: validation and recovery checks
- Testing: frozen test evaluation and verification
- Metrics: saved results, reports, and local presentation materials

Original data, model weights, and local presentation materials are kept private and are not included in the public repository.
