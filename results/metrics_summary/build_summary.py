"""Consolidate existing results only. Does not train or evaluate a model."""
from pathlib import Path
import json,csv,hashlib,shutil,html
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[2]; OUT=Path(__file__).resolve().parent
text=ROOT/'results/experiments/official_text/OFFICIAL-6W-TEXT-v2_seed42_20261008T095827Z/KAGGLE_RECOVERY_v1_20261009_356721456/raw_evidence/bert-base'
mm=ROOT/'results/experiments/multimodal/OFFICIAL-6W-MM-USABLE-v2_seed42_20261027/final_362955511'
im=ROOT/'results/experiments/image_only/CLOUD_COMPLETION_OBSERVED_20261103.json'
paper='https://arxiv.org/html/1911.03854v2'
models=[('text_only','Text-only · BERT-base',text,[.7696,.7677],'Independent saved-artifact verification passed'),('text_image','Text + image · BERT-base + ResNet-50',mm,[.86,.8588],'Independent saved-artifact verification passed'),('image_only','Image-only · ResNet-50',None,[.7529,.7549],'Cloud-reported; independent local artifact verification pending')]
keys=['accuracy','micro_f1','macro_f1','weighted_f1','balanced_accuracy','loss','samples']
labels=['Accuracy','Micro-F1','Macro-F1','Weighted-F1','Balanced accuracy','Cross-entropy loss','Samples']
records=[]; manifest=[]
def record_file(p):
 manifest.append({'path':str(p.relative_to(ROOT)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
for slug,title,base,bench,status in models:
 d=OUT/slug;d.mkdir(exist_ok=True)
 for i,split in enumerate(['validation','test']):
  source=base/(split+'_metrics.json') if base else im
  m=json.loads(source.read_text());m=m if base else m[split]
  assert set(keys)<=m.keys() and m['accuracy']==m['micro_f1']
  (d/(split+'_metrics.json')).write_text(json.dumps({'model':title,'split':split,'status':status,'source':str(source.relative_to(ROOT)),'metrics':m},indent=2)+'\n')
  record_file(source)
  records.append({'model':title,'model_id':slug,'split':split,'status':status,**m,'paper_accuracy':bench[i],'accuracy_difference_percentage_points':100*(m['accuracy']-bench[i]),'paper_other_metrics':'Not reported','source':str(source.relative_to(ROOT))})
 if base:
  for split in ['validation','test']:
   for p in base.glob(split+'_*'):
    if ('classification_report' in p.name or 'confusion' in p.name) and p.suffix in ['.json','.csv']:
     shutil.copy2(p,d/p.name);record_file(p)
 else:
  (d/'PENDING.md').write_text('Image-only per-class precision, recall, F1, support, confusion matrices and per-epoch results have not yet been retrieved into the local accepted archive. Download saved Kaggle version 364917396 and run scripts/verify_image_only_saved_v1.py before final acceptance. Do not reconstruct missing class metrics from overall values.\n')
with (OUT/'all_metrics.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(records[0]));w.writeheader();w.writerows(records)
(OUT/'all_metrics.json').write_text(json.dumps({'generated_utc':datetime.now(timezone.utc).isoformat(),'paper_url':paper,'paper_reference':'Table 4, six-way columns; matching modality; maximum fusion for text + image','records':records},indent=2)+'\n')
(OUT/'source_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
notes='These are numerical reference comparisons, not controlled improvements. Our fine-tuning and checkpoint selection differ from the paper. Text-only uses 682,661 released rows; image branches use 682,170 pairs after 491 approved image decoding exclusions. The paper/release count discrepancy and documented cross-split image duplicates remain limitations. One seed per baseline; no significance or state-of-the-art claim. Image-only values remain cloud-reported pending local verification.'
md=['# UROP validation and test metrics','', 'Open `index.html` for the readable comparison; `all_metrics.csv` for a spreadsheet; `all_metrics.json` for exact machine-readable values. Original results remain intact.','', 'Five score metrics are displayed as percentages. Loss is unscaled (lower is better). Accuracy equals Micro-F1 for this single-label six-class task. Macro-F1 weights classes equally; weighted-F1 weights by support; balanced accuracy averages class recall.','']
sections=[]
for slug,title,base,bench,status in models:
 md+=['## '+title,'',status,'','| Split | Accuracy | Micro-F1 | Macro-F1 | Weighted-F1 | Balanced accuracy | Cross-entropy loss | Samples |','|---|---:|---:|---:|---:|---:|---:|---:|']
 rows=[]
 for r in [r for r in records if r['model_id']==slug]:
  vals=[f'{r[k]*100:.4f}%' for k in keys[:5]]+[f'{r["loss"]:.9f}',f'{r["samples"]:,}']
  md.append('| '+r['split'].title()+' | '+' | '.join(vals)+' |')
  rows.append('<tr><th>'+r['split'].title()+'</th>'+''.join('<td>'+v+'</td>' for v in vals)+'</tr>')
 md+=['', 'Evidence: '+', '.join('['+r['split']+'](../../'+r['source']+')' for r in records if r['model_id']==slug), '']
 sections.append('<section><h2>'+html.escape(title)+'</h2><p class="'+('pending' if slug=='image_only' else 'verified')+'">'+status+'</p><div class="scroll"><table><thead><tr><th>Split</th>'+''.join('<th>'+x+'</th>' for x in labels)+'</tr></thead><tbody>'+''.join(rows)+'</tbody></table></div></section>')
md+=['## Accuracy compared with the paper','', '| Model | Split | Ours | Paper | Difference | Numerically higher |','|---|---|---:|---:|---:|---|']
comp=[]
for r in records:
 delta=r['accuracy_difference_percentage_points'];winner='🟢 Ours ↑' if delta>0 else '🔴 Paper ↑' if delta<0 else 'Equal'
 vals=[r['model'],r['split'].title(),f'{100*r["accuracy"]:.4f}%',f'{100*r["paper_accuracy"]:.2f}%',f'{delta:+.4f} pp',winner]
 md.append('| '+' | '.join(vals)+' |')
 comp.append('<tr>'+''.join('<td>'+html.escape(x)+'</td>' for x in vals)+'</tr>')
md+=['','Paper Micro-F1, Macro-F1, weighted-F1, balanced accuracy, cross-entropy loss and per-class precision/recall/F1: **not reported** for these matching comparisons. Do not invent a winner for those metrics.','', '[Paper Table 4]('+paper+') was checked against the original six-way columns.','',notes,'','## Detailed results','', 'Each model folder contains validation/test JSON. Text-only and text + image also contain the available class reports and raw/normalized confusion matrices. Image-only missing details are explicitly listed in `image_only/PENDING.md`.','', 'Highest recorded validation and test accuracy among our models: text + image. Text-only and image branches use different cohorts, so this is descriptive rather than a controlled ablation.','', 'Full source paths and SHA-256 values: `source_manifest.json`. This consolidation changes no data, models, experiment state or acceptance status.']
(OUT/'README.md').write_text('\n'.join(md)+'\n')
page='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>UROP · Validation & Test Metrics</title><style>body{font:16px/1.6 system-ui,sans-serif;color:#182536;background:#f4f6f9;margin:0}main{max-width:1250px;margin:auto;padding:42px 24px}h1{font-size:34px;line-height:1.2}h2{font-size:21px}.intro{color:#536174;max-width:900px}section{background:white;border:1px solid #dce3ea;border-radius:14px;margin:25px 0;padding:24px}.scroll{overflow:auto}table{width:100%;border-collapse:collapse;font-variant-numeric:tabular-nums;white-space:nowrap;font-size:14px}td,th{text-align:right;padding:12px;border-bottom:1px solid #e7ecf1}td:first-child,th:first-child{text-align:left}thead{color:#536174;background:#f8fafc}.verified{color:#187449}.pending{color:#865700;background:#fff5d9;padding:10px 14px;border-radius:8px}a{color:#245fd0}small{color:#536174}@media print{section{break-inside:avoid}main{padding:0}body{background:white}}</style><main><p>UROP · RESEARCH RESULTS</p><h1>Validation & test metrics</h1><p class="intro">Six-class classification · Selected checkpoints · dataset <small>(provided by the faculty)</small></p><p><a href="all_metrics.csv">Download CSV</a> · <a href="all_metrics.json">Exact JSON</a> · <a href="README.md">Evidence and notes</a></p><p class="intro">Scores are percentages; cross-entropy loss is unscaled and lower is better. Image-only results await independent local artifact verification.</p>'''+''.join(sections)+'<section><h2>Accuracy compared with the paper</h2><div class="scroll"><table><thead><tr><th>Model</th><th>Split</th><th>Ours</th><th>Paper</th><th>Difference</th><th>Higher value</th></tr></thead><tbody>'+''.join(comp)+'</tbody></table></div><p>Other matching paper metrics: <strong>not reported</strong>. pp = percentage points.</p><a href="'+paper+'">Original paper · Table 4</a></section><section><h2>Interpretation</h2><p>'+notes+'</p><p>Text + image has the highest recorded accuracy among our models. Detailed available class reports and confusion matrices are saved in the model folders.</p></section></main></html>'
(OUT/'index.html').write_text(page)
print('Saved',len(records),'model/split records; files',len(list(OUT.rglob('*'))))
