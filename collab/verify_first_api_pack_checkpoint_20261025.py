"""Bounded independent full readback of the first real API pack checkpoint."""
from pathlib import Path
import hashlib
import json
import os
import sys
from datetime import datetime,timezone
source=Path('/content/urop_api_transport_source_e9efc3742d3a3e61')
sys.path.insert(0,str(source/'collab'))
from drive_api_storage_v1 import DriveStore,atomic_json
from pack_usable_images_api_v1 import SOURCE_FOLDER,SCHEMA,COHORT,INDEX_SHA
import google.auth
from google.auth.transport.requests import AuthorizedSession
credentials,_=google.auth.default()
with AuthorizedSession(credentials) as session:
    store=DriveStore(session)
    parent=store.meta(SOURCE_FOLDER)['parents'];assert len(parent)==1
    control=store.folder(parent[0],'api_transport_v1');files=store.children(control)
    state_raw=store.read_small(files['STATE.json']);state=json.loads(state_raw)
    assert state['job_id']=='CPU_API_PACK_af175d22e92d4a0caecf8a850bf94a3f'
    assert state['schema']==SCHEMA and state['cohort']==COHORT and state['index_sha256']==INDEX_SHA
    assert state['phase']=='bounded_checkpoint' and state['pending'] is None
    assert state['committed_images']==337907 and state['packed_shards']==19
    name='images_pack_e3061b6ff9044fdebd9b3fb98d180368.tar'
    committed=json.loads(store.read_small(files[name.replace('.tar','_committed.json')]))
    receipt_meta=store.meta(committed['receipt']['id']);receipt_raw=store.read_small(receipt_meta)
    receipt=json.loads(receipt_raw)
    assert receipt['archive']==name and len(receipt['images'])==18087
    assert len({r['id'] for r in receipt['images']})==18087
    original_ids={r['id']:r for r in receipt['images']}; matched=set()
    for cached in Path('/content/urop_api_transport_v1/source_receipts').glob('*.receipt.json'):
        raw=cached.read_bytes();original=json.loads(raw)
        for row in original['images']:
            if row['id'] not in original_ids:continue
            copied=original_ids[row['id']]
            assert row['id'] not in matched
            for key in ['id','split','clean_title','6_way_label','bytes','image_sha256','member','source_member']:
                assert row[key]==copied[key],key
            assert copied['input_shard']==original['archive'] and copied['input_shard_sha256']==original['sha256']
            matched.add(row['id'])
    assert len(matched)==18087
    archive=store.meta(committed['archive']['id'])
    proof=store.verify_remote(archive,receipt['sha256'])
    assert proof['bytes']==receipt['bytes'] and proof['md5Checksum']==state['archive_checks'][archive['id']]['md5Checksum']
    assert store.read_small(store.meta(files['STATE.json']['id']))==state_raw
    result={'utc':datetime.now(timezone.utc).isoformat(),'state':'first_API_pack_recovery_readback_passed',
            'job_id':state['job_id'],'phase':state['phase'],'pending':False,'durable_images':337907,'durable_packs':19,
            'new_images_independently_joined_to_original_receipts':18087,'archive':name,
            'archive_bytes':proof['bytes'],'archive_sha256':proof['sha256'],
            'receipt_bytes':len(receipt_raw),'receipt_sha256':hashlib.sha256(receipt_raw).hexdigest(),
            'control_sha256':hashlib.sha256(state_raw).hexdigest(),
            'full_remote_SHA_MD5_readback_verified':True,'runtime_image_gate_passed':False,
            'source_originals_preserved':True,'training':False,'test_inference':False}
    store.put_json(control,'FIRST_API_PACK_RECOVERY_VERIFIED_20261025.json',result)
    atomic_json('/content/UROP_FIRST_API_PACK_RECOVERY_VERIFIED_20261025.json',result)
    print(json.dumps(result),flush=True)
