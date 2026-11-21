# BERT + DeiT III experiment — complete

## Final result

| Selected checkpoint | Validation accuracy | Held-out test accuracy | Difference | Test rows |
|---|---:|---:|---:|---:|
| Epoch 4 | 90.89698% | 90.72887% | Test is 0.16811 percentage points lower | 59,270 |

Training completed through Epoch 4. The receipt records `stage_complete`, `history_epochs: 4`, and `no_test: true`; Epoch 4 was selected using validation results. One held-out evaluation was run on the frozen checkpoint and passed independent CSV verification. The training process did not read the test split.

- Session receipt SHA-256: `283ed2c28c63d5e2ef92b95519aad1e57d97ad34a7ae8c4c7f1f9a5e5f4b5c78`
- Selected Epoch 4 checkpoint SHA-256: `94eb92621c7dcdf21feb5e7e7117e9c4b3a9fac75f9bf6b9e572024dab3c957a`
- Test prediction CSV SHA-256: `006d2e1fd8ca3336b037d9bed1206a7aeb41df3874072f4afaa4dba8910488cb`

Detailed evidence is in the [post-run audit](POSTRUN_AUDIT.md) and [machine-readable result record](final_results.json).

## Experiment setup

This is a six-class title-plus-image experiment using BERT-base and fine-tuned DeiT III B/16 with maximum fusion. The usable-pair cohort contains 563,601 training, 59,299 validation, and 59,270 test posts. The Epoch 4 validation accuracy was 90.89698%; the independently verified held-out test accuracy was 90.72887%. Test performance did not select the checkpoint.

## Historical handoff and preparation notes

The dated notes below preserve the earlier state and are superseded by the final result above.

## Session 1 readback (18 November)

Kaggle version 370762240 finished after approximately 6h45m. Its displayed receipt reports `stage_complete`, two history epochs, and a recovery cursor at epoch 3, with no test. Two recovery-generation files are visible in the output. The epoch 2 metrics file reports validation accuracy 0.8995429939796624 and macro-F1 0.8459234326022042 on 59,299 pairs; epoch 2 is the current best, with selected weights SHA-256 `1165e2e850a48334701afc6416d974748fb1b360f2a16efe79e08b8d8a605026`. The log reports session receipt SHA-256 `cb845905ff96584520e8776cb81ba23437dd7854687338d49ccfed4787768f83`. These are Kaggle UI readbacks, not yet independent local hash verification.

The refreshed quota showed 27:10 of 30 hours used. A bounded continuation notebook was prepared but not submitted. Training, final validation selection, frozen test evaluation and independent readback remain incomplete.

On 18 November, the approved continuation was submitted as private Kaggle version 370849309. The startup log registered the expected predecessor receipt and preflight hashes, with `no_test: true`, and began caching image archives. The trainer's recovery load and subsequent progress have not yet been confirmed. The segment is bounded to 6,000 seconds with a clean-stop margin because only 2h50m of GPU quota remained at launch.

Continuation version 370849309 completed successfully after 4,878.2 seconds. Its receipt reports a clean stop in epoch 3, training cursor 204,992, with two completed validation epochs and no test. The saved generation is `ebe4417d7cba4ca1a4cdbbe00b97b569.pt`, SHA-256 `b9dfce8e3aa4facf2d7f5499745580910128d55447c5badb83e76cc0259b65b4`, and the session receipt SHA-256 is `8bbd69f7e80b0ae6d002b1c418147356698ad11618da3493c3ec0a68104338ba`. These are Kaggle readbacks; the receipt reports no recovery fallback errors. Epoch 2 remains the current best; no later validation has completed.

After that segment Kaggle displayed 28:31 / 30 GPU hours used (1h29m remaining). The session builder reserves one hour for recovery and safety; the remaining allowance permits at most 29 minutes of a new session, including roughly 8 minutes of archive staging plus checkpoint load/save. A new run was therefore not started pending enough quota for a useful segment. The latest receipt above is the required predecessor for continuation.

## 20 November handoff check

The active draft is the user's `panvee58/notebook258a666564` notebook (identifier ending `6564`), and its Kaggle session is off. The approved paired-manifest dataset is now attached: the Add Input search returned no dataset by title/slug, but searching the exact dataset URL `https://www.kaggle.com/datasets/rocky62/urop-faculty-usable-packed-input-v3` returned the private dataset and it was added. The Rocky62 dataset page lists the `Panvee 58 to 62` group as a collaborator; the Error profile's group page lists Rocky 62 as owner and panvee58 as member. This confirms the correct notebook, dataset, private group share, and account access.

The draft still contains the earlier session-1 receipt (`cb845...`) and placeholder quota value. Do not run that cell. A corrected local continuation notebook is kept at `training/text_plus_image/Cloud/continuation_epoch4_20261120_run1/training.ipynb`; it points to the latest session-2 receipt `8bbd69f7...` and refuses to launch unless live quota covers the measured epoch estimate, setup, and reserve. The local corrected notebook is not yet imported into the Kaggle draft. Kaggle's Settings > Accelerator menu in the `panvee58` profile showed both GPU T4 x2 and TPU disabled; the session remains off. Account settings explicitly say that `panvee58` is not phone-verified and show GPU quota `00:00 / 30 hrs`. Kaggle's current documentation says all GPU accelerators require phone verification. The prior `28:31 / 30 hrs` reading belongs to the separate Rocky62 account and does not establish `panvee58`'s quota or access. Phone verification is the actionable GPU-access prerequisite; the user must complete its phone-number flow in Kaggle.

No full training was started, no held-out test was run, and no result or 89% claim is available. Before resuming, make a GPU option selectable in this profile (or explicitly switch to a GPU-enabled account), import the corrected local handoff, refresh the live quota, and verify that the dataset and pinned input hashes pass before starting a bounded continuation. The held-out test remains reserved for one evaluation after validation-based checkpoint selection and freeze.

## 20 November local handoff verification

The corrected one-cell Kaggle continuation notebook parses as Python and references the expected session-2 predecessor receipt, official manifest, BERT weights, DeiT checkpoint, and passed T4 preflight hashes. The model, trainer, frozen evaluator, paired prediction verifier, and shared CSV verifier also parse successfully. These are local static checks only: they do not show that Kaggle imported or executed the handoff or that current inputs hash-match in the cloud. The live Kaggle draft was rechecked and still shows the stale session-1 cell; the GPU accelerator remains disabled, the session remains off, and no test ran. Kaggle account settings showed phone verification incomplete and `00:00 / 30 hrs` GPU quota for `panvee58`.

## 20 November `panvee58` draft UI check

The user-confirmed draft URL is `/code/panvee58/notebook258a666564/edit` (suffix `6564`), and Kaggle shows its session off. The source cell is still the stale session-1 continuation (`cb845...`, quota placeholder `0.01`), so it must not be run. The notebook import panel opened but the local file chooser did not; no notebook file was selected or imported. On Kaggle Settings for `panvee58`, the page still says the account is not verified, offers `Phone verify`, and reports GPU quota `00:00 / 30 hrs`. Thus there is no eligible accelerator or usable GPU quota to begin the next bounded segment. No run was started, no dataset was removed, and the old `6567` draft was not deleted. The account owner needs to complete Kaggle phone verification directly, then recheck GPU eligibility/quota. Once available, import `training/text_plus_image/Cloud/continuation_epoch4_20261120_run1/training.ipynb` into `6564`, confirm the attached dataset and exact pinned inputs, and only then run the guarded continuation. The held-out test remains untouched.

## 21 November revalidation

The current `panvee58` account settings were reopened and still report phone verification incomplete and `00:00 / 30 hrs` GPU. The `6564` notebook is still open with its stale session-1 continuation and no execution. The corrected local notebook exists (41,516 bytes, one code cell), contains the current session-2 receipt and quota guard, and does not contain the session-1 receipt. It has not been uploaded because the Kaggle import panel's Browse Files control does not open a file chooser through the available browser interface. The actual training gate is still unmet: this account has neither GPU eligibility nor quota. No cloud training or held-out evaluation occurred.

## 20 November offline-loading failure and repair

The `panvee58/notebook258a666564` attempt copied the prior recovery output and cached the approved image archives, but it did not complete an epoch. Its trainer failed when Transformers tried to resolve `google-bert/bert-base-uncased` from Hugging Face while Kaggle Internet was off. The traceback ends in `LocalEntryNotFoundError` / `OSError`; no validation or test evaluation occurred. The Kaggle notebook also reported `Failed to save draft`, so that attempt and its output are preserved as failed evidence.

The trainer and GPU preflight now load a hash-pinned BERT config and tokenizer from `model/text_plus_image/bert_deit3/bert-base-assets/` using local-only mode. The retry package embeds and verifies those assets, reruns the real-pair CUDA preflight before training, writes to a separate retry output folder, and prints structured sample/epoch progress. Recovery accepts only the audited offline-loading trainer change plus the three pinned BERT assets; cohort, config, runtime versions, and all shared model/data sources must still match. This retains the prior optimizer/recovery state without changing the experiment settings.

The corrected retry notebook is `training/text_plus_image/Cloud/continuation_epoch4_20261120_retry1/training.ipynb`. It is prepared locally but has not been imported or launched in Kaggle. Internet can remain off for this version. No training progress or new metrics are claimed until Kaggle displays `TRAINING_PROGRESS` / `VALIDATION_EPOCH` output and a clean `TRAINING_SESSION_RECEIPT`.

The corrected retry file was selected in Kaggle's Import Notebook dialog in the existing `6564` draft. Kaggle remained on a `Loading...` spinner, so import/save completion could not be confirmed. No retry training was launched from that state. The original failed run remains the only cloud attempt; the local corrected notebook is intact for a fresh import.
