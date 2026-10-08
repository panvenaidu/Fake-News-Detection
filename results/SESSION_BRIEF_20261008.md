# UROP session briefing — 8 October 2026

Today's outcome: official six-way BERT has five completed training/validation epochs but no final test. A separate BERT+ResNet-50 multimodal pilot completed three GPU epochs, validation and final testing. ModernBERT has not trained. No GPU training job is currently running.

## Dataset and classification

The faculty's Fakeddit multimodal release was used unchanged for full-cohort text: 564,000 train / 59,342 validation / 59,319 test = 682,661 rows. Files: multimodal_train.tsv, multimodal_validate.tsv, multimodal_test_public.tsv in data/official_multimodal_v2/. Official split membership, file hashes and six-way labels are preserved; clean_title is the text input.

The multimodal engineering pilot used 2,000 train / 300 validation / 300 test, drawn within the original splits from the 75,995 locally available paired images. All those IDs, titles and labels were rechecked against the faculty's official TSVs. No unrelated Kaggle dataset was used. Kaggle is our compute/storage platform. The pilot is not the whole official dataset.

Six classes: True; Satire/Parody; Misleading Content; Imposter Content; False Connection; Manipulated Content. No new two-way or three-way model was trained today.

## Models and number of trainings

- Today: one official BERT-base text run (five epochs validated, selected epoch4, interrupted before final test); one BERT-base+ResNet-50 maximum-fusion pilot (three epochs, selected epoch3, complete).
- Eight epoch-validation checks and one final test today. Epochs are passes through the training data, not independent model runs.
- Project total: four documented runs with actual training: two earlier BERT subset runs, today's official BERT run, and the multimodal pilot. Three are completed at their own scope; the official BERT run is incomplete. There are three documented final-test evaluations across those runs, only one today.
- Startup failures, cancelled allocation attempts, status-monitor executions and CPU smoke checks are not additional trained models. Kaggle v1 failed before its first optimizer step; v2 completed.
- ModernBERT-base is implemented/prepared but not trained. Image-only, CLIP and HGAT have no completed training results. ResNet-50 is the implemented image backbone; not ResNet-55. Newly implemented for our project does not mean the latest published model: BERT/ResNet are established baselines, and ModernBERT is the newer planned text comparison.

## Results: all values below expressed as percentages

| Model / scope | Validation accuracy | Validation Macro-F1 | Test accuracy | Test Macro-F1 |
|---|---:|---:|---:|---:|
| Earlier BERT subset, preliminary scheduler issue | 78.20 | 70.12 | 77.90 | 68.91 |
| Earlier BERT subset, clean | 78.01 | 70.22 | 78.10 | 69.66 |
| Paper six-way BERT text | 76.96 | Not reported in Table4 | 76.77 | Not reported in Table4 |
| Our official BERT, selected epoch4 | 82.74 | 77.87 | Pending | Pending |
| Paper six-way BERT+ResNet50 maximum fusion | 86.00 | Not reported in Table4 | 85.88 | Not reported in Table4 |
| Our BERT+ResNet50 engineering pilot | 79.33 | 59.62 | 74.33 | 55.90 |

Paper source: https://arxiv.org/html/1911.03854v2#S3.T4. The paper's 86.54/86.44 text scores are binary, not six-way. Our text uses BERT-base fine-tuning, whereas the paper describes BERT-large feature extraction; the released row count also differs slightly. Earlier subset results are reconstructed notebook evidence, as labelled in their JSON artifacts, not full official benchmark results.

Our selected text validation accuracy is 5.78 percentage points above the paper, exceeding the validation +1pp target. A confirmed overall/test improvement is not established: six-way text test target is at least77.77%, still pending. For the multimodal paper test, +1pp means86.88%; this small pilot has not achieved that target and its different cohort prevents a direct benchmark claim. New text validation is numerically higher than the previous clean result, but the cohorts differ. Macro-F1 gives equal weight to the six classes; the pilot missed all six imposter test samples (F1=0).

## Engineering and documentation work

Reviewed relevant project context, decisions, experiment logs, model status, configs, source, saved training evidence and literature survey. Preserved historical results. Verified official splits/hashes and all available image-to-official-row joins. Implemented/train-tested BERT+ResNet maximum fusion, RGB preprocessing, GPU mixed precision, validation-based checkpoint selection, final-test export and checkpoint recovery. Fixed the pilot image staging failure without changing its scientific source or data membership. Retrieved the original five-epoch BERT history and multimodal original metrics, class reports, confusion matrices and GPU environment; recalculated aggregate metrics from both confusion matrices and matched the saved values. Prepared a BERT recovery integrity checker and separate Kaggle recovery notebook; these are not yet executed.

README, PROJECT_CONTEXT, DECISIONS, EXPERIMENT_LOG, TASK_REPORT, RESUME_HERE, COLAB_WORKLOG and MODEL_STATUS have current updates. Original input files are preserved. Code/notebooks/docs and small result JSON/CSV evidence are pushed to GitHub; large data/images/model weights are excluded.

## GPU and scheduled task

Colab: Tesla T4 for official BERT. Earlier resource panel showed0 purchased compute units; it later refused GPU allocation due to usage limits. This is not a precise measurement of remaining free GPU hours; Colab's free quota/reset is dynamic and unpublished. Its current unit balance was not rechecked in this briefing.

Kaggle: Tesla T4 x2 allocated; training used device0, not distributed across both. Current UI shows9 minutes used /30h, approximately29h51m remaining. Active Events confirms0 active jobs; v2 successful, v1 failed, interactive session cancelled. Pilot saved notebook runtime297.9s (~5min).

Could not verify a working local UROP scheduled-task definition; app view returned no readable status beyond a rendered card. The cause of the Untitled load error is unconfirmed. No replacement task created. A scheduler is optional for follow-ups; manual continuation tomorrow is possible and does not depend on that task.

## Original evidence locations and next step

- Official TSVs: data/official_multimodal_v2/; images: images/; pilot manifests/provenance: data/paired_pilot_20261009/.
- Original five-epoch text history and JSON evidence: results/experiments/official_text/OFFICIAL-6W-TEXT-v2_seed42_20261008T095827Z/bert-base/.
- Original synced multimodal result, history, environment, class reports and confusion matrices: results/experiments/multimodal/MM-PILOT-6W-v1_seed42_20261009/.
- Original BERT weights/recovery (also locally recovered and integrity-verified): https://drive.google.com/drive/u/0/folders/15K7CqdsqrZVEdJH1rGNFhlnswNCdMD1j. Checkpoint ZIP is now under data/cloud_recovery/ and verified at epoch5 batch15000; no GPU recovery job launched.
- Multimodal weights/checkpoints and prediction CSVs: private Kaggle saved version2 https://www.kaggle.com/code/rocky62/urop-official-six-way-text-recovery?scriptVersionId=356486031. Complete300-row validation and300-row test prediction CSVs are now synced locally and verified. Weights remain in the private Kaggle output.
- GitHub: https://github.com/panvenaidu/Fake-News-Detection. Completed-pilot milestone d522e96 verified on remote main.

First finish original BERT recovery and final test. Then train ModernBERT on the same official protocol. Expand multimodal data with matched text/image controls and address rare-class coverage, using validation for tuning. Further improvement is possible but +1pp test improvement cannot be guaranteed.
