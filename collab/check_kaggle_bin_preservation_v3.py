"""Tiny actual private-storage feasibility fixture; no faculty images/model."""
from pathlib import Path
import hashlib
import io
import json
import tarfile
import time
from PIL import Image
from kagglehub.clients import build_kaggle_client
from kagglehub.gcs_upload import UploadDirectoryInfo
from kagglesdk.datasets.types.dataset_api_service import ApiCreateDatasetRequest
from transfer_verified_packs_to_kaggle_v1 import upload_file, atomic_json

root = Path('/content/urop_bin_fixture_v3')
root.mkdir(exist_ok=True)
file = root / 'transport_fixture.bin'
assert not (root / 'CREATE_SUBMITTED').exists(), 'Inspect existing private fixture before any create retry'
with tarfile.open(file, 'w') as archive:
    for i in range(2):
        buffer = io.BytesIO()
        Image.new('RGB', (16, 16), color=(i * 100, 40, 90)).save(buffer, format='PNG')
        raw = buffer.getvalue()
        member = tarfile.TarInfo('images/synthetic' + str(i) + '.png')
        member.size = len(raw)
        archive.addfile(member, io.BytesIO(raw))
raw = file.read_bytes()
entry = {'name': file.name, 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest(),
         'md5Checksum': hashlib.md5(raw).hexdigest()}
item = {}
upload_file(file, entry, item, lambda: atomic_json(root / 'PRIVATE_UPLOAD_STATE.json', item), time.monotonic() + 180)
assert item['complete']
request = ApiCreateDatasetRequest()
request.owner_slug = 'rocky62'
request.slug = 'urop-packed-bin-engineering-fixture-20261026'
request.title = 'UROP packed binary engineering fixture'
request.is_private = True
proto = UploadDirectoryInfo(name='root', files=[item['token']]).to_proto()
request.files, request.directories = proto.files, proto.directories
(root / 'CREATE_SUBMITTED').write_text('Inspect actual private saved input; no blind retry\n')
with build_kaggle_client() as client:
    client.datasets.dataset_api_client.create_dataset(request)
print(json.dumps({'state': 'private_binary_fixture_submitted', 'synthetic_images': 2,
                  'source_file_bytes': len(raw), 'original_sha256': entry['sha256'],
                  'dataset': 'rocky62/' + request.slug, 'faculty_images': 0, 'training': False}), flush=True)
