from pathlib import Path
import json, os, html, re
R=Path('/Users/panveenaidu/Downloads/SEM7/UROP'); J=R/'context/organization_20261029'
cloud=json.loads((J/'kaggle_renames.json').read_text())['rows']; moves=json.loads((J/'local_moves.json').read_text())
def write(p,s):
 p=R/p;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(s)
# Complete basename references in presentation-only navigation docs.
for p in (R/'docs/explainers').rglob('*.md'):
 s=p.read_text()
 for a,b in {'WATCH.html':'watch_video.html','TRANSCRIPT.md':'narration.md','VIVA_FAQ.md':'faculty_questions.md','VIDEO_RECEIPT.json':'video_verification.json','DEVMOTION_HANDOFF.md':'video_render_notes.md','captions.srt':'subtitles.srt','build_video.py':'render_english_video.py','build_elevenlabs_video.py':'render_elevenlabs_video.py','assemble_elevenlabs_audio.py':'prepare_elevenlabs_audio.py','mux.swift':'combine_audio_video.swift','verify_audio.swift':'check_audio.swift','tempo.swift':'adjust_audio_speed.swift'}.items():s=s.replace(a,b)
 p.write_text(s)
write('START_HERE.md','''# UROP — Start Here

Open [the project overview](START_HERE.html) for a clean faculty presentation menu.

- [Text-only results](results/UROP_Text_Only.html) · [research report](results/TEXT_ONLY_FINAL_REPORT_20261009.md)
- [Text + image results](results/UROP_Multimodal_Final_20261028.html) · [research report](results/MULTIMODAL_FINAL_REPORT_20261028.md)
- [Telugu-English explainer](data/presentations/urop_explainer_telugu_remotion/WATCH.html)
- [Notebooks by purpose](notebooks/README.md)
- [Documents, literature and videos](docs/README.md)
- [Full research handoff](clicky_handoff/CLICKY.md)
- [Folder map](FOLDER_GUIDE.md)
- [Every rename and old-link resolver](context/RENAME_LOG.md)

Text-only and text + image have completed final result records. Image-only has not started; the organization task does not change experiment status.
''')
write('FOLDER_GUIDE.md','''# UROP folder guide

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
''')
write('docs/README.md','''# Documents

## Show the faculty

- [Text-only results](../results/UROP_Text_Only.html) · [text-only report](../results/TEXT_ONLY_FINAL_REPORT_20261009.md)
- [Text + image results](../results/UROP_Multimodal_Final_20261028.html) · [text + image report](../results/MULTIMODAL_FINAL_REPORT_20261028.md)
- [Literature survey](reports/literature_survey.pdf)
- [Telugu-English video](../data/presentations/urop_explainer_telugu_remotion/WATCH.html)
- [English video — ElevenLabs](explainers/english_elevenlabs/watch_video.html)
- [English video — original edition](explainers/english_basic/watch_video.html)
- [Architecture questions and answers](explainers/english_basic/faculty_questions.md)

## Reference and history

- [Applied Sciences reference](literature/applied_sciences_reference.pdf)
- [Week-one research plan](reports/historical/week_1_research_plan.pdf)
- [Historical BERT progress](reports/historical/bert_baseline_progress.pdf)
- [Early training summary](reports/historical/early_training_summary.pdf)
- [Historical text dashboard export](reports/historical/text_dashboard_export/index.html)
- [Private original browser exports](../data/cloud_recovery/browser_exports_20261027/) — retained evidence, not current launchers.

The historical reports describe earlier stages. Use the final reports above for current results. Media remains in private `data/presentations/`; source, subtitles, narration and small verification files are in `docs/explainers/`. [All name changes](../context/RENAME_LOG.md).
''')
notebook_purposes={
 'text_only/train_text_models.ipynb':'Original official text experiment launcher; includes registered/queued model definitions. Not proof every model ran.',
 'text_only/resume_and_evaluate.ipynb':'Resume the original text experiment and evaluate its selected checkpoint.',
 'text_only/recover_bert_checkpoint.ipynb':'Recover the saved BERT state; historical recovery launcher.',
 'text_image/final_training_and_test.ipynb':'Final continuation and held-out evaluation notebook; completed run history.',
 'text_image/continue_training_and_validation.ipynb':'Part 2 continuation from the accepted Part 1 recovery.',
 'preparation/check_gpu_and_recovery.ipynb':'Synthetic CUDA and checkpoint checks; not scientific training.',
 'preparation/prepare_faculty_images_v1.ipynb':'Earlier CPU image-preparation notebook.',
 'preparation/prepare_faculty_images_v2.ipynb':'Later CPU image-preparation notebook; retained distinct source.',
 'templates/train_epoch_usable_images.ipynb':'Approved usable-image cohort epoch template; not a new run.',
 'archive/train_epoch_all_images_superseded.ipynb':'Superseded all-images template from before the approved exclusions.',
 'pilot/train_and_evaluate_paired_pilot.ipynb':'Historical paired-subset pilot, separate from official full-cohort results.'}
write('notebooks/README.md','# Notebook catalog\n\nNotebook bytes and code cells are unchanged by the reorganization. Open a completed Kaggle result for a demonstration; running an old notebook can allocate compute or repeat work.\n\n## Local notebooks\n\n| Notebook | Purpose |\n|---|---|\n'+''.join(f'| [{p}]({p}) | {v} |\n' for p,v in notebook_purposes.items())+'\n## Kaggle notebooks\n\n| Clear name | Saved version, when recorded |\n|---|---|\n'+''.join(f'| [{x["new_name"]}]({x["new_url"]}) | {x.get("saved_version_id") or "See notebook version history"} |\n' for x in cloud)+'\nThe text-results notebook has older multimodal pilot history in version 356486031; final text evidence is version 356721456. Renaming does not turn old versions into new experiments. Kaggle dataset names/versions and input mounts are unchanged. Historical launcher strings may mention an old slug: consult the rename ledger and pinned version before any future execution.\n\n[Full old → new ledger](../context/RENAME_LOG.md).\n')
write('results/README.md','''# Results and evidence

## Current faculty results

| Modality | Dashboard | Full report | Completion evidence |
|---|---|---|---|
| Text only | [Open](UROP_Text_Only.html) | [Read](TEXT_ONLY_FINAL_REPORT_20261009.md) | Official text experiment evidence under experiments/official_text |
| Text + image | [Open](UROP_Multimodal_Final_20261028.html) | [Read](MULTIMODAL_FINAL_REPORT_20261028.md) | [Final receipt](MM_FINAL_COMPLETION_RECEIPT_20261028.json) |

- [Project progress](PROGRESS_TRACKER.md)
- [Per-run scientific artifacts](experiments/)
- [Historical screenshots and observations](archive/README.md)
- [Rename ledger / old-path resolver](../context/RENAME_LOG.md)

Numeric JSON/CSV evidence and dated reports are canonical records with references and hashes. Their registered names stay intact. They are not a list of extra completed trainings. Historical screenshots and intermediate statuses do not supersede the final completion receipt. Raw data and weights remain private under data/ and cloud storage.
''')
write('results/archive/README.md','# Historical operational evidence\n\n- `screenshots/`: browser/cloud UI observations; a screenshot is not a live job status.\n- `observations/`: retained status reads, errors, throughput notes and literature extraction.\n\nFiles were moved without changing their bytes. Original paths in historical receipts resolve through [the rename ledger](../../context/RENAME_LOG.md). These private UI/log exports are excluded from new Git publication unless they were already tracked and retained as history.\n')
write('context/README.md','''# Project context

- [Every file and Kaggle name change](RENAME_LOG.md)
- [Current multimodal completion receipt](../results/MM_FINAL_COMPLETION_RECEIPT_20261028.json)
- [Final multimodal report](../results/MULTIMODAL_FINAL_REPORT_20261028.md)
- [Full project explanation](../clicky_handoff/CLICKY.md)
- [Folder map](../FOLDER_GUIDE.md)

Dated execution plans and recovery records are historical source material. New accepted receipts override older status claims. Existing decision records and registered plans were preserved rather than rewritten to match the new names. `organization_20261029/` contains the reversible path mapping, checksums, reference-update record and verification.
''')
for path,title,body in [
 ('scripts/README.md','Local utilities','`verify_*` independently inspect evidence; `prepare_*` prepare inputs; `build_*` build bundles or reports; `make_*` generate notebook artifacts. `organize_project_files.py` is the audited one-time rename utility (dry-run by default; refuses reapplication). Inspect each program before execution. No scripts were executed for training during file organization. Registered scientific script names and hashes are preserved.'),
 ('collab/README.md','Cloud programs','Cloud preparation, training, validation, input transport, recovery and engineering checks. Historical names preserve exact source identity referenced by completed runs. Use the current approved plan and pinned source hashes before launching; do not infer the active launcher from filename sorting. For faculty demonstrations use the clearly named Kaggle notebooks linked in ../notebooks/README.md.'),
 ('configs/README.md','Registered configurations','Experiment JSON settings are frozen reproducibility records. Keep source/config hashes consistent with the accepted receipt. Filenames include modality, protocol or version identifiers intentionally. Do not rewrite configs to tidy names or restart a completed run.'),
 ('src/README.md','Model implementation','Reusable implementations are under fakenews_baselines/. This organization task does not change model architecture, training logic or imports. The final report and Clicky handoff link actual implementation and registered cloud source.'),
 ('work_logs/README.md','Work logs','MODEL_STATUS.md records model progress; TROUBLESHOOTING.md retains failures and recovery evidence. Current completion is established by results/MM_FINAL_COMPLETION_RECEIPT_20261028.json and its verification, not old log status.'),
 ('data/README.md','Private project storage','official_multimodal_v2 contains official TSV inputs; official_paired_v2 contains approved image/cohort preparation and diagnostics; official_paired_v1 is historical paired data; paired_pilot_20261009 is a pilot; cloud_recovery contains retained cloud outputs/checkpoints; presentations contains video/media projects. Fakeddit datasetv2.0 is original faculty reference material: treat it as read-only. Check actual manifests for authoritative paths. Do not upload data, weights or credentials to GitHub.'),
 ('images/README.md','Historical paired-subset images','This folder and root images.zip belong to the earlier verified paired subset. Keep image IDs and bytes unchanged. They are not replacements for the current faculty usable-image cohort. See data/official_paired_v2 and the final report for the current multimodal lineage.'),
 ('experiments/README.md','Legacy experiment folder','Scientific artifacts are stored in results/experiments/. This previously empty legacy folder is retained; use the results catalog instead.')]:write(path,'# '+title+'\n\n'+body+'\n')
log='# Rename and organization log\n\nAs of 29 October 2026. Organization only; no training, evaluation or experiment-state changes.\n\n## Kaggle notebooks\n\nAll 11 titles were verified in Your Work. Six private dataset names/versions were deliberately retained to preserve input identities. Titles changed the notebook slugs; use the new links below. Saved-version IDs remain experiment identifiers. Final multimodal saved version 362955511 was opened after rename: Private, Version 1 of 1, Edit link still points to run/362955511.\n\n| Old name | New name / current link | Original URL |\n|---|---|---|\n'
for x in cloud:log+=f'| {x["old_name"]} | [{x["new_name"]}]({x["new_url"]}) | {x["old_url"]} |\n'
log+='\n## Local moves\n\n107 files: 11 notebooks, 25 document/source files, and 71 historical screenshots/observations. Every move had matching SHA-256 before and immediately after. Navigation references and presentation build-source paths were then updated; receipt JSON and notebook contents were not rewritten.\n\n| Old path | New path | Original SHA-256 |\n|---|---|---|\n'
for x in moves:log+=f'| `{x["old_path"]}` | `{x["new_path"]}` | `{x["sha256_before"]}` |\n'
log+='''
## Verification and recovery

- [Machine-readable moves](organization_20261029/local_moves.json)
- [Kaggle old/new URLs](organization_20261029/kaggle_renames.json)
- [Reference edits](organization_20261029/reference_updates.json)
- [Protected-file hash baseline](organization_20261029/protected_files.json)
- [Verification](organization_20261029/verification.json)

558 tracked source/config/result/context files were checked unchanged immediately after moves. Canonical scientific receipts and reports retain original paths/bytes and may intentionally mention historical notebook names. Resolve those references here rather than editing historical evidence. Private data, images, weights, media and inputs were not renamed or copied. Existing user edits to results/UROP_Text_Only.html remain untouched.

To reverse a move: stop any related editing, consult local_moves.json, check the recorded hash/current reference-update hash, ensure the old path is free, and move the file back. Restore only the corresponding reference text from the private reference_backups/ copy if needed. Never overwrite a newer revision. Browser title changes are reversible through Kaggle's Edit title control; changing back may also change its slug.

No training, new notebook versions, dataset versions or sharing changes were requested by this organization task. Historical launchers may contain old notebook slugs/input mounts; they are intentionally byte-preserved. A future execution must resolve current URLs and verify pinned inputs, not blindly run an archived launcher.
'''
write('context/RENAME_LOG.md',log)
# Root README keeps its full prior history, adding navigation only.
p=R/'README.md';s=p.read_text();marker='> **Project navigation:**'
if marker not in s:p.write_text('> **Project navigation:** [Start Here](START_HERE.md) · [Faculty menu](START_HERE.html) · [Folder guide](FOLDER_GUIDE.md) · [Notebook catalog](notebooks/README.md) · [Rename history](context/RENAME_LOG.md)\n\n'+s)
cards=[('Text only','Completed results dashboard','results/UROP_Text_Only.html'),('Text + image','Completed results dashboard','results/UROP_Multimodal_Final_20261028.html'),('Telugu-English explainer','Narrated architecture overview','data/presentations/urop_explainer_telugu_remotion/WATCH.html'),('Research reports','Literature, reports and explanations','docs/README.md'),('Notebook catalog','Training, preparation and checks','notebooks/README.md'),('Project handoff','Decisions, evidence and explanations','clicky_handoff/CLICKY.md')]
write('START_HERE.html','''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>UROP · Project overview</title><style>body{margin:0;background:#f5f6f8;color:#182334;font:17px system-ui,sans-serif}main{max-width:1080px;margin:70px auto;padding:0 30px}small{color:#3564c8;letter-spacing:.12em}h1{font-size:46px;margin:16px 0}p{color:#5a6574;line-height:1.6}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(290px,1fr));gap:18px;margin:36px 0}.card{display:block;padding:28px;background:white;border:1px solid #e0e5eb;border-radius:14px;text-decoration:none;color:inherit}.card:hover{border-color:#3564c8}.card b{font-size:22px}.card span{display:block;color:#657182;margin-top:12px}footer{padding-top:20px;border-top:1px solid #dce1e8}a{color:#285bb8}</style><main><small>UROP RESEARCH PROJECT</small><h1>Multimodal misinformation classification</h1><p>Faculty-provided dataset · Text and image representations · Research-defined categories</p><div class="grid">'''+''.join(f'<a class="card" href="{u}"><b>{html.escape(t)}</b><span>{html.escape(d)} →</span></a>' for t,d,u in cards)+'''</div><footer><a href="FOLDER_GUIDE.md">Folder guide</a> &nbsp;·&nbsp; <a href="context/RENAME_LOG.md">Rename history</a> &nbsp;·&nbsp; <a href="https://www.kaggle.com/work">Kaggle workspace</a><p>Use completed result dashboards for presentations. Preparation checks and historical drafts are separately labelled.</p></footer></main></html>''')
# Private UI exports and original reference backups must not be newly published.
p=R/'.gitignore';s=p.read_text();s+='\n# Organization audit private UI/reference backups\ncontext/organization_20261029/*.png\ncontext/organization_20261029/reference_backups/\nresults/archive/screenshots/\nresults/archive/observations/\n';p.write_text(s)
print('Navigation, catalog, folder guides and rename ledger created.')
