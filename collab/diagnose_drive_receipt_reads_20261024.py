# Bounded read-only source-receipt diagnostic; no training, extraction or repack.
from google.colab import drive
from pathlib import Path
import json,os,time,traceback
print(json.dumps({'state':'bounded_drive_receipt_read_diagnostic','pid':os.getpid()}),flush=True)
for folder in [Path('/root/.config/Google/DriveFS/Logs'),Path('/tmp/drivefs')]:
 if folder.is_dir():
  print(json.dumps({'log_directory':str(folder),'files':[{'name':p.name,'bytes':p.stat().st_size} for p in folder.iterdir() if p.is_file()]}),flush=True)
# Only error-class log records; mask URLs, tokens and account strings.
import re
log=Path('/root/.config/Google/DriveFS/Logs/drive_fs.txt')
if log.is_file():
 with log.open('rb') as f:
  f.seek(max(0,log.stat().st_size-64000));text=f.read().decode(errors='replace')
 for line in text.splitlines():
  if re.search(r'FATAL|Out of memory|out of memory|ENOSPC|Segmentation|Check failed|Permission denied|quota|fatal|crash',line):
   line=re.sub(r'https?://\S+','[URL]',line)
   line=re.sub(r'[A-Za-z0-9_.+-]+@[A-Za-z0-9.-]+','[ACCOUNT]',line)
   line=re.sub(r'(?i)(token|authorization|cookie|secret)[^,; ]*[=: ]+[^,; ]+',r'\1=[REDACTED]',line)
   print('DRIVE_ERROR',line[:800],flush=True)
drive.mount('/content/drive',force_remount=True)
r=Path('/content/drive/MyDrive/UROP/official_images_v1')
start=time.monotonic();counts=0
try:
 paths=sorted((r/'shards').glob('*.receipt.json'))
 print(json.dumps({'state':'source_receipt_read_start','files':len(paths)}),flush=True)
 for n,p in enumerate(paths,1):
  if time.monotonic()-start>180:raise TimeoutError('Diagnostic180secondwallbound; no long workload')
  print(json.dumps({'state':'reading_receipt','n':n,'name':p.name,'bytes':p.stat().st_size}),flush=True)
  d=json.loads(p.read_text());counts+=len(d['images'])
  del d
 print(json.dumps({'state':'source_receipt_read_complete','files':len(paths),'images':counts,'seconds':time.monotonic()-start}),flush=True)
except Exception as e:
 print(json.dumps({'state':'source_receipt_read_failed','n':n,'name':p.name,'error':str(e),'traceback':traceback.format_exc()}),flush=True)
