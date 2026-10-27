"""Same scientific experiment: bounded epochs3-4 then frozen evaluation if time permits.
No token/OAuth, source change, new cohort, optimizer reset or test-driven selection.
Run only in copied private Kaggle GPU notebook after current UI capacity/job check.
"""
from pathlib import Path
import datetime,hashlib,json,os,subprocess,sys,time,shutil,importlib.metadata,gc
ATTEMPT='OFFICIAL-6W-MM-USABLE-v2_seed42_20261027'
COMMIT='342d287007b7cbe795031228bdb4c2c5b4ee70b6'
DEADLINE=datetime.datetime.fromisoformat('2026-10-27T19:35:00+00:00')
RETURN_DEADLINE=datetime.datetime.fromisoformat('2026-10-27T19:43:00+00:00')
BASE=Path('/kaggle/working/urop_mm_part2_20261027')
SOURCE_HASHES={'scripts/train_usable_multimodal_v2.py':'7f7fb90deb08a5901d1ca8343b780f6d82dd42b3e278d51f333568435becee0e','scripts/multimodal_recovery_v1.py':'2f5f67ce79289c69279040d21b483e28535895f5c99c63e0021da3eee6d3d1c8','scripts/usable_cohort_v2.py':'22bff1eb0fa14d102ad07786f936c5c1ed1582ec7bd5cee2b8e8dc5eb3520092','scripts/packed_image_io_v3.py':'a29e66d9c2962eb5bdfdce9abab02866fc77ad44aa5711ec8009a09dda7bb60d','scripts/verify_usable_multimodal_v2.py':'bc314502833835a42bba8bab2d069074018bafc807106a3eb503386e2671139b','configs/multimodal_usable_6way_v2.json':'ad8f86f86b1fef453ae3bccda0aeb13cc50b298dc0d5d502f87c9ac4b041b483'}
def now():return datetime.datetime.now(datetime.timezone.utc)
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(4*1024**2),b''):h.update(b)
 return h.hexdigest()
def write(p,d):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(d,indent=2,allow_nan=False)+'\n');os.replace(tmp,p)
def matching(name,digest):
 matches=[p for p in Path('/kaggle/input').rglob(name) if p.is_file() and sha(p)==digest]
 assert matches,'Missing pinned input '+name
 # Multiple identical nested copies are harmless; exact bytes decide.
 return sorted(matches,key=lambda p:(len(p.parts),str(p)))[0]
def run(audit):
 start=time.monotonic();BASE.mkdir(parents=True,exist_ok=True)
 assert os.environ.get('CUDA_VISIBLE_DEVICES')=='0'
 assert (now()-datetime.datetime.fromisoformat(audit['observed_utc'])).total_seconds()<1200,'Refresh actual UI capacity/active-jobs check'
 assert audit['active_jobs']==0 and audit['account']=='rocky62' and audit['quota_used_hours']+7<30 and audit['original_environment']=='2026-10-22'
 assert (DEADLINE-now()).total_seconds()>12000,'At least one full epoch plus saving margin must fit'
 assert shutil.disk_usage('/kaggle/working').free>12*1024**3
 assert not any('train_usable_multimodal_v2.py' in p for p in subprocess.check_output(['ps','-eo','args'],text=True).splitlines()),'Conflicting trainer'
 src=BASE/'registered_source'
 import requests
 for relative,digest in SOURCE_HASHES.items():
  p=src/relative;p.parent.mkdir(parents=True,exist_ok=True)
  if not p.exists():
   r=requests.get('https://raw.githubusercontent.com/panvenaidu/Fake-News-Detection/'+COMMIT+'/'+relative,timeout=45);r.raise_for_status();assert hashlib.sha256(r.content).hexdigest()==digest;p.write_bytes(r.content)
  assert sha(p)==digest
 # Only already-used package version may be restored, never silently upgrade contract.
 try:tv=importlib.metadata.version('transformers')
 except importlib.metadata.PackageNotFoundError:tv=None
 if tv!='4.48.3':subprocess.run([sys.executable,'-m','pip','-q','install','transformers==4.48.3'],check=True,timeout=600)
 prior=matching('cloud_job_runtime_result.json','743f0ee306091cbbe699319d7c2c4a862f752ea54a76eec5e4a32374d0d6274f').parent
 protocol=json.loads((prior/'protocol.json').read_text());assert sha(prior/'protocol.json')=='bcb36efe3383c7ecfcc4c94b0c5943df570435bb6debe2dcb04d808a67502e43'
 for name,digest in protocol['sources'].items():assert sha(src/'scripts'/name)==digest
 assert {n:importlib.metadata.version(n) for n in ['torch','torchvision','transformers','numpy','pillow']}=={k:v for k,v in protocol['versions'].items() if k!='python'}
 assert sys.version==protocol['versions']['python'],'Python contract mismatch'
 coverage=matching('packed_runtime_coverage.json',protocol['inputs']['coverage_sha256']);cov=json.loads(coverage.read_text());root=Path(cov['runtime_root']);assert root.is_dir()
 index=matching('packed_image_index.sqlite',protocol['inputs']['packed_index_sha256'])
 assert cov['dataset_version']==1 and cov['usable']==682170 and cov['image_gate_passed'] and cov['split_counts']=={'train':563601,'validation':59299,'test':59270}
 output=BASE/ATTEMPT;assert not output.exists(),'Existing attempt requires explicit verified recovery, not overwrite'
 assert not (prior/'trainer.lock').exists()
 assert sha(prior/'recovery/2b57a4d8c3ca422f8c2e3773fdd845b7.pt')=='357c0707a80ef97f485cfe1824b537327aeb6810b89890055e6d18866e1f1819'
 assert sha(prior/'selected_epoch2_f9d1f5e980e74a1ba68c6432b9a6bba1.pt')=='fe3f78e27a77410884bddd2f0929e2fc4b9717424251adbbaa325441989dda40'
 shutil.copytree(prior,output)
 sys.path.insert(0,str(src/'scripts'))
 import torch
 assert torch.cuda.is_available() and torch.cuda.device_count()==1 and torch.cuda.get_device_name(0)=='Tesla T4'
 from multimodal_recovery_v1 import load_generation
 payload,proof=load_generation(output/'recovery');assert payload['contract']==protocol and payload['gradients_cleared'];state=payload['state']
 assert state['epoch']==3 and state['cursor']==0 and state['phase']=='train' and len(state['history'])==2 and state['updates']==35211 and state['skips']==15
 assert payload['scheduler']['last_epoch']==35211 and len(payload['rng']['cuda'])==1 and all(k in payload for k in ['model','optimizer','scheduler','scaler','rng']);assert payload['optimizer']['state'] and payload['scaler']
 del payload;gc.collect()
 release={'utc':now().isoformat(),'state':'verified_part2_resume_release','audit':audit,'attempt':ATTEMPT,'prior_output':str(prior),'prior_recovery':proof,'coverage':str(coverage),'index':str(index),'input_root':str(root),'protocol_sha256':sha(output/'protocol.json'),'source_commit':COMMIT,'training_deadline_utc':DEADLINE.isoformat(),'final_test_only_after_training_complete':True,'gpu':torch.cuda.get_device_name(0),'cuda_visible_devices':os.environ.get('CUDA_VISIBLE_DEVICES')}
 write(output/'part2_release.json',release);print(json.dumps(release),flush=True)
 warmstarts=list(Path('/kaggle/input').rglob('selected_epoch4.pt'))
 # Resume does not consume --warmstart; the mandatory path is provenance only.
 warmstart=prior/'selected_epoch2_f9d1f5e980e74a1ba68c6432b9a6bba1.pt'
 command=[sys.executable,'-u',str(src/'scripts/train_usable_multimodal_v2.py'),'--root',str(root),'--coverage',str(coverage),'--packed-index',str(index),'--config',str(src/'configs/multimodal_usable_6way_v2.json'),'--output',str(output),'--warmstart',str(warmstart),'--stage','part2','--stop-after-epoch','4','--resume']
 requested=False;log=BASE/'part2_training_console.log'
 with log.open('x') as stream:
  proc=subprocess.Popen(command,stdout=stream,stderr=subprocess.STDOUT,env=os.environ.copy())
  while proc.poll() is None:
   status=json.loads((output/'status.json').read_text()) if (output/'status.json').exists() else {'state':'starting'}
   if now()>=DEADLINE and not requested:(output/'STOP_REQUESTED').touch();requested=True
   heartbeat={'utc':now().isoformat(),'trainer_alive':True,'pid':proc.pid,'safe_stop_requested':requested,'status':status,'remaining_task_compute_seconds':(DEADLINE-now()).total_seconds()}
   write(output/'part2_heartbeat.json',heartbeat);print(json.dumps(heartbeat),flush=True)
   if now()>=RETURN_DEADLINE:
    proc.terminate()
    try:proc.wait(timeout=120)
    except subprocess.TimeoutExpired:proc.kill();proc.wait()
    break
   time.sleep(30)
 assert proc.returncode==0,'Trainer failed; preserve checkpoint and console before any retry'
 payload,proof=load_generation(output/'recovery');state=payload['state'];assert payload['contract']==protocol and payload['scheduler']['last_epoch']==state['updates']
 del payload;gc.collect()
 from usable_cohort_v2 import load_input
 import pandas as pd
 from verify_usable_multimodal_v2 import verify_export
 expected,_=load_input(root);official=pd.DataFrame([r for r in expected.values() if r['split']=='validation'])
 values=[verify_export(output,h['epoch'],official) for h in state['history']]
 best=max(values,key=lambda v:(v['metrics']['macro_f1'],-v['metrics']['loss'],-v['epoch']));assert best['epoch']==state['best']['epoch'];assert sha(output/state['best']['weights_file'])==state['best']['weights_sha256']
 complete=state['epoch']>4 or state['early_stopped'];result={'utc':now().isoformat(),'state':'registered_training_complete' if complete else 'partial_part2_durable_runtime_checkpoint','training_complete':complete,'epochs_validated':len(values),'next_epoch':state['epoch'],'cursor':state['cursor'],'phase':state['phase'],'recovery':proof,'selected':state['best'],'validation':values,'elapsed_seconds':time.monotonic()-start,'no_test_performed':True,'requires_private_saved_version_and_independent_local_readback':True}
 write(output/'part2_runtime_result.json',result)
 if complete and (RETURN_DEADLINE-now()).total_seconds()>900:
  evaluator=BASE/'evaluate_frozen_multimodal_v1.py';assert evaluator.is_file()
  subprocess.run([sys.executable,'-u',str(evaluator),'--run',str(output),'--root',str(root),'--index',str(index)],env=dict(os.environ,PYTHONPATH=str(src/'scripts')+os.pathsep+str(BASE)),check=True,timeout=max(60,int((RETURN_DEADLINE-now()).total_seconds())-120))
  result['no_test_performed']=False;result['state']='runtime_train_validation_test_verified';write(output/'part2_runtime_result.json',result)
 print(json.dumps(result),flush=True)
 return result
