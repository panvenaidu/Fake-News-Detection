# Task Report — Baseline Architecture Decision Analysis

## Task

Research and decide scientifically credible, reproducible, compute-feasible baselines for Fakeddit text-only, image-only and text+image fake-news detection. Select an initial label setting without training or implementation.

## Status

**Completed — research and decision only.** The 75,995-item verified paired manifest remains the canonical dataset and has not been changed.

## What Was Investigated

- Official Fakeddit documentation, repository and the original Nakamura, Levy and Wang LREC 2020 benchmark.
- The supplied data-centric reference paper: Kuntur et al., *Fake News Detection: It's All in the Data!* (Applied Sciences, 2026; DOI: 10.3390/app16031585).
- Relevant recent evidence, prioritizing primary sources:
  - Stepanova and Ross, *Temporal Generalizability in Multimodal Misinformation Detection* (GenBench/ACL 2023).
  - Tahmasebi et al., *Improving Generalization for Multimodal Fake News Detection* (ICMR 2023).
  - Saha and Kobti, *DeBERTNeXT* (ICCS 2023), as evidence of a heavier DeBERTa + ConvNeXt concatenation alternative.
  - 2025 COLING work using BERT-base with a ViT-base encoder as a stronger, more complex later-family reference.
- Candidate encoder families: BERT/DistilBERT/DeBERTa for text; ResNet-50, ViT, ConvNeXt and CLIP-family encoders for images or joint representations; maximum, concatenation and learned cross-modal fusion.
- Comparability conditions: label granularity, official versus altered/temporal split, subset size, paired-image availability, preprocessing, metric and whether encoders were fine-tuned. Published headline scores were not used as directly comparable targets.

## Decisions

| Requirement | Decision |
|---|---|
| Text-only baseline | Fine-tuned `bert-base-uncased` + linear classifier. |
| Image-only baseline | Fine-tuned ImageNet-pretrained ResNet-50 + linear classifier. |
| Text+image baseline | BERT-base + ResNet-50; project representations to the same width, fuse by element-wise maximum, then classify with a small MLP. |
| Initial task | **6-way** Fakeddit classification. Choose on validation macro-F1; report class-wise metrics and confusion matrix, with accuracy/micro-F1 supplemental. |
| Dataset and inputs | Fixed official split membership within `data/verified_paired_manifest.csv`; use paired image + `clean_title` + selected label only. |

## Why This Is the Baseline Set

- It directly follows the original Fakeddit benchmark family: that paper reported BERT + ResNet-50 with maximum fusion as its best simple multimodal combination, and ResNet-50 as its strongest tested image model.
- The backbones are open, extensively documented and shared across the unimodal and multimodal conditions, yielding controlled modality ablations.
- BERT-base (110M parameters) is much more practical than BERT-large for repeated experiments; ResNet-50 is roughly 26M parameters. The combined backbone is about 136M parameters, practical on T4/A100 cloud hardware with mixed precision and small batches. The M3/MPS is suitable for debugging; the RTX 3050 should use conservative batches/gradient accumulation after its VRAM is confirmed. These are feasibility estimates, not measured runtimes.
- Six-way classification preserves Fakeddit's fine-grained purpose, matches the manifest stratification, and will reveal class-specific weaknesses. It has the same encoder compute as 2-way. The main trade-off is imbalance, which makes macro-F1 and per-class reporting necessary. The 3-way setting is not selected initially because the intermediate class is small and published Fakeddit analysis found it behaved similarly to 2-way.

## Evidence Used

- [Nakamura, Levy and Wang (LREC 2020)](https://aclanthology.org/2020.lrec-1.755/) introduced Fakeddit's 2-, 3- and 6-way labels and reported BERT + ResNet-50 maximum fusion as its strongest simple multimodal combination. Its reported numbers apply to its own paired-sample filtering, preprocessing and split, not this project’s 75,995-item manifest.
- [Fakeddit official repository](https://github.com/entitize/Fakeddit) documents the public data and image-download structure; this project uses only the already-downloaded verified pairs, not the private test data.
- [Stepanova and Ross (GenBench 2023)](https://aclanthology.org/2023.genbench-1.6/) found increasing imbalance at finer Fakeddit granularity, 3-way behavior similar to 2-way, and substantial degradation under temporal out-of-domain evaluation.
- [Tahmasebi et al. (ICMR 2023)](https://doi.org/10.1145/3591106.3592230) showed that standard multimodal fake-news systems can degrade sharply under content manipulations, supporting a later robustness evaluation rather than a claim based only on an in-domain split.
- [Kuntur et al. (Applied Sciences 2026)](https://doi.org/10.3390/app16031585) emphasizes that dataset construction, labels, bias and availability govern generalizability and result comparability.
- [Saha and Kobti (ICCS 2023)](https://doi.org/10.1007/978-3-031-36021-3_36) provides a published heavier DeBERTa-v3 + ConvNeXt-Large concatenation alternative; it was not selected as the starting baseline because it is substantially less compute-efficient.

## Main Limitations and Failure Points to Investigate Later

1. **Temporal/topic/subreddit shift:** Fakeddit's released split is in-domain and labels are distant, subreddit-level assignments; a high score may capture dataset regularities rather than factual verification.
2. **Weak cross-modal reasoning:** maximum fusion combines features but does not explicitly model text–image agreement, contradiction or irrelevant images.
3. **Fine-grained minority classes:** the 6-way task is imbalanced; macro performance and error patterns may differ sharply from accuracy.
4. **Pair availability bias:** the verified image subset excludes 4,005 unavailable/corrupt URL images. It is valid and fixed for paired modelling but may differ from the original manifest.
5. **No external factual evidence:** this scope deliberately does not retrieve claims or use social context, so it detects dataset-associated signals rather than proves truth.

## Emerging Research-Gap Candidates — Not Finalized

1. **Compute-efficient robust fusion:** add a light, explicit text–image consistency mechanism to the BERT+ResNet baseline and test whether it improves temporal/subreddit-shift macro-F1 without adopting a large vision-language backbone.
2. **Shift-aware, fine-grained calibration:** improve reliability for rare 6-way classes under temporal/class-distribution shift, with calibration and per-class robustness rather than only in-split accuracy.
3. **Modality-quality-aware fusion:** make fusion respond to irrelevant, weak or conflicting images so the model can rely on the more informative modality without silently exploiting one modality.

These are evidence-supported candidates, not a final research contribution. They require baseline failure analysis before selection.

## Unresolved Questions

- Exact RTX 3050 VRAM and practical batch size; these must be measured only after approval to implement.
- Whether maximum fusion remains superior to projected concatenation on this exact verified subset; the original result is precedent, not a guaranteed replication.
- Whether a temporal or subreddit-held-out test can be constructed reproducibly from existing manifest metadata without changing the approved initial benchmark; decide after standard baselines.
- The final research contribution and any external-dataset/generalization claim remain open.

## What Was Not Done

- No model implementation, training, inference, hyperparameter search or benchmark run.
- No dataset or image download, no change to the 80K manifest, and no re-sampling.
- No use of private test labels, comments, metadata features or external claim verification.
- No final research gap or final proposed model selected.

## Recommended Next Step

Approve a short, fixed experimental protocol for E002/E003/E004: preprocessing, seed policy, training budget, optimizer/schedule search bounds, checkpoint-selection metric, hardware log fields, and final metrics. Only then implement the three selected baselines and begin with the text-only 6-way run.

## Agent and Date

Codex — 2026-09-08
