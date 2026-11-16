# CPU-only bounded original-payload diagnosis; no Drive mount, no training.
from pathlib import Path
from datetime import datetime, timezone
import bz2, hashlib, io, json, os, tarfile, time, uuid, fcntl, zipfile
import requests
from urllib3.exceptions import HTTPError as UrllibHTTPError
from PIL import Image
SOURCE_ID='1cjY6HsHaSZuLVHywIxD5xQqng33J5S2b'
SOURCE_URL='https://drive.usercontent.google.com/download'
ARCHIVE_BYTES=113623359224
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

def payload_kind(raw):
    prefix = raw[:4096].lstrip().lower()
    if prefix.startswith(b'<!doctype html') or prefix.startswith(b'<html'):
        return 'HTML document, not a raster image'
    if prefix.startswith(b'<?xml') or prefix.startswith(b'<svg'):
        return 'XML/SVG document; inspect privately before any conversion'
    for signature, name in [(b'\xff\xd8\xff', 'JPEG'), (b'\x89PNG\r\n\x1a\n', 'PNG'),
                            (b'GIF87a', 'GIF'), (b'GIF89a', 'GIF'), (b'%PDF-', 'PDF')]:
        if raw.startswith(signature):
            return name
    if raw.startswith(b'RIFF') and raw[8:12] == b'WEBP':
        return 'WebP'
    if raw[4:8] == b'ftyp':
        return 'ISO base-media container; codec not inferred'
    return 'Unknown signature'

class DiagnosticBoundary(Exception):
    pass

class LimitedReader:
    def __init__(self, reader, byte_budget, deadline):
        self.reader = reader
        self.budget = byte_budget
        self.deadline = deadline

    def read(self, size=-1):
        if time.monotonic() >= self.deadline or self.reader.pos >= self.budget:
            raise DiagnosticBoundary('Bounded time/byte limit reached; no full source scan')
        remaining = self.budget - self.reader.pos
        return self.reader.read(min(size if size >= 0 else 1024**2, remaining))

    def readable(self):
        return True

    def seekable(self):
        return False

def run_stateless():
    lock=open('/content/urop_failed_specimen_stateless_v1.lock','a+')
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    base=Path('/content/urop_failed_specimens_stateless_v1')
    if base.exists():
        raise RuntimeError('Prior diagnostic exists; inspect report before retry')
    base.mkdir()
    records=[];targets=['dhgu9qk','c74xt4o','c964b6s'];started=time.monotonic()
    reader=PublicArchiveReader(max_retries=1)
    reason='requested specimens captured';error=None
    try:
        limited=LimitedReader(reader,512*1024**2,started+180)
        with bz2.BZ2File(limited,'rb') as expanded,tarfile.open(fileobj=expanded,mode='r|') as archive:
            for member in archive:
                if not member.isfile() or Path(member.name).stem not in targets:continue
                ident=Path(member.name).stem
                if member.size>32*1024**2:raise ValueError('32MiB specimen cap')
                raw=archive.extractfile(member).read();dest=base/Path(member.name).name
                with dest.open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
                try:
                    with Image.open(io.BytesIO(raw)) as im:im.load();im.convert('RGB').load();decoded={'strict_decode':True,'format':im.format,'size':list(im.size)}
                except Exception as e:decoded={'strict_decode':False,'error_type':type(e).__name__,'error':str(e)}
                row={'id':ident,'original_member':member.name,'file':dest.name,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'kind':payload_kind(raw),**decoded}
                records.append(row);targets.remove(ident);print(json.dumps({'state':'original_specimen_captured',**row}),flush=True)
                if not targets:break
    except DiagnosticBoundary as e:reason=str(e)
    except Exception as e:error={'type':type(e).__name__,'message':str(e)};reason='diagnostic failed; inspect error'
    finally:
        reader.close()
        result={'utc':datetime.now(timezone.utc).isoformat(),'state':'bounded_stateless_original_diagnostic_finished','specimens':records,'requested':3,'captured':len(records),'uncaptured_ids':targets,'stop_reason':reason,'error':error,'source_reader_sha256':'5b9be91021d4d397d8f3bd74c0354d0496b7cfb685723cf2c3c3ee24ea6266e6','compressed_bytes_consumed':reader.pos,'byte_budget':512*1024**2,'elapsed_seconds':time.monotonic()-started,'source_id':SOURCE_ID,'parent_archive_sha256':'e3f8fd7dfae6d864585affd0729ac06544471c93f6dc713c6f78d0bbe4a00abd','failure_report_sha256':'262a40e9e04629cda8c13388478a112016ba17ef42ed2d423bc517dc8911ebe0','full_crc_this_diagnostic':False,'image_gate_passed':False,'dataset_modified':False,'decoder_policy_changed':False,'training':False,'test_inference':False}
        (base/'diagnostic.json').write_text(json.dumps(result,indent=2))
        print(json.dumps(result),flush=True)
        zpath=base.with_suffix('.zip')
        with zipfile.ZipFile(zpath,'x',compression=zipfile.ZIP_STORED) as z:
            for f in sorted(base.iterdir()):z.write(f,f.name)
        print(json.dumps({'state':'specimen_bundle_ready','file':str(zpath),'bytes':zpath.stat().st_size,'sha256':hashlib.sha256(zpath.read_bytes()).hexdigest()}),flush=True)
        fcntl.flock(lock,fcntl.LOCK_UN);lock.close()
    from google.colab import files
    files.download(str(zpath))
run_stateless()
