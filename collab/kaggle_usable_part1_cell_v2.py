"""Guarded notebook launcher for one registered Part1 epoch job.

Prepared only: no cloud job starts by importing this module. A real release
receipt must be populated after full data, actual CUDA and measured preflight.
Never evaluates the test split, shrinks data, resets schedules, or buys resources.
"""
import datetime, hashlib, importlib.metadata, importlib.util, json, math, os
from pathlib import Path
import subprocess, sys, time

SOURCE_COMMIT='UNRELEASED'
SOURCE_HASHES={'scripts/train_usable_multimodal_v2.py': '88412d918b77f8a54569b25a8c469618c028ebaeeeb0b6050385dc55bd20ac1e', 'scripts/multimodal_recovery_v1.py': '2f5f67ce79289c69279040d21b483e28535895f5c99c63e0021da3eee6d3d1c8', 'scripts/verify_usable_multimodal_v2.py': 'bc314502833835a42bba8bab2d069074018bafc807106a3eb503386e2671139b', 'scripts/usable_cohort_v2.py': '22bff1eb0fa14d102ad07786f936c5c1ed1582ec7bd5cee2b8e8dc5eb3520092', 'configs/multimodal_usable_6way_v2.json': 'ad8f86f86b1fef453ae3bccda0aeb13cc50b298dc0d5d502f87c9ac4b041b483'}
COUNTS={'train':563601,'validation':59299,'test':59270}
COHORT='FACULTY-6W-USABLE-682170-v1'
COHORT_SHA='3fe0b622958a1eee6732789d4f7acf6b450c0e3bda87312e5cbb6500fb405ce5'

def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def sha(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  for b in iter(lambda:f.read(4*1024**2),b''):h.update(b)
 return h.hexdigest()
def write(path,value):
 path=Path(path);temporary=path.with_suffix('.tmp')
 with temporary.open('w') as f:json.dump(value,f,indent=2,allow_nan=False);f.write('\n');f.flush();os.fsync(f.fileno())
 os.replace(temporary,path)
def evidence(reference):
 path=Path(reference['path'])
 if sha(path)!=reference['sha256']:raise ValueError('Evidence checksum mismatch '+path.name)
 return json.loads(path.read_text())
def check_release(release,working_root=Path('/kaggle/working')):
 if release.get('state')!='registered_after_verified_full_preflight':raise ValueError('Draft release cannot launch training')
 if release.get('stage')!='part1' or release.get('stop_after_epoch') not in [1,2] or release.get('final_test') is not False:raise ValueError('Part1 only; no final test')
 if len(SOURCE_COMMIT)!=40 or any(c not in '0123456789abcdef' for c in SOURCE_COMMIT):raise ValueError('Source revision not released')
 if release.get('source_commit')!=SOURCE_COMMIT:raise ValueError('Unexpected source revision')
 if type(release.get('resume')) is not bool:raise ValueError('Explicit resume boolean required')
 if release['resume'] and release.get('prior_job_verified_terminal') is not True:raise ValueError('Verify prior job terminal before resume')
 if not Path(release['input_root']).resolve().is_relative_to(Path('/kaggle/input')):raise ValueError('Immutable Kaggle input root required')
 output=Path(release['output']).resolve();working_root=Path(working_root).resolve()
 if output==working_root or not output.is_relative_to(working_root):raise ValueError('Dedicated Kaggle working attempt directory required')
 if release.get('conflicting_attempt_jobs')!=[]:raise ValueError('Existing conflicting job not cleared')
 checked=datetime.datetime.fromisoformat(release['active_job_check_utc'])
 age=(datetime.datetime.now(datetime.timezone.utc)-checked).total_seconds()
 if not 0<=age<=600:raise ValueError('Refresh actual cloud-job/quota check before launch')
 if type(release.get('private_input_version')) is not int or release['private_input_version']<1:raise ValueError('Immutable private input version required')
 coverage=evidence(release['coverage'])
 if coverage.get('image_gate_passed') is not True or coverage.get('required')!=682170 or coverage.get('usable')!=682170 or coverage.get('cohort_id')!=COHORT or coverage.get('cohort_registration_sha256')!=COHORT_SHA or coverage.get('split_counts')!=COUNTS:raise ValueError('Fullapproved682170runtimeimagegaterequired')
 fixture=evidence(release['cuda_fixture'])
 if fixture.get('status')!='passed_cuda_engineering_fixture' or fixture.get('trainer_sha256')!=SOURCE_HASHES['scripts/train_usable_multimodal_v2.py'] or fixture.get('recovery_sha256')!=SOURCE_HASHES['scripts/multimodal_recovery_v1.py']:raise ValueError('Actual production CUDA recovery fixture required')
 measured=evidence(release['throughput'])
 if measured.get('status')!='passed_measured_multimodal_preflight' or measured.get('train_only') is not True or measured.get('measurement_seconds',0)<600:raise ValueError('Measured10minute train-only preflight required')
 if measured.get('config_sha256')!=SOURCE_HASHES['configs/multimodal_usable_6way_v2.json'] or measured.get('trainer_sha256')!=SOURCE_HASHES['scripts/train_usable_multimodal_v2.py']:raise ValueError('Preflight config/source mismatch')
 train=float(measured['train_examples_per_second']);evaluate=float(measured['eval_path_examples_per_second']);checkpoint=float(measured['checkpoint_seconds'])
 if not all(math.isfinite(x) for x in [train,evaluate,checkpoint]) or min(train,evaluate)<=0 or checkpoint<0:raise ValueError('Invalid measured throughput')
 epoch_seconds=563601/train+59299/evaluate+checkpoint
 budget=float(release['wall_seconds']);remaining=float(release['verified_session_seconds_remaining'])
 if not math.isfinite(budget) or not math.isfinite(remaining) or not 0<budget<=remaining-3600:raise ValueError('Reserve at least1hour for save/export before session cap')
 if budget<1.2*epoch_seconds:raise ValueError('Measured full epoch plus20percent margin does not fit')
 return output,fixture

def stage_sources(workspace):
 import requests
 workspace=Path(workspace);workspace.mkdir(parents=True,exist_ok=True)
 for relative,digest in SOURCE_HASHES.items():
  path=workspace/relative
  if not path.exists():
   response=requests.get('https://raw.githubusercontent.com/panvenaidu/Fake-News-Detection/'+SOURCE_COMMIT+'/'+relative,timeout=45);response.raise_for_status()
   if hashlib.sha256(response.content).hexdigest()!=digest:raise ValueError('Fetched source checksum mismatch')
   path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(response.content)
  if sha(path)!=digest:raise ValueError('Existing source differs; do not silently overwrite')
 return workspace

def run(release_path):
 release=json.loads(Path(release_path).read_text());output,fixture=check_release(release)
 os.environ['CUDA_VISIBLE_DEVICES']='0'
 import torch
 if not torch.cuda.is_available() or torch.cuda.device_count()!=1:raise RuntimeError('One used cloud CUDA device required')
 if torch.__version__!=fixture['torch'] or torch.version.cuda!=fixture['cuda'] or torch.cuda.get_device_name(0)!=fixture['device']:raise ValueError('Repeat CUDA fixture on actual device/software')
 versions={n:importlib.metadata.version(n) for n in ['torch','torchvision','transformers','numpy','Pillow']}
 if versions!=release['measured_versions']:raise ValueError('Actual environment differs from frozen measured preflight')
 workspace=stage_sources(output.parent/'registered_source');cfg=workspace/'configs/multimodal_usable_6way_v2.json'
 config=json.loads(cfg.read_text())
 if sha(release['warmstart'])!=config['warmstart_sha256']:raise ValueError('Selected text warm-start checksum mismatch')
 sys.path.insert(0,str(workspace/'scripts'))
 import multimodal_recovery_v1 as recovery
 if bool(release['resume']):
  payload,proof=recovery.load_generation(output/'recovery')
  if payload['contract']['config_sha256']!=SOURCE_HASHES['configs/multimodal_usable_6way_v2.json']:raise ValueError('Recovery config mismatch')
  if (output/'trainer.lock').exists():raise RuntimeError('Verify original job/PID before clearing any attempt lock')
  if len(payload['state']['history'])>=release['stop_after_epoch']:
   import verify_usable_multimodal_v2 as verifier
   import pandas as pd
   cohort_rows,_=verifier.load_input(release['input_root'])
   official=pd.DataFrame([r for r in cohort_rows.values() if r['split']=='validation'])
   values=[verifier.verify_export(output,h['epoch'],official) for h in payload['state']['history']]
   if len(payload['state']['history'])==2:verifier.verify_part1(output,release['input_root'])
   result={'utc':now(),'state':'existing_epoch_job_verified_no_new_training','epochs_validated':len(values),'no_test_performed':True,'private_cloud_durability_verified':False}
   print(json.dumps(result),flush=True);return result
  # The caller has verified prior job terminal and this snapshot's integrity.
  (output/'STOP_REQUESTED').unlink(missing_ok=True)
 else:
  if output.exists():raise ValueError('Existing attempt requires verified resume')
 output.mkdir(parents=True,exist_ok=True)
 write(output/'cloud_job_release.json',release)
 command=[sys.executable,str(workspace/'scripts/train_usable_multimodal_v2.py'),'--root',release['input_root'],'--coverage',release['coverage']['path'],'--config',str(cfg),'--output',str(output),'--warmstart',release['warmstart'],'--stage','part1','--stop-after-epoch',str(release['stop_after_epoch'])]
 if release['resume']:command.append('--resume')
 # Trainer owns creation of a new attempt directory.
 if not release['resume']:(output/'cloud_job_release.json').unlink();output.rmdir()
 start=time.monotonic();requested=False;budget=float(release['wall_seconds'])
 with (output.parent/(output.name+'_console.log')).open('a') as log:
  process=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,env=os.environ.copy())
  while process.poll() is None:
   if time.monotonic()-start>=budget and not requested:
    output.mkdir(parents=True,exist_ok=True);(output/'STOP_REQUESTED').touch();requested=True
   if requested and time.monotonic()-start>budget+600:
    process.terminate()
    try:process.wait(timeout=120)
    except subprocess.TimeoutExpired:process.kill();process.wait()
    break
   status=json.loads((output/'status.json').read_text()) if (output/'status.json').exists() else {'state':'initializing'}
   print(json.dumps({'utc':now(),'pid':process.pid,'job_alive':True,'safe_stop_requested':requested,'trainer_status':status}),flush=True)
   time.sleep(30)
 if process.returncode:raise RuntimeError('Trainer stopped unsuccessfully; preserve outputs and inspect console before restart')
 payload,recovered=recovery.load_generation(output/'recovery');state=payload['state']
 import verify_usable_multimodal_v2 as verifier
 import pandas as pd
 cohort_rows,_=verifier.load_input(release['input_root'])
 official=pd.DataFrame([r for r in cohort_rows.values() if r['split']=='validation'])
 values=[verifier.verify_export(output,item['epoch'],official) for item in state['history']]
 if len(state['history'])==2:verifier.verify_part1(output,release['input_root'])
 result={'utc':now(),'state':'epoch_job_finished' if len(state['history'])>=release['stop_after_epoch'] else 'safe_boundary_checkpointed','epochs_validated':len(state['history']),'next_epoch':state['epoch'],'cursor':state['cursor'],'recovery':recovered,'validation':values,'no_test_performed':True,'private_cloud_durability_verified':False,'next':'Save private Kaggle output/version, verify after runtime loss, retrieve/hash recovery and update Git before claiming accepted Part1'}
 write(output/'cloud_job_release.json',release);write(output/'cloud_job_runtime_result.json',result);print(json.dumps(result),flush=True)
 return result

if __name__=='__main__':
 import argparse
 parser=argparse.ArgumentParser();parser.add_argument('--release',type=Path,required=True);args=parser.parse_args();run(args.release)
