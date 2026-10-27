"""Independent trusted-file readback of a saved Part2 output, including partial recovery.
CPU-only verification; no model inference/training and no network calls.
"""
from pathlib import Path
import argparse,json,math,sys
import pandas as pd
import torch
from usable_cohort_v2 import load_input
from multimodal_recovery_v1 import load_generation,sha,order
from verify_usable_multimodal_v2 import verify_export
from verify_multimodal_final_v1 import verify

def run(project,folder):
 project,folder=Path(project).resolve(),Path(folder).resolve();assert folder.is_relative_to(project/'data/cloud_recovery')
 root=project/'data/cloud_recovery/local_protocol_verification_root';expected,reg=load_input(root)
 protocol=json.loads((folder/'protocol.json').read_text());reference=json.loads((project/'results/experiments/multimodal/OFFICIAL-6W-MM-USABLE-v2_seed42_20261027/protocol.json').read_text());assert protocol==reference
 payload,recovery=load_generation(folder/'recovery');assert payload['contract']==protocol and payload['gradients_cleared'];state=payload['state'];assert payload['cursor']==state['cursor']==state['seen']
 assert state['epoch'] in [3,4,5] and state['phase'] in ['train','validation'] and 0<=state['cursor']<=563601
 assert state['cursor']%32==0 or state['cursor']==563601
 assert state['updates']+state['skips']==17613*(state['epoch']-1)+math.ceil(state['cursor']/32)
 assert payload['scheduler']['last_epoch']==state['updates']
 assert {'model','optimizer','scheduler','scaler','rng','state','contract'}.issubset(payload);assert payload['optimizer']['state'] and payload['scaler'] and len(payload['rng']['cuda'])==1
 assert set(payload['rng'])=={'python','numpy','torch','cuda'}
 assert [h['epoch'] for h in state['history']]==list(range(1,state['epoch']))
 official=pd.DataFrame([r for r in expected.values() if r['split']=='validation'])
 values=[verify_export(folder,h['epoch'],official) for h in state['history']]
 for h,v in zip(state['history'],values):
  for k,n in v['metrics'].items():assert abs(h['validation'][k]-n)<1e-10
 selected=max(values,key=lambda v:(v['metrics']['macro_f1'],-v['metrics']['loss'],-v['epoch']));best=state['best'];assert selected['epoch']==best['epoch']
 selected_path=folder/best['weights_file'];assert sha(selected_path)==best['weights_sha256'];weights=torch.load(selected_path,map_location='cpu',weights_only=True)
 assert set(weights)==set(payload['model']) and all(v.shape==payload['model'][k].shape and v.dtype==payload['model'][k].dtype for k,v in weights.items())
 ref=-1.;stale=0
 for h in state['history']:
  if h['validation']['macro_f1']>=ref+.001:ref=h['validation']['macro_f1'];stale=0
  else:stale+=1
 assert abs(ref-state['patience_reference'])<1e-12 and stale==state['stale']
 assert state['early_stopped']==(len(state['history'])>=3 and stale>=2)
 complete=state['epoch']>4 or state['early_stopped'];result={'status':'verified_saved_part2_partial' if not complete else 'verified_saved_registered_training','training_complete':complete,'epochs_validated':len(values),'next_epoch':state['epoch'],'cursor':state['cursor'],'phase':state['phase'],'updates':state['updates'],'skips':state['skips'],'recovery':recovery,'selected':best,'validation':values,'test_verified':False,'selected_weight_strict_key_shape_dtype_check':True,'local_model_inference':False}
 train=[r['id'] for r in expected.values() if r['split']=='train'];indices=order(42,state['epoch'],len(train))[state['cursor']:state['cursor']+16].tolist();result['next_expected_ids']=[train[i] for i in indices]
 if (folder/'test_metrics.json').exists():
  assert complete
  freeze=json.loads((folder/'final_selection_frozen.json').read_text());assert freeze['selected']==best and freeze['protocol_sha256']==sha(folder/'protocol.json')
  result['test']=verify(folder,'test',pd.DataFrame([r for r in expected.values() if r['split']=='test']),'test')
  result['selected_validation']=verify(folder,'validation',official,'validation')
  roundtrip=json.loads((folder/'selected_weight_roundtrip.json').read_text());assert roundtrip['strict_load'] and roundtrip['maximum_logit_delta']==0 and roundtrip['sha256']==best['weights_sha256']
  result['test_verified']=True;result['status']='verified_saved_train_validation_test'
 elif not complete:assert not (folder/'test_start.json').exists(),'Test was started before training complete'
 files=[p for p in folder.rglob('*') if p.is_file()];result['artifacts']={str(p.relative_to(folder)):{'bytes':p.stat().st_size,'sha256':sha(p)} for p in files}
 return result
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--project',required=True,type=Path);a.add_argument('--run',required=True,type=Path);a.add_argument('--output',required=True,type=Path);p=a.parse_args();r=run(p.project,p.run);p.output.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:v for k,v in r.items() if k!='artifacts'}))
