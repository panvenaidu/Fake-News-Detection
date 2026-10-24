"""Bounded metadata-only inventory via approved Drive API; no DriveFS or training.

Original receipts/TARs remain untouched. Receipt byte caches stay on cloud CPU
scratch. Only a new small derived index is written to the same private folder.
Not an image hash/decode gate, TSV title join, packing job or scientific result.
"""
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter
import hashlib, json, re, time

FOLDER = '1tY3NP96gcuHQwGUponsxRlqLD-sfXo9U'
COUNTS = {'train': 563601, 'validation': 59299, 'test': 59270}
CLASSES = {'train': {'0':222081,'1':33480,'2':107221,'3':11784,'4':167459,'5':21576},
 'validation': {'0':23320,'1':3520,'2':11277,'3':1238,'4':17768,'5':2176},
 'test': {'0':23507,'1':3514,'2':11297,'3':1224,'4':17423,'5':2305}}
API = 'https://www.googleapis.com/drive/v3/files'


def read_receipt(session, meta):
    size = int(meta['size'])
    if not 0 < size < 5_000_000 or not re.fullmatch(r'images_[a-f0-9]+\.receipt\.json',meta['name']):
        raise ValueError('Unexpected receipt size/name')
    data = bytearray()
    with session.get(API+'/'+meta['id'],params={'alt':'media'},headers={'Accept-Encoding':'identity'},
                     stream=True,timeout=(15,20)) as response:
        response.raise_for_status()
        if response.status_code != 200 or int(response.headers.get('Content-Length',-1)) != size:
            raise ValueError('Receipt response length/status mismatch')
        for chunk in response.iter_content(256*1024):
            if len(data)+len(chunk)>size: raise ValueError('Receipt exceeds pinned metadata size')
            data.extend(chunk)
    if len(data)!=size or hashlib.md5(data).hexdigest()!=meta['md5Checksum']:
        raise ValueError('Receipt differs from current original Drive bytes')
    return bytes(data)


def run(session):
    started=time.monotonic(); stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    cache=Path('/content/urop_api_receipts_'+stamp);cache.mkdir(exist_ok=False)
    items=[];token=None
    while True:
        with session.get(API,params={'q':f"'{FOLDER}' in parents and trashed = false",'pageSize':1000,
                         'fields':'nextPageToken,files(id,name,size,md5Checksum,mimeType)',
                         **({'pageToken':token} if token else {})},timeout=20) as response:
            response.raise_for_status();page=response.json()
        items.extend(page['files']);token=page.get('nextPageToken')
        if not token:break
        if time.monotonic()-started>240:raise TimeoutError('240 second metadata bound')
    by_name={x['name']:x for x in items}
    if len(by_name)!=len(items):raise ValueError('Duplicate original Drive filenames')
    receipts=sorted([x for x in items if x['name'].endswith('.receipt.json')],key=lambda x:x['name'])
    if len(receipts)!=150:raise ValueError('Expected exactly150 original source receipts')
    seen=set();counts=Counter();classes={s:Counter() for s in COUNTS};proof=[]
    for n,meta in enumerate(receipts,1):
        if time.monotonic()-started>240:raise TimeoutError('240 second metadata bound')
        path=cache/meta['name'];raw=read_receipt(session,meta);value=json.loads(raw)
        archive=by_name[value['archive']]
        if value['archive']!=meta['name'].replace('.receipt.json','.tar') or int(archive['size'])!=value['bytes']:
            raise ValueError('Original archive name/size mismatch')
        if not re.fullmatch('[a-f0-9]{64}',value['sha256']):raise ValueError('Invalid archive digest')
        for row in value['images']:
            ident=row['id'];split=row['split'];label=int(row['6_way_label'])
            if ident in seen or split not in COUNTS or label not in range(6):raise ValueError('Duplicate/invalid original membership')
            if not row['clean_title'].strip() or not re.fullmatch('[a-f0-9]{64}',row['image_sha256']):raise ValueError('Invalid original receipt row')
            seen.add(ident);counts[split]+=1;classes[split][str(label)]+=1
        path.write_bytes(raw)
        proof.append({'receipt':meta,'receipt_sha256':hashlib.sha256(raw).hexdigest(),
                      'archive':archive,'archive_sha256':value['sha256'],'images':len(value['images'])})
        if n%20==0 or n==150:print(json.dumps({'state':'api_metadata_inventory_progress','receipts':n,'images':len(seen),'seconds':time.monotonic()-started}),flush=True)
    if dict(counts)!=COUNTS or {s:dict(c) for s,c in classes.items()}!=CLASSES:raise ValueError('Approved cohort counts/classes mismatch')
    index={'utc':datetime.now(timezone.utc).isoformat(),'state':'api_source_metadata_inventory_passed',
           'cohort_id':'FACULTY-6W-USABLE-682170-v1','receipt_files':150,'images':len(seen),
           'split_counts':dict(counts),'class_counts':{s:dict(c) for s,c in classes.items()},
           'artifacts':proof,'cloud_scratch_cache':str(cache),'image_bytes_verified_this_run':False,
           'original_TSV_join_this_run':False,'packing':False,'training':False,'test_inference':False}
    raw=json.dumps(index,indent=2).encode();(cache/'index.json').write_bytes(raw)
    with session.get(API+'/'+FOLDER,params={'fields':'parents'},timeout=20) as response:
        response.raise_for_status();parents=response.json()['parents']
    if len(parents)!=1:raise ValueError('Ambiguous approved source root')
    name='API_SOURCE_METADATA_INDEX_'+stamp+'.json'
    boundary='urop_private_metadata_index_v1'
    metadata=json.dumps({'name':name,'parents':parents,'mimeType':'application/json'}).encode()
    body=(b'--'+boundary.encode()+b'\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n'+metadata+
          b'\r\n--'+boundary.encode()+b'\r\nContent-Type: application/json\r\n\r\n'+raw+b'\r\n--'+boundary.encode()+b'--\r\n')
    with session.post('https://www.googleapis.com/upload/drive/v3/files',params={'uploadType':'multipart','fields':'id,name,size,md5Checksum'},
                      headers={'Content-Type':'multipart/related; boundary='+boundary},data=body,timeout=25) as response:
        response.raise_for_status();saved=response.json()
    if int(saved['size'])!=len(raw) or saved['md5Checksum']!=hashlib.md5(raw).hexdigest():raise ValueError('Derived index durable metadata mismatch')
    with session.get(API+'/'+saved['id'],params={'alt':'media'},timeout=20) as response:
        response.raise_for_status()
        if response.content!=raw:raise ValueError('Derived private index readback mismatch')
    summary={k:v for k,v in index.items() if k not in ('artifacts','cloud_scratch_cache')}
    summary.update(private_index=saved['name'],private_index_id=saved['id'],index_sha256=hashlib.sha256(raw).hexdigest(),
                   index_bytes=len(raw),durable_readback_verified=True,seconds=time.monotonic()-started)
    print(json.dumps(summary),flush=True);return summary


if __name__=='__main__':
    import google.auth
    from google.auth.transport.requests import AuthorizedSession
    credentials,_=google.auth.default()
    with AuthorizedSession(credentials) as session:run(session)
