"""CPU engineering check of 640 staged images; no scientific training/test."""
from pathlib import Path
from collections import Counter
from datetime import datetime, timezone
import hashlib, io, json, platform, shutil, importlib.metadata
from PIL import Image
assert len(expected_images)==640 and len({r['id'] for r in expected_images})==640
source_stem='images_590bbadd6dcd433b83059f13e85137bc'
roots=[p for p in Path('/kaggle/input').rglob(source_stem) if p.is_dir()]
assert len(roots)==1, f'Expected exactly one staging source wrapper, got {roots}'
root=roots[0];seen=[];counts=Counter();aggregate=hashlib.sha256()
for row in expected_images:
    path=root/row['member'];assert path.resolve().is_relative_to(root.resolve())
    raw=path.read_bytes();assert len(raw)==row['bytes'] and hashlib.sha256(raw).hexdigest()==row['image_sha256'], row['id']
    with Image.open(io.BytesIO(raw)) as image:image.load();image.convert('RGB').load()
    seen.append(row['id']);counts[row['split']]+=1;aggregate.update((row['id']+':'+row['image_sha256']+'\n').encode())
actual=[p for p in (root/'images').rglob('*') if p.is_file()]
assert len(actual)==len(seen)==640
versions={}
for name in ['torch','torchvision','transformers','Pillow','numpy']:
    try:versions[name]=importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:versions[name]='not installed'
report={'utc':datetime.now(timezone.utc).isoformat(),'state':'private_staging_input_integrity_passed','scope':'Engineering integrity of existing640images only; INCOMPLETE official cohort','verified_images':640,'split_counts':dict(counts),'input_root':str(root.parent),'observed_layout':str(root.relative_to(root.parent))+'/images/<id>.<suffix>','full_image_gate_passed':False,'training':False,'validation_inference':False,'test_inference':False,'requested_accelerator':'None','python':platform.python_version(),'versions':versions,'working_disk':dict(zip(['total','used','free'],shutil.disk_usage('/kaggle/working'))),'aggregate_image_hash':aggregate.hexdigest()}
output=Path('/kaggle/working/MM_PART1_PRIVATE_STAGING_ENGINEERING_20261024.json');output.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report),flush=True)
