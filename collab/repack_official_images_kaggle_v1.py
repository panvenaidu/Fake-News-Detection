"""Repack verified image bytes into <=47 transport archives for private Kaggle.

No dataset selection, model execution, downloads or authentication. Original
shards stay unchanged. CLI refuses incomplete original source/CRC evidence.
"""
import argparse, hashlib, importlib.util, io, json, math, os, re, shutil, tarfile, time, uuid
from pathlib import Path
spec=importlib.util.spec_from_file_location('prep',Path(__file__).with_name('prepare_official_images_drive_v1.py'))
prep=importlib.util.module_from_spec(spec);spec.loader.exec_module(prep)

def rows_for(root,expected):
    seen={};sources=[]
    for p in sorted((root/'shards').glob('*.receipt.json')):
        d=json.loads(p.read_text());a=root/'shards'/d['archive']
        if a.parent.resolve()!=(root/'shards').resolve() or not a.is_file() or a.stat().st_size!=d['bytes']:raise ValueError('Source shard path/size mismatch')
        for row in d['images']:
            ident=row['id']
            if ident in seen or ident not in expected or any(row.get(k)!=v for k,v in expected[ident].items()):raise ValueError('Source ID/TSV mismatch')
            seen[ident]=row
        sources.append((a,d))
    if set(seen)!=set(expected):raise ValueError('Incomplete source coverage; no reduced cohort')
    return sources,seen

def pack(source,output,expected,target_bytes=2*1024**3,max_seconds=3600,max_new_shards=47,check_scratch=True):
    source=Path(source);output=Path(output)
    if source.resolve()==output.resolve() or source.resolve().is_relative_to(output.resolve()):raise ValueError('Separate derived output required')
    output.mkdir(parents=True,exist_ok=True);dest=output/'shards';dest.mkdir(exist_ok=True)
    sources,source_rows=rows_for(source,expected);seen={};proof=[]
    for p in dest.glob('*.receipt.json'):
        d=json.loads(p.read_text());a=dest/d['archive']
        if a.parent.resolve()!=dest.resolve() or not a.is_file() or prep.sha(a)!=d['sha256']:raise ValueError('Packed generation corrupt')
        for row in d['images']:
            ident=row['id']
            if ident in seen or ident not in source_rows or row['image_sha256']!=source_rows[ident]['image_sha256'] or any(row.get(k)!=v for k,v in expected[ident].items()):raise ValueError('Packed/source image mismatch')
            seen[ident]=row['image_sha256']
        proof.append({'archive':a.name,'sha256':d['sha256'],'bytes':d['bytes']})
    writer=None;path=None;images=[];written=0;new=0;start=time.monotonic()
    def commit():
        nonlocal writer,images,written,new
        if writer is None:return
        writer.close();writer=None
        with path.open('rb') as f:os.fsync(f.fileno())
        d={'utc':prep.now(),'archive':path.name,'bytes':path.stat().st_size,'sha256':prep.sha(path),'images':images,'role':'Lossless private Kaggle transport repack; original source shards retained'}
        prep.record(path.with_suffix('.receipt.json'),d)
        for row in images:seen[row['id']]=row['image_sha256']
        proof.append({'archive':path.name,'sha256':d['sha256'],'bytes':d['bytes']});images=[];written=0;new+=1
        print(json.dumps({'utc':prep.now(),'state':'packed_shard_committed','images_committed':len(seen),'required':len(expected),'packed_shards':len(proof)}),flush=True)
    try:
        for archive,d in sources:
            if all(row['id'] in seen for row in d['images']):continue
            if prep.sha(archive)!=d['sha256']:raise ValueError('Source archive hash mismatch')
            with tarfile.open(archive,'r:') as tar:
                for row in d['images']:
                    if row['id'] in seen:continue
                    if time.monotonic()-start>=max_seconds or (check_scratch and shutil.disk_usage('/content').free<8*1024**3):
                        commit();return {'state':'bounded_pack_checkpoint','images_committed':len(seen),'required':len(expected),'complete':False}
                    member=row['member']
                    if member!='images/'+Path(member).name or Path(member).stem!=row['id']:raise ValueError('Unsafe source member')
                    raw=tar.extractfile(member).read()
                    if len(raw)!=row['bytes'] or hashlib.sha256(raw).hexdigest()!=row['image_sha256']:raise ValueError('Source image bytes mismatch')
                    if writer is not None and written+len(raw)+1024>target_bytes:
                        commit()
                        if new>=max_new_shards:return {'state':'bounded_pack_checkpoint','images_committed':len(seen),'required':len(expected),'complete':False}
                    if writer is None:
                        path=dest/('images_pack_'+uuid.uuid4().hex+'.tar');writer=tarfile.open(path,'w')
                    info=tarfile.TarInfo(member);info.size=len(raw);info.mtime=0;writer.addfile(info,io.BytesIO(raw))
                    images.append({**row,'input_shard':archive.name,'input_shard_sha256':d['sha256'],'input_member':member});written+=len(raw)+1024
        commit()
        if len(proof)>47:raise ValueError('Transport top-level archive budget exceeded; preserve outputs and revise packaging')
        if set(seen)!=set(expected):raise ValueError('Packed cohort incomplete')
        result={'utc':prep.now(),'state':'lossless_transport_pack_complete','complete':True,'images_committed':len(seen),'packed_shards':len(proof),'artifacts':proof,'image_gate_passed':False,'scope':'Transport copy only; full target runtime decode/hash audit required','source_retained':True}
        prep.record(output/('repack_'+uuid.uuid4().hex+'.json'),result);return result
    finally:
        if writer is not None:writer.close()

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--source-root',type=Path,required=True);ap.add_argument('--output-root',type=Path,required=True);ap.add_argument('--extraction-report',type=Path,required=True);ap.add_argument('--max-seconds',type=int,default=3600);a=ap.parse_args()
    complete=json.loads(a.extraction_report.read_text())
    if complete.get('source_id')!=prep.SOURCE_ID or not re.fullmatch('[0-9a-f]{64}',complete.get('compressed_archive_sha256','')) or not complete.get('image_gate_passed') or complete.get('usable')!=682661 or complete.get('required')!=682661 or complete.get('compressed_archive_bytes')!=113623359224 or not complete.get('source_crc_consumed') or complete.get('missing_ids') or complete.get('decode_failures'):raise ValueError('Complete original source CRC/coverage proof required')
    expected=prep.expected_rows(a.source_root);assert len(expected)==682661
    sources,rows=rows_for(a.source_root,expected)
    # Round up conservatively; reserve3 top-level archives/files for metadata.
    predicted=sum(row['bytes']+1024 for row in rows.values())
    target=max(2*1024**3,math.ceil(predicted/44/(64*1024**2))*(64*1024**2))
    if not a.output_root.resolve().is_relative_to(a.source_root.resolve()):raise ValueError('Derived pack must remain inside approved source root')
    a.output_root.mkdir(parents=True,exist_ok=True)
    for _,name,_,digest,_ in prep.TSVS:
        output=a.output_root/name
        if output.exists():assert prep.sha(output)==digest
        else:shutil.copyfile(a.source_root/name,output);assert prep.sha(output)==digest
    report=a.output_root/a.extraction_report.name
    if report.exists():assert prep.sha(report)==prep.sha(a.extraction_report)
    else:shutil.copyfile(a.extraction_report,report)
    print(json.dumps(pack(a.source_root,a.output_root,expected,target_bytes=target,max_seconds=a.max_seconds)),flush=True)
if __name__=='__main__':main()
