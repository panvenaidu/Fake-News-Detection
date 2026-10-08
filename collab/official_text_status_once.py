from pathlib import Path
import json, subprocess
from datetime import datetime, timezone, timedelta
r=Path('/content/drive/MyDrive/Colab Notebooks/UROP/official_text_runs/OFFICIAL-6W-TEXT-v2_seed42_20261008T095827Z')
s=json.loads((r/'bert-base/status.json').read_text())
h=json.loads((r/'bert-base/history.json').read_text())
b=json.loads((r/'bert-base/best_checkpoint.json').read_text())
c=json.loads((r/'bert-base/recovery_checkpoint.json').read_text())
print('OFFICIAL FAKEDDIT — SIX-CLASS TEXT TRAINING')
print('Checked:',datetime.now(timezone(timedelta(hours=5,minutes=30))).strftime('%d %b %Y %I:%M:%S %p IST'))
print('BERT trainer:', 'RUNNING' if trainer.poll() is None else 'FINISHED / CHECK RESULTS')
print('Stage:',s['state'],'| Epoch:',s.get('epoch'),'of 6 | Batch:',s.get('step'),'of 17625')
print('GPU:',subprocess.check_output(['nvidia-smi','--query-gpu=name,utilization.gpu,memory.used','--format=csv,noheader'],text=True).strip())
print('Latest validation: accuracy %.2f%% | Macro-F1 %.2f%% (epoch %d)'%(100*h[-1]['validation']['accuracy'],100*h[-1]['validation']['macro_f1'],h[-1]['epoch']))
print('Selected checkpoint by Macro-F1: epoch',b['epoch'])
print('Saved recovery: epoch',c['epoch'],'batch',c['step'],'at',c['saved_utc'])
for model in ['bert-base','modernbert-base']:
    result=r/model/'result.json'
    if result.exists():
        test=json.loads(result.read_text())['test']
        print(model,'FINAL TEST: accuracy %.2f%% | Macro-F1 %.2f%%'%(100*test['accuracy'],100*test['macro_f1']))
    else: print(model,'final test pending' if model=='bert-base' else 'queued; not started')
print('This status check is complete. BERT continues independently; run this cell once to refresh.')
