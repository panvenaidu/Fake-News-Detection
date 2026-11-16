"""Validate complete official prediction evidence without running model inference."""
import hashlib
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, balanced_accuracy_score, classification_report, confusion_matrix, f1_score

LABELS = ['True','Satire/Parody','Misleading Content','Imposter Content','False Connection','Manipulated Content']

def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()

def verify_split(folder, split, frame):
    folder=Path(folder)
    pred=pd.read_csv(folder/f'{split}_predictions.csv',dtype={'id':str})
    assert len(pred)==len(frame) and not pred.id.duplicated().any()
    assert pred.id.tolist()==frame.id.tolist(), f'{split}: IDs/order differ from official file'
    y=frame['6_way_label'].astype(int).to_numpy();p=pred.predicted_label.to_numpy()
    assert np.array_equal(pred.true_label.to_numpy(),y)
    assert np.isin(p,np.arange(6)).all()
    assert np.isfinite(pred.confidence).all() and pred.confidence.between(0,1).all()
    scores={'accuracy':float(accuracy_score(y,p)), 'micro_f1':float(f1_score(y,p,average='micro')),
        'macro_f1':float(f1_score(y,p,average='macro',labels=range(6),zero_division=0)),
        'weighted_f1':float(f1_score(y,p,average='weighted',zero_division=0)),
        'balanced_accuracy':float(balanced_accuracy_score(y,p)), 'samples':len(y)}
    saved=json.loads((folder/f'{split}_metrics.json').read_text())
    for key,value in scores.items():
        assert key in saved and math.isclose(value,saved[key],rel_tol=0,abs_tol=1e-12),(split,key,value,saved.get(key))
    assert math.isfinite(saved['loss']) and saved['loss']>=0
    cm=confusion_matrix(y,p,labels=range(6))
    assert np.array_equal(cm,pd.read_csv(folder/f'{split}_confusion_matrix.csv',index_col=0).to_numpy())
    normalized=cm/np.maximum(cm.sum(axis=1,keepdims=True),1)
    assert np.allclose(normalized,pd.read_csv(folder/f'{split}_confusion_matrix_normalized.csv',index_col=0).to_numpy(),rtol=0,atol=1e-12)
    report=classification_report(y,p,labels=range(6),target_names=LABELS,output_dict=True,zero_division=0)
    saved_report=json.loads((folder/f'{split}_classification_report.json').read_text())
    for label in LABELS+['macro avg','weighted avg']:
        for key,value in report[label].items():
            assert math.isclose(value,saved_report[label][key],rel_tol=0,abs_tol=1e-12),(split,label,key)
    return {'rows':len(pred),'metrics_recomputed':scores,'prediction_sha256':sha(folder/f'{split}_predictions.csv'),
        'loss_verified':'finite stored inference loss; confidence alone does not reconstruct CE loss'}

def verify_complete(folder, frames, require_weights=True):
    folder=Path(folder);result=json.loads((folder/'result.json').read_text())
    frozen=json.loads((folder/'selected_checkpoint.json').read_text())
    if require_weights:assert sha(folder/'best_weights.pt')==frozen['weight_sha256']
    assert result['selected_weight_sha256']==frozen['weight_sha256']
    assert result['checkpoint_epoch']==frozen['epoch']
    history=json.loads((folder/'history.json').read_text())
    assert len(history)==result['epochs_completed']
    selected=min(history,key=lambda x:(-x['validation']['macro_f1'],x['validation']['loss'],x['epoch']))
    assert selected['epoch']==frozen['epoch'] and selected['validation']==result['validation_selection']
    for row in history:
        assert math.isfinite(row['train_loss'])
        assert all(math.isfinite(float(v)) for v in row['validation'].values())
    checks={s:verify_split(folder,s,frames[s]) for s in ['validation','test']}
    for split in checks:
        for key,value in checks[split]['metrics_recomputed'].items():
            assert math.isclose(value,result[split][key],rel_tol=0,abs_tol=1e-12)
    assert result['optimizer_updates']+result['skipped_updates']==len(history)*17625
    return {'status':'verified','tolerance':1e-12,'selected_epoch':frozen['epoch'],
        'selected_weight_sha256':frozen['weight_sha256'],'splits':checks,'single_seed':True}
