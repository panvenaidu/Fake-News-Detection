"""Bounded private transfer index after complete transport AND metadata.
No download, upload to Kaggle, model, new auth or visibility change. Only a small
private Drive JSON is created. Private file IDs are not printed or put in Git.
"""
from pathlib import Path
import hashlib,json,sys,signal
from contextlib import contextmanager
from datetime import datetime,timezone
sys.path.insert(0,str(Path(__file__).resolve().parent))
from drive_api_storage_v1 import DriveStore
from pack_usable_images_api_v1 import SOURCE_FOLDER,SCHEMA,COHORT,INDEX_SHA
import google.auth
from google.auth.transport.requests import AuthorizedSession
credentials,_=google.auth.default()
@contextmanager
def deadline():
    def expired(*_):raise TimeoutError('Ten-minute private metadata index bound')
    previous=signal.signal(signal.SIGALRM,expired);signal.alarm(600)
    try:yield
    finally:signal.alarm(0);signal.signal(signal.SIGALRM,previous)
with deadline(), AuthorizedSession(credentials) as session:
    store=DriveStore(session)
    parents=store.meta(SOURCE_FOLDER)['parents'];assert len(parents)==1
    root=parents[0];control=store.folder(root,'api_transport_v1');files=store.children(control)
    state_raw=store.read_small(files['STATE.json']);state=json.loads(state_raw)
    metadata_job=json.loads(store.read_small(files['METADATA_JOB_V2.json'])) if 'METADATA_JOB_V2.json' in files else {}
    ready=(state.get('schema')==SCHEMA and state.get('cohort')==COHORT and state.get('index_sha256')==INDEX_SHA
           and state.get('phase')=='complete' and state.get('pending') is None and state.get('committed_images')==682170
           and metadata_job.get('phase')=='complete'
           and metadata_job.get('transport_control_sha256')==hashlib.sha256(state_raw).hexdigest())
    if not ready:
        print(json.dumps({'state':'private_transfer_index_deferred','transport_phase':state.get('phase'),
                          'images':state.get('committed_images'),'metadata_phase':metadata_job.get('phase'),
                          'training':False,'test_inference':False}),flush=True)
    else:
        raw=store.read_small(store.meta(metadata_job['receipt_meta']['id']),metadata_job['receipt_sha256'])
        metadata=json.loads(raw)
        packed=store.children(store.folder(store.folder(root,'kaggle_packed_usable_v2'),'shards'))
        entries=[]
        for name,meta in sorted(packed.items()):
            if not name.endswith('.receipt.json'):continue
            receipt_raw=store.read_small(meta);receipt=json.loads(receipt_raw)
            archive=store.meta(packed[receipt['archive']]['id']);cached=state['archive_checks'][archive['id']]
            proof=metadata_job['archive_proofs'][archive['name']]
            assert int(archive['size'])==receipt['bytes']==cached['bytes']
            assert archive['md5Checksum']==cached['md5Checksum']
            assert receipt['sha256']==cached['sha256']
            assert proof['verified_current_metadata'] is True
            assert proof['receipt_sha256']==hashlib.sha256(receipt_raw).hexdigest()
            assert all(proof[key]==cached[key] for key in ('id','name','bytes','sha256','md5Checksum'))
            assert proof['version']==archive['version']
            entries.append({'name':archive['name'],'id':archive['id'],'bytes':receipt['bytes'],
                            'sha256':receipt['sha256'],'md5Checksum':archive['md5Checksum'],'version':archive['version']})
        assert len(entries)==state['packed_shards']
        for item in metadata['packages']:
            meta=store.meta(item['private_file']['id'])
            assert int(meta['size'])==item['bytes'] and meta['md5Checksum']==item['md5Checksum']
            entries.append({'name':item['name'],'id':meta['id'],'bytes':item['bytes'],
                            'sha256':item['sha256'],'md5Checksum':item['md5Checksum'],'version':meta['version']})
        assert len(entries)<=50 and len({e['name'] for e in entries})==len(entries)
        result={'utc':datetime.now(timezone.utc).isoformat(),'state':'private_transfer_index_ready','cohort':COHORT,
                'transport_job':state['job_id'],'manifest_sha256':metadata['manifest_sha256'],
                'files':entries,'total_bytes':sum(e['bytes'] for e in entries),
                'training':False,'test_inference':False,'runtime_image_gate_passed':False}
        existing=store.children(control).get('KAGGLE_TRANSFER_MANIFEST_V2.json')
        saved=store.put_json(control,'KAGGLE_TRANSFER_MANIFEST_V2.json',result,existing)
        digest=hashlib.sha256(store.read_small(saved)).hexdigest()
        print(json.dumps({'state':result['state'],'files':len(entries),'total_bytes':result['total_bytes'],
                          'sha256':digest,'private_location':'api_transport_v1/KAGGLE_TRANSFER_MANIFEST_V2.json',
                          'training':False,'test_inference':False}),flush=True)
