# UROP companion: questions you should be able to answer

This accompanies the 18-chapter video. Results refer to the verified single-seed six-way multimodal experiment, not untested alternatives. A counterfactual below is an engineering expectation unless a measured result is explicitly cited.

## Beginner

**What does the project do?** It predicts one Fakeddit benchmark label from a title and image. It does not retrieve external evidence or certify factual truth. Source-community weak labels, ambiguous categories and dataset shortcuts constrain real-world claims.

**Why two modalities?** Text supplies context and claims; images supply visual content. A mismatch can matter for False Connection. Whether a particular fusion model actually uses complementary information requires controlled ablations; an accuracy gain alone does not establish that mechanism.

**Was the previous 75,995-pair dataset invented?** It was historical Fakeddit subset work, with different filtering/split decisions. Keep its results as historical experiments rather than direct official-benchmark comparisons. The current run uses the faculty-linked three TSVs and the explicitly approved usable-image cohort.

**What was removed?** Exactly 491 strict image-decoding failures: 489 False Connection and two Satire/Parody examples. Approval preserved original TSVs, IDs, labels and official split assignments. No failures were dropped because their predictions looked difficult. The exclusions still create a class-skewed comparability limitation.

**What is complete?** Text-only and text+image baselines are complete. Image-only scientific training remains pending. Four multimodal epochs are one seed-42 experiment, not four independent repetitions.

## Architecture

**What is an encoder?** A function that turns an input into learned numerical features. BERT-base-uncased supplies a 768-component CLS vector. ResNet-50, with its original classifier removed, supplies 2,048 pooled components.

**What happens inside BERT?** BERT-base has 12 transformer blocks, 12 attention heads and hidden width 768. Token, position and segment embeddings feed repeated attention/feed-forward blocks. Our single-title input supplies token IDs and an attention mask, capped at 128 tokens. CLS is a learned representation, not a literal truth score.

**What does ResNet-50 mean?** The standard architecture uses a convolutional stem and four bottleneck stages with 3, 4, 6 and 3 blocks, followed by global pooling. Residual additions give information/gradients shorter paths. These intentional internal skip connections are different from skipping validation or omitting a project stage. This experiment uses ResNet-50, not ResNet-55.

**Why these initial weights?** Text starts from the verified selected text-only epoch-4 model; vision starts from ImageNet1K V2. Both encoders are subsequently fine-tuned. This adds prior training compute and is a reason our setup is not an exact paper reproduction.

**Why project to 512?** Text and image vectors have different widths. Separate Linear→LayerNorm modules yield equal-sized 512-vectors for elementwise fusion. This is the registered design; no completed ablation establishes that 512 is universally best.

**What exactly is max fusion?** At coordinate j, z[j]=max(text_projection[j], image_projection[j]). Different coordinates may come from different modalities. It does not choose one whole branch or average class probabilities. Projections learn a useful shared feature space; coordinates are not manually named semantic concepts.

**What follows fusion?** Linear(512,256) → GELU → Dropout(0.2) → Linear(256,6). The six outputs are logits. Training cross-entropy takes logits directly. Softmax is applied to export six probabilities; argmax gives the predicted class. Dropout is disabled during evaluation.

**What if I remove a projection?** The 768- and 2,048-vectors cannot be combined elementwise as-is. A new shape-compatible design must be trained and validated. Removing normalization can change feature scaling; its precise performance effect is not measured here.

**What if I use concatenation, addition, CLIP or a vision transformer?** Those are viable new experiments, not drop-in claims of improvement. Concatenating two 512-vectors gives width 1,024 and changes the head. Register architecture/budget/cohort, select on validation and protect test use. We did not evaluate these alternatives in the completed run.

**What if I remove an encoder or freeze it?** You change capacity, gradients and inputs. Train/validate that new baseline rather than trusting the old fusion head. An image-only baseline and matched-cohort ablations will help separate modality effects.

## Training and evaluation

**What does effective batch 32 mean?** Microbatch eight × four accumulation steps. The frozen implementation scales each microbatch contribution by its actual size within the accumulation group; the final partial group uses its actual size. Changing accumulation or batch size can alter optimization.

**What were the other settings?** AdamW; BERT LR 1e-5, image LR 1e-4, head LR 1e-3; warmup fraction 0.1; gradient clipping 1; FP16 autocast plus scaler. Four epochs contain 70,452 optimizer boundaries: 70,422 successful updates and 30 AMP skips. The scheduler follows successful updates. Same contract was preserved across continuations.

**How were images transformed?** RGB; stable seed/epoch/ID-based random resized crop during training (area range 0.8–1.0, aspect ratio 0.75–4/3), resized to 224. Validation/test resize the short edge to 232 and center-crop to 224. ImageNet normalization is applied. Changes can shift inputs; they must not be hidden during comparisons.

**Why validation and test?** Validation selects the checkpoint. The held-out test estimates performance of that frozen choice. Tuning after reading test performance contaminates its role. We ran four full validations on the same 59,299 IDs and one full 59,270-ID test. Independent CSV recomputation does not run the model again.

**Why epoch 4 if epoch 3 had higher accuracy?** The predeclared primary metric was validation Macro-F1, then lower loss, then earlier epoch. Epoch 4 Macro-F1 0.829303 beat epoch 3's 0.827924. Epoch 3 accuracy 88.5344% slightly exceeded epoch 4's 88.5074%. We did not change the rule after testing.

**Why did loss worsen?** Cross-entropy uses confidence, whereas accuracy uses only the winning class. More confident mistakes can worsen loss despite improved aggregate decisions. That is a plausible explanation, not a measured calibration diagnosis. Epoch-4 validation loss was 0.694795 versus 0.587545 at epoch 3.

**What do precision, recall and F1 mean?** Precision: how many predictions for a class were correct. Recall: how many actual class examples were found. F1 is their harmonic mean. Macro-F1 weights classes equally; weighted-F1 weights by support; micro-F1 equals accuracy for this exhaustive single-label task. Balanced accuracy averages class recalls.

**What is still weak?** Imposter Content had test F1 0.662188 and recall 0.563725. False Connection F1 was 0.955496. Overall accuracy can hide differences in class support and difficulty. Inspect the per-class reports and confusion matrices rather than quoting accuracy alone.

## Systems and scientific judgment

**Why did preparation take so long?** Recorded stages included strict image decoding, failed/slow cloud preparation and transfers, input layout and loader bottlenecks, and recovery verification. Lossless packed input and a cached reader enabled the accepted run. Fresh timestamps and counters distinguish activity from stale UI. Do not treat every old failure hypothesis as a confirmed root cause; consult the chronological project logs for specifics.

**Why are weights alone insufficient for exact recovery?** Optimization depends on momentum/variance state, learning-rate position, AMP scaler, RNG states, sample order/cursor, deterministic crops, BatchNorm buffers and selection history. Losing those can alter the resumed trajectory even when weights load successfully.

**How do we trust the result?** Frozen source/config/data hashes, strict joins and IDs, full prediction exports, finite normalized probabilities, gold/prediction consistency, per-row cross-entropy, independently recomputed metrics/class reports/confusions, selected-weight reload/logit checks, archive CRCs and verified remote documentation backup.

**Did we beat the paper?** Numerically: selected validation 88.5074% versus 86.00%; test 88.1458% versus 85.88%, a +2.2658-point test difference. This meets the numerical +1-point aspiration. Different feature/fine-tuning pipelines, extra text warm-start training, single seed, 491 skewed exclusions, the unresolved 335-row paper/release difference and 3,561 cross-split byte-identical image groups prevent controlled-superiority or state-of-the-art claims. Paper F1/loss are not reported comparably.

**What should we do next?** Register and complete image-only; consider matched-cohort text/image/fusion ablations, independent seeds and uncertainty estimates. Only then consider a separately registered newer model. Do not rerun the finished test just to chase a better number.

## Evidence map

All paths below are relative to the UROP root:

- `results/MM_FINAL_COMPLETION_RECEIPT_20261028.json`: final scientific/backup acceptance.
- `results/MM_FINAL_SAVED_VERIFIED_20261028.json`: independent validation/test/recovery checks and hashes.
- `results/MULTIMODAL_FINAL_REPORT_20261028.md`: aggregate/per-class results and limitations.
- `results/experiments/multimodal/OFFICIAL-6W-MM-USABLE-v2_seed42_20261027/final_362955511/`: four-epoch history, metrics, frozen selection, class reports and raw/normalized confusion matrices.
- `configs/multimodal_usable_6way_v2.json`: registered settings.
- `scripts/train_usable_multimodal_v2.py`: model, preprocessing, actual loops and optimizer groups.
- `scripts/multimodal_recovery_v1.py`: crop/order/RNG/generation rules.
- `context/DECISIONS.md`, `context/EXPERIMENT_LOG.md`, `collab/COLAB_WORKLOG.md`, `work_logs/TROUBLESHOOTING.md`: historical decisions/failures; current receipts supersede stale statuses.
- Faculty dataset: https://drive.google.com/drive/folders/1DuH0YaEox08ZwzZDpRMOaFpMCeRyxiEF
- Paper Tables 4–6: https://arxiv.org/html/1911.03854v2
