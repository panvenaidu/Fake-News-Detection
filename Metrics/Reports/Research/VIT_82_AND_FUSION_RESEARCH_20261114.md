# Research plan: 82% image-only ViT accuracy and stronger multimodal fusion

Research completed 14 November 2026. This is a proposed experimental programme, not a new training result. No training was launched for this review.

The recommended first experiment is end-to-end fine-tuning of the existing ViT-B/16, followed by a small comparison of stronger pretrained ViT checkpoints. For text plus image, start with learned gated fusion and retain maximum pooling and concatenation as controls. Add token-level cross-attention only after establishing whether a cheaper gate improves the matched baseline. Reaching 82% image-only accuracy is an empirical target; the reviewed evidence does not guarantee it on our cohort.

## 1. What our evidence actually says

| Completed model | Training regime | Test accuracy | Test macro-F1 |
|---|---|---:|---:|
| ViT-B/16 | Frozen ImageNet1K V1 encoder; trained linear head | 65.6487% | 0.481237 |
| ResNet-50, matched comparison | Frozen ImageNet1K V2 encoder; trained linear head | 71.9082% | 0.527292 |
| ResNet-50, historical baseline | All layers fine-tuned under its original recipe | 81.1557% | 0.661796 |
| BERT + ResNet-50, historical baseline | Both encoders fine-tuned; supervised BERT warm start; maximum fusion | 88.1458% | 0.826415 |

These image-containing runs use 563,601 training / 59,299 validation / 59,270 test posts. The frozen pair shares preprocessing, head training order and selection rules. The historical fine-tuned runs use different recipes and cannot isolate the effect of architecture or fusion. The historical text-only BERT result is 82.3901%, but uses the larger title cohort; it is not a matched unimodal control for the usable-image cohort.

Sources: [verified frozen comparison](/Users/panveenaidu/Downloads/SEM7/UROP/Metrics/Results/IMAGE_ONLY_VIT_RESNET_REPORT.md), [historical image baseline](/Users/panveenaidu/Downloads/SEM7/UROP/Metrics/Results/IMAGE_ONLY_FINAL_REPORT_20261102.md), [historical multimodal baseline](/Users/panveenaidu/Downloads/SEM7/UROP/Metrics/Results/MULTIMODAL_FINAL_REPORT_20261028.md).

The earlier shorthand “ResNet 81%, ViT 71%” is incorrect. About 71.9% belongs to the **frozen ResNet**, while the verified frozen ViT score is about **65.65%**. ViT needs a 16.3513 percentage-point improvement to reach 82%; the target is 0.8443 points above the historical fine-tuned ResNet. The ResNet improvement between regimes is evidence that adaptation deserves investigation, not a forecast of the ViT improvement.

The current multimodal implementation also does **not** concatenate its projected features: `MaximumFusion.forward` applies `torch.maximum` to two 512-dimensional projections. See [actual model](</Users/panveenaidu/Downloads/SEM7/UROP/Model/Text + Image/train_usable_multimodal_v2.py:50>). Maximum fusion, concatenation and learned gates must therefore all appear in the experiment matrix.

Define two separate outcomes:

- **Image-only goal:** one selected ViT predicts six labels from RGB pixels and reaches at least 82% test accuracy on the registered cohort. No headline, metadata, external caption or explicit OCR branch enters this predictor.
- **Multimodal goal:** demonstrate a reproducible gain over matched maximum/concatenation controls, with the historical 88.1458% accuracy / 0.826415 macro-F1 as context. Reaching 82% multimodally would already be below our existing result and would not establish the image-only goal.

## 2. Research method and evidence quality

I inspected local configurations, source and verified reports; used the requested Consensus paper search through its connected Composio integration; and checked original papers, publisher pages and author repositories. Searches covered six-class Fakeddit, image-only ViT, fine-tuning, pretrained ViT families, gating, cross-attention, cross-modal ambiguity and contrastive learning. Consensus's separate native Deep Research endpoint failed, but its connected paper search returned results successfully. This is a targeted research review, not a claim of an exhaustive systematic census or reproduction of the papers.

The requested [autoresearch skill](/Users/panveenaidu/.codex/skills/autoresearch/SKILL.md) is accessible. Its executable workflow targets `karpathy/autoresearch`, language-model `val_bpb`, and five-minute training runs. Those are not our task or evaluation. This plan adapts its hypothesis–experiment–measure–keep/discard discipline; it does not run its LM scripts, alter the evaluation harness, or initiate its indefinite training loop.

| Primary evidence | What it supports | Relevance and limitation |
|---|---|---|
| [Fakeddit, Nakamura et al., 2020](https://aclanthology.org/2020.lrec-1.755/) | Multimodal benchmark with 2/3/6-way labels obtained by distant supervision | Direct task definition. Binary accuracy is not interchangeable with six-class accuracy; labels are not independent fact-checks. |
| [ViT, Dosovitskiy et al., 2021](https://arxiv.org/abs/2010.11929) | Pretraining and transfer of patch-based image transformers | Supports adapting a pretrained ViT, not an 82% prediction on Fakeddit. |
| [DeiT, Touvron et al., 2021](https://proceedings.mlr.press/v139/touvron21a.html) | Data-efficient ViT training and teacher–student distillation | Supports training-recipe and image-teacher experiments. ImageNet results are not Fakeddit results. |
| [DeiT III, 2022](https://arxiv.org/abs/2204.07118) | Improved supervised ViT recipes and transfer, including ImageNet-21k pretraining | Strong candidate checkpoint family, without changing to Swin. |
| [MAE, He et al., 2022](https://openaccess.thecvf.com/content/CVPR2022/html/He_Masked_Autoencoders_Are_Scalable_Vision_Learners_CVPR_2022_paper.html) and [official fine-tuning code](https://github.com/facebookresearch/mae/blob/main/main_finetune.py) | Self-supervised initialization; practical warmup, weight decay, gradient accumulation and layer-wise learning-rate decay | Supports a recipe family. Exact hyperparameters below are our proposals, not validated Fakeddit defaults. |
| [DINOv2, Oquab et al., 2023/2024](https://arxiv.org/abs/2304.07193) | Transferable self-supervised visual representations | Candidate image-only initialization; common base model uses 14-pixel patches. |
| [DINOv3 official repository, 2025](https://github.com/facebookresearch/dinov3) | Released pretrained ViT family including an 86M-parameter ViT-B/16 | Current alternative worth screening. Weight access requires an application/acceptance flow; availability in our account is unverified. Different pretraining data prevents a pure architecture comparison. |
| [Multimodal Fake News Detection, Segura-Bedmar & Alonso-Bartolome, 2022](https://www.mdpi.com/2078-2489/13/6/284) | Six-class Fakeddit multimodal study reporting 87% accuracy | Supports multimodal information's relevance. Its data and protocol differ from ours; do not rank by headline percentages. |
| [TweFuse-W, Saad Eldien et al., 2026, Tables III and VI](https://thesai.org/Downloads/Volume17No1/Paper_86-Interpreting_Multimodal_Fake_News_Detection_Models.pdf) | On its stated official six-class test split: macro-F1 0.838 gated versus 0.820 concatenation; subset ablation 0.854 versus 0.833 | Directly relevant gating evidence. Uses BERTweet + Swin, not our BERT + ViT; subset and full results differ, one fixed seed, exact image membership not independently matched. These are **F1 scores, not accuracy**. |
| [CAFE, Chen et al., WWW 2022](https://doi.org/10.1145/3485447.3511968) | Adaptive use of unimodal and cross-modal information according to ambiguity | Mechanism evidence from Twitter/Weibo, not a six-class Fakeddit performance guarantee. |
| [FND-CLIP, Zhou et al., 2022 preprint / ICME 2023](https://arxiv.org/abs/2205.14304) | CLIP similarity and modality attention alongside unimodal features | Evaluated on Weibo, PolitiFact and GossipCop in the checked preprint. Useful design inspiration, not direct target evidence. |
| [MMFN, Zhou et al., ICMR 2023](https://arxiv.org/abs/2304.00827) | Token-level fusion plus coarse CLIP information and unimodal branches | Supports testing local interactions separately from global pooled features. |
| [MulT, Tsai et al., ACL 2019](https://aclanthology.org/P19-1656/) | Directional cross-modal attention | General fusion method on multimodal language sequences; transfer to Fakeddit is our hypothesis. |
| [Low-rank multimodal fusion, Liu et al., ACL 2018](https://aclanthology.org/P18-1209/) | Efficient multiplicative interactions without a full outer-product tensor | A comparatively small alternative to attention; not direct Fakeddit evidence. |
| [COOLANT, Wang et al., ACM MM 2023](https://arxiv.org/abs/2302.14057) | Contrastive alignment, softened negatives and cross-modal aggregation | Twitter/Weibo experiments. Label-aware treatment of mismatches needs special care here. |
| [Logit adjustment, Menon et al., ICLR 2021](https://arxiv.org/abs/2007.07314) | Learning with imbalanced classes | Supports a controlled minority-class experiment; improving balanced metrics need not improve ordinary accuracy. |
| [CLIP, Radford et al., ICML 2021](https://proceedings.mlr.press/v139/radford21a.html) | Visual representations learned from image–text pairs | Its image encoder can be used without text at inference, but pretraining still used language. Disclose this distinction. |
| [Robustness evaluation, Chen et al., 2022](https://arxiv.org/abs/2206.08788) | Multimodal fake-news detectors can degrade under modality attacks | Supports corruption/missing-modality checks rather than assuming fusion always helps. |

Two screening decisions matter. First, papers about real-versus-deepfake images address a different target from these six misinformation-related categories. Second, [RoViT-Detect, 2026](https://link.springer.com/article/10.1007/s10791-026-10281-z) reports 85.14% on Fakeddit but describes a text-dominant Fakeddit setting and a two-logit classifier. That is not evidence for 82% image-only six-class performance. Recent high scores without verified label settings, image availability and split membership were not used to forecast gains.

I did not establish a published result with the same six-class labels, our exact usable-image cohort, and a verified image-only ViT protocol achieving 82%. This is an evidence gap, not proof that the target is impossible.

## 3. Diagnose before spending the training budget

The completed ViT never updated its encoder. Its validation macro-F1 peaked at epoch 2 and declined slightly in epochs 3–4. This does not justify simply training the same cached-feature head much longer. The low-dimensional class boundary and the visual representation both deserve inspection.

The full-test Imposter recall was only 0.001634 for frozen ViT. Use this historical observation to require per-class reporting; inspect **training and validation examples** to design interventions. Do not inspect test mistakes to choose crops, losses or model changes.

Before the pilot:

1. Audit a fixed, stratified sample of training/validation images for caption truncation, screenshots, aspect ratio, decoding, and label ambiguity. Verify class mapping against the registered manifest. Keep labels and exclusions unchanged.
2. Compare training and validation learning curves. Low scores on both suggest representation/optimization problems; a widening gap suggests overfitting or a distribution issue. Verify encoder gradients and actual parameter updates after unfreezing.
3. Audit identical-image groups with conflicting labels on training/validation. For a deterministic image-only classifier, repeated identical inputs with different labels cannot all be correct. The within-split diagnostic ceiling is `sum_g max_c count(g,c) / N`, using identical input groups. This is only an empirical bound for that inspected split, not an estimate of real-world Bayes accuracy.
4. Preserve the official cohort. Report the existing exact-byte no-training-overlap test subset separately: 56,052 posts. Exact hashes do not remove near duplicates, event overlap or possible overlap with large external pretraining corpora.

## 4. Image-only experiment recipe

Start with the current TorchVision ViT-B/16 weights to establish continuity. Initialize a six-output classifier and fine-tune all layers. A cached final embedding cannot be reused for end-to-end training: pixels must pass through the encoder on every training step.

| Setting | Proposed starting value | Controlled alternatives |
|---|---|---|
| Input | 224 × 224 RGB, checkpoint-compatible normalization | Preserve aspect ratio with padding versus the existing mild crop; later 336/384 if supported |
| Optimizer | AdamW | Keep fixed while comparing other changes |
| Encoder LR | 3e-5 | 1e-5 and 1e-4 |
| New head LR | 3e-4 | Maintain a 10× ratio in the initial LR screen |
| Weight decay | 0.05 on matrix weights; zero for biases/norm parameters | 0.01 only in a later isolated trial |
| Schedule | 10% warmup, cosine decay | Register schedule in optimizer updates, not approximate wall time |
| Effective batch | 64 | Microbatch 8 or 16 plus accumulation, selected by measured memory |
| Numerics | FP16 AMP with FP32 parameters; gradient clipping 1.0 | Detect skipped updates; advance scheduler only after successful updates |
| Loss | Ordinary six-class cross-entropy | Label smoothing 0.05; separately, mild logit adjustment or class weighting |
| Dropout | 0.2 in head | Adjust only after examining validation overfitting |
| Layer LR decay | None in initial continuity run | 0.75 in a later trial, with lower learning rates in earlier blocks |
| Full training cap | Initially register up to 8 epochs if measured quota permits | Extend a later registered run to 12 only if validation curves justify it |
| Early stopping | After at least 4 epochs; patience 3 full validation checks | Best checkpoint selection remains separate from the stopping criterion |

These values are testable starting choices, not a proven optimal combination. Fine-tuning changes several aspects of the frozen recipe; do not attribute the full difference solely to unfreezing without an appropriate ablation.

Use the historical mild random-resized-crop range of 0.8–1.0 as one candidate and a full-frame padded view as another. Inspect whether either removes readable text or manipulation cues. Start without horizontal flips, rotations, CutMix or strong random erasing. MixUp/CutMix helped generic classification recipes, but combining unrelated posts may corrupt the evidence for these labels; evaluate them later as explicit hypotheses.

Promote a pretrained-weight comparison after the continuity run: supervised DeiT III / ImageNet-21k ViT, then a self-supervised ViT candidate. DINOv3-B/16 is an option if weights are accessible; otherwise DINOv2-B/14 or MAE-B/16 provides an alternative. Pin checkpoint, revision, preprocessing and source/license metadata. A better pretrained model winning is a practical result, not proof that architecture alone caused the gain. Swin belongs in the subsequently requested architecture study and should be labeled separately.

Optional later strategies: image-only ResNet-to-ViT distillation using training images, partial unfreezing when memory is tight, or visual prompt tuning if full fine-tuning is unaffordable. Distillation does not guarantee that the student will exceed its teacher. Using a multimodal teacher would change the training-information regime and must be a separate experiment, even if inference remains image-only. Explicit OCR or a headline branch does not satisfy this plan's strict single-ViT baseline.

## 5. Alternatives to concatenation

Concatenation followed by a sufficiently capable MLP can learn interactions; it is not inherently invalid or restricted to equal modality importance. The question is whether another method improves generalization or efficiency under matched conditions.

| Method | How it combines information | Priority / cost |
|---|---|---|
| Elementwise maximum | Keeps the larger projected activation at each feature coordinate | Mandatory existing control |
| Concatenation + MLP | Preserves both vectors and learns a classifier over them | Mandatory simple control |
| Decision-level fusion | Weighted sum of separately calibrated text/image class probabilities | Cheap first control; cannot model detailed word–patch relations |
| Learned gate | Predicts per-post weights for projected text and image vectors | **First proposed replacement**; small additional head |
| Interaction features / low-rank bilinear fusion | Uses feature products/differences or learned multiplicative factors | Next cheap comparison; rank/width requires tuning |
| Token cross-attention | Text tokens attend to ViT image patches, optionally in both directions | Higher cost; appropriate for local text–image relationships |
| CLIP similarity branch | Supplies pretrained text–image compatibility alongside unimodal evidence | Later; additional model/data provenance and inference cost |
| Ambiguity-aware expert routing | Learns when to rely on text, image or joint evidence | Later research extension after simpler controls succeed |

The first gated implementation should project both pooled embeddings to 512 dimensions, normalize them, and use a small `1024 → 128 → 2` MLP with softmax:

```
t = text_projection(BERT_CLS)
v = image_projection(ViT_CLS)
[a_text, a_image] = softmax(gate(concat(t, v)))
z = a_text * t + a_image * v
logits = classifier(z)  # six outputs
```

The gate itself may concatenate inputs; the **fusion operation** is a learned weighted sum. A later ablation can give the gate `abs(t-v)` and `t*v`, or retain those interaction features in the classifier. Do not combine these additions in the first test, because then the source of an improvement becomes unclear. Log gate distributions and use modality-removal tests; gate values are not calibrated probabilities of factual reliability or causal explanations.

For cross-attention, start with one block, width 256 or 512 and four attention heads. Use actual text token states and the 196 patch states at 224 pixels for ViT-B/16. Keep padding masks, positional information, residual connections and unimodal bypasses. Passing only two pooled CLS vectors into an attention module would not test word–patch correspondence. Add the reverse attention direction only if the first block helps.

Cache pooled features for the cheap fusion screen, not every patch token for the full cohort. Training-image patch states alone would occupy approximately 169.7 GB at FP16 (`563601 × 196 × 768 × 2` bytes), excluding text states, IDs and validation. Stream or compute token states per batch for cross-attention, or use a bounded pilot cache. Higher-resolution trials also require verified positional-embedding handling and model input-size support; changing only the image resize is insufficient for a fixed-size TorchVision ViT.

CLIP similarity is a compatibility feature, not a truth score: a false statement can match its picture, and a true post can use a generic image. Likewise, do not force every observed text–image pair to align through a contrastive objective, or treat every negative label as an image mismatch. If contrastive learning is tested, retain the six-class classification objective, distinguish semantic correspondence from veracity, and validate the auxiliary loss weight.

Keep BERT initialization identical across fusion arms. The historical multimodal run had a supervised BERT warm start; giving that advantage to only one candidate would invalidate the fusion comparison. First compare pooled fusion methods on identical cached frozen features, then retrain the best candidates end-to-end under equal budgets. Frozen rankings are screening results and may change after fine-tuning.

## 6. Ordered execution queue and promotion rules

Run these in stages, not as a Cartesian product of every setting.

| Stage | Trials | Decision produced |
|---|---|---|
| 0: correctness and timing | Real-image train/validation smoke, encoder-gradient check, checkpoint reload, measured memory/throughput | A working full-fine-tuning pipeline and affordable budget |
| 1: ViT continuity | Three LR settings on one fixed 30,000-row stratified training pilot; same seed/order, two complete pilot epochs each, full validation | Reject unstable settings; retain at least two plausible candidates rather than overtrusting short-run rankings |
| 2: representations | Screen one supervised stronger ViT and one accessible self-supervised ViT under the same pilot budget | Select initialization candidates; label all pilot scores as pilots |
| 3: targeted ablations | Full-frame versus crop, then layer LR decay; imbalance intervention only if validation shows persistent rare-class collapse | Identify useful changes individually |
| 4: full cohort | Top two affordable configurations on all 563,601 training rows, with full validation and registered epoch caps | Select architecture/recipe without consulting test results |
| 5: repeatability | Fixed seeds 42, 43, 44 for the selected recipe where budget allows | Mean, variability and per-class stability; no best-seed cherry-picking |
| 6: multimodal screen | Same BERT + ViT features: maximum, concatenation, decision fusion, gate; then product/bilinear or one cross-attention block | Determine whether fusion changes help independently of backbone changes |
| 7: controlled fusion confirmation | ResNet/ViT × maximum/gate (2×2), plus ViT concatenation; matched initialization and end-to-end budgets | Separate visual-backbone gains from fusion gains |
| 8: frozen evaluation | Freeze selected configs/checkpoints and evaluate preregistered final arms | Independently verified test metrics and overlap analysis |

If only one full model fits the budget, finish the image-only branch first. Multimodal work is a distinct follow-on. No stage should consume the time reserved for saving, recovery and verification. If the original ViT remains weak after stable fine-tuning, prioritize better initialization and error analysis before adding a large head or repeated cosmetic hyperparameter changes.

For the **new image-only accuracy objective**, propose checkpoint selection by highest unrounded validation accuracy, then macro-F1, then lower loss, then earlier epoch. This is an explicit change from the completed experiments' macro-F1-first rule and must be registered before the new runs. Report both accuracy and macro-F1 for every candidate; retain the old rule/results intact. For the multimodal scientific comparison, retain macro-F1-first selection and report accuracy as a co-primary outcome, or preregister a different rule before starting all arms. Never switch criteria after seeing test results.

Do not optimize a gate and report its fit on the same validation rows as independent evidence. If decision-fusion weights or calibration are fitted on validation predictions, split validation deterministically into fitting and selection portions, or fit the small module on training data and reserve validation for selection.

## 7. Compute budget, reproducibility and acceptance

The frozen comparison took about 78 minutes, but that included cached forward passes and tiny heads. It does not estimate repeated full-backbone forward/backward training. The old observation of 30 available GPU hours is not a current quota check.

Measure at least a few hundred optimizer steps after warmup, including image loading. With effective batch 64, an epoch has approximately 8,807 optimizer updates. Estimate:

`total seconds = staging + epochs × (updates_per_epoch × measured_seconds_per_update + full_validation_seconds) + test + save/reload/verification`.

Account for gradient accumulation in the measured update time. Inspect GPU quota and disk space immediately before running; reserve roughly 15–20% of the available window for recovery and verification. Treat this percentage as a planning choice. If using both T4 devices, verify distributed data coverage, effective batch, deterministic validation gathering, and the platform's actual quota accounting. An allocation of two devices does not mean the existing script uses both.

Use the verified packed-image reader, strict RGB decoding and cohort registration. Before execution, check the moved trainers' imports and paths; their location under `Model/` is not evidence that all old launch paths still work. Create separate proposed configs/output directories, preserving completed baselines. Save complete optimizer/scheduler/scaler/RNG/sampler state and periodic checkpoints, not just final weights.

Adapted autoresearch log fields: run ID, parent configuration, single hypothesis, changed settings, code/config/checkpoint hashes, split hashes, seed, trainable parameters, effective batch, optimizer updates, validation accuracy/macro-F1/loss, each class recall, peak VRAM, GPU/wall time, failure reason and keep/discard decision. A crashed run gets missing metrics and a failure reason, not an artificial zero score. Store immutable experiment variants; no destructive Git reset or automatic commits are required in this existing checkout.

Five-minute runs are suitable for engineering checks, not for confidently ranking convergence on 563,601 images. Short pilots must compare equal data exposure and be confirmed at full scale. Report compute-efficiency comparisons separately from equal-update comparisons.

The official test set has already been evaluated by earlier models. Avoid further adaptive use; acknowledge its repeated benchmark use. A genuinely prospective untouched external set would strengthen a generalization claim if available, without replacing the official-cohort result. Test only the preregistered final arms/seeds, after validation selection and checkpoint hashes are frozen.

Acceptance means a selected image-only ViT's observed accuracy is at least 82% on the registered full test set, with six-class coverage and independent metric verification. Report seed means/std when replicated, ordinary and group-aware uncertainty where possible, macro-F1, balanced accuracy, per-class precision/recall/F1, confusion matrices, and the exact-byte no-training-overlap subset. For model comparisons use paired prediction differences, paired/bootstrap intervals and, if a significance claim is made, an appropriate paired test such as McNemar; duplicate groups and repeated trials limit naive independence assumptions. An 82% point estimate is not the same claim as a confidence interval entirely above 82%.

Independently recompute from saved predictions: unique/exact IDs, labels, finite six-way probabilities summing to one, argmax agreement, losses and all metrics. Reload selected checkpoints in a fresh process, reproduce fixed validation logits and reopen saved remote outputs. Maintain private data, per-post predictions and weights.

If the best valid run is below 82%, report the measured outcome and remaining hypotheses. Do not cross the threshold by dropping difficult classes, selecting an easier test subset, relabeling samples, using test feedback, or quietly adding text. The research-supported first move remains **full ViT fine-tuning**, followed by **better pretrained ViT weights**; the first multimodal change remains **a small learned gate tested against both maximum fusion and concatenation**.
