"""Publish small Part1 reports only after independently verified cloud readback.

No model execution, test inference, checkpoint changes or Git mutation here.
Large tensors, predictions and raw data remain in approved private storage.
"""
import csv,datetime,hashlib,json,shutil
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'data/cloud_recovery/part1_verified_pipeline_20261027'
ATTEMPT='OFFICIAL-6W-MM-USABLE-v2_seed42_20261027'
RUN=BASE/'epoch2_saved_output/urop_mm_science_20261027'/ATTEMPT
OUT=ROOT/'results/experiments/multimodal'/ATTEMPT
def load(path):return json.loads(Path(path).read_text())
def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(4*1024**2),b''):h.update(b)
    return h.hexdigest()
def write(path,value):Path(path).write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')

proof=load(ROOT/'results/MM_PART1_EPOCH2_VERIFIED_20261027.json')
assert proof['status']=='passed_independent_retrieved_epoch_verification'
assert proof['epochs_trained']==proof['epochs_validated']==2 and proof['next_epoch']==3 and proof['next_cursor']==0
assert proof['no_test_performed'] and proof['private_cloud_saved_version']['independent_readback']
assert proof['private_cloud_saved_version']['kernel']=='rocky62/urop-mm-part1-science-epoch2-20261027/1'
audit=load(ROOT/'results/MM_PART1_FINAL_CLOUD_AUDIT_20261027.json')
assert audit['request_succeeded'] and all(s=='KernelWorkerStatus.COMPLETE' for s in audit['kernels'].values())
assert audit['gpu_quota']['time_reserved']==0
metadata=load(BASE/'final_notebook_metadata/kernel-metadata.json')
assert metadata['is_private'] is True and metadata['enable_gpu'] and metadata['machine_shape']=='NvidiaTeslaT4'
assert metadata['id']=='rocky62/urop-mm-part1-science-epoch2-20261027'
reg=load(ROOT/'results/MM_PART1_USABLE_COHORT_REGISTRATION_20261024.json')
assert sha(ROOT/'results/MM_PART1_USABLE_COHORT_REGISTRATION_20261024.json')=='3fe0b622958a1eee6732789d4f7acf6b450c0e3bda87312e5cbb6500fb405ce5'
protocol=load(RUN/'protocol.json');recovery=load(RUN/'runtime_recovery.json')
assert protocol['config_sha256']=='ad8f86f86b1fef453ae3bccda0aeb13cc50b298dc0d5d502f87c9ac4b041b483'
assert recovery['state']['epoch']==3 and recovery['state']['cursor']==0 and recovery['state']['phase']=='train'
assert recovery['state']['updates']+recovery['state']['skips']==35226
values=proof['validation'];selected=max(values,key=lambda x:(x['metrics']['macro_f1'],-x['metrics']['loss'],-x['epoch']))
assert selected['epoch']==proof['selected_epoch']==recovery['state']['best']['epoch']
assert all(v['metrics']['samples']==59299 for v in values)
OUT.mkdir(parents=True,exist_ok=True)
names=['protocol.json','environment.json','history.json','runtime_recovery.json','cloud_job_runtime_result.json','recovery/generations.json']
names += ['validation_epoch%d_%s.json'%(e,s) for e in [1,2] for s in ['metrics','classification_report','confusions']]
for name in names:
    src=RUN/name
    if name in proof['artifacts']:assert sha(src)==proof['artifacts'][name]['sha256']
    dst=OUT/Path(name).name
    if dst.exists():assert sha(dst)==sha(src),'Preserve an existing conflicting aggregate'
    else:shutil.copyfile(src,dst)
for e in [1,2]:
    conf=load(OUT/f'validation_epoch{e}_confusions.json')
    for kind in ['raw','row_normalized']:
        with (OUT/f'validation_epoch{e}_confusion_{kind}.csv').open('w',newline='') as f:
            writer=csv.writer(f);writer.writerow(['Gold / predicted',*conf['labels']])
            writer.writerows([label,*row] for label,row in zip(conf['labels'],conf[kind]))
write(OUT/'selected_checkpoint.json',recovery['state']['best'])
write(OUT/'private_large_artifact_manifest.json',{'private_cloud_version':proof['private_cloud_saved_version'],
    'local_private_run':str(RUN.relative_to(ROOT)), 'artifacts':proof['artifacts'],
    'raw_data_weights_predictions_not_in_git':True})
aggregates={str(p.relative_to(ROOT)):{'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(OUT.iterdir()) if p.name!='aggregate_artifact_manifest.json'}
write(OUT/'aggregate_artifact_manifest.json',{'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'files':aggregates,'manifest_excludes_itself':True})
benchmark=load(ROOT/'results/MM_PAPER_BENCHMARK_RECHECK_20261027.json')
delta=100*(selected['metrics']['accuracy']-benchmark['validation_accuracy'])
q=audit['gpu_quota'];remaining=(q['total_time_allowed']-q['time_used']-q['time_reserved'])/3600
receipt={'schema':1,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'state':'verified_part1_science_and_recovery',
    'attempt':ATTEMPT,'cohort':reg['cohort_id'],'split_counts':reg['split_counts'],'original_rows':682661,'approved_usable_pairs':682170,'approved_exclusions':491,
    'registered_epochs':4,'epochs_trained':2,'epochs_validated':2,'scientific_experiments':1,'scientific_cloud_jobs':2,'seed':42,
    'model':'BERT-base-uncased + ResNet-50 maximum fusion','text_warmstart_epoch':4,'classification':'six-way',
    'validation':values,'selected_epoch':selected['epoch'],'selected_weights':recovery['state']['best'],
    'recovery_next_epoch':3,'recovery_next_cursor':0,'recovery':proof['recovery'],
    'successful_optimizer_updates':recovery['state']['updates'],'amp_skipped_updates':recovery['state']['skips'],
    'no_test_performed':True,'part2_started':False,'private_output':proof['private_cloud_saved_version'],
    'independent_verification_receipt':'results/MM_PART1_EPOCH2_VERIFIED_20261027.json',
    'aggregate_artifact_manifest':str((OUT/'aggregate_artifact_manifest.json').relative_to(ROOT)),
    'private_large_artifact_manifest':str((OUT/'private_large_artifact_manifest.json').relative_to(ROOT)),
    'paper_validation_accuracy':benchmark['validation_accuracy'],'paper_test_accuracy':benchmark['test_accuracy'],
    'selected_validation_accuracy_gain_pp':delta,'minimum_plus1pp_validation_target_met':delta>=1,
    'final_test_target_status':'Pending Part2; not measured in Part1',
    'cloud_gpu':'Tesla T4; one visible/used device, T4x2 allocation','environment':load(RUN/'environment.json'),
    'actual_docker_image':metadata['docker_image'],'gpu_quota_observed':audit,'observed_gpu_hours_remaining':remaining,
    'workflow_percent':{'text_only':100,'text_plus_image':60,'image_only':20,'overall':60},
    'part1_package_percent':100,'final_documentation_git_backup_verified':False,
    'final_git_backup_receipt':'results/MM_PART1_FINAL_GIT_BACKUP_20261027.json',
    'limitations':['Approved usable-image cohort excludes491 strict decode failures; released cohort differs from paper count.',
        'Our end-to-end BERT-base warmstart/projection/budget differs from paper fixed BERT feature and tuned classifier pipeline.',
        'Single seed; validation numerical improvement is not a final-test or statistical-superiority claim.']}
write(ROOT/'results/MM_PART1_RECEIPT_20261027.json',receipt)
lines=['# Multimodal Part 1 — verified results','',
    'One registered four-epoch experiment, seed 42. **Epochs 1–2 and both full validations are complete.** Part 2 and final test inference have not started.','',
    '## Acceptance steps','',
    '- 4 — Passed actual T4 CUDA/AMP recovery and measured capacity. Exact interrupted/resumed fixture agreed; storage fix improved measured training from 10.13 to 57.40 pairs/s and reduced loader waiting from 84.80% to 0.25%.',
    '- 5 — Completed epoch 1 on 563,601 pairs and validation on 59,299; saved/retrieved/reloaded checkpoints and independently recomputed all metrics.',
    '- 6 — Resumed the same experiment; completed epoch 2 and a second full 59,299-pair validation.',
    '- 7 — Independently verified predictions, six-class reports/confusions, selected weights and complete epoch 3 / cursor 0 recovery; local/private artifacts and project records preserved. Final Git proof is linked below.','',
    '## Faculty data','',
    '[Faculty dataset](https://drive.google.com/drive/folders/1DuH0YaEox08ZwzZDpRMOaFpMCeRyxiEF): original `multimodal_train.tsv`, `multimodal_validate.tsv`, `multimodal_test_public.tsv`. Original files, IDs, titles, split assignments and six labels are preserved.','',
    '| Split | Original TSV rows | Approved usable pairs | Documented exclusions |','|---|---:|---:|---:|',
    '| Train | 564000 | 563601 | 399 |','| Validation | 59342 | 59299 | 43 |','| Public test, integrity only | 59319 | 59270 | 49 |',
    '| Total | 682661 | 682170 | 491 |','',
    'The 491 strict decoding failures were explicitly approved for exclusion on 24 October. No further rows, difficult classes or duplicates were silently removed. All 682,170 images passed byte-hash and strict-decoding checks in the saved image gate; all 39 raw packs retain their original bytes.','',
    'The paper lists 682,996 multimodal samples, while the released TSVs total 682,661; the 335-row release discrepancy remains unresolved. Our approved usable cohort is 682,170. Exclusion class counts are retained in the pinned cohort registration; missing images are not assumed to be missing at random.','',
    '## Actual architecture and workflow','',
    'BERT-base-uncased is initialized from the verified selected text-only epoch 4 weights. ResNet-50 uses ImageNet1K V2 initialization. Both encoders are fine-tuned using the frozen multimodal configuration.','',
    '```mermaid','flowchart LR','  T[clean_title] --> K[BERT WordPiece · max 128] --> B[BERT-base · CLS 768] --> P[Linear 768→512 + LayerNorm]',
    '  I[Faculty image · RGB 224×224] --> R[ResNet-50 · feature 2048] --> Q[Linear 2048→512 + LayerNorm]',
    '  P --> M[Elementwise maximum · 512]','  Q --> M','  M --> H[Linear 512→256 · GELU · dropout 0.2] --> C[Linear 256→6 logits]','```','',
    'Workflow: verify immutable data/source hashes → restore model/optimizer/scheduler/scaler/RNG → train full epoch → full validation → export per-ID probabilities/loss → independently verify → private/local/Git backup → resume next epoch. No LR/sampler restart, resampling, test-driven selection or model substitution.','',
    '## Full validation metrics','',
    '| Metric | Paper six-way multimodal | Epoch 1 | Epoch 2 |','|---|---:|---:|---:|']
for key,label,percent in [('accuracy','Accuracy',True),('micro_f1','Micro-F1',False),('macro_f1','Macro-F1',False),('weighted_f1','Weighted-F1',False),('balanced_accuracy','Balanced accuracy',True),('loss','Cross-entropy loss',False)]:
    vals=[f"{100*v['metrics'][key]:.4f}%" if percent else f"{v['metrics'][key]:.6f}" for v in values]
    paper='86.0000%' if key=='accuracy' else 'Not reported'
    lines.append('| '+label+' | '+paper+' | '+' | '.join(vals)+' |')
lines += ['',f"Selected checkpoint: **epoch {selected['epoch']}**, by validation Macro-F1, then lower loss, then earlier epoch. Each validation contains exactly 59,299 unique approved IDs.",'',
    f"Selected validation accuracy is **{100*selected['metrics']['accuracy']:.4f}%**, **{delta:+.4f} percentage points** versus the paper's 86.00%. The minimum +1-point validation aspiration is {'met' if delta>=1 else 'not met'}. The paper's test accuracy is 85.88%; our final test is pending Part 2, with the registered 86.88% aspiration.",'',
    "Source: [paper Tables 4–5](https://arxiv.org/html/1911.03854v2). Other aggregate metrics and class F1 are not reported; Table 6 gives test-class error proportions, which are not F1. Our cohort and fine-tuning procedure differ, so this is a numerical validation reference, not an exact paper replication or proof of a test improvement.",'',
    'Epoch 2 improved accuracy and Macro-F1; its loss increased from 0.499369 to 0.564860. The registered Macro-F1 selection rule is retained.','',
    '## Six-class validation reports','']
for e in [1,2]:
    report=load(OUT/f'validation_epoch{e}_classification_report.json');conf=load(OUT/f'validation_epoch{e}_confusions.json')
    lines += [f'### Epoch {e}','','| Class | Precision | Recall | F1 | Support |','|---|---:|---:|---:|---:|']
    for label in conf['labels']:
        r=report[label];lines.append(f"| {label} | {r['precision']:.6f} | {r['recall']:.6f} | {r['f1-score']:.6f} | {int(r['support'])} |")
    lines += ['',f'Raw and row-normalized 6×6 confusion matrices: `{OUT.relative_to(ROOT)}/validation_epoch{e}_confusions.json`, plus labelled CSV copies in the same folder.','']
text=load(ROOT/'results/MM_TEXT_SAME_USABLE_VALIDATION_20261027.json')
lines += ['## Comparison with preserved text-only results','',
    f"On the same 59,299 usable validation IDs, saved text-only predictions give accuracy {100*text['metrics']['accuracy']:.4f}% and Macro-F1 {text['metrics']['macro_f1']:.6f}. Selected multimodal validation accuracy differs by {100*(selected['metrics']['accuracy']-text['metrics']['accuracy']):+.4f} points. This comparison performs no new model inference and preserves the original text results. The text model trained on 564,000 rows; multimodal uses 563,601. Filtered text loss cannot be reconstructed from confidence-only predictions and is not estimated.",'',
    '## Cloud, recovery and evidence','',
    '- Kaggle private scientific jobs: [epoch 1](https://www.kaggle.com/code/rocky62/urop-mm-part1-science-usable-20261027) and [epoch 2](https://www.kaggle.com/code/rocky62/urop-mm-part1-science-epoch2-20261027), both Version 1. Two bounded jobs are one experiment, not two independent seeds.',
    '- Recovery engineering fixture: random tiny BERT plus full random ResNet-50 on 13 synthetic pairs; same-T4 interrupted/resumed state difference was zero. The separate 600-second capacity measurement used the actual pretrained full model and real train images. This is not a cross-device bitwise reproducibility claim.',
    '- Actual used GPU: Tesla T4, one CUDA-visible device 0. Kaggle allocated T4×2; the second device was not used for model training.',
    '- Runtime: Python 3.13.15, PyTorch 2.11.0+cu128/CUDA 12.8, torchvision 0.26.0+cu128, Transformers 4.48.3, NumPy 2.1.3, Pillow 13.0.0; actual GPU Docker digest is in the final receipt.',
    f"- Observed account GPU quota at {audit['utc']}: used {q['time_used']/3600:.4f}h / total {q['total_time_allowed']/3600:.4f}h, reserved {q['time_reserved']/3600:.4f}h, remaining {remaining:.4f}h. All registered jobs are terminal COMPLETE.",
    f"- Recovery for Part 2: epoch 3, consumed cursor 0; model/BatchNorm, optimizer, four-epoch scheduler, AMP scaler, RNG, selection history and source/data contracts are present. Successful optimizer updates {recovery['state']['updates']}; skipped AMP updates {recovery['state']['skips']}; total 35,226 registered boundaries.",
    f"- Latest recovery SHA256: `{proof['recovery']['loaded']['sha256']}`; private/local tensor files are listed in `{OUT.relative_to(ROOT)}/private_large_artifact_manifest.json`.",
    '- Large model tensors, original data/images and per-ID prediction exports stay in ignored local/private cloud storage. Git contains code, aggregate results, reports and checksums.',
    '- Final backup proof: `results/MM_PART1_FINAL_GIT_BACKUP_20261027.json` (written after remote readback).','',
    '## Progress and next action','',
    'Part 1 package 100%. Text-only 100%; text + image 60%; image-only 20%; three-modality overall 60%. Multimodal training 2/4 and full validation 2/4; final test 0.','',
    'Part 2 starts from the verified epoch 3 / cursor 0 checkpoint of this SAME attempt and configuration. Read `context/MULTIMODAL_PART2_EXECUTION_PLAN_20261023.md` with the approved usable-cohort amendment. Finish remaining registered training/validation, select by the frozen validation procedure, then perform the authorized one-time final public test and independent reporting. Part 2 and image-only were not run here.','']
(ROOT/'results/MM_PART1_REPORT_20261027.md').write_text('\n'.join(lines))
print(json.dumps({'report':'results/MM_PART1_REPORT_20261027.md','receipt':'results/MM_PART1_RECEIPT_20261027.json','selected_epoch':selected['epoch'],'validation_accuracy':selected['metrics']['accuracy'],'paper_gain_pp':delta,'aggregate_files':len(aggregates),'private_artifact_checks':len(proof['artifacts']),'final_git_proof_pending':True}))
