"""Focused CPU recovery gates; safe to repeat on the installed Kaggle Torch."""
import argparse
import copy
import gc
import json
from datetime import datetime, timezone
from pathlib import Path

import torch
from torch.utils.data import DataLoader, TensorDataset
from text_recovery_order_v1 import SCHEMA, FixedSuffixSampler, epoch_order, order_hash, recover_order, update_counters


def sampler_gate():
    rows=128;bs=8
    ds=TensorDataset(torch.arange(rows));g=torch.Generator().manual_seed(42)
    old=DataLoader(ds,batch_size=bs,shuffle=True,generator=g,num_workers=2,persistent_workers=True)
    list(old)  # persistent workers already initialized in original epoch 1
    start=g.get_state().clone()
    itr=iter(old);prefix=[]
    for _ in range(10):prefix.extend(next(itr)[0].tolist())
    observed_mid=g.get_state().clone()
    tail=[]
    for b in itr:tail.extend(b[0].tolist())
    old_next=g.get_state().clone()
    state={'epoch':2,'sampler_start':start,'loader_rng':observed_mid,
           'step_in_epoch':10,'samples_seen':80}
    order,next_state,cursor=recover_order(state,rows,bs)
    assert order.tolist()==prefix+tail and torch.equal(next_state,old_next)
    sampler=FixedSuffixSampler();sampler.configure(order,cursor)
    fresh=DataLoader(ds,batch_size=bs,sampler=sampler,generator=torch.Generator().manual_seed(1042),num_workers=2,persistent_workers=True)
    resumed=[v for batch in fresh for v in batch[0].tolist()]
    assert resumed==tail and len(set(prefix+resumed))==rows
    second={**state,'recovery_schema':SCHEMA,'sampler_next_rng':next_state,
            'epoch_order_sha256':order_hash(order),'step_in_epoch':13,'samples_seen':104}
    second_order,second_next,second_cursor=recover_order(second,rows,bs)
    assert second_order[second_cursor:].tolist()==order[104:].tolist() and torch.equal(second_next,next_state)
    reference_next=[v for b in old for v in b[0].tolist()]
    boundary_order,_,boundary_next=epoch_order(rows,next_state)
    assert boundary_order.tolist()==reference_next and torch.equal(boundary_next,g.get_state())
    sampler.configure(boundary_order)
    assert [v for b in fresh for v in b[0].tolist()]==reference_next
    del old,fresh,itr;gc.collect()
    return {'later_epoch_resume':'same exact suffix; no duplicates or omissions',
            'second_interruption':'same remaining suffix',
            'epoch_boundary':'same next epoch and exhausted sampler RNG',
            'persistent_workers':2,'rows':rows,'batch_size':bs}


def tensor_equal(a,b):
    if isinstance(a,torch.Tensor):return torch.equal(a,b)
    if isinstance(a,dict):return a.keys()==b.keys() and all(tensor_equal(a[k],b[k]) for k in a)
    if isinstance(a,(list,tuple)):return len(a)==len(b) and all(tensor_equal(x,y) for x,y in zip(a,b))
    return a==b


def numerical_gate():
    # Real CPU GradScaler overflows verify actual optimizer skip handling.
    def construct():
        model=torch.nn.Sequential(torch.nn.Linear(4,8),torch.nn.Dropout(.2),torch.nn.Linear(8,2))
        opt=torch.optim.AdamW(model.parameters(),lr=.002)
        sched=torch.optim.lr_scheduler.LambdaLR(opt,lambda step:max(0.,1-step/48))
        scaler=torch.amp.GradScaler('cpu',init_scale=128,growth_interval=100)
        return model,opt,sched,scaler
    def run(restarts):
        torch.manual_seed(123);model,opt,sched,scaler=construct()
        g=torch.Generator().manual_seed(42);updates=skips=0;trace=[]
        for ep in range(1,4):
            start=g.get_state().clone();order,_,nxt=epoch_order(128,start);g.set_state(nxt)
            for step in range(16):
                ids=order[step*8:(step+1)*8];trace.extend(ids.tolist())
                x=(ids[:,None]+torch.arange(4)).float()/128;y=ids%2
                opt.zero_grad(set_to_none=True)
                loss=torch.nn.functional.cross_entropy(model(x),y)
                scaler.scale(loss).backward()
                serial=(ep-1)*16+step+1
                if serial in [4,22]:next(model.parameters()).grad.fill_(float('inf'))
                scaler.unscale_(opt);torch.nn.utils.clip_grad_norm_(model.parameters(),1.)
                before=scaler.get_scale();scaler.step(opt);scaler.update()
                updates,skips=update_counters(sched,updates,skips,before,scaler.get_scale())
                if serial in restarts:
                    snapshot=copy.deepcopy({'model':model.state_dict(),'opt':opt.state_dict(),
                        'scheduler':sched.state_dict(),'scaler':scaler.state_dict(),
                        'rng':torch.get_rng_state(),'updates':updates,'skips':skips,
                        'sampler_start':start,'sampler_next_rng':nxt,'loader_rng':nxt,'epoch':ep,
                        'step_in_epoch':step+1,'samples_seen':(step+1)*8,
                        'recovery_schema':SCHEMA,'epoch_order_sha256':order_hash(order)})
                    model,opt,sched,scaler=construct()
                    model.load_state_dict(snapshot['model']);opt.load_state_dict(snapshot['opt'])
                    sched.load_state_dict(snapshot['scheduler']);scaler.load_state_dict(snapshot['scaler'])
                    recovered,next_rng,cursor=recover_order(snapshot,128,8)
                    assert torch.equal(recovered,order) and cursor==(step+1)*8
                    g.set_state(next_rng);torch.set_rng_state(snapshot['rng'])
                    updates,skips=snapshot['updates'],snapshot['skips']
        return {'model':model.state_dict(),'optimizer':opt.state_dict(),'scheduler':sched.state_dict(),
            'scaler':scaler.state_dict(),'rng':torch.get_rng_state(),'trace':trace,'updates':updates,'skips':skips}
    reference=run([])
    for cuts in [[26],[32],[26,29]]:
        assert tensor_equal(reference,run(cuts)),f'Numerical state mismatch at interruptions {cuts}'
    assert reference['updates']==46 and reference['skips']==2 and reference['scheduler']['last_epoch']==46
    return {'mid_epoch_and_boundary_and_second_resume':'exact CPU weights/AdamW/LR/scaler/RNG/order match',
            'successful_updates':46,'actual_amp_overflows':2,'scheduler_steps':46,
            'gpu_equivalence_claimed':False}


def actual_gate(path):
    state=torch.load(path,map_location='cpu',weights_only=False)
    order,nxt,cursor=recover_order(state,564000,32,'a776b65a95c4fd26a8ceb1f2f55b48f30b8adb92bb1b388ed39a0cacb6eec6f6')
    assert state['epoch']==5 and state['step_in_epoch']==15000 and cursor==480000
    assert state['updates']==85466 and state['skips']==34
    result={'epoch':5,'step':15000,'cursor':cursor,'remaining':len(order)-cursor,
        'permutation_sha256':order_hash(order),'next_indices':order[cursor:cursor+32].tolist(),
        'next_epoch_rng_sha256':__import__('hashlib').sha256(nxt.numpy().tobytes()).hexdigest()}
    del state;gc.collect();return result


def main():
    p=argparse.ArgumentParser();p.add_argument('--checkpoint');p.add_argument('--output',required=True);args=p.parse_args()
    results={'utc':datetime.now(timezone.utc).isoformat(),'torch':torch.__version__,'schema':SCHEMA,
        'sampler':sampler_gate(),'numerical':numerical_gate()}
    if args.checkpoint:results['actual_checkpoint']=actual_gate(args.checkpoint)
    results['status']='passed';Path(args.output).write_text(json.dumps(results,indent=2)+'\n')
    print(json.dumps(results,indent=2))

if __name__=='__main__':main()
