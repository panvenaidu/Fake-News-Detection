"""Bounded original-byte continuation; fill observed terminal predecessor first.

No model or test inference. Current notebook must show predecessor terminal.
Private API STATE, original source shards and closed archives are preserved.
"""
from pathlib import Path
import hashlib
import json
import os
import runpy
import sys
from datetime import datetime, timezone

EXPECTED_PREDECESSOR = 'CPU_API_PACK_af175d22e92d4a0caecf8a850bf94a3f'
if not EXPECTED_PREDECESSOR:
    raise ValueError('DRAFT: observed terminal predecessor must be pinned before launch')
deployment = Path('/content/urop_api_transport_source_e9efc3742d3a3e61')
pins = {'collab/drive_api_storage_v1.py':'d7603e6bad1af1560a9422caccf7846de0ca73e37b4d10cbb6249744c2568be4',
        'collab/pack_usable_images_api_v1.py':'9adbb9f1b00aaeaed5fc35de8dc23b3574f20b9a0af601b25b51737bcf5a2e54',
        'scripts/usable_cohort_v2.py':'22bff1eb0fa14d102ad07786f936c5c1ed1582ec7bd5cee2b8e8dc5eb3520092'}
for name, digest in pins.items():
    if hashlib.sha256((deployment/name).read_bytes()).hexdigest()!=digest:
        raise ValueError('Deployed source differs from verified transport release')
sys.path[:0] = [str(deployment/'collab'), str(deployment/'scripts')]
import google.auth
from google.auth.transport.requests import AuthorizedSession
from drive_api_storage_v1 import DriveStore
from pack_usable_images_api_v1 import SOURCE_FOLDER, SCHEMA, COHORT, INDEX_SHA
credentials,_ = google.auth.default()
with AuthorizedSession(credentials) as session:
    store=DriveStore(session)
    with session.get('https://www.googleapis.com/drive/v3/about',params={'fields':'user(emailAddress),storageQuota'},timeout=30) as response:
        response.raise_for_status();about=response.json()
    if about['user']['emailAddress']!='panvee62@gmail.com':raise ValueError('Wrong approved Google account')
    free=int(about['storageQuota']['limit'])-int(about['storageQuota']['usage'])
    if free<85*1024**3:raise ValueError('Insufficient private Drive capacity')
    root=store.meta(SOURCE_FOLDER)['parents']
    if len(root)!=1:raise ValueError('Ambiguous source root')
    control=store.folder(root[0],'api_transport_v1')
    state=json.loads(store.read_small(store.children(control)['STATE.json']))
    if (state.get('schema')!=SCHEMA or state.get('cohort')!=COHORT or state.get('index_sha256')!=INDEX_SHA
            or state.get('job_id')!=EXPECTED_PREDECESSOR or state.get('phase')!='bounded_checkpoint'
            or state.get('pending') is not None or state.get('packed_shards')!=19
            or state.get('committed_images',0)<=319820 or not state.get('terminal_utc')):
        raise ValueError('Expected durable first-pack terminal state not proven')
    verified=json.loads(store.read_small(store.children(control)['FIRST_API_PACK_RECOVERY_VERIFIED_20261025.json']))
    if (verified.get('state')!='first_API_pack_recovery_readback_passed'
            or verified.get('job_id')!=EXPECTED_PREDECESSOR
            or verified.get('full_remote_SHA_MD5_readback_verified') is not True
            or verified.get('durable_images')!=337907 or verified.get('durable_packs')!=19):
        raise ValueError('Independent first-pack recovery proof missing')
    print(json.dumps({'utc':datetime.now(timezone.utc).isoformat(),'state':'bounded_API_continuation_release_verified',
                      'predecessor':EXPECTED_PREDECESSOR,'durable_images':state['committed_images'],
                      'durable_packs':state['packed_shards'],'pack_seconds':3600,'audit_seconds':1800,
                      'max_new_packs':47,'account_matches_approved':True,'Drive_free':free,
                      'runtime_pid':os.getpid(),'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
                      'training':False,'test_inference':False}),flush=True)
path=deployment/'collab/pack_usable_images_api_v1.py'
sys.argv=[str(path),'--index-id','1S0OQ0MIazcMMIXp0hQJMKfH1_drZmTZj','--pack-seconds','3600','--audit-seconds','1800','--max-new-packs','47']
runpy.run_path(str(path),run_name='__main__')
