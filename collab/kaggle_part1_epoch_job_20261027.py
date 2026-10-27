"""Registered one-epoch Kaggle job, launched only with fresh verified evidence.

Call run(audit) in a fresh Python process with CUDA_VISIBLE_DEVICES=0. The caller
embeds the fresh API job/quota check and hashes of independently retrieved
preflight/previous-job artifacts. No test inference or protocol changes.
"""
from pathlib import Path
import datetime,hashlib,importlib.metadata,json,math,os,shutil,subprocess,sys,time
import requests
LAUNCHER_COMMIT='e92161dd737208bcb162736ff84d21fd67af8b4f'
LAUNCHER_SHA='94caea5e8ecd4a2368978005df73253e43f4248b0599ac7c52934a168d73a3a6'
SCIENCE_COMMIT='1b22467fc4d404e172e3d938f44e7d37e345e4bc'
ATTEMPT='OFFICIAL-6W-MM-USABLE-v2_seed42_20261027'
BASE=Path('/kaggle/working/urop_mm_science_20261027')


def sha(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as stream:
  for block in iter(lambda:stream.read(4*1024**2),b''):h.update(block)
 return h.hexdigest()


def run(audit):
 started=time.monotonic()
 assert os.environ.get('CUDA_VISIBLE_DEVICES')=='0'
 assert audit['stop_after_epoch'] in [1,2] and audit['final_test'] is False
 cap=int(audit['session_timeout_seconds']);assert 3600<cap<=43200
 checked=datetime.datetime.fromisoformat(audit['api_check']['utc'])
 age=(datetime.datetime.now(datetime.timezone.utc)-checked).total_seconds()
 assert 0<=age<=600,'Fresh actual API job/quota check required'
 assert all(v in ['KernelWorkerStatus.COMPLETE','KernelWorkerStatus.ERROR','KernelWorkerStatus.CANCELLED'] for v in audit['api_check']['kernels'].values()),'Conflicting cloud job'
 quota=audit['api_check']['gpu_quota'];remaining=quota['total_time_allowed']-quota['time_used']-quota['time_reserved']-age
 assert remaining>3600,'Insufficient actual GPU allowance'
 free=shutil.disk_usage('/kaggle/working').free
 assert free>=12*1024**3,'Reserve disk for two recovery generations, temporary writes and exports'
 active=subprocess.check_output(['ps','-eo','args'],text=True)
 assert not any('train_usable_multimodal_v2.py' in line for line in active.splitlines()),'Existing scientific trainer in runtime'
 print(json.dumps({'state':'cloud_capacity_verified','scratch_free_bytes':free,'gpu_quota_seconds_available':remaining,'requested_session_seconds':cap,'scientific_training':False}),flush=True)
 summaries=list(Path('/kaggle/input').rglob('GPU_PREFLIGHT_SUMMARY.json'))
 assert len(summaries)==1,'Exactly one immutable measured preflight output required'
 summary_path=summaries[0];assert sha(summary_path)==audit['preflight_summary_sha256']
 summary=json.loads(summary_path.read_text());assert summary['state']=='gpu_preflight_verified'
 def remap(old):return summary_path.parent/Path(old).relative_to('/kaggle/working/urop_mm_part1_20261026')
 fixture,throughput=remap(summary['fixture']),remap(summary['throughput'])
 assert sha(fixture)==summary['fixture_sha256'] and sha(throughput)==summary['throughput_sha256']
 for key in ['coverage','packed_index']:
  assert sha(summary[key])==summary[key+'_sha256']
 assert summary['coverage_sha256']=='afe8c723f91fe74f791908e0c16fab94d919af64c7cb7c9b5a37e676361d95e5'
 assert summary['packed_index_sha256']=='fc8dc03a4f773da5762891c8392375add5fb8087251b527f3b37a880308e6018'
 measured=json.loads(throughput.read_text());epoch=563601/measured['train_examples_per_second']+59299/measured['eval_path_examples_per_second']+measured['checkpoint_seconds']
 budget=1.25*epoch+600
 assert math.isfinite(budget) and budget+3600<min(cap,remaining),'Full registered epoch does not fit with reserve'
 try:transformers_version=importlib.metadata.version('transformers')
 except importlib.metadata.PackageNotFoundError:transformers_version=None
 if transformers_version!='4.48.3':
  subprocess.run([sys.executable,'-m','pip','-q','install','transformers==4.48.3'],check=True,timeout=600)
 BASE.mkdir(parents=True,exist_ok=True)
 launcher=BASE/'registered_epoch_launcher.py'
 response=requests.get('https://raw.githubusercontent.com/panvenaidu/Fake-News-Detection/'+LAUNCHER_COMMIT+'/collab/kaggle_usable_part1_cell_v2.py',timeout=45);response.raise_for_status()
 assert hashlib.sha256(response.content).hexdigest()==LAUNCHER_SHA
 launcher.write_bytes(response.content)
 output=BASE/ATTEMPT;resume=audit['stop_after_epoch']==2
 if resume:
  previous=list(Path('/kaggle/input').rglob(ATTEMPT+'/cloud_job_runtime_result.json'))
  assert len(previous)==1 and sha(previous[0])==audit['previous_runtime_result_sha256']
  prior=json.loads(previous[0].read_text());assert prior['epochs_validated']==1 and prior['state']=='epoch_job_finished'
  assert not output.exists(),'Preserve existing attempt'
  assert not (previous[0].parent/'trainer.lock').exists(),'Prior attempt lock remains'
  shutil.copytree(previous[0].parent,output)
 else:assert not output.exists(),'Existing attempt requires explicit verified resume'
 versions={n:importlib.metadata.version(n) for n in ['torch','torchvision','transformers','numpy','Pillow']}
 assert versions==summary['versions'],'Repeat preflight if actual environment changed'
 release={'state':'registered_after_verified_full_preflight','stage':'part1','stop_after_epoch':audit['stop_after_epoch'],'final_test':False,'source_commit':SCIENCE_COMMIT,'resume':resume,'prior_job_verified_terminal':resume,'input_root':summary['input_root'],'output':str(output),'conflicting_attempt_jobs':[],'active_job_check_utc':audit['api_check']['utc'],'private_input_version':1,'coverage':{'path':summary['coverage'],'sha256':summary['coverage_sha256']},'packed_index':summary['packed_index'],'cuda_fixture':{'path':str(fixture),'sha256':summary['fixture_sha256']},'throughput':{'path':str(throughput),'sha256':summary['throughput_sha256']},'wall_seconds':budget,'verified_session_seconds_remaining':min(cap,remaining)-(time.monotonic()-started),'warmstart':summary['warmstart'],'measured_versions':versions,'runtime_reader_sha256':summary['runtime_reader_sha256'],'prelaunch_audit':audit,'launcher_sha256':LAUNCHER_SHA}
 path=BASE/'registered_job_release.json';path.write_text(json.dumps(release,indent=2)+'\n')
 print(json.dumps({'state':'registered_epoch_job_released','stop_after_epoch':audit['stop_after_epoch'],'estimated_epoch_seconds':epoch,'wall_seconds':budget,'no_test':True}),flush=True)
 subprocess.run([sys.executable,'-u',str(launcher),'--release',str(path)],check=True,timeout=math.ceil(budget)+900)
