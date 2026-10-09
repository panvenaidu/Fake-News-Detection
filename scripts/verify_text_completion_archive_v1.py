"""Verify retrieved BERT evidence/weights; no training, inference or downloads."""
import argparse
import gc
import json
import math
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import torch
from transformers import AutoConfig, AutoModelForSequenceClassification, AutoTokenizer, get_linear_schedule_with_warmup
from verify_completed_text_v1 import sha, verify_complete
from text_recovery_order_v1 import SCHEMA, epoch_order, order_hash


def main():
    p=argparse.ArgumentParser();p.add_argument('--evidence',required=True)
    p.add_argument('--weights',required=True);p.add_argument('--data',required=True)
    p.add_argument('--config',required=True);p.add_argument('--receipt',required=True)
    args=p.parse_args();root=Path(args.evidence);weights=Path(args.weights)
    cfg=json.loads(Path(args.config).read_text())
    assert json.loads((root/'protocol.json').read_text())==cfg
    assert sha(root/'protocol.json')==sha(args.config)
    manifest=json.loads((root/'artifact_manifest.json').read_text())
    for name,info in manifest.items():
        path=(root/name).resolve();assert path.is_relative_to(root.resolve())
        assert path.is_file() and path.stat().st_size==info['bytes'] and sha(path)==info['sha256'],name
    frames={};seen=set()
    for split,info in cfg['splits'].items():
        path=Path(args.data)/info['filename'];assert sha(path)==info['sha256']
        frame=pd.read_csv(path,sep='\t',dtype=str,keep_default_na=False,usecols=['id','clean_title','6_way_label'])
        assert len(frame)==info['rows'] and not frame.id.duplicated().any()
        assert not seen.intersection(frame.id);seen.update(frame.id)
        frames[split]=frame
    folder=root/'bert-base';checks=verify_complete(folder,frames,require_weights=False)
    frozen=json.loads((folder/'selected_checkpoint.json').read_text())
    assert sha(weights/'best_weights.pt')==frozen['weight_sha256']
    assert json.loads((weights/'selected_checkpoint.json').read_text())==frozen
    state=torch.load(weights/'resume_checkpoint.pt',map_location='cpu',weights_only=False)
    result=json.loads((folder/'result.json').read_text());history=json.loads((folder/'history.json').read_text())
    assert state['recovery_schema']==SCHEMA and state['epoch_finished']
    assert state['history']==history and state['epoch']==len(history)
    assert state['step_in_epoch']==17625 and state['samples_seen']==564000
    assert state['updates']==result['optimizer_updates'] and state['skips']==result['skipped_updates']
    assert state['updates']+state['skips']==17625*len(history)
    assert state['best']['epoch']==frozen['epoch'] and state['best']['metrics']==result['validation_selection']
    stopped=len(history)==cfg['max_epochs'] or (len(history)>=cfg['min_epochs'] and state['stale']>=cfg['patience'])
    assert stopped,'Training stopped before the registered stopping rule'
    order,_,next_rng=epoch_order(564000,state['sampler_start'])
    assert order_hash(order)==state['epoch_order_sha256']
    assert torch.equal(next_rng,state['sampler_next_rng']) and torch.equal(next_rng,state['loader_rng'])
    for name in ['model','optimizer','scheduler','scaler','python_rng','numpy_rng','torch_rng','cuda_rng']:
        assert name in state
    assert state['scheduler']['last_epoch']==state['updates']
    for t in state['model'].values():
        if isinstance(t,torch.Tensor) and t.is_floating_point():assert bool(torch.isfinite(t).all())
    model_cfg=AutoConfig.from_pretrained(weights,local_files_only=True)
    assert model_cfg.num_labels==6 and model_cfg.hidden_size==768
    model=AutoModelForSequenceClassification.from_config(model_cfg)
    model.load_state_dict(state['model'],strict=True)
    groups=[{'params':[],'weight_decay':cfg['weight_decay']},{'params':[],'weight_decay':0.}]
    for name,param in model.named_parameters():
        groups[int(name.endswith('bias') or 'norm' in name.lower())]['params'].append(param)
    opt=torch.optim.AdamW(groups,lr=next(m for m in cfg['models'] if m['name']=='bert-base')['learning_rate'],eps=1e-8)
    total_steps=17625*cfg['max_epochs']
    scheduler=get_linear_schedule_with_warmup(opt,math.ceil(total_steps*cfg['warmup_fraction']),total_steps)
    scaler=torch.amp.GradScaler('cpu')
    opt.load_state_dict(state['optimizer']);scheduler.load_state_dict(state['scheduler']);scaler.load_state_dict(state['scaler'])
    assert scheduler.last_epoch==state['updates'] and scaler.state_dict()==state['scaler']
    for param,moments in opt.state.items():
        for name in ['exp_avg','exp_avg_sq']:
            assert moments[name].shape==param.shape and bool(torch.isfinite(moments[name]).all())
    best=torch.load(weights/'best_weights.pt',map_location='cpu',weights_only=True)
    model.load_state_dict(best,strict=True)
    for t in best.values():
        if t.is_floating_point():assert bool(torch.isfinite(t).all())
    tokenizer=AutoTokenizer.from_pretrained(weights/'tokenizer',local_files_only=True)
    assert tokenizer.vocab_size==model_cfg.vocab_size
    receipt={'status':'verified','verified_utc':datetime.now(timezone.utc).isoformat(),
        'model':'bert-base','protocol_id':cfg['protocol_id'],'classes':6,'seed':42,
        'selected_epoch':frozen['epoch'],'best_weights_sha256':sha(weights/'best_weights.pt'),
        'resume_checkpoint_sha256':sha(weights/'resume_checkpoint.pt'),
        'epochs_completed':len(history),'training_stop_rule_satisfied':True,
        'optimizer_updates':state['updates'],'skipped_updates':state['skips'],
        'strict_model_optimizer_scheduler_amp_tokenizer_load':'passed; no inference or downloads',
        'sampler_end_state_matches':True,'archived_file_manifest':'all members matched',
        'prediction_checks':checks,'source':'Retrieved immutable saved Kaggle version356721456',
        'target_test_accuracy':0.7777,'target_reached':result['test']['accuracy']>=.7777,
        'paper_comparison_caveats':['single seed','BERT-base fine-tuning versus paper BERT-Large feature pipeline','released multimodal cohort335 fewer rows than paper statistic']}
    Path(args.receipt).write_text(json.dumps(receipt,indent=2,allow_nan=False)+'\n')
    print(json.dumps(receipt,indent=2))
    del model,best,state,frames,opt,scheduler,scaler;gc.collect()

if __name__=='__main__':main()
