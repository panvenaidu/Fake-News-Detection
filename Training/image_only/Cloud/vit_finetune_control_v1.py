"""Validation-only promotion, prospective compute planning, and isolated frozen test."""
import math
import time
from pathlib import Path

import numpy as np
import torch

# Import lazily in the driver functions: the training entry point also uses this module.


def register(out, cfg, session, preflight, source_hashes, alt=None):
    from train_vit_finetune_v1 import read, require, save_json, sha, stamp
    path = out/'registration.json'
    if path.exists():
        prior = read(path)
        require(prior['config']==cfg and prior['sources']==source_hashes
                and prior['world_size']==session['world_size']
                and all(session['environment'][k]==v for k,v in prior['environment_pin'].items())
                and (not prior.get('alternative')
                     or prior['optional_packages']==session['environment'].get('optional_packages',{})),
                'Locked run recipe/source/topology/environment changed')
        return prior
    timing = read(out/'preflight/timing.json')
    saved_runtime = read(out/'sessions.json')[0]['environment']
    for key in ('python','packages','cuda','cudnn'):
        require(saved_runtime[key]==session['environment'][key], f'Runtime pin changed: {key}')
    require(timing['device_count_used']==session['world_size'], 'Timing used a different GPU topology')
    require(session['environment']['free_bytes_working'] >= 10*1024**3, 'Insufficient saved output disk')
    require(timing['continuation_passed'] and timing['validation_reload_exact']
            and timing['encoder_and_head_changed'], 'Real-image smoke proof is absent')
    train_rate = timing['train_rows_per_second']
    eval_rate = timing['validation_rows_per_second']
    available = 3600*cfg['initial_quota_hours'] - 60*session['quota_used_minutes_observed']
    reserve = (3600*cfg['initial_quota_hours'])*cfg['reserve_fraction']
    remaining_wall = (available-reserve)/session['accounting_multiplier']
    full_rows, val_rows, test_rows = (preflight['inputs']['counts'][s] for s in ('train','validation','test'))
    save = timing['checkpoint_seconds']
    save_every = cfg['checkpoint_seconds']
    full_step_time = full_rows/train_rate
    pilot_step_time = cfg['pilot_rows']/train_rate
    per_full = 1.14*(full_step_time + val_rows/eval_rate + (math.ceil(full_step_time/save_every)+1)*save + 12)
    per_pilot = 1.14*(pilot_step_time + val_rows/eval_rate + (math.ceil(pilot_step_time/save_every)+1)*save + 12)
    test = 1.25*(test_rows/eval_rate+120)+session['setup_seconds']
    # Allow separate clean save sessions and continuation startup when approaching 12 hours.
    usable = remaining_wall - test - 3*max(600, session['setup_seconds']) - 900
    require(usable >= per_full, 'Measured quota cannot support a full training epoch and final evaluation')
    preferred_min = min(4, max(1, math.floor(usable/per_full)))
    pilots = []
    for epochs in (2, 1):
        if usable - len(cfg['pilot_lrs'])*epochs*per_pilot >= preferred_min*per_full:
            pilots = [{'id':f'pilot_lr_{lr:g}', 'kind':'pilot', 'lr':lr, 'epochs':epochs,
                       'rows':cfg['pilot_rows'], 'hypothesis':'Learning rate alters short-run adaptation',
                       'parent':'continuity_defaults'} for lr in cfg['pilot_lrs']]
            break
    remaining_train = usable-sum(p['epochs']*per_pilot for p in pilots)
    cap = min(cfg['full_max_epochs'], math.floor(remaining_train/per_full))
    require(cap>=1, 'No affordable full epoch')
    alternative = None
    optional = session['environment'].get('optional_packages', {})
    if alt and set(optional)=={'timm','safetensors'}:
        alt_cost = per_full * alt['estimated_cost_factor']
        max_alt = min(cfg['full_max_epochs'], math.floor((remaining_train-4*per_full)/alt_cost))
        if max_alt >= alt['minimum_epochs']:
            # Reserve at least four epochs per family before allocating extra epochs.
            cap=min(cap,max(4,math.floor((remaining_train-alt['minimum_epochs']*alt_cost)/per_full)))
            alt_epochs=min(cfg['full_max_epochs'],math.floor((remaining_train-cap*per_full)/alt_cost))
            alternative={'id':'deit3_seed42','kind':'full','rows':full_rows,'epochs':alt_epochs,
                         'variant':alt,'parent':'continuity', 'hypothesis':alt['hypothesis']}
    record = {'utc':stamp(),'config':cfg, 'world_size':session['world_size'], 'sources':source_hashes,
              'environment_pin':{k:saved_runtime[k] for k in ('python','packages','cuda','cudnn')},
              'preflight_sha256':sha(out/'preflight/timing.json'), 'cohort_contract':preflight,
              'optional_packages':optional,
              'budget':{'observed_initial_gpu_hours':cfg['initial_quota_hours'],
                        'live_used_minutes':session['quota_used_minutes_observed'],
                        'minimum_reserved_gpu_hours':reserve/3600,
                        'accounting_multiplier':session['accounting_multiplier'],
                        'estimated_full_epoch_seconds':per_full,'estimated_pilot_epoch_seconds':per_pilot,
                        'estimated_test_seconds':test,'startup_and_checkpoint_margin':3*max(600, session['setup_seconds'])+900,
                        'estimated_train_rows_per_second':train_rate,'estimated_validation_rows_per_second':eval_rate,
                        'checkpoint_seconds_measured':save,
                        'maximum_pilot_trials':len(pilots),'maximum_full_trials':1+int(alternative is not None),
                        'full_epoch_cap':cap,'alternative_epoch_cap':alternative['epochs'] if alternative else 0,
                        'additional_seed_count':0},
              'pilots':pilots,'alternative':alternative, 'full':{'id':'full_seed42','kind':'full','epochs':cap,'rows':full_rows,
                                      'parent':'best pilot or default if screening is unaffordable',
                                      'hypothesis':'Training all ViT blocks improves the image-only representation'}}
    save_json(path,record)
    print('budget_registered',record['budget'],flush=True)
    return record


def train_registered(buffer, out, cfg, store, frames, device):
    from train_vit_finetune_v1 import (read, require, save_json, sha, rank, barrier, stamp,
                                       selection, train_trial)
    reg_path=out/'registration.json'
    reg=read(reg_path)
    deadline=read(buffer/'session.json')['deadline_epoch']
    completed=[]
    for trial in reg['pilots']:
        result=train_trial(frames,store,cfg,device,trial,out/trial['id'],sha(reg_path),deadline)
        if result is None:
            return
        completed.append(result)
    ranked=sorted(completed,key=lambda x:selection(x['best']),reverse=True)
    full={**reg['full'], 'lr':ranked[0]['trial']['lr'] if ranked else cfg['encoder_lr']}
    promotion={'full_trial':full,'pilot_ranking':[{'trial':x['trial']['id'],'best':x['best']}
                                                  for x in ranked],
               'next_plausible_candidate':ranked[1]['trial']['id'] if len(ranked)>1 else None}
    if rank()==0:
        path=out/'promotion.json'
        if path.exists():
            require(read(path)==promotion,'Promotion changed after registration')
        else:
            save_json(path,promotion)
        print('promotion',promotion,flush=True)
    barrier()
    final=train_trial(frames,store,cfg,device,full,out/full['id'],sha(reg_path),deadline)
    if final is None:
        return
    finalists=[final]
    if reg.get('alternative') and not (out/'alternative_unavailable.json').exists():
        alt={**reg['alternative'], 'lr':full['lr']}
        challenger=train_trial(frames,store,cfg,device,alt,out/alt['id'],sha(reg_path),deadline)
        if challenger is None:
            return
        finalists.append(challenger)
    winner=max(finalists,key=lambda x:selection(x['best']))
    final=winner
    full=winner['trial']
    if rank()==0:
        freeze=out/'selection_frozen.json'
        receipt={'registration_sha256':sha(reg_path),'promotion_sha256':sha(out/'promotion.json'),
                 'state':'frozen_before_test','final_trial':full,'selected':final['best'],
                 'finalists':{x['trial']['id']:{'trial':x['trial'],'selected':x['best'],
                         'complete_sha256':sha(out/x['trial']['id']/'complete.json')} for x in finalists},
                 'complete_sha256':sha(out/full['id']/'complete.json'),
                 'seed':cfg['seed'], 'additional_seeds':[]}
        weight=out/full['id']/final['best']['selected_weight']
        require(sha(weight)==final['best']['weight_sha256'],'Selected weight file failed verification')
        if freeze.exists():
            require({k:v for k,v in read(freeze).items() if k!='utc'}==receipt,'Frozen selection changed')
        else:
            save_json(freeze,{**receipt,'utc':stamp()})
        print('frozen_validation_selection',sha(freeze),final['best'],flush=True)
    barrier()


def selected(out):
    from train_vit_finetune_v1 import read, require, sha
    freeze=read(out/'selection_frozen.json')
    path=out/freeze['final_trial']['id']/freeze['selected']['selected_weight']
    require(sha(out/'registration.json')==freeze['registration_sha256']
            and sha(out/'promotion.json')==freeze['promotion_sha256']
            and sha(out/freeze['final_trial']['id']/'complete.json')==freeze['complete_sha256']
            and sha(path)==freeze['selected']['weight_sha256'],'Frozen selection contract differs')
    return freeze,path


def fixed_validation(buffer, out, cfg, store, validation, device):
    from train_vit_finetune_v1 import (read, require, save_json, sha, network, predict, stamp)
    import pandas as pd
    freeze,path=selected(out)
    epoch=freeze['selected']['epoch']
    rows=validation.iloc[:cfg['eval_batch']]
    m=network(device,cfg,variant=freeze["final_trial"].get("variant"))
    m.load_state_dict(torch.load(path,map_location='cpu',weights_only=True),strict=True)
    prob,ce=predict(m, rows, store, cfg, device)
    exported=path.parent/f'validation_epoch{epoch}_predictions.csv'
    require(sha(exported)==freeze['selected']['validation_predictions_sha256'],'Selected validation predictions changed')
    saved=pd.read_csv(exported,dtype={'id':str},nrows=len(rows))
    require(saved.id.tolist()==rows.id.tolist() and np.array_equal(saved.true_label, rows['6_way_label']),
            'Fixed validation IDs/labels changed')
    np.testing.assert_allclose(prob,saved[[f'p{i}' for i in range(6)]],rtol=0,atol=.0003)
    np.testing.assert_allclose(ce,saved.cross_entropy,rtol=0,atol=.002)
    save_json(out/'fixed_validation_receipt.json', {'utc':stamp(),'state':'fresh_process_passed',
              'checkpoint_sha256':sha(path),'selection_sha256':sha(out/'selection_frozen.json'),
              'validation_predictions_sha256':sha(exported),'rows':len(rows),
              'probability_atol':.0003,'cross_entropy_atol':.002,
              'probability_max_error':float(np.max(np.abs(prob-saved[[f'p{i}' for i in range(6)]].to_numpy()))),
              'ce_max_error':float(np.max(np.abs(ce-saved.cross_entropy.to_numpy())))})


def frozen_test(buffer, out, cfg, store, train, device):
    from train_vit_finetune_v1 import (read, require, save_json, sha, network, predict, export_eval,
                                       stamp, frames_from_buffer)
    freeze,path=selected(out)
    receipt=read(out/'fixed_validation_receipt.json')
    require(sha(path)==receipt['checkpoint_sha256'] and receipt['state']=='fresh_process_passed'
            and sha(out/'selection_frozen.json')==receipt['selection_sha256'],'Fresh reload proof does not match release')
    if (out/'test_saved.json').is_file():
        print('Test predictions already saved; never rerun a completed test',flush=True)
        return
    test=frames_from_buffer(buffer,('test',))['test']
    require(len(test)==59270,'Wrong full test size')
    mask=~test.image_sha256.isin(set(train.image_sha256))
    require(int(mask.sum())==cfg['expected_no_train_hash_count'],'Exact byte overlap count differs')
    test_started=out/'test_started.json'
    require(not test_started.exists(),'An interrupted held-out evaluation requires review before retry')
    save_json(test_started, {'selection_sha256':sha(out/'selection_frozen.json'),
              'test_manifest_sha256':sha(out/'test_manifest.csv'),'utc':stamp()})
    m=network(device,cfg,variant=freeze["final_trial"].get("variant"))
    m.load_state_dict(torch.load(path,map_location='cpu',weights_only=True),strict=True)
    prob,ce=predict(m,test,store,cfg,device,read(buffer/'session.json')['deadline_epoch'])
    export_eval(out,'test',test,prob,ce)
    export_eval(out,'test_no_train_hash',test[mask].reset_index(drop=True),prob[mask],ce[mask])
    save_json(out/'test_saved.json',{'test_started_sha256':sha(test_started),
              'fixed_validation_sha256':sha(out/'fixed_validation_receipt.json'),
              'test_predictions_sha256':sha(out/'test_predictions.csv'),'utc':stamp()})
    print('frozen_test_complete',flush=True)
