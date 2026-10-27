"""Build, never submit, the private bounded registered Part1 epoch notebook."""
import argparse,datetime,hashlib,json,math
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--preflight',type=Path,required=True);p.add_argument('--preflight-kernel',required=True);p.add_argument('--metadata',type=Path,required=True);p.add_argument('--api-check',type=Path,required=True);p.add_argument('--destination',type=Path,required=True);p.add_argument('--epoch',type=int,choices=[1,2],required=True);p.add_argument('--previous',type=Path);p.add_argument('--previous-version',type=int);a=p.parse_args()
root=Path(__file__).resolve().parents[1]
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
summary_path=next(a.preflight.rglob('GPU_PREFLIGHT_SUMMARY.json'));s=json.loads(summary_path.read_text());assert s['state']=='gpu_preflight_verified'
check=json.loads(a.api_check.read_text());assert check['request_succeeded'] and all(v=='KernelWorkerStatus.COMPLETE' for v in check['kernels'].values())
age=(datetime.datetime.now(datetime.timezone.utc)-datetime.datetime.fromisoformat(check['utc'])).total_seconds();assert 0<=age<300
stage=s['raw_archive_cache']['seconds'];assert 0<=stage<=3600 and len(s['raw_archive_cache']['archives'])==39
cap=math.ceil((1.25*(s['estimated_epoch_seconds']+stage)+600+3600+300)/300)*300;assert cap<=43200
m=json.loads(a.metadata.read_text());assert m['enable_gpu'] and m['machine_shape']=='NvidiaTeslaT4' and '@sha256:' in m['docker_image'],'Actual successful T4 Docker digest required'
previous_slug='rocky62/urop-mm-part1-science-usable-20261027'
slug=previous_slug if a.epoch==1 else 'rocky62/urop-mm-part1-science-epoch2-20261027'
sources=['rocky62/urop-official-six-way-text-recovery','rocky62/urop-mm-packed-faculty-image-gate-20261026/2',a.preflight_kernel]
audit={'stop_after_epoch':a.epoch,'final_test':False,'session_timeout_seconds':cap,'api_check':check,'preflight_summary_sha256':sha(summary_path)}
if a.epoch==2:
 assert a.previous is not None and a.previous_version is not None
 previous=next(a.previous.rglob('cloud_job_runtime_result.json'));r=json.loads(previous.read_text());assert r['epochs_validated']==1 and r['state']=='epoch_job_finished';audit['previous_runtime_result_sha256']=sha(previous);sources.append(previous_slug+'/'+str(a.previous_version))
code=(root/'collab/kaggle_part1_epoch_job_20261027.py').read_text()
wrapper="import os,sys,json,subprocess,hashlib\nfrom pathlib import Path\nscript=Path('/kaggle/working/registered_epoch_driver.py')\nscript.write_text("+repr(code+"\nrun("+repr(audit)+")\n")+")\nprint('REGISTERED_EPOCH_DRIVER_SHA256',hashlib.sha256(script.read_bytes()).hexdigest(),flush=True)\nenv=dict(os.environ,CUDA_VISIBLE_DEVICES='0',CUBLAS_WORKSPACE_CONFIG=':4096:8')\nsubprocess.run([sys.executable,'-u',str(script)],env=env,check=True,timeout="+str(cap-300)+")\n"
nb={'nbformat':4,'nbformat_minor':5,'metadata':{'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'}},'cells':[{'id':'registered-epoch','cell_type':'code','execution_count':None,'metadata':{},'outputs':[],'source':wrapper}]}
metadata={'id':slug,'title':'UROP MM Part1 science usable 20261027' if a.epoch==1 else 'UROP MM Part1 science epoch2 20261027','code_file':'registered_epoch.ipynb','language':'python','kernel_type':'notebook','is_private':True,'enable_gpu':True,'enable_tpu':False,'enable_internet':True,'dataset_sources':['rocky62/urop-faculty-usable-packed-input-v3'],'kernel_sources':sources,'competition_sources':[],'model_sources':[],'docker_image':m['docker_image'],'docker_image_pinning_type':'original','machine_shape':'NvidiaTeslaT4'}
a.destination.mkdir(parents=True,exist_ok=True);(a.destination/'registered_epoch.ipynb').write_text(json.dumps(nb,indent=2)+'\n');(a.destination/'kernel-metadata.json').write_text(json.dumps(metadata,indent=2)+'\n');(a.destination/'launch_audit.json').write_text(json.dumps(audit,indent=2)+'\n');print(json.dumps({'folder':str(a.destination.resolve()),'session_timeout_seconds':cap,'epoch':a.epoch,'notebook_sha256':sha(a.destination/'registered_epoch.ipynb'),'submitted':False}))
