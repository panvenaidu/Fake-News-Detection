"""Bounded CPU-only recovery inventory; no image extraction or full download."""
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter
import json, shutil, hashlib, requests, torch
assert not torch.cuda.is_available(), 'CPU only'
root=Path('/content/drive/MyDrive/UROP/official_images_v1')
assert root.is_dir(), 'Approved Drive mount required'
receipts=[]; seen=set(); counts=Counter(); archive_bytes=0
for p in sorted((root/'shards').glob('*.receipt.json')):
    v=json.loads(p.read_text()); a=root/'shards'/v['archive']
    assert a.is_file() and a.stat().st_size==v['bytes'], 'Committed shard size mismatch'
    for row in v['images']:
        assert row['id'] not in seen, 'Duplicate receipt ID'
        seen.add(row['id']); counts[row['split']]+=1
    archive_bytes+=v['bytes'];receipts.append({'name':p.name,'images':len(v['images']),'bytes':v['bytes'],'sha256':v['sha256']})
trusted={x['name'].replace('.receipt.json','.tar') for x in receipts}
orphans=[{'name':p.name,'bytes':p.stat().st_size} for p in (root/'shards').glob('*.tar') if p.name not in trusted]
report={'utc':datetime.now(timezone.utc).isoformat(),'state':'metadata_recovery_inventory','committed_images_in_receipts':len(seen),'counts':dict(counts),'shard_count':len(receipts),'shard_bytes':archive_bytes,'shards':receipts,'orphans_untrusted':orphans,'scratch_free':shutil.disk_usage('/content').free,'source_bytes':(root/'public_images.tar.bz2').stat().st_size,'source_sha256_not_recomputed':True,'full_image_gate_passed':False,'no_extraction':True,'no_training':True,'hash_verification_pending':True,'result_files':[p.name for p in root.glob('*_result.json')]}
print(json.dumps({k:v for k,v in report.items() if k!='shards'}),flush=True)
# Read at most 4 KiB from the same public author archive; never write archive bytes.
url='https://drive.usercontent.google.com/download'
try:
    with requests.get(url,params={'id':'1cjY6HsHaSZuLVHywIxD5xQqng33J5S2b','export':'download','confirm':'t'},headers={'Range':'bytes=0-4095','Accept-Encoding':'identity'},stream=True,timeout=(15,25)) as response:
        first=response.raw.read(4096)
        report['public_stream_probe']={'http_status':response.status_code,'content_length':response.headers.get('Content-Length'),'content_range':response.headers.get('Content-Range'),'content_type':response.headers.get('Content-Type'),'sample_bytes':len(first),'sample_sha256':hashlib.sha256(first).hexdigest(),'magic_bzh9':first[:4]==b'BZh9','bounded_read_only':True}
except Exception as error:
    report['public_stream_probe']={'error_type':type(error).__name__,'failed':True}
path=root/('recovery_inventory_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'.json')
with path.open('x') as f:json.dump(report,f,indent=2)
print(json.dumps({'state':'recovery_inventory_saved','receipt':path.name,'summary':{k:v for k,v in report.items() if k!='shards'}}),flush=True)
