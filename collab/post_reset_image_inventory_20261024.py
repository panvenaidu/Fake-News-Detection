"""Read-only bounded image/receipt inventory after the user-approved CPU reset."""
from google.colab import drive
from pathlib import Path
from datetime import datetime,timezone
from collections import Counter
import json,os,time,hashlib,shutil,traceback
now=lambda:datetime.now(timezone.utc).isoformat()
drive.mount('/content/drive')
root=Path('/content/drive/MyDrive/UROP/official_images_v1')
print(json.dumps({'utc':now(),'state':'post_reset_CPU_mounted','pid':os.getpid(),'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'scratch_free':shutil.disk_usage('/content').free,'root_exists':root.is_dir()}),flush=True)
report={'utc':now(),'state':'post_reset_receipt_inventory','training':False,'test_inference':False,'archive_bytes_rehashed':False,'image_bytes_reverified':False,'inventories':{}}
start=time.monotonic();active=None
try:
 for role,folder,count,rows in [('original_source',root/'shards',150,682170),('closed_transport',root/'kaggle_packed_usable_v2/shards',18,319820)]:
  paths=sorted(folder.glob('*.receipt.json'));assert len(paths)==count,(role,len(paths))
  seen=set();splits=Counter();proof=[]
  for n,path in enumerate(paths,1):
   active={'role':role,'n':n,'file':path.name}
   if time.monotonic()-start>240:raise TimeoutError('240second inventory bound')
   raw=path.read_bytes();v=json.loads(raw);archive=folder/v['archive']
   assert archive.parent.resolve()==folder.resolve() and archive.is_file() and archive.stat().st_size==v['bytes']
   for row in v['images']:
    assert row['id'] not in seen,'Duplicate receipt ID';seen.add(row['id']);splits[row['split']]+=1
   proof.append({'file':path.name,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'archive':v['archive'],'archive_bytes':v['bytes'],'archive_sha256':v['sha256'],'images':len(v['images'])})
   if n%20==0 or n==len(paths):print(json.dumps({'utc':now(),'state':'post_reset_receipts_read','role':role,'files':n,'total_files':len(paths),'images':len(seen)}),flush=True)
  assert len(seen)==rows,(role,len(seen))
  report['inventories'][role]={'receipt_files':len(paths),'images':len(seen),'splits':dict(splits),'artifacts':proof}
 report.update(state='post_reset_receipt_inventory_passed',utc=now(),seconds=time.monotonic()-start)
 destination=root/('POST_RESET_INVENTORY_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'.json')
 with destination.open('x') as f:json.dump(report,f,indent=2);f.flush();os.fsync(f.fileno())
 print(json.dumps({'utc':now(),'state':report['state'],'seconds':report['seconds'],'receipt':destination.name,'sha256':hashlib.sha256(destination.read_bytes()).hexdigest(),'source_images':682170,'closed_transport_images':319820,'runtime_image_gate_passed':False,'training':False}),flush=True)
except Exception as error:
 print(json.dumps({'utc':now(),'state':'post_reset_receipt_inventory_failed','active':active,'error':str(error),'traceback':traceback.format_exc(),'seconds':time.monotonic()-start,'training':False}),flush=True)
