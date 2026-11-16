"""Meaningful synthetic restart and ranged-network failure checks; no network."""
import hashlib, importlib.util, io, json, tarfile, tempfile
from pathlib import Path
from PIL import Image
spec=importlib.util.spec_from_file_location('stream_v2',Path(__file__).resolve().parents[1]/'collab/prepare_official_images_stream_v2.py')
p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)

class Response:
    def __init__(self,data,offset,total,fail=False,bad=False):
        self.status_code=206;self.headers={'Content-Range':f'bytes {offset}-{total-1}/{total}','Content-Length':str(total-offset),'ETag':'same'}
        if bad:self.headers['Content-Range']='bytes 0-1/2'
        class Raw(io.BytesIO):
            def read(self,n=-1):
                if fail:raise IOError('injected transport failure')
                return super().read(n)
        self.raw=Raw(data[offset:]);self.closed=False
    def close(self):self.closed=True
    def raise_for_status(self):pass
class Session:
    def __init__(self,data,bad=False):self.data=data;self.ranges=[];self.bad=bad
    def get(self,url,params,headers,**kwargs):
        offset=int(headers['Range'].split('=')[1].split('-')[0]);self.ranges.append(offset)
        return Response(self.data,offset,len(self.data),fail=len(self.ranges)==2 and not self.bad,bad=self.bad)
    def close(self):pass

def main():
    payload=b'BZh9'+bytes(range(250))*20
    session=Session(payload)
    reader=p.PublicArchiveReader(total=len(payload),session=session)
    # Force a reconnect after a partial successful consumption, then a failure.
    out=reader.read(17);reader.response.close();reader.response=None
    saved=p.time.sleep;p.time.sleep=lambda _:None
    try:
        while reader.pos<len(payload):out+=reader.read(127)
    finally:p.time.sleep=saved;reader.close()
    assert out==payload and session.ranges==[0,17,17] and reader.reconnects==1
    bad=p.PublicArchiveReader(total=len(payload),session=Session(payload,bad=True))
    try:bad.read(1)
    except ValueError:pass
    else:raise AssertionError('Incorrect range accepted')
    expected={str(i):{'id':str(i),'split':['train','validation','test'][i%3],'clean_title':'synthetic','6_way_label':i%6} for i in range(9)}
    with tempfile.TemporaryDirectory(dir='data/official_paired_v1',prefix='stream-recovery-') as tmp:
        root=Path(tmp);(root/'shards').mkdir()
        archive=root/'fixture.tar.bz2'
        with tarfile.open(archive,'w:bz2') as tar:
            for i in range(9):
                b=io.BytesIO();Image.new('RGB',(20,20),(i*20,1,2)).save(b,format='PNG');raw=b.getvalue();info=tarfile.TarInfo('original/'+str(i)+'.png');info.size=len(raw);tar.addfile(info,io.BytesIO(raw))
        raw=archive.read_bytes()
        class Source(io.BytesIO):
            total=len(raw)
        factory=lambda:Source(raw)
        first=p.extract(root,expected,max_seconds=0,source_factory=factory,check_scratch=False)
        assert first['image_gate_passed'] is False
        result=p.extract(root,expected,shard_bytes=180,source_factory=factory,check_scratch=False)
        assert result['image_gate_passed'] and result['usable']==9 and result['compressed_archive_bytes']==len(raw) and result['compressed_archive_sha256']==hashlib.sha256(raw).hexdigest()
        hashes={x.name:p.prep.sha(x) for x in (root/'shards').glob('*.tar')}
        (root/'shards/orphan.tar').write_bytes(b'not trusted')
        again=p.extract(root,expected,source_factory=factory,check_scratch=False)
        assert again['usable']==9 and all(p.prep.sha(root/'shards'/name)==sha for name,sha in hashes.items())
        receipt=next((root/'shards').glob('*.receipt.json'));d=json.loads(receipt.read_text());(root/'shards'/d['archive']).write_bytes(b'corrupt')
        try:p.extract(root,expected,source_factory=factory,check_scratch=False)
        except ValueError:pass
        else:raise AssertionError('Corrupt shard accepted')
    report={'status':'passed','scope':'Synthetic only; no network or faculty-data experiment','checks':['Partial HTTP source consumption and exact-offset retry preserve every byte','Changed/inconsistent source range rejected','Bounded stop and subsequent full CRC/hash extraction','Exact nine-image coverage and original bytes','Repeated run skips trusted images and preserves immutable shards','Orphan ignored; corrupt committed shard rejected'],'source_sha256':hashlib.sha256(Path(p.__file__).read_bytes()).hexdigest()}
    Path('results/multimodal_stream_recovery_checks_20261024.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
