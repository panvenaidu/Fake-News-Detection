"""Lossless, recovery-safe API packing of the exact approved faculty cohort.

CPU cloud only. Reuses all verified committed packs. No DriveFS, original image
extraction, exclusions, model execution or final test. Private STATE contains
resumable session URIs and must NEVER enter Git or printed/public receipts.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import fcntl
import gc
import hashlib
import io
import json
import math
import os
from pathlib import Path
import shutil
import sys
import tarfile
import time
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from usable_cohort_v2 import load_cohort, REGISTRATION, REGISTRATION_SHA, COHORT
from drive_api_storage_v1 import DriveStore, hashes, atomic_json, safe_error

INDEX_SHA = '291a2c5b27aa39f1b1b16b3726655609927a08cee03a34e35d9fe7e47670a87a'
SOURCE_FOLDER = '1tY3NP96gcuHQwGUponsxRlqLD-sfXo9U'
LEGACY_TERMINAL_JOB = 'CPU_USABLE_TRANSPORT_4239db2e543d4215bfe7f48f8517c0ae'
SCHEMA = 'UROP_API_LOSSLESS_PACK_V1'


def now(): return datetime.now(timezone.utc).isoformat()


def emit(**value):
    print(json.dumps({'utc':now(), **value}, allow_nan=False), flush=True)


def validate_member(row):
    member=row['member']
    if member!='images/'+Path(member).name or Path(member).stem!=row['id'] or not isinstance(row['bytes'],int) or row['bytes']<=0:
        raise ValueError('Unsafe or invalid original image member')
    return member


def check_row(row, expected):
    if any(row.get(k)!=expected[k] for k in ['id','split','clean_title','6_way_label']):
        raise ValueError('Original TSV title/label/split join mismatch')
    validate_member(row)


def write_member(writer, row, raw):
    member=validate_member(row)
    if len(raw)!=row['bytes'] or hashlib.sha256(raw).hexdigest()!=row['image_sha256']:
        raise ValueError('Original image bytes/hash mismatch')
    info=tarfile.TarInfo(member);info.size=len(raw);info.mtime=0
    writer.addfile(info,io.BytesIO(raw))


class Packer:
    def __init__(self, store, index_id, scratch, resume_job=None):
        self.store=store;self.scratch=Path(scratch);self.scratch.mkdir(parents=True,exist_ok=True)
        self.index_id=index_id;self.resume_job=resume_job;self.seen=set();self.receipts=[]
        self.state=None;self.state_meta=None;self.stage='initializing';self.new_packs=0

    def save(self):
        self.state['updated_utc']=now()
        self.state_meta=self.store.put_json(self.control_folder,'STATE.json',self.state,self.state_meta)
        atomic_json(self.scratch/'private_state.json',self.state)

    def source_file(self, root_files, name, expected_sha):
        if name not in root_files:raise ValueError('Required original metadata absent: '+name)
        path=self.scratch/'original_metadata'/name
        return self.store.download(root_files[name],path,expected_sha)

    def initialize(self):
        self.stage='verified_input_metadata'
        index_raw=self.store.read_small(self.store.meta(self.index_id),INDEX_SHA,cap=1024**2)
        self.index=json.loads(index_raw)
        if self.index['state']!='api_source_metadata_inventory_passed' or self.index['images']!=682170 or self.index['receipt_files']!=150:
            raise ValueError('Pinned source metadata index differs')
        parents=self.store.meta(SOURCE_FOLDER)['parents']
        if len(parents)!=1:raise ValueError('Ambiguous original source parent')
        self.root=parents[0];root_files=self.store.children(self.root)
        legacy=root_files.get('USABLE_V2_TRANSPORT_JOB.json')
        if legacy and json.loads(self.store.read_small(legacy))['job_id']!=LEGACY_TERMINAL_JOB:
            raise ValueError('Unexpected legacy job: inspect authoritative live state')
        # Preserve old failed job guard. Only this derived control folder is mutable.
        self.control_folder=self.store.folder(self.root,'api_transport_v1',create=True)
        controls=self.store.children(self.control_folder);self.state_meta=controls.get('STATE.json')
        old=json.loads(self.store.read_small(self.state_meta)) if self.state_meta else None
        if old and (old.get('schema')!=SCHEMA or old.get('cohort')!=COHORT or old.get('index_sha256')!=INDEX_SHA):
            raise ValueError('Private API control provenance differs')
        if old and old.get('phase')=='running' and self.resume_job!=old.get('job_id'):
            raise ValueError('API job may be live; explicit observed-terminal resume required')
        if old and self.resume_job and self.resume_job!=old.get('job_id'):
            raise ValueError('Wrong predecessor job identity')
        self.job='CPU_API_PACK_'+uuid.uuid4().hex
        self.state={'schema':SCHEMA,'cohort':COHORT,'index_sha256':INDEX_SHA,'phase':'running',
                    'job_id':self.job,'prior_job':old.get('job_id') if old else None,'pid':os.getpid(),
                    'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
                    'archive_checks':old.get('archive_checks',{}) if old else {},
                    'pending':old.get('pending') if old else None,'committed_images':old.get('committed_images',319820) if old else 319820,
                    'packed_shards':old.get('packed_shards',18) if old else 18,
                    'training':False,'test_inference':False,'source_originals_unchanged':True}
        self.save()
        self.store.put_json(self.control_folder,self.job+'_launch.json',{
            k:v for k,v in self.state.items() if k not in ('archive_checks','pending')})
        reg_path=self.source_file(root_files,REGISTRATION,REGISTRATION_SHA)
        reg=json.loads(reg_path.read_text())
        approval=self.source_file(root_files,reg['approval_file'],reg['approval_sha256'])
        report=self.source_file(root_files,reg['extraction_report_file'],reg['extraction_report_sha256'])
        for item in reg['original_files']:self.source_file(root_files,item['filename'],item['sha256'])
        expected,self.reg=load_cohort(reg_path.parent,reg_path,report,approval)
        self.rows={};self.sources={}
        for n,item in enumerate(self.index['artifacts'],1):
            meta=self.store.meta(item['receipt']['id'])
            if any(str(meta[k])!=str(item['receipt'][k]) for k in ('id','name','size','md5Checksum')):
                raise ValueError('Pinned original receipt changed')
            cached=self.scratch/'source_receipts'/meta['name'];cached.parent.mkdir(exist_ok=True)
            if cached.exists():
                raw=cached.read_bytes()
                if hashlib.sha256(raw).hexdigest()!=item['receipt_sha256']:raise ValueError('Preserve conflicting receipt cache')
            else:
                raw=self.store.read_small(meta,item['receipt_sha256']);cached.write_bytes(raw)
            receipt=json.loads(raw);archive=self.store.meta(item['archive']['id'])
            if any(str(archive[k])!=str(item['archive'][k]) for k in ('id','name','size','md5Checksum')):
                raise ValueError('Pinned original archive metadata changed')
            if receipt['archive']!=archive['name'] or receipt['sha256']!=item['archive_sha256'] or receipt['bytes']!=int(archive['size']):
                raise ValueError('Original receipt/archive binding mismatch')
            for row in receipt['images']:
                ident=row['id']
                if ident in self.rows or ident not in expected:raise ValueError('Duplicate/unapproved original ID')
                check_row(row,expected[ident]);self.rows[ident]=row
            self.sources[archive['name']]={'meta':archive,'receipt':receipt}
            if n%30==0:emit(state='api_source_join_verified',receipts=n,images=len(self.rows))
        if set(self.rows)!=set(expected):raise ValueError('Exact approved source membership incomplete')
        del expected;gc.collect()
        estimated=sum(row['bytes']+1024 for row in self.rows.values())
        self.target=max(2*1024**3,math.ceil(estimated/44/(64*1024**2))*(64*1024**2))
        self.packed_root=self.store.folder(self.root,'kaggle_packed_usable_v2')
        self.packed_folder=self.store.folder(self.packed_root,'shards')
        self.packed_files=self.store.children(self.packed_folder)
        emit(state='api_original_TSV_and_source_metadata_joins_passed',images=len(self.rows),target_pack_bytes=self.target,
             source_receipts=len(self.sources),training=False)

    def audit_packs(self,audit_seconds):
        self.stage='audit_committed_packs';started=time.monotonic()
        files=sorted((v for k,v in self.packed_files.items() if k.endswith('.receipt.json')),key=lambda x:x['name'])
        if len(files)<18:raise ValueError('Previously durable18pack receipts missing')
        for n,meta in enumerate(files,1):
            receipt=json.loads(self.store.read_small(meta));name=receipt['archive'];archive=self.store.meta(self.packed_files[name]['id'])
            if meta['name']!=name.replace('.tar','.receipt.json') or int(archive['size'])!=receipt['bytes']:
                raise ValueError('Committed pack receipt/archive mismatch')
            for row in receipt['images']:
                ident=row['id']
                if ident in self.seen or ident not in self.rows:raise ValueError('Duplicate/unapproved committed pack ID')
                source=self.rows[ident];check_row(row,source)
                if row['image_sha256']!=source['image_sha256'] or row['bytes']!=source['bytes']:
                    raise ValueError('Committed image differs from original source')
                self.seen.add(ident)
            cached=self.state['archive_checks'].get(archive['id'])
            unchanged=(cached and cached['sha256']==receipt['sha256'] and cached['bytes']==int(archive['size'])
                       and cached['md5Checksum']==archive['md5Checksum'] and cached.get('version') is not None
                       and cached.get('version')==archive.get('version'))
            if not unchanged:
                checked=self.store.verify_remote(archive,receipt['sha256'])
                self.state['archive_checks'][archive['id']]=checked;self.save()
            self.receipts.append({'archive':archive['name'],'sha256':receipt['sha256'],'bytes':receipt['bytes']})
            emit(state='api_prior_pack_verified',packs_checked=n,total_packs=len(files),images=len(self.seen),cached_unchanged=bool(unchanged))
            if time.monotonic()-started>audit_seconds and n<len(files):
                return False
        if len(self.seen)<319820 or len(self.receipts)>47:raise ValueError('Committed coverage/budget mismatch')
        self.state['committed_images']=len(self.seen);self.state['packed_shards']=len(self.receipts);self.save()
        return True

    def source_path(self,name):
        item=self.sources[name];path=self.scratch/'source_archives'/name
        if shutil.disk_usage(self.scratch).free<8*1024**3+int(item['meta']['size']):
            raise ValueError('Insufficient cloud scratch; preserve current checkpoint')
        self.stage='download_verified_source_archive'
        return self.store.download(item['meta'],path,item['receipt']['sha256'])

    def rebuild_pending(self,pending,receipt,path):
        """At most one uncommitted transport pack is replayed from durable originals."""
        local=None;current=None
        path.parent.mkdir(parents=True,exist_ok=True)
        with tarfile.open(path,'x',format=tarfile.PAX_FORMAT) as writer:
            for row in receipt['images']:
                name=row['input_shard']
                if name!=current:
                    if local:local.close()
                    source=self.source_path(name);local=tarfile.open(source,'r:');current=name
                original=self.rows.get(row['id'])
                if original is None:raise ValueError('Pending ID not approved')
                check_row(row,original)
                if row['image_sha256']!=original['image_sha256'] or row['input_shard_sha256']!=self.sources[name]['receipt']['sha256']:
                    raise ValueError('Pending image provenance differs')
                member=local.getmember(validate_member(row))
                if not member.isfile() or member.size!=row['bytes']:raise ValueError('Pending source member mismatch')
                with local.extractfile(member) as stream:raw=stream.read()
                write_member(writer,row,raw)
        if local:local.close()
        if path.stat().st_size!=pending['archive_bytes'] or hashes(path)!=(pending['archive_sha256'],pending['archive_md5']):
            raise ValueError('Reconstructed pending pack differs; do not publish')

    def complete_pending(self):
        pending=self.state.get('pending')
        if not pending:return
        self.stage='recover_or_publish_pending_pack'
        receipt_raw=self.store.read_small(pending['receipt_meta'],pending['receipt_sha256'])
        receipt=json.loads(receipt_raw);name=receipt['archive'];path=self.scratch/'new_packs'/name
        if (name!=pending['archive'] or receipt['sha256']!=pending['archive_sha256']
                or receipt['bytes']!=pending['archive_bytes'] or len({r['id'] for r in receipt['images']})!=len(receipt['images'])):
            raise ValueError('Pending receipt/archive transaction differs')
        remote=self.store.children(self.packed_folder).get(name)
        if remote:
            if int(remote.get('size',-1))!=pending['archive_bytes'] or remote.get('md5Checksum')!=pending['archive_md5']:
                raise ValueError('Preserve conflicting pending remote pack')
        else:
            if not path.exists():self.rebuild_pending(pending,receipt,path)
            if hashes(path)!=(pending['archive_sha256'],pending['archive_md5']):raise ValueError('Pending local pack corrupted')
            def save_upload(value):
                self.state['pending']['archive_upload']=value;self.save()
            remote=self.store.upload_file(path,self.packed_folder,name,pending.get('archive_upload'),save_upload)
        receipt_path=self.scratch/'new_packs'/name.replace('.tar','.receipt.json')
        receipt_path.parent.mkdir(parents=True,exist_ok=True);receipt_path.write_bytes(receipt_raw)
        def save_receipt_upload(value):
            self.state['pending']['receipt_upload']=value;self.save()
        receipt_meta=self.store.upload_file(receipt_path,self.packed_folder,receipt_path.name,
                                            pending.get('receipt_upload'),save_receipt_upload)
        if self.store.read_small(receipt_meta,pending['receipt_sha256'])!=receipt_raw:
            raise ValueError('Committed image receipt durable readback mismatch')
        ids={row['id'] for row in receipt['images']};overlap=ids&self.seen
        if overlap and overlap!=ids:raise ValueError('Partially overlapping pending pack')
        for row in receipt['images']:
            original=self.rows.get(row['id'])
            if original is None:raise ValueError('Pending receipt ID not approved')
            check_row(row,original)
            if row['image_sha256']!=original['image_sha256']:raise ValueError('Pending receipt hash differs from original')
        if not overlap:
            self.seen.update(ids);self.receipts.append({'archive':name,'sha256':receipt['sha256'],'bytes':receipt['bytes']})
        remote=self.store.meta(remote['id'])
        self.state['archive_checks'][remote['id']]={'id':remote['id'],'name':name,'bytes':receipt['bytes'],
             'sha256':receipt['sha256'],'md5Checksum':remote['md5Checksum'],'version':remote.get('version')}
        self.state['pending']=None;self.state['committed_images']=len(self.seen);self.state['packed_shards']=len(self.receipts);self.save()
        self.store.put_json(self.control_folder,name.replace('.tar','_committed.json'),{
            'utc':now(),'state':'api_pack_committed','job_id':self.job,'archive':remote,'receipt':receipt_meta,
            'archive_sha256':receipt['sha256'],'images_committed':len(self.seen),'packed_shards':len(self.receipts),
            'archive_durability':'Remote size/MD5 equals full local SHA+MD5 mapping; receipt byte readback verified; target-runtime full SHA/decode still mandatory',
            'training':False,'test_inference':False})
        self.new_packs+=1
        emit(state='api_pack_committed',images_committed=len(self.seen),required=682170,packed_shards=len(self.receipts),new_packs=self.new_packs)
        # Remove ONLY our derived CPU scratch after verified durable archive+receipt.
        if path.exists():path.unlink()

    def commit(self,path,images):
        if not images:return
        self.stage='commit_original_byte_pack'
        with path.open('rb') as stream:os.fsync(stream.fileno())
        sha,md5=hashes(path)
        receipt={'utc':now(),'archive':path.name,'bytes':path.stat().st_size,'sha256':sha,'images':images,
                 'role':'Lossless private Kaggle transport repack via bounded Drive API; original source shards retained'}
        receipt_path=path.with_suffix('.receipt.json');atomic_json(receipt_path,receipt)
        pending_name=path.stem+'_pending.receipt.json'
        # Make image membership/hash provenance durable BEFORE the large archive upload.
        pending_meta=self.store.upload_file(receipt_path,self.control_folder,pending_name)
        receipt_sha=hashes(receipt_path)[0]
        self.store.read_small(pending_meta,receipt_sha)
        self.state['pending']={'archive':path.name,'archive_bytes':receipt['bytes'],'archive_sha256':sha,'archive_md5':md5,
                              'receipt_meta':pending_meta,'receipt_sha256':receipt_sha,'format':'Python tarfile.PAX_FORMAT; TarInfo images/id,mtime0'}
        self.save();self.complete_pending()

    def pack(self,seconds,max_new_packs):
        self.stage='pack_original_bytes';started=time.monotonic();writer=None;path=None;images=[];written=0
        self.complete_pending()
        try:
            for name,item in self.sources.items():
                remaining=[row for row in item['receipt']['images'] if row['id'] not in self.seen]
                if not remaining:continue
                if time.monotonic()-started>=seconds or self.new_packs>=max_new_packs:break
                source=self.source_path(name)
                with tarfile.open(source,'r:') as archive:
                    members=[m for m in archive.getmembers() if m.isfile()]
                    if len(members)!=len(item['receipt']['images']) or len({m.name for m in members})!=len(members):
                        raise ValueError('Original TAR file member count/duplicates differ')
                    for row in remaining:
                        if time.monotonic()-started>=seconds:break
                        member=archive.getmember(validate_member(row))
                        if not member.isfile() or member.size!=row['bytes']:raise ValueError('Original image TAR member mismatch')
                        if writer is not None and written+row['bytes']+1024>self.target:
                            writer.close();writer=None;self.commit(path,images);images=[];written=0
                            if self.new_packs>=max_new_packs:break
                        if writer is None:
                            if len(self.receipts)>=47:raise ValueError('Transport archive budget47 reached; preserve all data')
                            path=self.scratch/'new_packs'/('images_pack_'+uuid.uuid4().hex+'.tar');path.parent.mkdir(exist_ok=True)
                            writer=tarfile.open(path,'x',format=tarfile.PAX_FORMAT)
                        with archive.extractfile(member) as stream:raw=stream.read()
                        write_member(writer,row,raw)
                        images.append({**row,'input_shard':name,'input_shard_sha256':item['receipt']['sha256'],'input_member':row['member']})
                        written+=len(raw)+1024
                # This cloud cache is derived and reproducible; original source is never deleted.
                source.unlink()
                if time.monotonic()-started>=seconds or self.new_packs>=max_new_packs:break
            if writer is not None:
                writer.close();writer=None;self.commit(path,images)
        finally:
            if writer is not None:writer.close()
        return len(self.seen)==682170

    def run(self,pack_seconds=3600,audit_seconds=1800,max_new_packs=47):
        started=time.monotonic()
        try:
            self.initialize()
            audited=self.audit_packs(audit_seconds)
            complete=self.pack(pack_seconds,max_new_packs) if audited else False
            self.state['phase']='complete' if complete else 'bounded_checkpoint';self.state['terminal_utc']=now();self.save()
            result={'utc':now(),'state':'api_transport_terminal','job_id':self.job,'phase':self.state['phase'],
                    'images_committed':self.state['committed_images'],'required':682170,
                    'packed_shards':self.state.get('packed_shards',0),'new_packs':self.new_packs,
                    'prior_pack_audit_complete':audited,'complete':complete,'seconds':time.monotonic()-started,
                    'source_originals_unchanged':True,'runtime_image_gate_passed':False,'training':False,'test_inference':False}
            self.store.put_json(self.control_folder,self.job+'_terminal.json',result);emit(**result)
            return result
        except Exception as error:
            failure={'utc':now(),'state':'api_transport_failed','job_id':getattr(self,'job',None),'stage':self.stage,
                     'error_type':type(error).__name__,'error':safe_error(error),'training':False,'test_inference':False}
            atomic_json(self.scratch/'last_failure.json',failure);emit(**failure)
            if self.state is not None:
                self.state['phase']='failed';self.state['last_failure']=failure
                try:self.save()
                except Exception as saving_error:emit(state='api_failure_control_write_unverified',error_type=type(saving_error).__name__)
            raise


def main():
    p=argparse.ArgumentParser();p.add_argument('--index-id',required=True);p.add_argument('--scratch',type=Path,default=Path('/content/urop_api_transport_v1'))
    p.add_argument('--pack-seconds',type=int,default=3600);p.add_argument('--audit-seconds',type=int,default=1800)
    p.add_argument('--max-new-packs',type=int,default=47);p.add_argument('--resume-job')
    args=p.parse_args()
    if not 0<args.pack_seconds<=3600 or not 0<args.audit_seconds<=1800 or not 0<args.max_new_packs<=47:
        raise ValueError('Bounded job settings exceed registered preparation limits')
    if not str(args.scratch.resolve()).startswith('/content/') or not Path('/var/colab/hostname').exists():
        raise ValueError('Cloud Colab CPU scratch required; never run large transport on laptop')
    import google.auth
    from google.auth.transport.requests import AuthorizedSession
    args.scratch.mkdir(parents=True,exist_ok=True)
    with (args.scratch/'execution.lock').open('a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        credentials,_=google.auth.default()
        with AuthorizedSession(credentials) as session:
            last=[0]
            def progress(**value):
                if time.monotonic()-last[0]>=30:
                    emit(**value);last[0]=time.monotonic()
            runner=Packer(DriveStore(session,progress),args.index_id,args.scratch,args.resume_job)
            runner.run(args.pack_seconds,args.audit_seconds,args.max_new_packs)


if __name__=='__main__':main()
