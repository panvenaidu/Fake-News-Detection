"""Independently verify retrieved scientific epochs, predictions and recovery.

CPU-only artifact readback; no model inference or training on the laptop.
"""
import argparse,datetime,json,math
from pathlib import Path
import pandas as pd
from usable_cohort_v2 import load_input, REGISTRATION, REGISTRATION_SHA, PROTOCOL
from multimodal_recovery_v1 import load_generation,sha
from verify_usable_multimodal_v2 import verify_export,verify_part1


def verify(project,folder,epochs):
 project,folder=Path(project).resolve(),Path(folder).resolve()
 assert folder.is_relative_to(project/'data/cloud_recovery')
 # Present the unchanged local references in the cloud verifier's layout.
 root=project/'data/cloud_recovery/local_protocol_verification_root'
 (root/'results').mkdir(parents=True,exist_ok=True);(root/'data').mkdir(exist_ok=True)
 registration=project/'results'/REGISTRATION;reg=json.loads(registration.read_text())
 sources={REGISTRATION:registration,reg['approval_file']:project/'results'/reg['approval_file']}
 extraction=project/'results'/reg['extraction_report_file']
 if not extraction.is_file():extraction=project/'data/official_paired_v1/source_recovery'/reg['extraction_report_file']
 sources[reg['extraction_report_file']]=extraction
 for name,source in sources.items():
  target=root/'results'/name
  if not target.exists():target.symlink_to(source)
  assert target.resolve()==source.resolve()
 target=root/'data/official_multimodal_v2'
 if not target.exists():target.symlink_to(project/'data/official_multimodal_v2',target_is_directory=True)
 assert target.resolve()==(project/'data/official_multimodal_v2').resolve()
 expected,_=load_input(root);official=pd.DataFrame([r for r in expected.values() if r['split']=='validation'])
 protocol=json.loads((folder/'protocol.json').read_text());assert protocol['config_sha256']=='ad8f86f86b1fef453ae3bccda0aeb13cc50b298dc0d5d502f87c9ac4b041b483'
 assert protocol['config']['planned_epochs']==4 and protocol['config']['protocol_id']==PROTOCOL and protocol['config']['seed']==42
 assert protocol['inputs']['cohort_registration_sha256']==REGISTRATION_SHA
 runtime=json.loads((folder/'cloud_job_runtime_result.json').read_text());assert runtime['state']=='epoch_job_finished' and runtime['epochs_validated']==epochs and runtime['no_test_performed']
 payload,recovery=load_generation(folder/'recovery');assert payload['contract']==protocol and payload['gradients_cleared']
 assert {'model','optimizer','scheduler','scaler','rng','state','contract'}.issubset(payload)
 state=payload['state'];assert state['epoch']==epochs+1 and state['cursor']==0 and state['phase']=='train' and payload['cursor']==0
 assert [h['epoch'] for h in state['history']]==list(range(1,epochs+1))
 assert state['updates']+state['skips']==17613*epochs
 assert payload['scheduler']['last_epoch']==state['updates'] and len(payload['rng']['cuda'])==1
 assert all(k in payload['rng'] for k in ['python','numpy','torch','cuda'])
 assert payload['model'] and payload['optimizer']['state'] and payload['scaler']
 values=[verify_export(folder,e,official) for e in range(1,epochs+1)]
 for history,value in zip(state['history'],values):
  assert math.isfinite(history['train_loss'])
  for key,number in value['metrics'].items():assert abs(history['validation'][key]-number)<1e-10
 selected=max(values,key=lambda x:(x['metrics']['macro_f1'],-x['metrics']['loss'],-x['epoch']))
 assert selected['epoch']==state['best']['epoch'] and sha(folder/state['best']['weights_file'])==state['best']['weights_sha256']
 assert not list(folder.glob('test*_predictions.csv')) and not list(folder.glob('test*_metrics.json'))
 if epochs==2:verify_part1(folder,root)
 names=['protocol.json','history.json','runtime_recovery.json','cloud_job_runtime_result.json','cloud_job_release.json','recovery/generations.json',state['best']['weights_file']]
 names += ['recovery/'+x['file'] for x in json.loads((folder/'recovery/generations.json').read_text())['generations']]
 for epoch in range(1,epochs+1):names += ['validation_epoch%d_%s'%(epoch,suffix) for suffix in ['predictions.csv','metrics.json','classification_report.json','confusions.json']]
 artifacts={n:{'bytes':(folder/n).stat().st_size,'sha256':sha(folder/n)} for n in names}
 return {'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'passed_independent_retrieved_epoch_verification','epochs_trained':epochs,'epochs_validated':epochs,'next_epoch':state['epoch'],'next_cursor':0,'selected_epoch':selected['epoch'],'validation':values,'recovery':recovery,'artifacts':artifacts,'no_test_performed':True,'local_model_inference':False,'private_cloud_version_confirmation_required_separately':True}


if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--project',type=Path,required=True);p.add_argument('--run',type=Path,required=True);p.add_argument('--epochs',type=int,choices=[1,2],required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 result=verify(a.project,a.run,a.epochs);a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='artifacts'}))
