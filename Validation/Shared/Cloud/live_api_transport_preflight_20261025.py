# Bounded synthetic transport preflight only; not image/training results.
from drive_api_storage_v1 import DriveStore,hashes,atomic_json
from pathlib import Path
from datetime import datetime,timezone
import google.auth,json,time
from google.auth.transport.requests import AuthorizedSession
start=time.monotonic();work=Path('/content/urop_api_engineering_v1');work.mkdir(exist_ok=True)
fixture=work/'synthetic_transport_9MiB.bin'
if not fixture.exists():
 with fixture.open('wb') as stream:
  for _ in range(9):stream.write(bytes(range(256))*4096)
sha,md5=hashes(fixture);credentials,_=google.auth.default()
with AuthorizedSession(credentials) as session:
 store=DriveStore(session);root_id=store.meta('1tY3NP96gcuHQwGUponsxRlqLD-sfXo9U')['parents'][0]
 engineering_folder=store.folder(root_id,'api_transport_engineering_v1',create=True)
 uploaded=store.upload_file(fixture,engineering_folder,fixture.name)
 verified=store.verify_remote(store.meta(uploaded['id']),sha)
 note=store.put_json(engineering_folder,'bounded_control_patch_check.json',{'state':'synthetic_only','phase':0})
 note=store.put_json(engineering_folder,'bounded_control_patch_check.json',{'state':'synthetic_only','phase':1},note)
 assert json.loads(store.read_small(note))['phase']==1
 report={'utc':datetime.now(timezone.utc).isoformat(),'state':'live_API_transport_engineering_passed','bytes':fixture.stat().st_size,'sha256':sha,'md5':md5,'full_remote_archive_SHA_verified':True,'control_PATCH_and_readback_passed':True,'seconds':time.monotonic()-start,'synthetic_only':True,'real_image_packing':False,'training':False,'test_inference':False}
 saved=store.put_json(engineering_folder,'API_TRANSPORT_ENGINEERING_PREFLIGHT_20261025.json',report)
 atomic_json(work/'engineering_receipt.json',report)
 print(json.dumps(report),flush=True)
