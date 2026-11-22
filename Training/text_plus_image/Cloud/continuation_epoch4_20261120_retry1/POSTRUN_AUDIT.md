# UROP BERT-DeiT3 Epoch 4 Post-Run Audit

Audit date: 2026-11-21 (Asia/Kolkata)  
Training Kaggle notebook: `panvee58/notebook258a666564`, committed version `371637230`  
Held-out Kaggle notebook: `panvee58/urop-bert-deit3-frozen-held-out-evaluation`, committed version `372039958`

## Outcome

- Training commit completed successfully on GPU T4 x2. The continuation resumed from receipt `8bbd69f7e80b0ae6d002b1c418147356698ad11618da3493c3ec0a68104338ba`, reached Epoch 4, and stopped with `state=stage_complete`, `history_epochs=4`, `no_test=true`.
- Epoch 4 is the validation-selected checkpoint. Its validation accuracy was **90.89698%**, higher than Epochs 1–3.
- The selection was frozen before the held-out evaluation (`state=frozen_before_test`, selected epoch 4). Exactly one final committed evaluation wrote `test_start.json`; two earlier evaluation attempts stopped before that file and before reading the test split.
- Held-out evaluation completed and its independent CSV verification passed. Test accuracy was **90.72887%**, which is **0.16811 percentage points lower** than Epoch 4 validation accuracy.

## Training log evidence

Full training log is preserved at `saved_output/execution_logs.txt`.

- `OFFLINE_LOCAL_ASSET_PREFLIGHT_START` at log entry 9; the associated preflight output reports `status=passed`, device `cuda`, GPU `Tesla T4`, paired images true, and the packed input index hash below. The offline asset preflight passed without Hugging Face/network errors.
- `TRAINING_SESSION_REGISTERED` at entry 210: `session_seconds=27000`, `stop_after_epoch=4`, `no_test=true`, previous receipt hash `8bbd69f7...`, preflight hash `ab25c6a3...`.
- `TRAINING_PROGRESS` advanced beyond the previous cursor 204,992, through the remainder of Epoch 3 and all of Epoch 4. Epoch 4 reached `samples_seen=563601/563601` (entry 1444).
- `VALIDATION_EPOCH` entries were recorded for Epochs 3 and 4; Epoch 4 accuracy was `0.9089697971297999` (entry 1467).
- `TRAINING_SESSION_RECEIPT` at entry 1469: `stage_complete`, `history_epochs=4`, `no_test=true`, `fallback_errors=[]`; selected Epoch 4 weights and validation predictions are identified in the receipt.
- `SESSION_RECEIPT_SHA256` at entry 1470: `283ed2c28c63d5e2ef92b95519aad1e57d97ad34a7ae8c4c7f1f9a5e5f4b5c78`.

## Validation results

| Epoch | Accuracy | Macro-F1 | Loss | Samples |
|---:|---:|---:|---:|---:|
| 1 | 89.09088% | 0.84145177 | 0.41801648 | 59,299 |
| 2 | 89.95430% | 0.84592343 | 0.47298824 | 59,299 |
| 3 | 90.37421% | 0.85823784 | 0.59570781 | 59,299 |
| 4 | 90.89698% | 0.86298685 | 0.67159676 | 59,299 |

Epoch 4 improved accuracy by 0.52277 percentage points over Epoch 3, 0.94268 points over Epoch 2, and 1.80610 points over Epoch 1.

## Kaggle saved-output checks

Verified in the committed training version's Output view:

- `urop_bert_deit3_retry_preflight.json`: `status=passed`.
- `session_receipt.json`, `training_runtime_complete.json`, `history.json` (four epochs), and `resume_protocol_migration.json` are present.
- Epoch 3 and Epoch 4 validation metric and prediction files are present; Epoch 4 is best.
- Selected epoch checkpoints 1–4 are present; `selected_epoch4_7dd15875227c43fcbd41d2d9929045ef.pt` is selected.
- `recovery/` contains `87000f8047f74a7b8a0e178f68860553.pt`, `e28048072ad946a7916b9e79c06aa4eb.pt`, and `generations.json`. The receipt records the latter checkpoint loaded with SHA-256 `474319c128c1b149e4deed1c5cad69a5a6f34ff2abc2ed0cdf429ec98e08042d` and no fallback errors.
- No `trainer.lock` appears in the saved output tree or the local saved-output copy.

## Frozen checkpoint and held-out verification

The evaluation output's `final_selection_frozen.json` records `state=frozen_before_test`, `training_complete=true`, selected epoch 4, and the same selected checkpoint hash as the training receipt. The final output's `final_evaluation_complete.json` records `passed_independent_csv_verification` on the `test` split.

- Test accuracy / micro-F1: `0.9072886789269445` (90.72886789%).
- Macro-F1: `0.8616054812645727`; weighted-F1: `0.9066403743848791`; balanced accuracy: `0.8448200264732101`; loss: `0.6917202113664017`.
- Test rows: 59,270.
- Independent verification: exact ordered IDs and labels; probability, cross-entropy, and confusion checks passed.
- Test prediction CSV SHA-256: `006d2e1fd8ca3336b037d9bed1206a7aeb41df3874072f4afaa4dba8910488cb`.
- Evaluation used Tesla T4 and the frozen Epoch 4 checkpoint hash below.

## Hash record

- Session receipt: `283ed2c28c63d5e2ef92b95519aad1e57d97ad34a7ae8c4c7f1f9a5e5f4b5c78`.
- Selected Epoch 4 weights: `94eb92621c7dcdf21feb5e7e7117e9c4b3a9fac75f9bf6b9e572024dab3c957a`.
- Epoch 4 validation predictions: `f9cfe709c19f7abd0823ad5347c38828ff1bef72addda2533f83ff1cad803850`.
- Resume protocol: `c4c286ba5dd22bb1d2581a6099fdc7bc0bf81b6d667bdcff3c215f50b5258be5`.
- Offline preflight: `ab25c6a3fb55607efa9de7c520356413e1e803bedfcfca72465e9b99775909e6`.
- Model source (`model.py`): `61dd410a4df6a87b52478ce3904338ddc463f058768711b7ce2ae2fdc36ac4b8`.
- Training source (`train.py`): `8724f44536c03957739dc28d409eb76e47a1478dd85b641bafb5e0fae5f535e6`.
- Config: `c3c28325dc780511f18f79ea699f920ddb234fd575a73d33d73b8237b79b50b1`.
- Tokenizer JSON: `d241a60d5e8f04cc1b2b3e9ef7a4921b27bf526d9f6050ab90f9267a1f9e5c66`.
- Tokenizer config: `e1c2a61a99bda00f6c55303a210b30e2f92dcf8b555e215812e2eb583e177ffd`.
- Packed index: `fc8dc03a4f773da5762891c8392375add5fb8087251b527f3b37a880308e6018`.
- Manifest: `96c84e9453401cc4a24999c41cdbeb182dafd08771383cf1c75feea9c3001caf`.
- Coverage: `afe8c723f91fe74f791908e0c16fab94d919af64c7cb7c9b5a37e676361d95e5`.
- Cohort registration: `3fe0b622958a1eee6732789d4f7acf6b450c0e3bda87312e5cbb6500fb405ce5`.
- Excluded IDs: `e5b32e3dc100460da857da499455c885f522b73059304233eb94b9b7d90fc065`.
- Extraction report: `262a40e9e04629cda8c13388478a112016ba17ef42ed2d423bc517dc8911ebe0`.
- Evaluation test prediction CSV: `006d2e1fd8ca3336b037d9bed1206a7aeb41df3874072f4afaa4dba8910488cb`.

## Independent local hash check

Local files under this run's `saved_output/urop_bert_deit3_training_retry1/` were hashed with SHA-256:

- `session_receipt.json`: `283ed2c28c63d5e2ef92b95519aad1e57d97ad34a7ae8c4c7f1f9a5e5f4b5c78` (matches the exact `SESSION_RECEIPT_SHA256` in Kaggle logs).
- `selected_epoch4_7dd15875227c43fcbd41d2d9929045ef.pt`: `94eb92621c7dcdf21feb5e7e7117e9c4b3a9fac75f9bf6b9e572024dab3c957a` (matches receipt and frozen-selection record).
- `history.json`: `e7ad92efb80b2f2bfd89a130d7687436f0648f03ac8b2a1a7fb85f56d9773080`.
- `validation_epoch4_metrics.json`: `96fed9339a4fbcb4691f20bcdd767b0c4d7647a378dda27d2134c79f52b6f414`.

The local mirror contains the execution log, receipt, history, protocol migration, Epoch 4 metrics, and selected Epoch 4 checkpoint. It does not yet contain every Kaggle output artifact (for example, validation predictions for every epoch and the evaluation CSVs); those files were verified in Kaggle's saved-output viewer. The notebook's bulk-output control previously led to a browser-blocked page, while per-file controls opened inline JSON pages rather than writing files. Therefore this report does not claim that a complete output-bundle download was completed.
