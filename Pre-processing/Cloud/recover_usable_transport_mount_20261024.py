# One-shot continuation after the captured in-kernel Drive endpoint failure.
from pathlib import Path
from datetime import datetime, timezone
import fcntl,hashlib,json,os,sys,runpy,gc,traceback
root=Path('/content/drive/MyDrive/UROP/official_images_v1')
try:
 guard=root/'USABLE_V2_TRANSPORT_JOB.json'
 prior=json.loads(guard.read_text())
 assert prior['job_id']=='CPU_USABLE_TRANSPORT_8091318e6b994f829ef34b62ce9ca587','Unexpected guard; inspect exact job'
 assert os.getpid()==1568,'Recheck notebook terminal/identity after runtime change'
 probe=open('/content/urop_stream_image_prep_v2.lock','a+')
 fcntl.flock(probe,fcntl.LOCK_EX|fcntl.LOCK_NB)
 retired=root/(prior['job_id']+'_retired_guard.json')
 assert not retired.exists(),'Recovery already submitted'
 receipts=list((root/'kaggle_packed_usable_v2/shards').glob('*.receipt.json'))
 assert len(receipts)==18
 count=0
 for path in receipts:
  item=json.loads(path.read_text());count+=len(item['images'])
  archive=path.parent/item['archive']
  assert archive.is_file() and archive.stat().st_size==item['bytes']
 assert count==319820,'Unexpected recovery state'
 proof={'utc':datetime.now(timezone.utc).isoformat(),'state':'terminal_drive_endpoint_recovery_verified','prior_job':prior['job_id'],'prior_kernel_cell_terminal':True,'observed_terminal_cell':'hasAItotepXo','cause_observed':'OSError107 Transport endpoint is not connected while reading source receipt; failure receipt write and flush also failed','underlying_disconnect_cause':'unproven','drive_remount_verified':True,'existing_pack_receipts':18,'committed_images':count,'new_images_written_by_failed_job':0,'existing_lock_free':True,'training':False,'scientific_protocol_changed':False}
 failure=root/(prior['job_id']+'_recovered_failure.json')
 with failure.open('x') as f:json.dump(proof,f,indent=2);f.flush();os.fsync(f.fileno())
 guard.rename(retired)
 fcntl.flock(probe,fcntl.LOCK_UN);probe.close()
 deployment=root/'owned_source_usable_v2_dc57564d8ffbc819'
 runner=deployment/'collab/run_usable_transport_job_v3.py'
 assert hashlib.sha256(runner.read_bytes()).hexdigest()=='60a0175d5faaba66e76752827e9a9052564351b0a0d15b35ce0803ae9f6fee94'
 # Discard only disposable Python metadata from the earlier failed wrapper.
 globals().pop('rows',None);gc.collect()
 sys.path.insert(0,str(deployment/'collab'));sys.path.insert(0,str(deployment/'scripts'))
 print(json.dumps(proof),flush=True)
 runpy.run_path(str(runner),run_name='__main__')
except Exception as error:
 print(json.dumps({'state':'drive_recovery_transport_refused_or_failed','error':str(error),'traceback':traceback.format_exc(),'training':False}),flush=True)
