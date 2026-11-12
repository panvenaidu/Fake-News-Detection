# Multimodal misinformation classification

This research project evaluates six-category classification using text, images, and text with images from the [Fakeddit dataset](https://github.com/entitize/fakeddit) (provided by the faculty). The models predict research-defined categories; a prediction alone does not establish whether a claim is true.

| Input | Model | Validation accuracy | Test accuracy |
|---|---|---:|---:|
| Text | BERT-base | 82.74% | 82.39% |
| Image | ResNet-50 | 80.93% | 81.16% |
| Text + image | BERT-base + ResNet-50 | 88.51% | 88.15% |

The reported results use one seed per model and the original split assignments. Image-based models use the approved cohort after excluding 491 images that could not be decoded. Text-only uses the full released title cohort, so comparisons across modalities are descriptive. Different training methods and cohorts also limit direct comparison with the [original paper](https://arxiv.org/abs/1911.03854).

Detailed results and verification are available in the [text report](results/TEXT_ONLY_FINAL_REPORT_20261009.md), [image report](results/IMAGE_ONLY_FINAL_REPORT_20261102.md), and [multimodal report](results/MULTIMODAL_FINAL_REPORT_20261028.md). Research code is in `scripts/`, model settings in `configs/`, and notebooks in `notebooks/`. Original data, model weights, and private working materials are maintained outside the public repository.
