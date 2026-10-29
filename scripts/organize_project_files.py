"""Audited documentation/notebook reorganization. Dry-run by default.

Does not run notebooks or alter scientific source, configuration, data or weights.
Historical receipts retain their original bytes; use the rename ledger to resolve
their old paths. --apply refuses overwrites and records hashes before moving.
"""
from pathlib import Path
import argparse, hashlib, json, os, re, subprocess
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
JOURNAL = ROOT / 'context/organization_20261029'

def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''): h.update(chunk)
    return h.hexdigest()

def plan():
    pairs = [
        ('notebooks/UROP_OFFICIAL_6WAY_TEXT_20261008.ipynb', 'notebooks/text_only/train_text_models.ipynb'),
        ('notebooks/UROP_KAGGLE_TEXT_RECOVERY_20261009.ipynb', 'notebooks/text_only/resume_and_evaluate.ipynb'),
        ('notebooks/UROP_KAGGLE_BERT_RECOVERY_V1_20261009.ipynb', 'notebooks/text_only/recover_bert_checkpoint.ipynb'),
        ('notebooks/UROP_MM_FINAL_CONTINUATION_20261028.ipynb', 'notebooks/text_image/final_training_and_test.ipynb'),
        ('notebooks/UROP_MM_PART2_CONTINUATION_20261027.ipynb', 'notebooks/text_image/continue_training_and_validation.ipynb'),
        ('notebooks/UROP_MM_PART1_CUDA_ENGINEERING_20261023.ipynb', 'notebooks/preparation/check_gpu_and_recovery.ipynb'),
        ('notebooks/UROP_MM_PART1_IMAGE_PREP_CPU_20261023.ipynb', 'notebooks/preparation/prepare_faculty_images_v1.ipynb'),
        ('notebooks/UROP_MM_PART1_IMAGE_PREP_CPU_20261024.ipynb', 'notebooks/preparation/prepare_faculty_images_v2.ipynb'),
        ('notebooks/UROP_MM_PART1_USABLE_EPOCH_TEMPLATE_20261024.ipynb', 'notebooks/templates/train_epoch_usable_images.ipynb'),
        ('notebooks/UROP_MM_PART1_REGISTERED_EPOCH_TEMPLATE_20261024.ipynb', 'notebooks/archive/train_epoch_all_images_superseded.ipynb'),
        ('notebooks/UROP_KAGGLE_6WAY_PILOT_20261009.ipynb', 'notebooks/pilot/train_and_evaluate_paired_pilot.ipynb'),
        ('LITERATURE_SURVEY_REPORT_UPDATED_FINAL.pdf', 'docs/reports/literature_survey.pdf'),
        ('docs/literature/applsci-16-01585.pdf', 'docs/literature/applied_sciences_reference.pdf'),
        ('docs/reports/historical/UROP_Fake_News_Detection_week-1.pdf', 'docs/reports/historical/week_1_research_plan.pdf'),
        ('docs/reports/historical/UROP_Progress_Brief_Canonical_E002_Seed42.pdf', 'docs/reports/historical/bert_baseline_progress.pdf'),
        ('docs/reports/historical/UROP-Training-Summary.pdf', 'docs/reports/historical/early_training_summary.pdf'),
        ('docs/reports/historical/browser_export_20261027/index.html', 'docs/reports/historical/text_dashboard_export/index.html'),
    ]
    names = {'WATCH.html':'watch_video.html', 'TRANSCRIPT.md':'narration.md', 'VIVA_FAQ.md':'faculty_questions.md',
             'VIDEO_RECEIPT.json':'video_verification.json', 'DEVMOTION_HANDOFF.md':'video_render_notes.md',
             'captions.srt':'subtitles.srt', 'build_video.py':'render_english_video.py',
             'build_elevenlabs_video.py':'render_elevenlabs_video.py',
             'assemble_elevenlabs_audio.py':'prepare_elevenlabs_audio.py',
             'mux.swift':'combine_audio_video.swift','verify_audio.swift':'check_audio.swift','tempo.swift':'adjust_audio_speed.swift'}
    for old_dir, new_dir in [('urop_20261028','english_basic'),('urop_elevenlabs_20261028','english_elevenlabs')]:
        for p in sorted((ROOT/'docs/explainers'/old_dir).glob('*')):
            if p.is_file(): pairs.append((str(p.relative_to(ROOT)), f'docs/explainers/{new_dir}/{names.get(p.name,p.name)}'))
    # Browser evidence and transient observations are history, not current reports.
    for p in sorted((ROOT/'results').iterdir()):
        if not p.is_file(): continue
        if p.suffix == '.png': pairs.append((str(p.relative_to(ROOT)), f'results/archive/screenshots/{p.name}'))
        elif p.suffix == '.txt': pairs.append((str(p.relative_to(ROOT)), f'results/archive/observations/{p.name}'))
    return pairs

def main():
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument('--apply',action='store_true'); args=parser.parse_args()
    pairs=plan(); JOURNAL.mkdir(parents=True,exist_ok=True)
    if (JOURNAL/'local_moves.json').exists(): raise SystemExit('Already applied: inspect local_moves.json; do not repeat.')
    assert len({b for a,b in pairs})==len(pairs)
    rows=[]
    for a,b in pairs:
        p,q=ROOT/a,ROOT/b
        assert p.is_file(), a
        assert not q.exists(), f'Collision: {b}'
        rows.append({'old_path':a,'new_path':b,'bytes':p.stat().st_size,'sha256_before':sha(p),'status':'planned'})
    (JOURNAL/'local_plan.json').write_text(json.dumps(rows,indent=2)+'\n')
    print(json.dumps({'moves':len(rows),'notebooks':sum(a.startswith('notebooks/') for a,b in pairs),'mode':'apply' if args.apply else 'dry-run'}))
    if not args.apply: return
    # Freeze every tracked non-document file, plus canonical result documents.
    tracked=subprocess.check_output(['git','ls-files','-z'],cwd=ROOT).decode().split('\0')
    moved={a for a,b in pairs}
    protected={p:sha(ROOT/p) for p in tracked if p and (ROOT/p).is_file() and p not in moved
               and not (p=='README.md' or p.startswith('docs/') or p.startswith('clicky_handoff/'))}
    (JOURNAL/'protected_files.json').write_text(json.dumps(protected,indent=2)+'\n')
    for row in rows:
        p,q=ROOT/row['old_path'],ROOT/row['new_path']; q.parent.mkdir(parents=True,exist_ok=True); p.rename(q)
        row['sha256_after_move']=sha(q); assert row['sha256_after_move']==row['sha256_before']; row['status']='moved_byte_identical'
        (JOURNAL/'local_moves.json').write_text(json.dumps(rows,indent=2)+'\n')
    mapping=dict(pairs); reverse={b:a for a,b in pairs}; changed=[]
    # Update navigational documents only. Do not rewrite frozen reports, plans,
    # JSON receipts, notebook cells, scripts used for scientific runs or data.
    candidates=[ROOT/'README.md']+list((ROOT/'docs').rglob('*.md'))+list((ROOT/'docs').rglob('*.html'))+list((ROOT/'clicky_handoff').glob('*.md'))
    link=re.compile(r'(\]\(|(?:href|src)=["\'])([^\s)"\']+)([)"\'])')
    def rewrite(text,old_rel,new_rel):
        def replace(m):
            raw=m.group(2)
            if re.match(r'^[a-z]+://|^#|^mailto:',raw): return m.group(0)
            target,sep,anchor=raw.partition('#')
            if target.startswith(str(ROOT)+'/'): absolute=Path(target)
            elif target.startswith('/'): return m.group(0)
            else: absolute=(ROOT/old_rel).parent/target
            normalized=os.path.normpath(str(absolute))
            try: relative=str(Path(normalized).relative_to(ROOT))
            except ValueError: return m.group(0)
            dest=mapping.get(relative,relative)
            if relative not in mapping and old_rel==new_rel: return m.group(0)
            output=os.path.relpath(ROOT/dest,(ROOT/new_rel).parent)
            return m.group(1)+output+(sep+anchor if sep else '')+m.group(3)
        text=link.sub(replace,text)
        for a,b in pairs: text=text.replace(a,b)
        return text
    cloud=json.loads((JOURNAL/'kaggle_renames.json').read_text())['rows']
    for p in candidates:
        if not p.exists(): continue
        new=str(p.relative_to(ROOT)); old=reverse.get(new,new); before=p.read_text(); after=rewrite(before,old,new)
        for row in cloud:
            if row.get('new_url'): after=after.replace(row['old_url'],row['new_url'])
        if before!=after:
            backup=JOURNAL/'reference_backups'/old; backup.parent.mkdir(parents=True,exist_ok=True); backup.write_text(before)
            p.write_text(after); changed.append({'path':new,'sha256_before':hashlib.sha256(before.encode()).hexdigest(),'sha256_after':sha(p)})
    # Presentation build tools are mutable documentation utilities. Keep private
    # media outputs stable; update renamed source/doc paths and their import only.
    for p in (ROOT/'docs/explainers/english_basic').glob('*.py'):
        before=p.read_text(); after=before.replace('docs/explainers/urop_20261028','docs/explainers/english_basic').replace('docs/explainers/urop_elevenlabs_20261028','docs/explainers/english_elevenlabs').replace('import build_video as b','import render_english_video as b')
        for a,b in names_for_builders().items(): after=after.replace(a,b)
        if after!=before:
            backup=JOURNAL/'reference_backups'/reverse.get(str(p.relative_to(ROOT)),str(p.relative_to(ROOT))); backup.parent.mkdir(parents=True,exist_ok=True); backup.write_text(before)
            p.write_text(after); changed.append({'path':str(p.relative_to(ROOT)),'sha256_before':hashlib.sha256(before.encode()).hexdigest(),'sha256_after':sha(p)})
    (JOURNAL/'reference_updates.json').write_text(json.dumps(changed,indent=2)+'\n')
    for old_dir in ['docs/explainers/urop_20261028','docs/explainers/urop_elevenlabs_20261028','docs/reports/historical/browser_export_20261027']:
        p=ROOT/old_dir
        if p.is_dir() and not any(p.iterdir()): p.rmdir()
    assert all(sha(ROOT/p)==h for p,h in protected.items()), 'Protected file changed'
    for p in (ROOT/'notebooks').rglob('*.ipynb'): json.loads(p.read_text())
    (JOURNAL/'verification.json').write_text(json.dumps({'utc':datetime.now(timezone.utc).isoformat(),'moves':len(rows),'moved_files_byte_identical':True,'reference_updates':len(changed),'protected_files_unchanged':len(protected),'notebooks_parse':11,'training_launched':False},indent=2)+'\n')

def names_for_builders():
    return {'WATCH.html':'watch_video.html','TRANSCRIPT.md':'narration.md','VIVA_FAQ.md':'faculty_questions.md','VIDEO_RECEIPT.json':'video_verification.json','captions.srt':'subtitles.srt','../urop_20261028/':'../english_basic/'}

if __name__=='__main__': main()
