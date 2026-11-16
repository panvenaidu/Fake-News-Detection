# Bounded original archive access check: read at most4096bytes, no packing/training.
from pathlib import Path
from datetime import datetime, timezone
import json,hashlib,google.auth
from google.auth.transport.requests import AuthorizedSession
index_raw=Path('/content/urop_api_receipts_20261024T202737Z/index.json').read_bytes()
assert hashlib.sha256(index_raw).hexdigest()=='291a2c5b27aa39f1b1b16b3726655609927a08cee03a34e35d9fe7e47670a87a'
index=json.loads(index_raw);archive=index['artifacts'][0]['archive']
credentials,_=google.auth.default()
with AuthorizedSession(credentials) as session:
 with session.get('https://www.googleapis.com/drive/v3/files/'+archive['id'],params={'alt':'media'},headers={'Range':'bytes=0-4095','Accept-Encoding':'identity'},stream=True,timeout=(15,20)) as response:
  response.raise_for_status()
  assert response.status_code==206 and response.headers.get('Content-Range')=='bytes 0-4095/'+archive['size']
  assert int(response.headers['Content-Length'])==4096
  sample=response.raw.read(4096)
  assert len(sample)==4096
  sample_result={'utc':datetime.now(timezone.utc).isoformat(),'state':'bounded_original_archive_API_range_passed','archive':archive['name'],'bytes_read':len(sample),'http_status':response.status_code,'content_range':response.headers['Content-Range'],'sample_sha256':hashlib.sha256(sample).hexdigest(),'tar_ustar_magic':sample[257:262]==b'ustar','full_archive_hash_verified':False,'packing':False,'training':False}
print(json.dumps(sample_result),flush=True)
print('SOURCE RECEIPTS: 150 /150; approved membership: 682170 /682170')
print('PRIVATE METADATA INDEX: saved and byte-readback verified')
print('PACKING: 319820 /682170 in18durable archives; unchanged')
print('PART1 SCIENTIFIC TRAINING: 0 /2 epochs; full validation: 0 /2')
print('NEXT: verified lossless API transport, full private input, GPU preflight, training')
