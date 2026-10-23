<!-- MM-PART1 EXECUTION -->
## Part 1 execution checkpoint — 23 October 2026

User authorized MM-PART1-v2. **In progress; waiting for the new CPU Colab notebook's Drive-access permission.** Desktop control opened/focused Rocky Chrome; extension verified panvee62@gmail.com. Kaggle re-login verified Rocky62; fresh quota00:00/30h used. No GPU job or scientific training started. Author image archive displays106G; large download was not confirmed. Drive shows78.96GB/5.39TB used, sufficient for a cloud staging route once authorized and verified. CPU notebook: https://colab.research.google.com/drive/1EQr8BSZEzyMpoGyQweXE3rRCkOHPbesU . Runtime connected; Drive mount awaits explicit permission. Initial reCAPTCHA-service warning did not prevent eventual CPU allocation.

Fresh complete local image decode audit:75,995 usable,0 decode failures,606,666 missing;110 groups of identical bytes across different official splits. Preserve official membership and report this limitation. Candidate/missing-ID manifests, per-image hashes and duplicate inventory live under ignored `data/official_paired_v1/`; coverage summary `results/official_image_coverage_v1.json`. No silent cohort reduction. Synthetic CPU recovery primitives passed deterministic crop/order, model/optimizer/scheduler/RNG/BatchNorm/dropout resume, corrupted-generation fallback and unsafe-save rejection. Strict BERT encoder mapping/load is recorded separately. These are component checks, not full-trainer/GPU/AMP certification.

Receipt: `results/MM_PART1_RECEIPT_20261023.json`. Full trainer/config, complete image preparation, two train epochs, two full validations and durable scientific checkpoint remain pending. Progress unchanged:text100%, multimodal40%, image-only20%, overall53%. Minimum aspiration+1pp (validation87.00%, eventual Part2 test86.88%) is not promised. Reserve:prepare/sync20%, handoff10%, hardstop5%. Next: approve this new notebook's Drive access, verify mounted capacity and resumable archive staging on CPU, then finish full trainer/checks before GPU launch. No final test in Part1.
<!-- /MM-PART1 EXECUTION -->

<!-- MM-PARTS-v2 CURRENT -->
## Current handoff — 23 October 2026

Two separate execution plans are ready: `context/MULTIMODAL_PART1_EXECUTION_PLAN_20261023.md` and `context/MULTIMODAL_PART2_EXECUTION_PLAN_20261023.md`; PDFs are in `results/UROP_Multimodal_Part1_Plan_20261023.pdf` and `results/UROP_Multimodal_Part2_Plan_20261023.pdf`. Recommended execution: GPT-6.1 Sol High, Part 1 then Part 2. Planning only; no new training or large download this session. This note supersedes older next-action/target/reserve wording below.

Use Chrome profile **Rocky / panvee62@gmail.com**; desktop controls may open/focus that application, then prefer enabled Chrome extension controls. Verify actual signed-in identity/workspace. The plan's public Drive check ran in a signed-out browser and did not verify private Kaggle access or GPU quota.

The [faculty dataset](https://drive.google.com/drive/folders/1DuH0YaEox08ZwzZDpRMOaFpMCeRyxiEF) has unchanged TSV hashes and 564,000/59,342/59,319 rows. Only75,995 images are locally inventoried;606,666 remain missing/unverified locally. Full-image coverage and a new recovery-tested full trainer are launch gates. No fresh full image decode or cloud archive download was performed. Text100%, full multimodal40%, image-only20%, overall53% remain unchanged; pilot separately100%.

Part1: full image gate, new trainer/checks, epochs1–2 with full validation and durable recovery (then multimodal60%). Part2: same-run continuation, validation selection, one frozen final test and verified archive (then multimodal100%; overall73% while image-only remains pending). Minimum aspiration is now **+1 percentage point**, validation87.00%/test86.88%; older +2–3pp is a stretch goal, never guaranteed. No Part1 final test. At20% assistant allowance save/checkpoint/update records and Git; at10% stop substantive work; at5% hard-stop after handoff. Saving must begin before the final5%. Current cloud quota is unknown.
<!-- /MM-PARTS-v2 CURRENT -->

<!-- MM-COMPLETE-v1 PLAN -->
## Full text + image: proposed next task — 9 October 2026

Read `context/MULTIMODAL_COMPLETION_PLAN_20261009.md` and `context/MULTIMODAL_PART1_GO.md` / `MULTIMODAL_PART2_GO.md`. **Awaiting go; planning only.** Part 1 targets 40%→60%; Part 2 targets 60%→100% for the first full-cohort multimodal baseline. Current progress is unchanged: text100%, text+image40%, image-only20%, overall53%; pilot100% separately.

The [faculty dataset](https://drive.google.com/drive/folders/1DuH0YaEox08ZwzZDpRMOaFpMCeRyxiEF) remains 564,000/59,342/59,319 rows with verified unchanged hashes. Only 75,995 paired images (11.13%) exist locally; 606,666 are still unavailable/unverified locally. Full image coverage and storage are the first execution gate. Do not substitute the historical subset or increase progress after preparation alone.

Proposed protocol: completed validation-selected BERT encoder + ResNet-50, maximum fusion, seed42, four-epoch cap. Part 1 trains/validates two epochs and verifies recovery; Part 2 resumes, finishes, tests once and archives. New protocol settings await go. CLIP/SigLIP2, image-only and repeated seeds remain separate. Target: 88–89% validation and 87.88–88.88% test accuracy, +2–3 percentage points over the matching paper row; no guarantee. Rough pilot extrapolation is 21 GPU hours, plus uncertain image preparation; remeasure before launch. Last recorded Kaggle quota29h09m is historical.

Audit/inventory: `results/MULTIMODAL_PLAN_AUDIT_20261009.json`; verification: `results/MULTIMODAL_PLAN_VERIFICATION_20261009.json`. No new training, large download, data modification or scheduler. Latest usage check: 11% current window /27% weekly remaining; reserve mode, documentation/Git handoff only. Preserve completed BERT and all historical artifacts. This note supersedes older next-action notes below.
<!-- /MM-COMPLETE-v1 PLAN -->

<!-- TEXT-COMPLETE-v1 LIVE -->
## BERT completion execution — 9 October 2026

BERT text-only six-class baseline is complete: six epochs, epoch4 selected; validation82.7407% accuracy/77.8682% Macro-F1; test82.3901%/77.4566% on all59319 rows. Test exceeds paper76.77% by5.6201 percentage points, reaching+1-point target. Both archives,69 manifest members and allprediction metrics/IDs verified. Model/optimizer/scheduler/AMP/tokenizer load and completed-result idempotence passed. Final epoch6 checkpoint and selected weights stored locally/private cloud. Original data/config/source/history retained. Text100%, full text+image40%, image20%, overall53%; pilot100% separately. No active cloud GPU job; Kaggle quota29h09m remaining at final observation.

BERT baseline complete. Read results/TEXT_ONLY_FINAL_REPORT_20261009.md; register a separate future ModernBERT comparison or full multimodal cohort before any new training. Final GitHub verification is recorded in the requirement audit.

Evidence: `results/text_completion_execution_20261009.json`; plan `context/TEXT_COMPLETION_PLAN_20261009.md`. The user has authorized execution. Historical entries below retain earlier observations.
GitHub backup verified: results and documentation commit `5527824302480de39cafd85a5a9a1c2b8cc68fd7` is on remote `main`. Receipt: `results/TEXT_COMPLETION_GITHUB_RECEIPT_20261009.json`. Latest assistant usage check: 24% five-hour / 42% weekly remaining; the final 20% remains reserved for safe handoff. No new model or GPU job was started after final evaluation.
Faculty presentation: [open the standalone HTML](results/UROP_Text_Only.html). Download the file and open it directly in Chrome; no server or external assets are required.
<!-- /TEXT-COMPLETE-v1 LIVE -->

## Text completion execution — 9 October 2026

The user approved `TEXT-COMPLETE-v1`. Versioned BERT-only recovery passed the original-checkpoint, sample-order and optimizer/AMP recovery gates. Private Kaggle input staging is in progress; no resumed GPU step or final text test is verified yet. Original data, weights, source/config and five-epoch observations are preserved. Current execution: `results/text_completion_execution_20261009.json`.

## Latest handoff - 9 October 2026: text completion plan ready

Read `context/TEXT_COMPLETION_PLAN_20261009.md` first. User requested a detailed GPT-6 Sol handoff and will approve execution next. This session audited data/code/evidence and saved a plan; no GPU training or final test was run. All official TSVs were rescanned and saved weight hashes reverified. Kaggle inspection: no active jobs, draft off, quota 00:06 / 30h used (about 29h54m remaining at observation).

**New prerequisite:** original mid-epoch resume changes sample order when fresh workers consume the sampler generator. CPU reproduction and actual checkpoint RNG inspection confirmed the mismatch. Saved weights are intact; repair and verify resume ordering before running the prepared recovery notebook. Also make a BERT-only job and export the missing full validation prediction CSV. Preserve original source/config/history; record versioned recovery changes. See `results/text_resume_order_diagnostic_20261009.json` and `results/TEXT_COMPLETION_PLAN_AUDIT_20261009.json`.

**Usage reserve:** start syncing around 25% remaining; at 20% start no new experiment and use the reserve to update all context/log/status files and safely commit/push. Leave a healthy submitted cloud job running independently; record its exact state and durable outputs. Do not imply local/GitHub updates happen while the agent is inactive. Latest planning check: 24% five-hour / 57% weekly remaining; finish documentation and handoff now.

Progress unchanged: BERT73%, full text+image40%, image-only20%, overall44%; multimodal pilot100% separately. BERT has five observed training/validation epochs, saved epoch5 batch15000, final test pending. A later approval to execute the saved plan authorizes its implementation and training sequence. Earlier entries below are historical where they conflict with this note.

## Current state — 8 October 2026, completed multimodal pilot

**Text-only, official full cohort:** BERT-base completed five training/validation epochs. Selected epoch4 has validation accuracy **82.7407%** and Macro-F1 **77.8682%**. Epoch5 accuracy **82.8031%**, Macro-F1 **77.8388%** did not replace the selected checkpoint. The trainer failed writing recovery metadata at the end of epoch5; Colab GPU allocation is blocked by usage limits. **Final test pending. ModernBERT not started.** Original five-epoch history is retrieved. Original tensor integrity is verified at epoch5 batch15000/17625, before epoch completion; resume will replay the remaining2625 batches of epoch5. Verification: `results/bert_recovery_verification.json`. No BERT recovery job is currently running.

**Text+image, engineering pilot:** BERT-base + ResNet-50 maximum fusion **completed three GPU epochs and a final test** on Kaggle version2, scriptVersionId356486031. Pilot: **2,000 train / 300 validation / 300 test**, all six classes, unchanged official split membership. Selected epoch3: validation **79.33% accuracy / 59.62% Macro-F1**; test **74.33% accuracy / 55.90% Macro-F1**. 188 optimizer updates, one AMP skip; 297.9-second notebook run. Original metrics, history, class reports, confusion matrices and GPU environment are synced to `results/experiments/multimodal/MM-PILOT-6W-v1_seed42_20261009/`; weights/checkpoints remain preserved in the private saved Kaggle output. All300 validation and300 test original predictions are now synced locally and verified against the official pilot IDs/labels. This is **not an official full-cohort benchmark**, not “50% of training”, and not evidence of outperforming the paper. Imposter test F1 is zero on six examples.

**Next:** privately attach the verified recovery archive and `data/cloud_recovery/recovery_verification.json` to Kaggle, then use `notebooks/UROP_KAGGLE_TEXT_RECOVERY_20261009.ipynb` to resume the unchanged original text protocol. It finishes BERT before ModernBERT; preserve the original Colab environment plus Kaggle resume environment. Do not rerun the completed multimodal pilot. `results/FACULTY_STATUS_20261009.md` is the short faculty summary. The earlier entries below describe historical observations and are superseded by this current section.

> Historical snapshot before interruption: official text training was active: BERT epoch-4 validation accuracy **82.74%**, Macro-F1 **77.87%** (original metrics retrieved). Epoch 5 running; selected checkpoint currently epoch 4 by Macro-F1; final test pending; ModernBERT queued. Finite status display repaired; trainer/GPU activity verified independently. Kaggle phone verified, 0/30 GPU hours used as last checked. See [current context](context/RESUME_HERE.md) and [live evidence](results/official_text_live_status.json).

> **Current update (2026-10-08):** Official full-cohort training is documented in `context/AUDIT_20261008.md`. Earlier 75,995-subset results remain historical. Four original full-precision validation observations and small cloud evidence are synchronized locally; final test and predictions are pending.

# Multimodal Fake News Detection Using Text + Image

A university research project investigating multimodal fake news detection using the [Fakeddit](https://fakeddit.netlify.app/) dataset.

## Overview

This project explores improving multimodal (text + image) fake news detection, focusing on robustness and generalization. We use the Fakeddit benchmark dataset, which contains over 1 million samples with 2-way, 3-way, and 6-way classification labels.

**Reference Paper:** "Fake News Detection: It's All in the Data!" (Applied Sciences, 2026)

**Dataset Paper:** Nakamura, Levy, Wang. "r/Fakeddit: A New Multimodal Benchmark Dataset for Fine-grained Fake News Detection" (LREC 2020)

## Project Structure

```
├── context/              # Shared project memory (context files)
│   ├── PROJECT_CONTEXT.md   # Current project state
│   ├── DECISIONS.md         # Important decisions and rationale
│   └── EXPERIMENT_LOG.md    # Experiment results and observations
├── src/                  # Source code (models, training, evaluation)
├── scripts/              # Utility scripts (data download, preprocessing)
├── configs/              # Training and model configurations
├── experiments/          # Experiment-specific files
├── results/              # Results, figures, tables
├── notebooks/            # Jupyter notebooks for exploration
├── docs/                 # Documentation and reports
├── README.md
└── requirements.txt
```

## Dataset

We use the **Fakeddit** dataset:
- **Website:** https://fakeddit.netlify.app/
- **Repository:** https://github.com/entitize/Fakeddit
- **Paper:** https://arxiv.org/abs/1911.03854

> **Note:** The full Fakeddit dataset is NOT included in this repository. See the [Data Setup](#data-setup) section below.

### Classification Tasks

| Task | Labels |
|------|--------|
| 2-way | True, Fake |
| 3-way | Completely true, Not enough info, Definitely false |
| 6-way | True, Satire/Parody, Misleading Content, Imposter Content, False Connection, Manipulated Content |

## Setup

### Prerequisites
- Python 3.8+
- PyTorch
- Additional requirements in `requirements.txt`

### Installation

```bash
git clone <this-repo-url>
cd <repo-name>
pip install -r requirements.txt
```

### Data Setup

1. Download the Fakeddit v2.0 TSV files from [Google Drive](https://drive.google.com/drive/folders/1jU7qgDqU1je9Y0PMKJ_f31yXRo5uWGFm?usp=sharing)
2. Place TSV files in `data/` directory (not tracked by Git)
3. For images, see the [Fakeddit repository](https://github.com/entitize/Fakeddit) for download options

> **Important:** Follow the [Fakeddit usage guidelines](https://fakeddit.netlify.app/) when using this dataset.

## Research Approach

1. **Phase 1:** Understand dataset and existing work
2. **Phase 2:** Data preparation and preprocessing
3. **Phase 3:** Establish baselines (text-only, image-only, text+image)
4. **Phase 4:** Identify research gap from baseline analysis
5. **Phase 5:** Implement proposed improvement
6. **Phase 6:** Evaluation and comparison
7. **Phase 7:** Paper writing and documentation

## Team

- **Panvee** — Implementation and experiments
- **Karthik** — Literature review and paper
- **Third Member** — Reports, documentation, presentations

## Context System

This project uses a shared context system in `context/` for collaboration across team members and AI agents. Before doing any project work, read:
1. `context/PROJECT_CONTEXT.md` — current project state
2. `context/DECISIONS.md` — important decisions
3. `context/EXPERIMENT_LOG.md` — experiment results

## Citation

If using Fakeddit, please cite:

```bibtex
@inproceedings{nakamura2020fakeddit,
  title={r/Fakeddit: A New Multimodal Benchmark Dataset for Fine-grained Fake News Detection},
  author={Nakamura, Kai and Levy, Sharon and Wang, William Yang},
  booktitle={Proceedings of the 12th Language Resources and Evaluation Conference},
  pages={6149--6157},
  year={2020}
}
```

## License

This project is for academic research purposes.
