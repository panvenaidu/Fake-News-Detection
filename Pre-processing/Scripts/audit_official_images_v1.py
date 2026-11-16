"""Audit exact official IDs and decode existing images; never downloads or trains.

Outputs missing IDs and an explicitly incomplete candidate manifest. Full training
must require image_gate_passed plus exact IDs/labels and a stable coverage hash.
"""
import argparse, csv, hashlib, json, os, sqlite3, time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from PIL import Image

def sha(path):
 h=hashlib.sha256()
 with open(path,'rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()

def atomic(path,value):
 path=Path(path);tmp=path.with_suffix(path.suffix+'.tmp')
 with tmp.open('w') as f:
  json.dump(value,f,indent=2,allow_nan=False);f.write('\n');f.flush();os.fsync(f.fileno())
 os.replace(tmp,path)

def inspect(pair):
 ident,p=pair
 try:
  with Image.open(p) as im:
   im.load(); mode=im.mode;size=im.size
   rgb=im.convert('RGB'); rgb.load()
  return ident,str(p),p.stat().st_size,sha(p),mode,size,''
 except Exception as e:return ident,str(p),0,'','',[],str(e)

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,default=Path('.'));ap.add_argument('--workers',type=int,default=4);a=ap.parse_args();root=a.root.resolve()
 out=root/'data/official_paired_v1';out.mkdir(parents=True,exist_ok=True)
 expected={};counts={};provenance=json.loads((root/'results/official_dataset_provenance.json').read_text());hashes={x['filename']:x['sha256'] for x in provenance['files']}
 for split,name,count in [('train','multimodal_train.tsv',564000),('validation','multimodal_validate.tsv',59342),('test','multimodal_test_public.tsv',59319)]:
  p=root/'data/official_multimodal_v2'/name
  if sha(p)!=hashes[name]:raise ValueError('TSV hash mismatch '+name)
  rows=list(csv.DictReader(p.open(),delimiter='\t'));assert len(rows)==count
  classes=Counter()
  for row in rows:
   ident=row['id'];label=int(row['6_way_label']);assert ident not in expected and label in range(6) and row['clean_title'].strip()
   expected[ident]=(split,row['clean_title'],label);classes[label]+=1
  counts[split]={'expected':count,'classes':dict(classes)}
 inventory={};duplicates=[]
 for p in sorted((root/'images').rglob('*')):
  if p.is_file() and p.suffix.lower() in ['.jpg','.jpeg','.png','.webp']:
   if p.stem in inventory:duplicates.append(p.stem)
   else:inventory[p.stem]=p
 cache=sqlite3.connect(out/'image_integrity.sqlite3');cache.execute('CREATE TABLE IF NOT EXISTS images(id TEXT PRIMARY KEY,path TEXT,bytes INTEGER,sha TEXT,mode TEXT,width INTEGER,height INTEGER,error TEXT)');cache.execute('DELETE FROM images');cache.commit()
 started=time.monotonic();done=0
 # Reinspect originals each explicit audit; sqlite is durable evidence, not a blind cache.
 with ThreadPoolExecutor(max_workers=a.workers) as pool:
  for ident,p,n,h,mode,size,error in pool.map(inspect,inventory.items()):
   cache.execute('INSERT OR REPLACE INTO images VALUES(?,?,?,?,?,?,?,?)',(ident,p,n,h,mode,size[0] if size else 0,size[1] if size else 0,error));done+=1
   if done%500==0:
    cache.commit();atomic(out/'audit_status.json',{'state':'decoding','decoded':done,'inventoried':len(inventory),'utc':datetime.now(timezone.utc).isoformat()})
 cache.commit();valid={r[0]:r for r in cache.execute('SELECT * FROM images WHERE error=""')};failures=list(cache.execute('SELECT id,error FROM images WHERE error!=""'))
 with (out/'missing_ids.csv').open('w') as f,(out/'candidate_manifest.csv').open('w') as g:
  missing=csv.writer(f);missing.writerow(['id','split','reason']);writer=csv.writer(g);writer.writerow(['id','split','clean_title','6_way_label','image_path','image_sha256'])
  for ident,(split,title,label) in expected.items():
   if ident not in valid:missing.writerow([ident,split,'absent' if ident not in inventory else 'decode_failed'])
   else:
    r=valid[ident];writer.writerow([ident,split,title,label,str(Path(r[1]).relative_to(root)),r[3]]);counts[split]['usable']=counts[split].get('usable',0)+1
 dup_content=[]
 for h,n in cache.execute('SELECT sha,COUNT(*) FROM images WHERE error="" GROUP BY sha HAVING COUNT(*)>1'):
  ids=[r[0] for r in cache.execute('SELECT id FROM images WHERE sha=?',(h,))];splits=sorted({expected[x][0] for x in ids if x in expected})
  if len(splits)>1:dup_content.append({'sha256':h,'ids':ids,'splits':splits})
 atomic(out/'cross_split_content_duplicates.json',dup_content)
 usable=sum(x.get('usable',0) for x in counts.values());passed=usable==len(expected) and not duplicates
 result={'utc':datetime.now(timezone.utc).isoformat(),'image_gate_passed':passed,'splits':counts,'required':len(expected),'usable':usable,'missing_or_failed':len(expected)-usable,'decode_failures':failures,'duplicate_id_stems':duplicates,'cross_split_duplicate_content_groups':len(dup_content),'elapsed_seconds':time.monotonic()-started,'manifest':'data/official_paired_v1/candidate_manifest.csv','manifest_sha256':sha(out/'candidate_manifest.csv'),'missing_ids_sha256':sha(out/'missing_ids.csv'),'scope':'Local image audit only; no download, training, validation or test inference'}

 if passed:
  import shutil
  shutil.copyfile(out/'candidate_manifest.csv',out/'paired_manifest.csv')
  result['manifest']='data/official_paired_v1/paired_manifest.csv'
 atomic(root/'results/official_image_coverage_v1.json',result);atomic(out/'audit_status.json',{'state':'complete','image_gate_passed':passed,'utc':result['utc']});print(json.dumps(result,indent=2));cache.close()
 if not passed:raise SystemExit(2)
if __name__=='__main__':main()
