"""Independently read back the saved Kaggle gate, without image inference."""
import argparse
from collections import Counter
import datetime
import hashlib
import json
from pathlib import Path
import sqlite3
from usable_cohort_v2 import load_cohort, registration, REGISTRATION, COHORT, REGISTRATION_SHA, COUNTS


def sha(path):
    digest=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(4*1024**2),b''):digest.update(block)
    return digest.hexdigest()


def verify(root, gate):
    root,gate=Path(root),Path(gate)
    receipt=gate/'packed_runtime_coverage.json'; index=gate/'packed_image_index.sqlite'
    r=json.loads(receipt.read_text())
    if (r.get('image_gate_passed') is not True or r.get('runtime_image_bytes_verified') is not True
        or r.get('cohort_id')!=COHORT or r.get('cohort_registration_sha256')!=REGISTRATION_SHA
        or r.get('input_layout')!='kaggle-packed-bin' or r.get('dataset_version')!=1
        or r.get('usable')!=682170 or r.get('required')!=682170 or r.get('split_counts')!=COUNTS):
        raise ValueError('Wrong saved gate protocol')
    if sha(index)!=r['packed_index_sha256']:raise ValueError('Saved index checksum mismatch')
    for filename,key in [('packed_image_io_v3.py','packed_adapter_sha256'),('verify_packed_usable_input_v3.py','gate_source_sha256')]:
        p=gate/'gate_source/scripts'/filename
        if sha(p)!=r[key] or sha(p)!=sha(root/'scripts'/filename):raise ValueError('Saved gate source mismatch')
    reg=registration(root/'results'/REGISTRATION)
    extraction=root/'results'/reg['extraction_report_file']
    if not extraction.is_file():extraction=root/'data/official_paired_v1/source_recovery'/reg['extraction_report_file']
    expected,_=load_cohort(root/'data/official_multimodal_v2',root/'results'/REGISTRATION,
                           extraction,root/'results'/reg['approval_file'])
    seen=set();counts=Counter();classes=Counter();archive_counts=Counter();total=0
    with sqlite3.connect('file:'+str(index.resolve())+'?mode=ro&immutable=1',uri=True) as db:
        if db.execute('PRAGMA integrity_check').fetchone()[0]!='ok':raise ValueError('Corrupt saved index')
        proofs={name:(size,digest,n) for name,size,digest,n in db.execute('SELECT name,bytes,sha256,images FROM archives')}
        if proofs!={x['file']:(x['bytes'],x['sha256'],x['images']) for x in r['shards']}:raise ValueError('Archive proof mismatch')
        for ident,archive,offset,size,digest in db.execute('SELECT id,archive,offset,size,sha256 FROM images'):
            if ident not in expected or ident in seen or offset<0 or size<=0 or len(digest)!=64:raise ValueError('Invalid index row')
            original=archive[:-4]+'.tar' if archive.endswith('.bin') else ''
            if original not in proofs or offset+size>proofs[original][0]:raise ValueError('Invalid archive range')
            int(digest,16);seen.add(ident);total+=size;archive_counts[original]+=1
            row=expected[ident];counts[row['split']]+=1;classes[(row['split'],row['6_way_label'])]+=1
    if seen!=set(expected) or dict(counts)!=COUNTS or total!=r['image_bytes']:raise ValueError('Saved cohort membership mismatch')
    if dict(archive_counts)!={k:v[2] for k,v in proofs.items()}:raise ValueError('Saved archive image count mismatch')
    return {'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'passed_independent_saved_gate_readback',
            'usable_images':len(seen),'split_counts':dict(counts),'archives':len(proofs),'image_bytes':total,
            'index_sha256':sha(index),'receipt_sha256':sha(receipt),'cohort_registration_sha256':REGISTRATION_SHA,
            'saved_gate':str(gate.resolve()),'scientific_training':False,'test_inference':False,
            'note':'All saved index IDs match approved official TSV membership; every image byte/decode was checked by the saved cloud gate. This readback does not repeat image decoding.'}


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--gate',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    value=verify(a.root,a.gate);a.output.write_text(json.dumps(value,indent=2)+'\n');print(json.dumps(value))
