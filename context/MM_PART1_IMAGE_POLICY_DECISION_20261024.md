# Image policy decision — approval required before training

Status: PROPOSAL ONLY. No exclusions, replacements, decoder changes or scientific training have been applied.

## Verified problem

The original author archive finished with full compressed SHA256/CRC verification. It contains 682,661 required IDs, but only 682,170 files passed the registered strict Pillow decode/RGB check. The 491 failures comprise 475 unrecognized files, 14 truncated-file errors and two pixel-limit errors. Bounded original-byte inspection confirmed all three inspected files are HTML documents stored as .jpg files (dhgu9qk, c74xt4o, c964b6s), independently checked against their saved byte hashes. This does not establish the formats of all 475 files. See results/MM_PART1_IMAGE_FAILURE_AUDIT_20261024.json and the latest specimen diagnostic receipt.

The approved MM-PART1-v2 plan requires ALL 682,661 images to be usable. HTML documents cannot satisfy that requirement through an image-codec fix. Continuing training therefore requires an explicit scientific protocol decision. Never flip the old source gate to true.

## Recommended practical option: register an available-image cohort

If approved, freeze a NEW versioned cohort defined only by the original archive plus the existing strict decode policy. Exclude exactly the 491 recorded failing IDs; retain all other rows, official split assignments, titles and six-class labels. Preserve the three complete original faculty TSVs and every original archive/shard. Do not fetch alternate URLs, relax decoding, use placeholder images, create new splits or select exclusions using model predictions.

| Split | Original rows | Proposed exclusions | Proposed usable pairs |
|---|---:|---:|---:|
| Train | 564,000 | 399 | 563,601 |
| Validation | 59,342 | 43 | 59,299 |
| Public test | 59,319 | 49 | 59,270 |
| Total | 682,661 | 491 | 682,170 |

The 491 exclusions are 0.071924% of rows, but are class-skewed: 489 False Connection and two Satire/Parody. The two pixel-limit cases are NOT proven corrupt; this option excludes them under the unchanged strict resource policy. A separate bounded large-image decoding policy would require explicit preregistration instead.

Before any scientific launch after approval:

1. Preserve and hash the exact 491-ID manifest privately; verify set equality with the original failed-decode report, official split joins and per-class exclusion counts. Publish only appropriate aggregate evidence.
2. Record the approval and register a new cohort/protocol ID. Update Part 1/2 acceptance counts and all guards, source provenance, schedules and expected prediction IDs consistently. Derive the four-epoch scheduler and warmup counts from the approved effective-batch rule BEFORE seeing validation. Document the existing text-encoder warm start trained on the full official training split.
3. Independently verify all 682,170 source images and their immutable private runtime bytes. Validate lossless packing, input joins, two-generation checkpoint storage, CUDA restoration and measured full-model throughput. No old failed gate bypass.
4. Train/fully validate epochs 1–2 of the same newly registered four-epoch multimodal experiment. Recover safely into Part 2; no final test in Part 1.
5. Complete registered training in Part 2; select by full-validation Macro-F1 and then perform the one frozen final test. Independently recompute all metrics, class reports and confusion matrices. Report changed cohort and class-skewed exclusions beside every paper comparison. A +1 percentage-point target is an aspiration, not a promised or directly identical benchmark result.
6. Preserve completed full-cohort text-only results. For a fair same-cohort modality table, recompute text metrics from its SAVED predictions restricted to the approved usable IDs; label these derived metrics separately and retain the full original results.
7. Verify local/private durable artifacts and remote Git backup at each boundary, using the existing usage reserve and progress rules.

Alternative: keep the all-682,661-pairs requirement and wait for faculty-approved replacement/corrected source or another explicit missing-image policy. This blocks scientific training; do not repeat full extraction or allocate a GPU while waiting.

The current trained multimodal epochs and validations remain 0. This document does not authorize its own execution.
