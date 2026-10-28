# UROP: beginner to architecture — ElevenLabs edition

Narration: ElevenLabs Alice / Multilingual v2, via Composio. Provider character alignment is scaled with the documented pitch-preserving tempo adjustment. Scientific content matches the original verified storyboard.

## 00:00 — What are we building?

Our UROP project studies multimodal fake news classification. Multimodal simply means using more than one kind of input: here, a short post title and its associated image. A model learns patterns from labelled examples and predicts one of six categories. It does not search the internet or independently prove whether a claim is true. This video builds from those basics to the actual architecture, decisions, results, and failure cases.

**What if?** A prediction is not independent fact-checking.

## 00:28 — Understand the six classes

The six labels are True, Satire or Parody, Misleading Content, Imposter Content, False Connection, and Manipulated Content. False Connection concerns a mismatch between text and image. Manipulated Content includes edited images. In Fakeddit, labels largely come from the source community rather than independent verification of every post. A system can therefore learn community style and dataset shortcuts. High benchmark accuracy does not automatically make it a reliable real world fact checker.

**What if?** These are weak benchmark labels, not verified truth certificates.

## 00:59 — The faculty dataset and lineage

We used the faculty linked Fakeddit release with three files: multimodal train, multimodal validate, and multimodal test public. The original files contain six hundred eighty two thousand six hundred sixty one rows. Exactly four hundred ninety one images failed strict decoding and were excluded with approval, before model results were used. The usable counts are on screen. Original files, identities, titles, six labels, and split assignments were preserved. We did not manually create replacement splits.

**What if?** Exactly 491 decode failures excluded with approval; no new splits.

## 01:31 — Train, validate, then test

Training data teaches the model. Validation data compares checkpoints without updating their weights. The held out test is reserved for the final frozen choice. If we repeatedly change a model after seeing its test result, that test stops being an honest final examination. Separate post identities do not guarantee independent images: our audit found cross split byte identical image groups. That is a remaining leakage and comparability risk, not something to hide.

**What if?** Skipping validation or tuning on test makes the reported result misleading.

## 01:58 — Turn titles into model inputs

A computer cannot feed raw words directly into BERT. Its WordPiece tokenizer converts a title into integer token identifiers. An attention mask identifies real tokens and padding. We cap inputs at one hundred twenty eight tokens, then pad each batch. BERT uses attention to relate words to their context. Its special classification token produces a seven hundred sixty eight dimensional representation. Changing tokenization or truncation changes the experiment and must be registered and checked.

**What if?** Removing the mask can make padding affect the representation.

## 02:29 — Prepare images consistently

Images are decoded, converted to red, green, and blue channels, and normalized using the expected ImageNet channel statistics. Training uses a reproducible random resized crop, linked to the seed, epoch, and example identity. Evaluation resizes the shorter side to two hundred thirty two, then center crops to two hundred twenty four pixels. These rules prevent arbitrary evaluation changes. Skipping normalization or using a different crop can shift the input distribution and change predictions.

**What if?** Skipping normalization shifts inputs away from the pretrained model's expectations.

## 02:59 — Two pretrained encoders

The text encoder is BERT base uncased, initialized from our verified selected text only checkpoint. The image encoder is ResNet fifty, initialized with ImageNet version two weights. ResNet uses residual connections to help information and gradients flow through a deep network. We remove its original image classifier and keep two thousand forty eight pooled features. Both encoders and the fusion head are fine tuned. Starting from useful pretrained representations reduces the burden compared with learning everything from random weights.

**What if?** Both encoders were fine-tuned; neither was frozen in this experiment.

## 03:32 — Make the feature sizes compatible

The two encoders produce different sized vectors. Separate learned linear projections map each to five hundred twelve dimensions. Layer normalization helps control feature scale. These projections are learned adapters, not manually defined semantic coordinates. Without matching sizes, elementwise maximum cannot combine the vectors. Removing normalization or changing the projection size would be a different architecture requiring new training and validation. We did not run an ablation proving this size is universally optimal.

**What if?** Without compatible projections, elementwise maximum has a shape mismatch.

## 04:03 — What maximum fusion really does

Maximum fusion compares the two projected values at every position and keeps the larger one. The small example on screen illustrates the operation; the real vectors have five hundred twelve positions. Some positions can come from text and others from the image. This is not voting between class predictions. Addition changes the combined scale. Concatenation creates a larger vector and needs a compatible head. Those are legitimate alternatives, but comparing them requires separately controlled experiments.

**What if?** It does not select one entire modality, or average class probabilities.

## 04:34 — From fused features to six probabilities

The fused vector enters a linear layer with two hundred fifty six outputs, a GELU activation, dropout with probability zero point two, and a final layer producing six scores called logits. GELU adds nonlinearity. Dropout discourages dependence on particular activations during training and is off during evaluation. For training, cross entropy takes the raw logits directly. For reporting predictions, softmax converts logits into six probabilities that sum to one. The largest probability gives the predicted label. The network has about one hundred thirty four million trainable parameters.

**What if?** Dropping a branch changes the model; retrain rather than reuse it blindly.

## 05:10 — How learning changes the weights

Cross entropy penalizes the model when it gives too little probability to the correct training label. Backpropagation calculates how weights contributed to that loss. Adam W updates the parameters, with weight decay for regularization. The learning rates differ: BERT uses one times ten to the minus five, the image encoder one times ten to the minus four, and the head one times ten to the minus three. A warmup and decay scheduler controls their evolution.

**What if?** Without updates, validation is measurement—not training.

## 05:38 — Fit the experiment onto a T4

We used one Tesla T four cloud GPU in Kaggle, even when two devices were allocated. Eight examples fit into each microbatch. Accumulating gradients over four microbatches produces an effective batch of thirty two before an optimizer boundary. Mixed precision saves memory, a gradient scaler helps handle numerical range, and gradient clipping limits extreme updates. These details affect learning and recovery. Changing batch size or the schedule midway would break the controlled continuation.

**What if?** A batch-size change can alter optimization; it is not just a speed switch.

## 06:09 — Four epochs, four validations, one test

One epoch is a complete pass over the training set. Our registered budget was four epochs, each followed by a full validation. The selection rule was highest validation macro F one, then lower loss, then earlier epoch if still tied. An early stopping rule existed, but this run completed all four epochs. Training interruptions were resumed within the same experiment. After validation selection was frozen, we ran one full final test. Independent metric recomputation is not an additional model test.

**What if?** Four epochs are one seed-42 experiment—not four independent replications.

## 06:39 — Which checkpoint won—and why?

Epoch three had the highest validation accuracy, eighty eight point five three four four percent. Epoch four had the highest macro F one, zero point eight two nine three zero three, so epoch four won under the declared rule. Its validation accuracy was slightly lower, and its loss was higher. Better class decisions can coexist with worse confidence on mistakes. We retained that tradeoff rather than changing the rule after seeing results or picking whichever checkpoint looked best on the test.

**What if?** Epoch 4's loss worsened; it did not improve every measure.

## 07:09 — Read the final metrics correctly

Final test accuracy was eighty eight point one four five eight percent, and macro F one was zero point eight two six four one five. Accuracy measures the fraction correct. Micro F one equals accuracy in this exhaustive single label task. Precision asks how many predicted class items were correct. Recall asks how many actual class items were found. F one balances precision and recall. Macro F one weights classes equally; weighted F one uses class frequency. Balanced accuracy averages class recalls. Cross entropy also evaluates confidence. Imposter Content remained the weakest class by test F one. Confusion matrices show which classes were mistaken for each other.

**What if?** Accuracy alone can conceal weaker minority classes.

## 07:51 — What does the paper comparison prove?

The matching paper reference is six way BERT plus ResNet fifty with maximum fusion. Our test accuracy is two point two six five eight percentage points higher, exceeding the numerical one point aspiration. However, the paper used a different feature and training pipeline. Our available image cohort excludes decoding failures, and we used extra text warm start training. One seed, cross split image duplication, and the unresolved paper versus release row count difference limit the claim. Comparable paper F one and loss values were not reported.

**What if?** +2.2658 test percentage points is a numerical comparison, not controlled superiority.

## 08:25 — Why preparation and recovery mattered

Preparation took time because image decoding, storage, transfers, and slow loading had to be resolved before trustworthy training. We preserved original image bytes, verified packed inputs, and used a cached archive reader on the cloud runtime. Recovery saved not just weights, but optimizer, scheduler, scaler, random states, sample cursor, crop rules, and selection history. A spinner or old notebook output is not proof of activity. Fresh counters, timestamps, saved outputs, checksums, and independent prediction checks establish what actually completed.

**What if?** Weights alone cannot reproduce the exact interrupted training trajectory.

## 08:58 — Defend the design—and know what is next

Why these models? They give a recognizable paper aligned baseline, useful pretrained features, and a feasible T four implementation. We did not prove they beat every newer alternative. CLIP, vision transformers, and newer text encoders are possible future studies, not completed experiments. Removing images, changing fusion, or freezing an encoder requires retraining and validation. Skipping the held out test removes our final performance check. Next is the image only baseline, followed by controlled ablations and repeated seeds if approved. You now have the pipeline, its rationale, its evidence, and its limits.

**What if?** Use a new registered experiment for newer models, ablations or different data.