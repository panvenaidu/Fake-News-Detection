"""Independently verify immutable, reopened ViT artifacts; no inference or tuning."""
import argparse
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import (accuracy_score, balanced_accuracy_score, classification_report,
                             confusion_matrix, f1_score)

from packed_image_io_v3 import sha

LABELS = ['True', 'Satire/Parody', 'Misleading Content', 'Imposter Content',
          'False Connection', 'Manipulated Content']


def read(p):
    return json.loads(p.read_text())


def require(ok, reason):
    if not bool(ok):
        raise ValueError(reason)


def match(saved, estimated, context):
    if isinstance(saved, dict) and isinstance(estimated, dict):
        require(saved.keys()==estimated.keys(), f'Field mismatch: {context}')
        for k in saved:
            match(saved[k], estimated[k], context+'.'+str(k))
    elif isinstance(estimated, (float, int, np.number)):
        require(abs(saved-estimated) <= 1e-10, f'Metric mismatch: {context}')
    else:
        require(saved==estimated, f'Value mismatch: {context}')


def prediction_file(folder, name, official):
    p = folder/f'{name}_predictions.csv'
    table = pd.read_csv(p, dtype={'id':str}, float_precision='round_trip')
    require(table.columns.tolist()==['id','split','true_label','predicted_label','cross_entropy',
                                     *[f'p{i}' for i in range(6)]], 'Unexpected prediction columns')
    require(table.id.is_unique and np.array_equal(table.id,official.id)
            and np.array_equal(table.split,official.split), f'{name}: ID or split mismatch')
    y = table.true_label.to_numpy(dtype=np.int64)
    pred = table.predicted_label.to_numpy(dtype=np.int64)
    require(np.array_equal(y,table.true_label) and np.array_equal(pred,table.predicted_label)
            and np.array_equal(y,official['6_way_label']), f'{name}: gold labels or argmax changed')
    probs = table[[f'p{i}' for i in range(6)]].to_numpy()
    ce = table.cross_entropy.to_numpy()
    require(np.isfinite(probs).all() and ((probs>=0)&(probs<=1)).all()
            and np.allclose(probs.sum(1), 1., atol=2e-6, rtol=0)
            and np.array_equal(pred,probs.argmax(1)), f'{name}: invalid probabilities or argmax')
    gold=probs[np.arange(len(y)),y]
    require(np.isfinite(ce).all() and (ce>=0).all() and (gold>0).all(),
            f'{name}: invalid cross entropy or probability underflow')
    loss=-np.log(gold)
    require(np.allclose(ce,loss,atol=2e-5,rtol=2e-5),f'{name}: probability loss mismatch')
    acc=float(accuracy_score(y,pred))
    metrics={'accuracy':acc,'micro_f1':acc,'macro_f1':float(f1_score(y,pred,labels=range(6),average='macro',zero_division=0)),
             'weighted_f1':float(f1_score(y,pred,labels=range(6),average='weighted',zero_division=0)),
             'balanced_accuracy':float(balanced_accuracy_score(y,pred)),
             'loss':float(ce.mean()),'samples':len(y)}
    classes=classification_report(y,pred,labels=range(6),target_names=LABELS,output_dict=True,zero_division=0)
    match(read(folder/f'{name}_metrics.json'),metrics,name+'.metrics')
    match(read(folder/f'{name}_classification_report.json'),classes,name+'.classes')
    cm=confusion_matrix(y,pred,labels=range(6))
    confusion=read(folder/f'{name}_confusions.json')
    require(confusion['labels']==LABELS and np.array_equal(confusion['raw'],cm),f'{name}: raw confusion mismatch')
    row_sum=cm.sum(1,keepdims=True)
    norm=np.divide(cm,row_sum,out=np.zeros_like(cm,dtype=float),where=row_sum!=0)
    np.testing.assert_allclose(confusion['row_normalized'],norm,atol=1e-12,rtol=0)
    return table,{'metrics':metrics,'probability_cross_entropy':float(loss.mean()),'classes':classes,
                  'confusion':confusion,'prediction_sha256':sha(p)}


def selection(point):
    m=point['validation']
    return m['accuracy'],m['macro_f1'],-m['loss'],-point['epoch']


def wilson(correct,total):
    p=correct/total
    z=1.959963984540054
    center=(p+z*z/(2*total))/(1+z*z/total)
    width=z*math.sqrt(p*(1-p)/total+z*z/(4*total*total))/(1+z*z/total)
    return [center-width,center+width]


def paired(base, current, expected_sha, expected_accuracy, image_group=None):
    require(sha(base)==expected_sha,'Baseline prediction artifact SHA mismatch')
    old=pd.read_csv(base,dtype={'id':str},usecols=['id','true_label','predicted_label'])
    require(old.id.is_unique and len(old)==len(current) and set(old.id)==set(current.id),
            'Incompatible paired baseline IDs')
    old=old.set_index('id').loc[current.id].reset_index()
    require(np.array_equal(old.true_label,current.true_label),'Incompatible paired baseline labels')
    old_ok=(old.true_label==old.predicted_label).to_numpy()
    require(abs(old_ok.mean()-expected_accuracy)<1e-6,'Wrong paired baseline accuracy')
    delta=(current.true_label==current.predicted_label).to_numpy(dtype=int)-old_ok.astype(int)
    n=len(delta)
    counts=np.bincount(delta+1,minlength=3)
    boot=np.random.default_rng(2135).multinomial(n,counts/n,20000)
    proof={'paired_delta':float(delta.mean()),'better':int(counts[2]),'worse':int(counts[0]),'tied':int(counts[1]),
           'paired_iid_bootstrap_95pct':np.quantile((boot[:,2]-boot[:,0])/n,[.025,.975]).tolist(),
           'baseline_prediction_sha256':expected_sha}
    if image_group is not None:
        proof['paired_byte_group_bootstrap_95pct']=group_interval(delta, image_group, 8221)
    return proof


def group_interval(row_values, image_group, seed):
    group=pd.Series(row_values).groupby(image_group).agg(['sum','count'])
    numerator=group['sum'].to_numpy()
    denominator=group['count'].to_numpy()
    group_rng=np.random.default_rng(seed)
    draws=[]
    for _ in range(50):
        weights=group_rng.poisson(1,(20,len(group)))
        totals = weights @ denominator
        nonempty = totals > 0
        draws.extend((weights @ numerator)[nonempty] / totals[nonempty])
    return np.quantile(draws,[.025,.975]).tolist()



def verify_recovery(path, complete, trial, config, registration_sha256, world_size):
    """Open the saved optimizer state on CPU and reconcile it with the trial receipt."""
    import torch

    receipt = read(path.with_suffix('.json'))
    require(path.stat().st_size == receipt['bytes']
            and complete['resume_sha256'] == receipt['sha256'] == sha(path),
            'Recovery checkpoint hash differs')
    state = torch.load(path, map_location='cpu', weights_only=True)
    expected_contract = {'trial': trial, 'config': config,
                         'registration_sha256': registration_sha256, 'world_size': world_size}
    require(state['contract'] == expected_contract, 'Recovery trial contract differs')
    progress = state['progress']
    require(progress == receipt['progress'] and all(complete[k] == v for k, v in progress.items()),
            'Recovery progress differs from the restart and completion receipts')
    require(progress['epoch'] == len(progress['history'])+1 and progress['cursor'] == 0,
            'Completed trial recovery has a partial epoch cursor')
    require(state['scheduler']['last_epoch'] == progress['updates'], 'Recovery learning rate step differs')
    optimizer = state['optimizer']
    require(len(optimizer['param_groups']) > 0 and bool(optimizer['state'])
            and bool(state['scaler']) and len(state['rng']) == world_size,
            'Recovery state lacks optimizer, AMP, or per-rank RNG data')
    require(state['model'] and all(isinstance(v, torch.Tensor) for v in state['model'].values()),
            'Recovery does not contain a tensor state dictionary')
    for rank_rng in state['rng']:
        require(len(rank_rng) == 4 and isinstance(rank_rng[2], torch.Tensor)
                and isinstance(rank_rng[3], torch.Tensor),
                'Recovery does not contain both CPU and CUDA RNG data for each rank')
    return receipt['sha256']


def verify(folder,baseline_specs=(), official_frames=None, source_version=None):
    folder=Path(folder)
    reg=read(folder/'registration.json')
    bad_names=set(reg['sources'])-set(p.name for p in (folder/'source').iterdir())
    require(not bad_names,'Saved source is missing')
    for name,digest in reg['sources'].items():
        require(sha(folder/'source'/name)==digest,f'Saved source differs: {name}')
    cfg=reg['config']
    require(cfg['input_features']==['RGB_pixels'] and cfg['selection']==[
            'accuracy','macro_f1','lower_cross_entropy','earlier_epoch'], 'Wrong modality or selection rule')
    timing_path=folder/'preflight/timing.json'
    timing=read(timing_path)
    require(sha(timing_path)==reg['preflight_sha256'] and timing['continuation_passed']
            and timing['validation_reload_exact'] and timing['encoder_and_head_changed'],
            'Saved preflight receipt did not pass')
    freeze=read(folder/'selection_frozen.json')
    require(freeze['state']=='frozen_before_test' and freeze['seed']==42 and not freeze['additional_seeds'],
            'Unrecognized test selection contract')
    require(sha(folder/'registration.json')==freeze['registration_sha256']
            and sha(folder/'promotion.json')==freeze['promotion_sha256'], 'Freeze contract hashes differ')
    finalists=freeze.get('finalists', {freeze['final_trial']['id']:{'trial':freeze['final_trial'],
                                                         'selected':freeze['selected'],
                                                         'complete_sha256':freeze['complete_sha256']}})
    trials=reg['pilots']+[x['trial'] for x in finalists.values()]
    manifests={}
    expected=reg['cohort_contract']['inputs']['counts']
    for split,n in {**expected,'pilot_train':cfg['pilot_rows']}.items():
        p=folder/f'{split}_manifest.csv'
        m=pd.read_csv(p,dtype={'id':str,'image_sha256':str},keep_default_na=False)
        s='train' if split=='pilot_train' else split
        require(len(m)==n and m.id.is_unique and m.split.eq(s).all() and set(m['6_way_label'])==set(range(6)),
                f'Bad saved split membership: {split}')
        require(m.image_sha256.str.fullmatch('[0-9a-f]{64}').all(),'Bad image byte hash')
        if split!='test':
            require(sha(p)==reg['cohort_contract']['splits'][split],f'Changed registered split {split}')
        if official_frames is not None and split!='pilot_train':
            keys=['id','split','6_way_label','image_sha256']
            require(m[keys].equals(official_frames[split][keys]),f'Saved {split} differs from authoritative inputs')
        manifests[split]=m
    require(pd.concat([manifests[x] for x in expected]).id.is_unique,'IDs overlap between splits')
    subset_keys=['6_way_label','image_sha256']
    official_train=manifests['train'].set_index('id')
    pilot=manifests['pilot_train'].set_index('id')
    require(pilot[subset_keys].equals(official_train.loc[pilot.index,subset_keys]),'Pilot is not a training subset')
    history={}
    for trial in trials:
        trialdir=folder/trial['id']
        complete=read(trialdir/'complete.json')
        require(trial==complete['trial'] and not complete['paused'],'Trial did not complete')
        h=complete['history']
        require(read(trialdir/'history.json')==h and len(h)>0 and
                [x['epoch'] for x in h]==list(range(1,len(h)+1)), 'Wrong validation history')
        require(len(h)==trial['epochs'] or (trial['kind']=='full' and complete['stopped_early']
                and len(h)>=cfg['early_stop_min_epochs']), 'Training missed its registered cap or early stop')
        if complete['stopped_early']:
            best_accuracy=max(point['validation']['accuracy'] for point in h)
            first_best=next(point['epoch'] for point in h if point['validation']['accuracy']==best_accuracy)
            require(h[-1]['epoch']-first_best>=cfg['early_stop_patience'],
                    'Early stop did not meet registered accuracy patience')
        saved_resume=trialdir/'resume.pt'
        recovery_sha256 = verify_recovery(saved_resume, complete, trial, cfg,
                                          freeze['registration_sha256'], reg['world_size'])
        epochs=[]
        previous_updates=previous_skips=0
        for point in h:
            _,proof=prediction_file(trialdir,f"validation_epoch{point['epoch']}",manifests['validation'])
            require(proof['prediction_sha256']==point['validation_predictions_sha256'],'Validation file was changed')
            match(point['validation'],proof['metrics'],'history validation')
            for name in LABELS:
                match(point['class_recall'][name],proof['classes'][name]['recall'],'history class recall')
            want=point['epoch']*math.ceil(trial['rows']/cfg['effective_batch'])
            require(point['updates']+point['skips']==want and point['updates']>=previous_updates
                    and point['skips']>=previous_skips,'Optimizer boundary/sample counts do not reconcile')
            previous_updates,previous_skips=point['updates'],point['skips']
            epochs.append({
                'epoch': point['epoch'],
                'metrics': proof['metrics'],
                'class_recall': {name: proof['classes'][name]['recall'] for name in LABELS},
                'updates': point['updates'],
                'skips': point['skips'],
                'prediction_sha256': proof['prediction_sha256'],
            })
        best=max(h,key=selection)
        require(best==complete['best'] and sha(trialdir/best['selected_weight'])==best['weight_sha256'],
                'Checkpoint chosen by the wrong validation rule or weight hash changed')
        history[trial['id']] = {
            'trial': trial, 'selected': best, 'epochs_verified': len(epochs),
            'epochs': epochs, 'stopped_early': complete['stopped_early'],
            'recovery_sha256': recovery_sha256,
        }
    for trial_id, info in finalists.items():
        require(info['selected']==history[trial_id]['selected']
                and sha(folder/trial_id/'complete.json')==info['complete_sha256'],
                'Finalist receipt changed')
    full=freeze['final_trial']['id']
    require(full==max(finalists,key=lambda k:selection(history[k]['selected'])), 'Wrong full-cohort finalist won')
    require(freeze['selected']==history[full]['selected']
            and sha(folder/full/'complete.json')==freeze['complete_sha256'], 'Frozen winner differs')
    promotion=read(folder/'promotion.json')
    ranked=sorted(reg['pilots'],key=lambda p:selection(history[p['id']]['selected']),reverse=True)
    best_lr=ranked[0]['lr'] if ranked else cfg['encoder_lr']
    base_plan={**reg['full'],'lr':best_lr}
    require(promotion['full_trial']==base_plan and finalists[base_plan['id']]['trial']==base_plan,
            'Pilot promotion was not based on validation')
    skip=folder/'alternative_unavailable.json'
    if reg.get('alternative') and not skip.exists():
        alt={**reg['alternative'],'lr':best_lr}
        require(finalists[alt['id']]['trial']==alt and len(finalists)==2,'Missing registered DeiT comparison')
    else:
        require(len(finalists)==1,'Unregistered full-cohort finalist')
        if skip.exists():
            skipped=read(skip)
            require(skipped['state']=='not_started' and skipped['trial']==reg['alternative']
                    and skipped['utc']<=freeze['utc'],'Invalid abandoned alternative record')
    release=read(folder/'fixed_validation_receipt.json')
    frozen_hash=sha(folder/'selection_frozen.json')
    require(release['state']=='fresh_process_passed' and release['selection_sha256']==frozen_hash
            and release['checkpoint_sha256']==freeze['selected']['weight_sha256']
            and release['validation_predictions_sha256']==freeze['selected']['validation_predictions_sha256']
            and release['probability_max_error']<=release['probability_atol']
            and release['ce_max_error']<=release['cross_entropy_atol']
            and release['rows']==cfg['eval_batch'], 'Fresh process validation proof failed')
    begun=read(folder/'test_started.json')
    saved=read(folder/'test_saved.json')
    require(begun['utc']>=release['utc']>=freeze['utc'] and saved['utc']>=begun['utc']
            and begun['selection_sha256']==frozen_hash
            and begun['test_manifest_sha256']==sha(folder/'test_manifest.csv')
            and saved['test_started_sha256']==sha(folder/'test_started.json')
            and saved['fixed_validation_sha256']==sha(folder/'fixed_validation_receipt.json'),
            'Test did not follow the saved freeze and fresh reload')
    test=manifests['test']
    mask=~test.image_sha256.isin(set(manifests['train'].image_sha256))
    require(int(mask.sum())==cfg['expected_no_train_hash_count'],'Wrong exact-byte subset')
    tab,test_eval=prediction_file(folder,'test',test)
    sub,subset_eval=prediction_file(folder,'test_no_train_hash',test[mask].reset_index(drop=True))
    require(tab[mask].reset_index(drop=True).equals(sub),'Overlap subset predictions differ')
    require(saved['test_predictions_sha256']==test_eval['prediction_sha256'],'Changed frozen-test predictions')
    correct=(tab.true_label==tab.predicted_label).to_numpy()
    acc=test_eval['metrics']['accuracy']
    baseline={name:paired(p,tab,digest,value,test.image_sha256) for name,p,digest,value in baseline_specs}
    baselines = {'frozen_vit': cfg['historical_frozen_vit_accuracy'],
                 'historical_resnet': cfg['historical_resnet_accuracy']}
    matched_names = {'frozen_vit': 'Frozen ViT-B/16', 'historical_resnet': 'Historical ResNet-50'}
    for key, name in matched_names.items():
        if name in baseline:
            baselines[key] = acc - baseline[name]['paired_delta']
    return {'state':'saved_output_independently_verified','source_version':source_version,
            'authoritative_input_rechecked':official_frames is not None,'selection_sha256':frozen_hash,
            'selection':freeze['selected'],'configuration':cfg,'budget':reg['budget'],'validation':history,
            'test':test_eval,'no_train_hash':subset_eval,'target_reached':acc>=cfg['goal_accuracy'],
            'accuracy_wilson_95pct':wilson(int(correct.sum()),len(correct)),
            'accuracy_byte_group_poisson_bootstrap_95pct':group_interval(correct,test.image_sha256,2135),
            'accuracy_delta_pp_vs_frozen_vit':(acc-baselines['frozen_vit'])*100,
            'accuracy_delta_pp_vs_historical_resnet':(acc-baselines['historical_resnet'])*100,
            'accuracy_margin_pp_vs_target':(acc-cfg['goal_accuracy'])*100,
            'paired':baseline,'sessions':read(folder/'sessions.json'),
            'model_plan':freeze['final_trial'],
            'training_wall_seconds':read(folder/full/'complete.json')['segments_seconds'],
            'validation_reload':release}


def report(proof):
    a=proof['test']['metrics']
    b=proof['no_train_hash']['metrics']
    selection=proof['selection']
    plan=proof['model_plan']
    cfg=proof['configuration']
    variant=plan.get('variant',{})
    model=variant.get('candidate',cfg['model'])
    init=variant.get('candidate',cfg['initialization'])
    weights=variant.get('sha256',cfg['weight_sha256'])
    reached='reached' if proof['target_reached'] else 'missed'
    lines=['# Image-only six-class ViT fine-tuning', '',
           f"Verified full-test accuracy was **{a['accuracy']:.4%}** on **{a['samples']:,}** posts. "
           f"The model {reached} the 82.00% target ({proof['accuracy_margin_pp_vs_target']:+.4f} pp). "
           f"It scored {proof['accuracy_delta_pp_vs_historical_resnet']:+.4f} pp relative to historical fine-tuned ResNet-50 "
           f"and {proof['accuracy_delta_pp_vs_frozen_vit']:+.4f} pp relative to frozen ViT-B/16.", '',
           f"The selected {model} used {init} (initialization SHA-256 `{weights}`). "
           f"Selected epoch {selection['epoch']}, seed {cfg['seed']}, encoder LR {plan['lr']:.1e}. "
           f"Full trial used {proof['training_wall_seconds']/3600:.2f} h of measured training/validation time across sessions. "
           f"The saved test version is {proof['source_version']}.", '',
           '| Test cohort | Accuracy | Macro-F1 | Weighted-F1 | Balanced accuracy | Cross-entropy |',
           '|---|---:|---:|---:|---:|---:|']
    for name,m in [('Full test',a),('No exact training byte match',b)]:
        lines.append(f"| {name} ({m['samples']:,}) | {m['accuracy']:.4%} | {m['macro_f1']:.6f} | {m['weighted_f1']:.6f} | {m['balanced_accuracy']:.4%} | {m['loss']:.6f} |")
    lo,hi=proof['accuracy_wilson_95pct']
    glo,ghi=proof['accuracy_byte_group_poisson_bootstrap_95pct']
    lines+=['',f'Full accuracy 95% intervals: Wilson {lo:.4%}–{hi:.4%}; exact-byte grouped Poisson bootstrap {glo:.4%}–{ghi:.4%}. These intervals describe evaluation-sample uncertainty, not variation across seeds.']
    for name,row in proof['paired'].items():
        lo,hi=row['paired_iid_bootstrap_95pct']
        lines+=['',f"Paired {name}: {100*row['paired_delta']:+.4f} pp (row bootstrap 95% interval {100*lo:+.4f} to {100*hi:+.4f} pp)."]
        if 'paired_byte_group_bootstrap_95pct' in row:
            lo,hi=row['paired_byte_group_bootstrap_95pct']
            lines[-1]+=f' Exact-byte grouped interval: {100*lo:+.4f} to {100*hi:+.4f} pp.'
    lines += ['', '## Full-cohort validation', '',
              '| Trial | Epoch | Accuracy | Macro-F1 | Balanced accuracy | CE | Imposter recall |',
              '|---|---:|---:|---:|---:|---:|---:|']
    for trial_id, trial_result in proof['validation'].items():
        if trial_result['trial']['kind'] != 'full':
            continue
        for epoch in trial_result['epochs']:
            m = epoch['metrics']
            imposter = epoch['class_recall']['Imposter Content']
            lines.append(
                f"| {trial_id} | {epoch['epoch']} | {m['accuracy']:.4%} | {m['macro_f1']:.6f} | "
                f"{m['balanced_accuracy']:.4%} | {m['loss']:.6f} | {imposter:.4%} |"
            )
    lines += ['', 'The independent receipt includes each pilot epoch and recall for all six classes.']
    for key,name in [('test','Full test'),('no_train_hash','No exact training byte match')]:
        lines+=['',f'## {name}: per-class metrics','','| Label | Precision | Recall | F1 | Support |',
                '|---|---:|---:|---:|---:|']
        for label in LABELS:
            m=proof[key]['classes'][label]
            lines.append(f"| {label} | {m['precision']:.6f} | {m['recall']:.6f} | {m['f1-score']:.6f} | {int(m['support']):,} |")
    lines+=['','Independent readback checked full split IDs and labels, probability rows, per-row loss, confusion matrices, exact-byte subset membership, optimizer update counts and validation-only selection. The selected checkpoint reproduced a fixed validation batch in a fresh process. The full and row-normalized confusion matrices are in the saved verification JSON.',
            '', 'The benchmark was used by earlier models. Exact byte hashes do not detect near duplicates or overlap with external pretraining. The ResNet recipe, pretraining, and macro-F1-first selection differ; this is a descriptive comparison, not a matched architecture ablation.','']
    return '\n'.join(lines)


if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('folder',type=Path)
    ap.add_argument('--source-version')
    ap.add_argument('--resnet-csv',type=Path)
    ap.add_argument('--resnet-sha256')
    ap.add_argument('--output',type=Path)
    ap.add_argument('--report',type=Path)
    args=ap.parse_args()
    baselines=[]
    if args.resnet_csv:
        require(bool(args.resnet_sha256),'Supply historical verified prediction SHA-256')
        baselines.append(('historical_resnet50',args.resnet_csv,args.resnet_sha256,.8115572802429559))
    proof=verify(args.folder,baselines,source_version=args.source_version)
    serialized=json.dumps(proof,indent=2,allow_nan=False)+'\n'
    if args.report:
        args.report.write_text(report(proof))
    if args.output:
        args.output.write_text(serialized)
    else:
        print(serialized)
