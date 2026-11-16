# One verified recovery of a terminal child process; no extraction/training.
from pathlib import Path
from datetime import datetime,timezone
import json,os,sys,runpy,uuid,traceback,hashlib
root=Path('/content/drive/MyDrive/UROP/official_images_v1')
try:
 guard=root/'USABLE_V2_TRANSPORT_JOB.json'
 prior=json.loads(guard.read_text())
 assert prior['job_id']=='CPU_USABLE_TRANSPORT_1f540c1b97ae493eb1e4d3e24a471a12'
 assert not (Path('/proc')/str(prior['pid'])).exists(),'Original PID still present; refuse duplicate'
 assert not list((root/'kaggle_packed_usable_v2/shards').glob('*.receipt.json')),'Unexpected committed packs; inspect before recovery'
 retired=root/(prior['job_id']+'_retired_guard.json')
 assert not retired.exists(),'Recovery already submitted; inspect its exact job before any retry'
 proof={'utc':datetime.now(timezone.utc).isoformat(),'state':'terminal_child_recovery_verified','prior_job':prior['job_id'],'prior_pid':prior['pid'],'pid_missing':True,'parent_observed_returncode':1,'committed_packs':0,'cause':'Child stderr was not captured; exact original exception unproven','change':'Execute same owned CPU source inside Colab kernel so stdout and Drive lifecycle have the notebook context','scientific_protocol_changed':False,'training':False}
 with (root/('CPU_USABLE_RECOVERY_'+uuid.uuid4().hex+'.json')).open('x') as f:json.dump(proof,f);f.flush();os.fsync(f.fileno())
 guard.rename(retired)
 deployment=root/'owned_source_usable_v2_dc57564d8ffbc819'
 script=deployment/'collab/run_usable_transport_job_v2.py'
 assert hashlib.sha256(script.read_bytes()).hexdigest()=='8ac949c105d34ce87d7d58a144231556cff772ad7751f7273657f1dbc7b13917'
 sys.path.insert(0,str(deployment/'collab'));sys.path.insert(0,str(deployment/'scripts'))
 print(json.dumps(proof),flush=True)
 runpy.run_path(str(script),run_name='__main__')
except Exception as e:print(json.dumps({'state':'in_kernel_transport_recovery_failed','error':str(e),'traceback':traceback.format_exc(),'training':False}),flush=True)
