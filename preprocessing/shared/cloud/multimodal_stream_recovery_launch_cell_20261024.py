# Bounded CPU-only recovery. NEVER run old extraction cells with this job.
from pathlib import Path
import json, hashlib, importlib.util, fcntl, os, traceback, time
root=Path('/content/drive/MyDrive/UROP/official_images_v1')
script=root/'prepare_official_images_stream_v2.py'
assert hashlib.sha256(script.read_bytes()).hexdigest()=='5b9be91021d4d397d8f3bd74c0354d0496b7cfb685723cf2c3c3ee24ea6266e6'
spec=importlib.util.spec_from_file_location('stream_recovery',script)
stream_recovery=importlib.util.module_from_spec(spec);spec.loader.exec_module(stream_recovery)
stream_recovery.prep.require_drive(root)
expected=stream_recovery.prep.expected_rows(root)
assert len(expected)==682661 and (root/'public_images.tar.bz2').stat().st_size==113623359224
job_lock=open('/content/urop_stream_image_prep_v2.lock','a+')
fcntl.flock(job_lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
job_id='CPU_STREAM_PREP_'+stream_recovery.uuid.uuid4().hex
launch={'utc':stream_recovery.prep.now(),'job_id':job_id,'pid':os.getpid(),'max_seconds_after_committed_hash_audit':28800,'script_sha256':'5b9be91021d4d397d8f3bd74c0354d0496b7cfb685723cf2c3c3ee24ea6266e6','original_source_id':stream_recovery.SOURCE_ID,'required':682661,'source_route':'Same original public author archive via verified HTTP ranges; no full source file written in VM','existing_metadata_count':505573,'existing_committed_shards':111,'existing_committed_shard_bytes':59466014720,'existing_hashes_rechecked_before_extraction':True,'uncommitted_orphans_ignored':['images_20ad5ec99d0c4f59990dc54e195383b7.tar','images_3d24f1ea619648fd9138ea942cffbe25.tar'],'gpu':False,'training':False,'final_test':False,'source_head_tail_identity_proof':'results/MM_PART1_STREAM_SOURCE_PROBE_20261024.json','scratch_safety_bytes':8*1024**3,'checkpoint':'New immutable shard receipts; each closed shard SHA256 and original per-image hashes; preserve prior111generations','recovery':'Verify terminal state; reuse committed shards; re-read compressed prefix without new archive storage. Do not run duplicate job.'}
stream_recovery.prep.record(root/(job_id+'_launch.json'),launch)
print(json.dumps({'state':'bounded_stream_recovery_started',**launch}),flush=True)
try:
    outcome=stream_recovery.extract(root,expected,max_seconds=28800)
    stream_recovery.prep.record(root/(job_id+'_result.json'),{'utc':stream_recovery.prep.now(),'job_id':job_id,'result':outcome})
    print(json.dumps({'state':'bounded_stream_recovery_finished','job_id':job_id,'result':outcome}),flush=True)
    from google.colab import drive
    drive.flush_and_unmount(timeout_ms=600000)
    print(json.dumps({'utc':stream_recovery.prep.now(),'state':'drive_flush_and_unmount_completed','job_id':job_id,'result_written_before_flush':True}),flush=True)
except Exception as error:
    failure={'utc':stream_recovery.prep.now(),'job_id':job_id,'error_type':type(error).__name__,'error':str(error),'traceback':traceback.format_exc(),'image_gate_passed':False,'recovery':'Prior committed receipts preserved. Open shard without receipt is untrusted. Diagnose before restarting.'}
    try:stream_recovery.prep.record(root/(job_id+'_failure.json'),failure)
    except Exception:pass
    print(json.dumps({'state':'bounded_stream_recovery_failed',**failure}),flush=True)
finally:
    fcntl.flock(job_lock,fcntl.LOCK_UN);job_lock.close()
