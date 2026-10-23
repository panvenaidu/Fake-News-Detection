"""Synthetic archive sharding/restart checks. Never downloads or mounts Drive."""
import importlib.util,io,json,tempfile,tarfile
from pathlib import Path
from PIL import Image
spec=importlib.util.spec_from_file_location('prep',Path(__file__).resolve().parents[1]/'collab/prepare_official_images_drive_v1.py');prep=importlib.util.module_from_spec(spec);spec.loader.exec_module(prep)

def main():
 expected={str(i):{'id':str(i),'split':['train','validation','test'][i%3],'clean_title':'synthetic','6_way_label':i%6} for i in range(6)}
 with tempfile.TemporaryDirectory(dir='data/official_paired_v1',prefix='prep-test-') as temp:
  root=Path(temp)
  with tarfile.open(root/'public_images.tar.bz2','w:bz2') as out:
   for i in range(6):
    stream=io.BytesIO();Image.new('RGB',(20,20),(i*30,10,20)).save(stream,format='PNG');raw=stream.getvalue();info=tarfile.TarInfo('original/'+str(i)+'.png');info.size=len(raw);out.addfile(info,io.BytesIO(raw))
  source_sha=prep.sha(root/'public_images.tar.bz2')
  first=prep.extract(root,expected,shard_bytes=100,max_shards=1);assert first['status']=='bounded extraction checkpoint' and first['usable_committed']==1
  complete=prep.extract(root,expected,shard_bytes=100,max_shards=None);assert complete['image_gate_passed'] and complete['usable']==6
  assert prep.sha(root/'public_images.tar.bz2')==source_sha
  seen=[]
  for receipt in (root/'shards').glob('*.receipt.json'):
   d=json.loads(receipt.read_text());assert prep.sha(root/'shards'/d['archive'])==d['sha256']
   with tarfile.open(root/'shards'/d['archive']) as tar:
    for row in d['images']:
     raw=tar.extractfile(row['member']).read();assert prep.hashlib.sha256(raw).hexdigest()==row['image_sha256'];seen.append(row['id'])
  assert len(seen)==len(set(seen))==6
  again=prep.extract(root,expected,shard_bytes=100);assert again['usable']==6
  # An orphan half-written shard has no receipt and cannot enter the dataset.
  (root/'shards/orphan.tar').write_bytes(b'incomplete')
  assert prep.extract(root,expected,shard_bytes=100)['usable']==6
  receipt=next((root/'shards').glob('*.receipt.json'));d=json.loads(receipt.read_text());(root/'shards'/d['archive']).write_bytes(b'corrupt')
  try:prep.extract(root,expected,shard_bytes=100)
  except ValueError as e:assert 'corrupt' in str(e)
  else:raise AssertionError('Corrupt committed shard accepted')
 result={'status':'passed','scope':'Synthetic6-image compressed archive only; no network or real images','checks':['Bounded extraction and subsequent restart','All committed original image bytes/hashes preserved','No duplicate rows on repeated extraction','Uncommitted orphan excluded','Corrupt committed shard rejected','Durable source unchanged'],'not_verified':['Real106G source transport/range-resume','Drive FUSE read/write throughput','Full author archive ID coverage','Private Kaggle import/extraction capacity']}
 Path('results/multimodal_image_prep_checks_20261023.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
