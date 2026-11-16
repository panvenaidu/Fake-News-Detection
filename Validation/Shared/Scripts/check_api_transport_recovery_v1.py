"""Small offline fault-injection checks; no real credentials/network/model/data."""
import copy
import hashlib
import io
import json
from pathlib import Path
import shutil
import sys
import tarfile
import tempfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'collab'))
import drive_api_storage_v1 as api
from pack_usable_images_api_v1 import Packer, write_member, validate_member

class Response:
    def __init__(self,status=200,data=b'',value=None,headers=None):
        self.status_code=status;self.data=data;self.value=value;self.headers=headers or {}
    def __enter__(self):return self
    def __exit__(self,*args):pass
    def raise_for_status(self):
        if self.status_code>=400:raise ConnectionError('synthetic HTTP error')
    def json(self):return self.value
    def iter_content(self,chunk_size):
        for n in range(0,len(self.data),chunk_size):yield self.data[n:n+chunk_size]

class DownloadSession:
    def __init__(self,raw,lose_once=False,wrong_range=False):
        self.raw=raw;self.lose_once=lose_once;self.wrong_range=wrong_range;self.starts=[]
        self.meta={'id':'original','name':'fixture.tar','size':str(len(raw)),'md5Checksum':hashlib.md5(raw).hexdigest(),'version':'1'}
    def get(self,url,**kw):
        if kw['params'].get('alt')!='media':return Response(value=self.meta)
        start=int(kw.get('headers',{}).get('Range','bytes=0-1').split('=')[1].split('-')[0]);self.starts.append(start)
        headers={'Content-Length':str(len(self.raw)-start),'Content-Range':f'bytes {start}-{len(self.raw)-1}/{len(self.raw)}'}
        if self.wrong_range:headers['Content-Range']='bytes 1-2/3'
        result=Response(206,data=self.raw[start:],headers=headers)
        if self.lose_once:
            self.lose_once=False
            def broken(chunk_size):
                yield self.raw[start:start+1024]
                raise ConnectionError('synthetic interrupted download')
            result.iter_content=broken
        return result

class UploadSession:
    def __init__(self,lose_once=False):self.data=bytearray();self.total=0;self.name=None;self.lose_once=lose_once;self.starts=[]
    def final(self):return {'id':'uploaded','name':self.name,'size':str(len(self.data)),'md5Checksum':hashlib.md5(self.data).hexdigest(),'version':'1'}
    def get(self,url,**kw):
        return Response(value={'files':[self.final()] if self.total and len(self.data)==self.total else []})
    def post(self,url,**kw):
        self.total=int(kw['headers']['X-Upload-Content-Length']);self.name=kw['json']['name']
        return Response(headers={'Location':'https://www.googleapis.com/upload/drive/v3/files?upload_id=private-fixture'})
    def put(self,url,**kw):
        content_range=kw['headers']['Content-Range']
        if content_range.startswith('bytes */'):
            if len(self.data)==self.total:return Response(value=self.final())
            return Response(308,headers={'Range':f'bytes=0-{len(self.data)-1}'} if self.data else {})
        start=int(content_range.split()[1].split('-')[0]);self.starts.append(start)
        assert start==len(self.data),'client skipped/repeated acknowledged bytes'
        if self.lose_once:
            self.lose_once=False;self.data.extend(kw['data'][:len(kw['data'])//2]);raise ConnectionError('lost response after partial server commit')
        self.data.extend(kw['data'])
        return Response(value=self.final()) if len(self.data)==self.total else Response(308,headers={'Range':f'bytes=0-{len(self.data)-1}'})

class MemoryStore:
    def __init__(self):self.files={};self.serial=0;self.fail_tar=False;self.fail_before_tar=False;self.downloads=0
    def add(self,parent,name,raw):
        self.serial+=1;meta={'id':str(self.serial),'name':name,'size':str(len(raw)),'md5Checksum':hashlib.md5(raw).hexdigest(),'version':'1'}
        self.files[meta['id']]=(parent,meta,bytes(raw));return copy.deepcopy(meta)
    def children(self,parent):return {m['name']:copy.deepcopy(m) for p,m,b in self.files.values() if p==parent}
    def meta(self,ident):return copy.deepcopy(self.files[ident][1])
    def read_small(self,meta,expected_sha=None,cap=32*1024**2):
        raw=self.files[meta['id']][2]
        if expected_sha:assert hashlib.sha256(raw).hexdigest()==expected_sha
        return raw
    def put_json(self,parent,name,value,existing=None):
        raw=(json.dumps(value,indent=2)+'\n').encode()
        if existing:
            meta=self.files[existing['id']][1];meta.update(size=str(len(raw)),md5Checksum=hashlib.md5(raw).hexdigest());self.files[meta['id']]=(parent,meta,raw);return copy.deepcopy(meta)
        return self.add(parent,name,raw)
    def upload_file(self,path,parent,name,state=None,save_state=None):
        raw=Path(path).read_bytes();old=self.children(parent).get(name)
        if old:
            assert self.read_small(old)==raw;return old
        if name.endswith('.tar') and self.fail_before_tar:
            self.fail_before_tar=False;raise ConnectionError('injected before archive commit')
        meta=self.add(parent,name,raw)
        if name.endswith('.tar') and self.fail_tar:
            self.fail_tar=False;raise ConnectionError('lost archive upload response')
        return meta
    def download(self,meta,path,expected_sha):
        self.downloads+=1;raw=self.read_small(meta,expected_sha);Path(path).parent.mkdir(parents=True,exist_ok=True);Path(path).write_bytes(raw);return Path(path)


def fixture(folder,store):
    raws={str(i):('synthetic-only-'+str(i)).encode()*7 for i in range(5)};rows=[]
    original=folder/'source.tar'
    with tarfile.open(original,'w',format=tarfile.PAX_FORMAT) as writer:
        for ident,raw in raws.items():
            row={'id':ident,'split':'train','clean_title':'synthetic fixture '+ident,'6_way_label':int(ident)%6,
                 'member':'images/'+ident+'.jpg','bytes':len(raw),'image_sha256':hashlib.sha256(raw).hexdigest()}
            write_member(writer,row,raw);rows.append(row)
    meta=store.add('source','source.tar',original.read_bytes());digest=api.hashes(original)[0]
    packed=folder/'new_packs/images_pack_fixture.tar';packed.parent.mkdir(exist_ok=True)
    enriched=[{**r,'input_shard':'source.tar','input_shard_sha256':digest,'input_member':r['member']} for r in rows]
    with tarfile.open(packed,'w',format=tarfile.PAX_FORMAT) as writer:
        for row in rows:write_member(writer,row,raws[row['id']])
    return packed,enriched,{r['id']:r for r in rows},{'source.tar':{'meta':meta,'receipt':{'sha256':digest}}}


def runner(store,folder,rows,sources,state=None):
    p=Packer(store,'fixture',folder);p.control_folder='control';p.packed_folder='packs';p.job='engineering_fixture';p.rows=rows;p.sources=sources
    p.state=state or {'schema':'fixture','phase':'running','archive_checks':{},'pending':None,'committed_images':0}
    p.state_meta=store.children('control').get('STATE.json');p.save();return p


def main():
    cases=[]
    with tempfile.TemporaryDirectory(dir=ROOT/'data') as tmp:
        work=Path(tmp);raw=b'fixture-bytes'*100000;digest=hashlib.sha256(raw).hexdigest()
        # An interrupted download must resume at its exact committed offset.
        session=DownloadSession(raw,True);path=api.DriveStore(session).download(session.meta,work/'download.tar',digest)
        assert path.read_bytes()==raw and session.starts==[0,1024];cases.append('interrupted_download_exact_offset')
        # Never accept the wrong HTTP range or silently overwrite conflicting scratch.
        try:api.DriveStore(DownloadSession(raw,wrong_range=True)).download(session.meta,work/'wrong.tar',digest);raise AssertionError('range accepted')
        except ValueError:cases.append('wrong_range_rejected')
        try:api.DriveStore(session).download(session.meta,work/'download.tar','0'*64);raise AssertionError('conflict overwritten')
        except ValueError:cases.append('conflicting_scratch_preserved')
        # Upload response loss after PARTIAL acceptance: use server Range, not sent bytes.
        original_chunk=api.CHUNK;api.CHUNK=256*1024
        try:
            for lost in [False,True]:
                upload=UploadSession(lost);states=[];meta=api.DriveStore(upload).upload_file(path,'private','fixture.tar',save_state=lambda s:states.append(copy.deepcopy(s)))
                assert bytes(upload.data)==raw and meta['md5Checksum']==hashlib.md5(raw).hexdigest() and states
                if lost:assert upload.starts[1]==128*1024
                cases.append('upload_partial_acceptance_recovery' if lost else 'upload_full_integrity')
        finally:api.CHUNK=original_chunk
        for header in ['bytes=1-8','bytes=0-999999999','garbage']:
            try:api.received_offset(Response(308,headers={'Range':header}),10);raise AssertionError('invalid range accepted')
            except ValueError:pass
        cases.append('bad_server_acknowledgements_rejected')
        for field,value in [('member','../escape.jpg'),('bytes',0)]:
            row={'id':'x','member':'images/x.jpg','bytes':3};row[field]=value
            try:validate_member(row);raise AssertionError('unsafe member accepted')
            except ValueError:pass
        cases.append('unsafe_members_rejected')
        for mode in ['normal','response_lost','scratch_lost_before_archive_upload','already_committed_receipt']:
            folder=work/mode;folder.mkdir();store=MemoryStore();pack,images,rows,sources=fixture(folder,store);p=runner(store,folder,rows,sources)
            store.fail_tar=mode in ('response_lost','already_committed_receipt');store.fail_before_tar=mode=='scratch_lost_before_archive_upload'
            try:p.commit(pack,images)
            except ConnectionError:
                state=json.loads(store.read_small(store.children('control')['STATE.json']))
                assert state['pending'],'durable pending image receipt was not saved first'
                recovery=folder/'recovered';recovery.mkdir();q=runner(store,recovery,rows,sources,state)
                if mode=='already_committed_receipt':
                    pending=state['pending'];receipt_raw=store.read_small(pending['receipt_meta']);receipt=json.loads(receipt_raw)
                    store.add('packs',receipt['archive'].replace('.tar','.receipt.json'),receipt_raw)
                    q.seen=set(rows);q.receipts=[{'archive':receipt['archive'],'bytes':receipt['bytes'],'sha256':receipt['sha256']}]
                q.complete_pending();p=q
                if mode=='response_lost':assert store.downloads==0,'completed archive unnecessarily rebuilt'
                if mode=='scratch_lost_before_archive_upload':assert store.downloads==1,'one bounded original TAR replay expected'
            assert len(p.seen)==5 and len(p.receipts)==1 and p.state['pending'] is None
            assert len([n for n in store.children('packs') if n.endswith('.tar')])==1
            cases.append(mode+'_exact_recovery')
    receipt={'state':'offline_api_transport_recovery_checks_passed','cases':cases,'count':len(cases),
             'real_network':False,'credentials_accessed':False,'scientific_training':False,
             'sources':[{'path':str(p.relative_to(ROOT)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
                        for p in [ROOT/'collab/drive_api_storage_v1.py',ROOT/'collab/pack_usable_images_api_v1.py']]}
    (ROOT/'results/api_transport_recovery_checks_20261025.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt))


if __name__=='__main__':main()
