# Notebook catalog

Notebook bytes and code cells are unchanged by the reorganization. Open a completed Kaggle result for a demonstration; running an old notebook can allocate compute or repeat work.

## Local notebooks

| Notebook | Purpose |
|---|---|
| [text_only/train_text_models.ipynb](text_only/train_text_models.ipynb) | Original official text experiment launcher; includes registered/queued model definitions. Not proof every model ran. |
| [text_only/resume_and_evaluate.ipynb](text_only/resume_and_evaluate.ipynb) | Resume the original text experiment and evaluate its selected checkpoint. |
| [text_only/recover_bert_checkpoint.ipynb](text_only/recover_bert_checkpoint.ipynb) | Recover the saved BERT state; historical recovery launcher. |
| [text_image/final_training_and_test.ipynb](text_image/final_training_and_test.ipynb) | Final continuation and held-out evaluation notebook; completed run history. |
| [text_image/continue_training_and_validation.ipynb](text_image/continue_training_and_validation.ipynb) | Part 2 continuation from the accepted Part 1 recovery. |
| [preparation/check_gpu_and_recovery.ipynb](preparation/check_gpu_and_recovery.ipynb) | Synthetic CUDA and checkpoint checks; not scientific training. |
| [preparation/prepare_faculty_images_v1.ipynb](preparation/prepare_faculty_images_v1.ipynb) | Earlier CPU image-preparation notebook. |
| [preparation/prepare_faculty_images_v2.ipynb](preparation/prepare_faculty_images_v2.ipynb) | Later CPU image-preparation notebook; retained distinct source. |
| [templates/train_epoch_usable_images.ipynb](templates/train_epoch_usable_images.ipynb) | Approved usable-image cohort epoch template; not a new run. |
| [archive/train_epoch_all_images_superseded.ipynb](archive/train_epoch_all_images_superseded.ipynb) | Superseded all-images template from before the approved exclusions. |
| [pilot/train_and_evaluate_paired_pilot.ipynb](pilot/train_and_evaluate_paired_pilot.ipynb) | Historical paired-subset pilot, separate from official full-cohort results. |

## Kaggle notebooks

| Clear name | Saved version, when recorded |
|---|---|
| [UROP Text + Image - Final Results](https://www.kaggle.com/code/rocky62/urop-text-image-final-results) | 362955511 |
| [UROP Text + Image - Training Part 2](https://www.kaggle.com/code/rocky62/urop-text-image-training-part-2) | 362859423 |
| [UROP Text + Image - Training Epoch 2](https://www.kaggle.com/code/rocky62/urop-text-image-training-epoch-2) | 362761315 |
| [UROP Text + Image - Training Epoch 1](https://www.kaggle.com/code/rocky62/urop-text-image-training-epoch-1) | See notebook version history |
| [UROP Images - Loader Speed Check](https://www.kaggle.com/code/rocky62/urop-images-loader-speed-check) | See notebook version history |
| [UROP Images - Index Speed Check](https://www.kaggle.com/code/rocky62/urop-images-index-speed-check) | See notebook version history |
| [UROP Text + Image - GPU Readiness Check](https://www.kaggle.com/code/rocky62/urop-text-image-gpu-readiness-check) | See notebook version history |
| [UROP Images - Quality Check](https://www.kaggle.com/code/rocky62/urop-images-quality-check) | 362643633 |
| [UROP Text + Image - Old Training Draft](https://www.kaggle.com/code/rocky62/urop-text-image-old-training-draft) | See notebook version history |
| [UROP Text + Image - Engineering Check](https://www.kaggle.com/code/rocky62/urop-text-image-engineering-check) | See notebook version history |
| [UROP Text Only - Final Results](https://www.kaggle.com/code/rocky62/urop-text-only-final-results) | 356721456 |

The text-results notebook has older multimodal pilot history in version 356486031; final text evidence is version 356721456. Renaming does not turn old versions into new experiments. Kaggle dataset names/versions and input mounts are unchanged. Historical launcher strings may mention an old slug: consult the rename ledger and pinned version before any future execution.

[Full old → new ledger](../context/RENAME_LOG.md).
