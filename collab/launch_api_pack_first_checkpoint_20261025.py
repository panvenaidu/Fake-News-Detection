# One bounded real-data CPU transaction after verified live transport checks.
# No model execution, test inference, DriveFS mount, account change or deletion.
from pathlib import Path
from datetime import datetime,timezone
import google.auth,json,hashlib,runpy,sys,shutil,os
from google.auth.transport.requests import AuthorizedSession
assert not Path('/content/drive/MyDrive').is_dir(),'Do not use a mounted DriveFS in this route'
assert json.loads(Path('/content/urop_api_engineering_v1/engineering_receipt.json').read_text())['state']=='live_API_transport_engineering_passed'
deployment=Path('/content/urop_api_transport_source_e9efc3742d3a3e61')
expected={'collab/drive_api_storage_v1.py':'d7603e6bad1af1560a9422caccf7846de0ca73e37b4d10cbb6249744c2568be4',
          'collab/pack_usable_images_api_v1.py':'9adbb9f1b00aaeaed5fc35de8dc23b3574f20b9a0af601b25b51737bcf5a2e54',
          'scripts/usable_cohort_v2.py':'22bff1eb0fa14d102ad07786f936c5c1ed1582ec7bd5cee2b8e8dc5eb3520092'}
for name,digest in expected.items():assert hashlib.sha256((deployment/name).read_bytes()).hexdigest()==digest
index=json.loads(Path('/content/urop_api_source_index.json').read_text())
credentials,_=google.auth.default()
with AuthorizedSession(credentials) as session:
 with session.get('https://www.googleapis.com/drive/v3/about',params={'fields':'storageQuota,user(emailAddress)'},timeout=25) as response:
  response.raise_for_status();about=response.json()
 assert about['user']['emailAddress']=='panvee62@gmail.com','Wrong authorized API account'
 quota=about['storageQuota'];free=int(quota['limit'])-int(quota['usage'])
 # Conservative full-source upper bound; originals remain preserved in Drive.
 required=sum(int(x['archive']['size']) for x in index['artifacts'])+4*1024**3
 assert free>required,'Insufficient private Drive capacity for lossless completion'
 assert shutil.disk_usage('/content').free>12*1024**3,'Insufficient bounded cloud scratch'
print(json.dumps({'utc':datetime.now(timezone.utc).isoformat(),'state':'bounded_API_pack_release_verified','account_matches_approved':True,'Drive_free':free,'conservative_free_required':required,'pack_seconds':3600,'audit_seconds':1800,'max_new_packs':1,'source_originals_retained':True,'runtime_pid':os.getpid(),'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'training':False,'test_inference':False}),flush=True)
path=deployment/'collab/pack_usable_images_api_v1.py'
sys.argv=[str(path),'--index-id','1S0OQ0MIazcMMIXp0hQJMKfH1_drZmTZj','--pack-seconds','3600','--audit-seconds','1800','--max-new-packs','1']
runpy.run_path(str(path),run_name='__main__')
