"""CPU recovery of the same author archive without DriveFS source caching.

Original compressed bytes stream from the original public Drive file; image
shards and receipts stay private in the approved Drive folder. No OAuth, GPU,
account changes, paid resources, local full archive, or dataset exclusions.
"""
import bz2, csv, hashlib, importlib.util, io, json, os, re, shutil, tarfile, time, uuid
from contextlib import contextmanager
from pathlib import Path
import requests
from urllib3.exceptions import HTTPError as UrllibHTTPError
from PIL import Image

_spec=importlib.util.spec_from_file_location('imageprep_v1',Path(__file__).with_name('prepare_official_images_drive_v1.py'))
prep=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(prep)
SOURCE_ID=prep.SOURCE_ID
ARCHIVE_BYTES=113623359224
SOURCE_URL='https://drive.usercontent.google.com/download'

class PublicArchiveReader:
    """Sequential bounded-memory reader; retries use verified HTTP byte ranges."""
    def __init__(self,total=ARCHIVE_BYTES,session=None,max_retries=4):
        self.total=total;self.pos=0;self.session=session or requests.Session()
        self.response=None;self.etag=None;self.max_retries=max_retries;self.reconnects=0
    def readable(self):return True
    def seekable(self):return False
    def _connect(self):
        if self.response is not None:self.response.close()
        response=self.session.get(SOURCE_URL,params={'id':SOURCE_ID,'export':'download','confirm':'t'},headers={'Range':f'bytes={self.pos}-{self.total-1}','Accept-Encoding':'identity'},stream=True,timeout=(20,90))
        try:
            response.raise_for_status()
            expected=f'bytes {self.pos}-{self.total-1}/{self.total}'
            if response.status_code!=206 or response.headers.get('Content-Range')!=expected:
                raise ValueError('Source range/total mismatch; refuse HTML or restarted response')
            if response.headers.get('Content-Encoding','identity') not in ('','identity'):
                raise ValueError('Encoded HTTP response is not original archive bytes')
            if int(response.headers.get('Content-Length','-1'))!=self.total-self.pos:
                raise ValueError('Source response length mismatch')
            etag=response.headers.get('ETag')
            if self.etag is not None and etag!=self.etag:raise ValueError('Source ETag changed')
            self.etag=etag;self.response=response
        except BaseException:response.close();raise
    def read(self,size=-1):
        # BZ2File requests small bounded reads. Never allocate the full archive.
        size=min(1024*1024, self.total-self.pos) if size<0 else min(size,self.total-self.pos)
        if size==0:return b''
        for attempt in range(self.max_retries+1):
            try:
                if self.response is None:self._connect()
                block=self.response.raw.read(size)
                if not block:raise IOError('Premature source EOF')
                self.pos+=len(block);return block
            except (requests.RequestException, UrllibHTTPError, IOError) as error:
                if self.response is not None:self.response.close()
                self.response=None
                if attempt>=self.max_retries:raise IOError('Bounded source retries exhausted') from error
                self.reconnects+=1;time.sleep(min(2**attempt,15))
        raise AssertionError('Unreachable')
    def close(self):
        if self.response is not None:self.response.close()
        self.session.close()
    def __enter__(self):return self
    def __exit__(self,*args):self.close()

def committed(root,expected):
    seen={};counts={};begin=time.monotonic()
    receipts=sorted((root/'shards').glob('*.receipt.json'))
    for number,path in enumerate(receipts,1):
        receipt=json.loads(path.read_text());archive=root/'shards'/receipt['archive']
        if archive.parent.resolve()!=(root/'shards').resolve() or not archive.is_file() or archive.stat().st_size!=receipt['bytes'] or prep.sha(archive)!=receipt['sha256']:
            raise ValueError('Committed shard bytes/hash invalid '+path.name)
        for row in receipt['images']:
            ident=row['id']
            if ident in seen or ident not in expected:raise ValueError('Duplicate/unexpected receipt ID')
            if any(row.get(key)!=value for key,value in expected[ident].items()):raise ValueError('Receipt differs from official TSV '+ident)
            seen[ident]=row['image_sha256']
        print(json.dumps({'utc':prep.now(),'state':'revalidating_committed_shards','shards_checked':number,'shards_total':len(receipts),'usable_verified':len(seen),'scratch_free':shutil.disk_usage('/content').free if str(root).startswith('/content/') else None}),flush=True)
    return seen

def extract(root,expected,max_seconds=28800,shard_bytes=512*1024**2,source_factory=PublicArchiveReader,check_scratch=True):
    root=Path(root);shardroot=root/'shards';shardroot.mkdir(exist_ok=True)
    seen=committed(root,expected);source_ids=set();failures=[];start=time.monotonic()
    writer=None;path=None;images=[];written=0;members=0
    def commit():
        nonlocal writer,path,images,written
        if writer is None:return
        writer.close();writer=None
        # Commit bytes before immutable receipt; leave incomplete writes as orphans.
        with path.open('rb') as f:os.fsync(f.fileno())
        receipt={'utc':prep.now(),'archive':path.name,'bytes':path.stat().st_size,'sha256':prep.sha(path),'images':images}
        prep.record(path.with_suffix('.receipt.json'),receipt)
        for row in images:seen[row['id']]=row['image_sha256']
        images=[];written=0
    def status(reader,state):
        result={'utc':prep.now(),'state':state,'usable_committed':len(seen),'usable_in_open_shard':len(images),'required':len(expected),'source_bytes_read':reader.count,'source_required_members_seen':len(source_ids),'elapsed_seconds':time.monotonic()-start,'scratch_free':shutil.disk_usage('/content').free if check_scratch else None}
        print(json.dumps(result),flush=True)
        return result
    try:
        with source_factory() as original:
            reader=prep.DigestReader(original)
            with bz2.BZ2File(reader,'rb') as decompressed,tarfile.open(fileobj=decompressed,mode='r|') as source:
                for member in source:
                    members+=1
                    if time.monotonic()-start>=max_seconds:
                        commit();return {**status(reader,'bounded_stream_checkpoint'),'image_gate_passed':False}
                    if not member.isfile():continue
                    ident=Path(member.name).stem
                    if ident not in expected:continue
                    if ident in source_ids:raise ValueError('Duplicate required source ID '+ident)
                    source_ids.add(ident)
                    if ident in seen:
                        if len(source_ids)%10000==0:status(reader,'replaying_verified_prefix')
                        continue
                    if member.size>512*1024**2:raise ValueError('Required image over512MiB '+ident)
                    raw=source.extractfile(member).read();digest=hashlib.sha256(raw).hexdigest()
                    try:
                        with Image.open(io.BytesIO(raw)) as image:image.load();image.convert('RGB').load()
                    except Exception as error:
                        failures.append({'id':ident,'error':str(error)});continue
                    if writer is not None and written+len(raw)>shard_bytes:commit()
                    if writer is None:
                        path=shardroot/('images_'+uuid.uuid4().hex+'.tar');writer=tarfile.open(path,'w')
                    name='images/'+ident+Path(member.name).suffix.lower()
                    info=tarfile.TarInfo(name);info.size=len(raw);info.mtime=0;writer.addfile(info,io.BytesIO(raw))
                    images.append({**expected[ident],'member':name,'image_sha256':digest,'bytes':len(raw),'source_member':member.name});written+=len(raw)
                    if (len(seen)+len(images))%1000==0:
                        status(reader,'extracting_from_public_author_stream')
                        if check_scratch and shutil.disk_usage('/content').free<8*1024**3:
                            commit();return {**status(reader,'scratch_safe_checkpoint'),'image_gate_passed':False}
                commit()
                while decompressed.read(1024*1024):pass
                expected_bytes=getattr(original,'total',None)
                if expected_bytes is not None and reader.count!=expected_bytes:raise ValueError('Incomplete compressed stream')
                missing=sorted(set(expected)-set(seen))
                result={'utc':prep.now(),'image_gate_passed':not missing and not failures,'required':len(expected),'usable':len(seen),'missing_ids':missing,'decode_failures':failures,'compressed_archive_sha256':reader.digest.hexdigest(),'compressed_archive_bytes':reader.count,'elapsed_seconds':time.monotonic()-start,'source_id':SOURCE_ID,'source_route':'Same public author Drive file streamed without DriveFS source cache','source_crc_consumed':True,'status':'Source extraction complete; private runtime hash/decode audit still required'}
                prep.record(root/('extraction_'+uuid.uuid4().hex+'.json'),result);return result
    except BaseException:
        # Preserve the last complete generation. Open TAR remains an untrusted orphan.
        raise
    finally:
        if writer is not None:writer.close()
