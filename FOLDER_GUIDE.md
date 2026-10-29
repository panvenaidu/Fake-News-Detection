# UROP folder guide

| Folder | Purpose | Start here |
|---|---|---|
| `docs/` | Faculty documents, literature, explanation videos | [Documents](docs/README.md) |
| `notebooks/` | Text-only, text + image, preparation, templates and historical pilots | [Notebook catalog](notebooks/README.md) |
| `results/` | Canonical scientific reports, metrics and verification receipts | [Results](results/README.md) |
| `results/archive/` | Historical browser screenshots and status observations | [Archive](results/archive/README.md) |
| `context/` | Decisions, execution plans, current-state records and rename history | [Context guide](context/README.md) |
| `work_logs/` | Model status and troubleshooting history | [Logs](work_logs/README.md) |
| `data/` | Private faculty data, recovery archives, checkpoints and video media | [Private storage guide](data/README.md) |
| `images/`, `images.zip` | Historical paired-subset images; not the current usable-cohort source | [Image provenance](images/README.md) |
| `configs/` | Registered experiment settings | [Configurations](configs/README.md) |
| `src/` | Reusable model implementation | [Source](src/README.md) |
| `scripts/` | Local audit, launch, verification and documentation utilities | [Scripts](scripts/README.md) |
| `collab/` | Cloud preparation, training, verification and recovery programs | [Cloud code](collab/README.md) |
| `clicky_handoff/` | Detailed navigable research explanation | [CLICKY.md](clicky_handoff/CLICKY.md) |
| `experiments/` | Empty legacy directory; actual experiment evidence is under results/experiments | [Results](results/README.md) |

## Naming rules

Kaggle: **UROP + modality/purpose + stage**, e.g. `UROP Text + Image - Final Results`.
Local notebooks: **purpose.ipynb inside a modality/stage folder**, e.g. `notebooks/preparation/check_gpu_and_recovery.ipynb`.
Documents: short descriptive names; historical reports are under `docs/reports/historical/`.
Use a version suffix only to distinguish genuinely different retained files.

Frozen scientific source/configuration, original data, experiment IDs, checkpoint names, numeric evidence and historical JSON receipts retain their registered paths and bytes. These are audit identifiers, not faculty presentation names. The catalog and rename ledger resolve old references; do not edit immutable receipts to make them prettier. Hidden caches and environments are operational folders.
