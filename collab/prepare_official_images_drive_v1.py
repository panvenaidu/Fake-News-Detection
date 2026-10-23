"""CPU-only, resumable staging of the author archive on an approved mounted Drive.

Run THROUGH THE COLAB NOTEBOOK only after Drive access is approved. No OAuth,
credentials, GPUs, sharing changes or paid resources are created by this script.
Download and extraction are separate bounded operations. Shards preserve bytes.
"""
import argparse,bz2,csv,hashlib,io,json,os,shutil,tarfile,time,uuid
from datetime import datetime,timezone
from pathlib import Path
from PIL import Image

SOURCE_ID='1cjY6HsHaSZuLVHywIxD5xQqng33J5S2b'
TSVS=[('train','multimodal_train.tsv','1XsOkD3yhxgWu8URMes0S9LVSwuFJ4pT6','9894cb4aa2f901c6f29b61ac3d95ce9f7e78c43be8062ae5deb1c219c82497bb',564000),('validation','multimodal_validate.tsv','1Z99QrwpthioZQY2U6HElmnx8jazf7-Kv','c70140ec376e083e3780b5b488c96c8933678ca5800139bfb78c92e95df6946e',59342),('test','multimodal_test_public.tsv','1p9EewIKVcFbipVRLZNGYc2JbSC7A0SWv','bc92378e070ca7b1a7497053d1c34cdc3f550be6232a76791a2c722d6d9bbf94',59319)]

def now():return datetime.now(timezone.utc).isoformat()
def sha(path):
 h=hashlib.sha256()
 with open(path,'rb') as f:
  for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
 return h.hexdigest()
def record(path,value):
 # Immutable generation files: consumers trust only a completed parse + hashes.
 with Path(path).open('x') as f:json.dump(value,f,indent=2,allow_nan=False);f.flush();os.fsync(f.fileno())
def require_drive(root):
 if not root.resolve().is_relative_to(Path('/content/drive/MyDrive/UROP/official_images_v1')):raise ValueError('Dedicated authorized Drive staging path required')
 if not Path('/content/drive/MyDrive').is_dir():raise RuntimeError('Drive is not mounted; obtain user permission first')
 import torch
 if torch.cuda.is_available():raise RuntimeError('CPU preparation requires accelerator None; preserve GPU allowance')
 root.mkdir(parents=True,exist_ok=True)
 quota=json.loads((root/'cloud_storage_receipt.json').read_text())
 if quota.get('available_bytes_lower_bound',0)<300*1024**3:raise RuntimeError('Need verified remote Drive quota >=300GiB')
 # Drive FUSE statvfs can report notebook scratch space instead of account quota.
 if shutil.disk_usage('/content').free<8*1024**3:raise RuntimeError('Need8GiB scratch margin for bounded staging')
 # Prove the basic Drive file/rename route before a long download.
 test=root/('write_test_'+uuid.uuid4().hex);moved=test.with_suffix('.moved')
 test.write_bytes(b'UROP storage preflight');os.replace(test,moved)
 if moved.read_bytes()!=b'UROP storage preflight':raise IOError('Drive readback mismatch')
 moved.unlink()
def expected_rows(root,download=False):
 result={}
 for split,name,fileid,digest,count in TSVS:
  p=root/name
  if not p.exists():
   if not download:raise FileNotFoundError(p)
   import gdown
   if not gdown.download(id=fileid,output=str(p),resume=True,use_cookies=False):raise RuntimeError('Official TSV download failed')
  if sha(p)!=digest:raise ValueError('Official TSV checksum mismatch '+name)
  with p.open() as f:rows=list(csv.DictReader(f,delimiter='\t'))
  if len(rows)!=count:raise ValueError('Official count mismatch')
  for r in rows:
   ident=r['id']
   if ident in result or not ident.isalnum() or int(r['6_way_label']) not in range(6) or not r['clean_title'].strip():raise ValueError('Official ID/label/text invalid')
   result[ident]={'id':ident,'split':split,'clean_title':r['clean_title'],'6_way_label':int(r['6_way_label'])}
 return result

def download(root):
 require_drive(root);expected_rows(root,download=True)
 archive=root/'public_images.tar.bz2';receipt=root/'archive_complete.json'
 if receipt.exists():
  d=json.loads(receipt.read_text());assert archive.stat().st_size==d['bytes'] and sha(archive)==d['sha256'];print('Verified complete source already present');return
 import gdown
 # Partial bytes remain in this Drive directory across runtime loss. gdown's
 # range-resume still needs real-source verification before calling it proven.
 result=gdown.download(id=SOURCE_ID,output=str(archive),resume=True,use_cookies=False)
 if not result or archive.stat().st_size<90_000_000_000:raise RuntimeError('Source incomplete or unexpected small response; preserve partial evidence')
 with archive.open('rb') as f:
  if f.read(3)!=b'BZh':raise ValueError('Expected bzip2, not HTML')
 record(receipt,{'utc':now(),'source_id':SOURCE_ID,'bytes':archive.stat().st_size,'sha256':sha(archive),'status':'transport complete; TAR coverage/CRC not yet verified'})

class DigestReader:
 def __init__(self,stream):self.stream=stream;self.digest=hashlib.sha256();self.count=0
 def read(self,size=-1):
  value=self.stream.read(size);self.digest.update(value);self.count+=len(value);return value
 def readable(self):return True
 def seekable(self):return False

def extract(root,expected,shard_bytes=2*1024**3,max_shards=None,max_seconds=None):
 """Resume by rereading durable compressed source and skipping committed IDs.

 Never redownloads the source. Abandoned shards are not trusted or silently used.
 Commit shard bytes first, then the corresponding receipt; crash before the
 receipt leaves an orphan for diagnosis. Shard receipts bind each image hash.
 """
 shardroot=root/'shards';shardroot.mkdir(parents=True,exist_ok=True);seen={};failures=[]
 for receipt in sorted(shardroot.glob('*.receipt.json')):
  r=json.loads(receipt.read_text());p=shardroot/r['archive']
  if not p.is_file() or sha(p)!=r['sha256']:raise ValueError('Committed shard corrupt '+p.name)
  for im in r['images']:
   if im['id'] in seen:raise ValueError('Duplicate committed ID')
   seen[im['id']]=im['image_sha256']
 writer=None;path=None;images=[];written=0;committed=0;archive_ids=set();start=time.monotonic()
 def commit():
  nonlocal writer,path,images,written,committed
  if writer is None:return
  writer.close();writer=None
  receipt={'utc':now(),'archive':path.name,'bytes':path.stat().st_size,'sha256':sha(path),'images':images}
  record(path.with_suffix('.receipt.json'),receipt)
  for im in images:seen[im['id']]=im['image_sha256']
  images=[];written=0;committed+=1
 try:
  with (root/'public_images.tar.bz2').open('rb') as original:
   reader=DigestReader(original)
   with bz2.BZ2File(reader,mode='rb') as decompressed,tarfile.open(fileobj=decompressed,mode='r|') as source:
    for member in source:
     if max_seconds is not None and time.monotonic()-start>=max_seconds:break
     if not member.isfile():continue
     ident=Path(member.name).stem
     if ident not in expected:continue
     if ident in archive_ids:raise ValueError('Duplicate required source ID '+ident)
     archive_ids.add(ident)
     if ident in seen:continue
     if member.size>512*1024**2:raise ValueError('Unexpected required image >512MiB '+ident)
     stream=source.extractfile(member)
     if stream is None:raise ValueError('Unreadable required member '+ident)
     raw=stream.read();digest=hashlib.sha256(raw).hexdigest()
     try:
      with Image.open(io.BytesIO(raw)) as im:im.load();im.convert('RGB').load()
     except Exception as e:failures.append({'id':ident,'error':str(e)});continue
     if writer is not None and written+len(raw)>shard_bytes:
      commit()
      if max_shards is not None and committed>=max_shards:break
     if writer is None:
      path=shardroot/('images_'+uuid.uuid4().hex+'.tar');writer=tarfile.open(path,'w')
     suffix=Path(member.name).suffix.lower();name='images/'+ident+suffix
     info=tarfile.TarInfo(name);info.size=len(raw);info.mtime=0;writer.addfile(info,io.BytesIO(raw))
     images.append({**expected[ident],'member':name,'image_sha256':digest,'bytes':len(raw),'source_member':member.name});written+=len(raw)
     if (len(seen)+len(images))%1000==0:
      status={'utc':now(),'state':'extracting','usable_committed':len(seen),'usable_in_open_shard':len(images),'required':len(expected),'elapsed_seconds':time.monotonic()-start}
      print(json.dumps(status),flush=True)
      if str(root).startswith('/content/drive/') and shutil.disk_usage('/content').free<8*1024**3:raise RuntimeError('Scratch margin fell below8GiB; preserve committed shards')
    else:
     commit()
     while decompressed.read(1024*1024):pass # consume bzip2 footer and verify its CRC
     if reader.count!=(root/'public_images.tar.bz2').stat().st_size:raise ValueError('Compressed source was not completely consumed')
     missing=sorted(set(expected)-set(seen))
     report={'utc':now(),'image_gate_passed':not missing and not failures,'required':len(expected),'usable':len(seen),'missing_ids':missing,'decode_failures':failures,'compressed_archive_sha256':reader.digest.hexdigest(),'compressed_archive_bytes':reader.count,'elapsed_seconds':time.monotonic()-start,'status':'Extraction complete; private Kaggle import/runtime hash audit still required'}
     record(root/('extraction_'+uuid.uuid4().hex+'.json'),report);return report
  commit();return {'status':'bounded extraction checkpoint','committed_shards':committed,'usable_committed':len(seen),'image_gate_passed':False}
 finally:
  if writer is not None:writer.close() # orphan without receipt remains untrusted

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--mode',choices=['download','extract'],required=True);ap.add_argument('--root',type=Path,default=Path('/content/drive/MyDrive/UROP/official_images_v1'));ap.add_argument('--max-shards',type=int,default=128);ap.add_argument('--max-seconds',type=int,default=14400);a=ap.parse_args();require_drive(a.root)
 if a.mode=='download':download(a.root)
 else:
  archive=json.loads((a.root/'archive_complete.json').read_text());p=a.root/'public_images.tar.bz2'
  if p.stat().st_size!=archive['bytes']:raise ValueError('Source archive size changed')
  if archive.get('sha256') and sha(p)!=archive['sha256']:raise ValueError('Source archive integrity failed')
  if archive.get('mtime_ns') and p.stat().st_mtime_ns!=archive['mtime_ns']:raise ValueError('Cloud copy modified since staging')
  print(json.dumps(extract(a.root,expected_rows(a.root),max_shards=a.max_shards,max_seconds=a.max_seconds),indent=2))
if __name__=='__main__':main()
