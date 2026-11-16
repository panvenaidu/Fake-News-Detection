# Read-only diagnostics; no remount, reset, data transfer or training.
from pathlib import Path
from datetime import datetime, timezone
import json, subprocess, re, os
result={'utc':datetime.now(timezone.utc).isoformat(),'state':'drive_failure_resource_diagnostic','pid':os.getpid(),'files':{},'training':False}
for name in ['/sys/fs/cgroup/memory.events','/sys/fs/cgroup/memory.current','/sys/fs/cgroup/memory.max','/proc/meminfo']:
 try: result['files'][name]=Path(name).read_text()[:4000]
 except Exception as e: result['files'][name]=type(e).__name__
try:
 p=subprocess.run(['dmesg','--ctime'],capture_output=True,text=True,timeout=8)
 result['kernel_oom_lines']=[x for x in p.stdout.splitlines() if re.search(r'(?i)out of memory|oom.kill|killed process|memory cgroup',x)][-15:];result['dmesg_returncode']=p.returncode
except Exception as e: result['dmesg_error']=str(e)
logs=[]
for p in Path('/root/.config/Google/DriveFS/Logs').glob('*.txt'):
 try:
  for line in p.read_text(errors='replace').splitlines():
   if not line.startswith('2026-10-24T20:'):continue
   if not re.search(r'(?i)fatal|out.of.memory|allocation|cannot allocate|core terminated|failure writing|inconsistent fields|crash|signal 9|SIGKILL',line):continue
   if re.search(r'(?i)token|oauth|cookie|authorization|secret|psk|commandline',line):continue
   line=re.sub(r'https?://\S+','[URL]',line);logs.append({'log':p.name,'line':line[:650]})
 except Exception: pass
result['drive_failure_lines']=logs[-25:]
Path('/content/UROP_DRIVE_RESOURCE_DIAGNOSTIC_20261025.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result),flush=True)
