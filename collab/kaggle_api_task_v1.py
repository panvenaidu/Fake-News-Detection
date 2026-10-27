"""Bounded official Kaggle API action; receive approved token through a FIFO.

No credential file, token output, shell interpolation, or laptop model training.
"""
import argparse,datetime,json,os,stat,sys
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--token-fifo',type=Path,required=True);p.add_argument('--request',type=Path,required=True);p.add_argument('--receipt',type=Path,required=True);a=p.parse_args()
project=Path(__file__).resolve().parents[1]
for path in [a.token_fifo,a.request,a.receipt]:
 if not path.resolve().is_relative_to(project):raise ValueError('Project paths only')
if not stat.S_ISFIFO(a.token_fifo.stat().st_mode):raise ValueError('Credential input must be a FIFO')
with a.token_fifo.open() as stream:token=stream.read().strip()
a.token_fifo.unlink()
if not token.startswith('KGAT_'):raise ValueError('Approved token missing')
os.environ['KAGGLE_API_TOKEN']=token
os.environ['KAGGLE_CONFIG_DIR']=str(project/'data/cloud_recovery/.kaggle-api-config')
request=json.loads(a.request.read_text());result={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'action':request['action']}
try:
 from kaggle.api.kaggle_api_extended import KaggleApi
 api=KaggleApi();api.authenticate()
 action=request['action']
 if action=='inspect':
  q=api.quota_view();g=q.gpu_quota
  result['gpu_quota']={k:getattr(g,k).total_seconds() if getattr(g,k) is not None else None for k in ['time_used','time_reserved','total_time_allowed']}
  result['quota_refresh_utc']=q.quota_refresh_time.isoformat() if q.quota_refresh_time else None
  result['kernels']={kernel:str(api.kernels_status(kernel).status) for kernel in request['kernels']}
 elif action=='pull':
  destination=Path(request['folder']).resolve()
  if not destination.is_relative_to(project):raise ValueError('Project folder required')
  api.kernels_pull(request['kernel'],str(destination),metadata=True,quiet=True);result['folder']=str(destination)
 elif action=='push':
  folder=Path(request['folder']).resolve()
  if not folder.is_relative_to(project):raise ValueError('Project folder required')
  r=api.kernels_push(str(folder),timeout=str(request['timeout_seconds']),acc=request.get('accelerator'),no_run=bool(request.get('no_run',False)))
  result.update(ref=r.ref,url=r.url,version=r.version_number,kernel_id=r.kernel_id,error=r.error,invalid_kernel_sources=r.invalid_kernel_sources,invalid_dataset_sources=r.invalid_dataset_sources)
  if r.error or r.invalid_kernel_sources or r.invalid_dataset_sources:raise ValueError('Kaggle rejected submission')
 elif action=='diagnose':
  r=api.kernels_status(request['kernel']);result.update(kernel=request['kernel'],status=str(r.status),failure_message=r.failure_message)
  destination=Path(request['folder']).resolve()
  if not destination.is_relative_to(project):raise ValueError('Project folder required')
  files,next_page=api.kernels_output(request['kernel'],str(destination),file_pattern=request.get('pattern',r'\.(json|log)$'),force=True,quiet=True,page_size=100)
  result.update(files=files,next_page=bool(next_page))
 elif action=='status':
  r=api.kernels_status(request['kernel']);result.update(kernel=request['kernel'],status=str(r.status),failure_message=r.failure_message)
 elif action=='output':
  destination=Path(request['folder']).resolve()
  if not destination.is_relative_to(project):raise ValueError('Project folder required')
  files,next_page=api.kernels_output(request['kernel'],str(destination),file_pattern=request['pattern'],force=False,quiet=True,page_size=100)
  result.update(files=files,next_page=bool(next_page))
 else:raise ValueError('Unknown bounded action')
 result['request_succeeded']=True
except Exception as error:
 result.update(request_succeeded=False,error_type=type(error).__name__)
 response=getattr(error,'response',None)
 if response is not None:result['http_status']=response.status_code
finally:
 os.environ.pop('KAGGLE_API_TOKEN',None)
 encoded=json.dumps(result,indent=2,default=str).replace(token,'[REDACTED]')
 a.receipt.write_text(encoded+'\n');print(encoded)
 if not result.get('request_succeeded'):sys.exit(1)
