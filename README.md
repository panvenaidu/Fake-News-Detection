## Current state — 8 October 2026, completed multimodal pilot

**Text-only, official full cohort:** BERT-base completed five training/validation epochs. Selected epoch4 has validation accuracy **82.7407%** and Macro-F1 **77.8682%**. Epoch5 accuracy **82.8031%**, Macro-F1 **77.8388%** did not replace the selected checkpoint. The trainer failed writing recovery metadata at the end of epoch5; Colab GPU allocation is blocked by usage limits. **Final test pending. ModernBERT not started.** Original five-epoch history is retrieved; original tensor recovery checkpoint must still be verified locally. No BERT recovery job is currently running.

**Text+image, engineering pilot:** BERT-base + ResNet-50 maximum fusion **completed three GPU epochs and a final test** on Kaggle version2, scriptVersionId356486031. Pilot: **2,000 train / 300 validation / 300 test**, all six classes, unchanged official split membership. Selected epoch3: validation **79.33% accuracy / 59.62% Macro-F1**; test **74.33% accuracy / 55.90% Macro-F1**. 188 optimizer updates, one AMP skip; 297.9-second notebook run. Original metrics, history, class reports, confusion matrices and GPU environment are synced to `results/experiments/multimodal/MM-PILOT-6W-v1_seed42_20261009/`; weights/checkpoints and prediction CSVs remain preserved in the private saved Kaggle output. This is **not an official full-cohort benchmark**, not “50% of training”, and not evidence of outperforming the paper. Imposter test F1 is zero on six examples.

**Next:** place the downloaded `bert-base-20261008T133126Z-1-001.zip` inside `data/cloud_recovery/`, verify original tensors with `scripts/verify_text_recovery.py`, privately attach archive and verification JSON to Kaggle, then use `notebooks/UROP_KAGGLE_TEXT_RECOVERY_20261009.ipynb` to resume the unchanged original text protocol. It finishes BERT before ModernBERT; preserve the original Colab environment plus Kaggle resume environment. Do not rerun the completed multimodal pilot. `results/FACULTY_STATUS_20261009.md` is the short faculty summary. The earlier entries below describe historical observations and are superseded by this current section.

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
