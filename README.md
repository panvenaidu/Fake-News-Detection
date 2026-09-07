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
