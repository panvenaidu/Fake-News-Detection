"""Evaluate one frozen, training-complete checkpoint; never optimize or select on test."""
import argparse,datetime,hashlib,json,os,sys,time
from pathlib import Path

def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def run(a):
 import numpy as np,pandas as pd,torch
 import train_usable_multimodal_v2 as t
 from usable_cohort_v2 import load_input
 from multimodal_recovery_v1 import sha,atomic_json,load_generation
 from verify_multimodal_final_v1 import verify,LABELS
 from sklearn.metrics import classification_report,confusion_matrix
 folder=Path(a.run);protocol=json.loads((folder/'protocol.json').read_text());cfg=protocol['config']
 payload,proof=load_generation(folder/'recovery');state=payload['state'];assert payload['contract']==protocol
 assert state['epoch']>4 or state['early_stopped'];assert len(state['history'])>=3
 selected=max(state['history'],key=lambda h:(h['validation']['macro_f1'],-h['validation']['loss'],-h['epoch']))
 assert selected['epoch']==state['best']['epoch'];best=state['best'];weights=folder/best['weights_file'];assert sha(weights)==best['weights_sha256']
 freeze=folder/'final_selection_frozen.json'
 value={'utc':now(),'state':'frozen_before_test','selection_rule':cfg['selection'],'selected':best,'protocol_sha256':sha(folder/'protocol.json'),'source_hashes':protocol['sources'],'inputs':protocol['inputs'],'training_complete':True,'recovery':proof}
 if freeze.exists():
  existing=json.loads(freeze.read_text());assert existing['selected']==best and existing['protocol_sha256']==value['protocol_sha256']
 else:atomic_json(freeze,value)
 expected,_=load_input(a.root);official=pd.DataFrame([r for r in expected.values() if r['split']=='test']);assert len(official)==59270
 manifest=pd.read_csv(Path(a.root)/'data/official_paired_v2/paired_manifest.csv',dtype=str,keep_default_na=False);assert sha(Path(a.root)/'data/official_paired_v2/paired_manifest.csv')==protocol['inputs']['manifest_sha256']
 test=manifest[manifest.split.eq('test')].set_index('id').loc[official.id].reset_index()
 for key in ['clean_title','6_way_label']:assert np.array_equal(test[key].astype(str).to_numpy(),official[key].astype(str).to_numpy())
 if (folder/'test_metrics.json').exists():
  result=verify(folder,'test',official,'test');atomic_json(folder/'test_independent_verification.json',result);return result
 assert not (folder/'test_start.json').exists(),'Interrupted test requires explicitly reviewed replay; never silently re-run'
 atomic_json(folder/'test_start.json',{'utc':now(),'weights_sha256':best['weights_sha256'],'selection_receipt_sha256':sha(freeze),'expected_rows':59270,'policy':'one full frozen evaluation; no optimizer or tuning'})
 tokenizer=t.AutoTokenizer.from_pretrained(folder/'tokenizer');bcfg=t.AutoConfig.from_pretrained(cfg['bert_checkpoint'],revision=cfg['bert_revision'])
 model=t.MaximumFusion(t.BertModel(bcfg,add_pooling_layer=False),t.resnet50(weights=None));model.image.fc=t.nn.Identity()
 loaded=torch.load(weights,map_location='cpu',weights_only=True);model.load_state_dict(loaded,strict=True);model=model.cuda().eval()
 # Same selected tensor, validation-only probe: strict reload roundtrip and logits.
 val=manifest[manifest.split.eq('validation')].iloc[:32].copy();ds=t.Pairs(val,a.root,tokenizer,cfg,False,a.index,protocol['inputs']['packed_index_sha256']);batch=next(iter(t.build_loader(ds,tokenizer,cfg,False)));batch.pop('ids');batch.pop('labels')
 with torch.inference_mode(),torch.autocast('cuda',dtype=torch.float16):before=model(**{k:v.cuda() for k,v in batch.items()})
 model.load_state_dict(loaded,strict=True)
 with torch.inference_mode(),torch.autocast('cuda',dtype=torch.float16):after=model(**{k:v.cuda() for k,v in batch.items()})
 assert torch.equal(before,after);atomic_json(folder/'selected_weight_roundtrip.json',{'utc':now(),'sha256':sha(weights),'strict_load':True,'validation_probe_rows':len(val),'maximum_logit_delta':float((before-after).abs().max())})
 del loaded,ds,batch,before,after
 started=time.monotonic();data=t.Pairs(test,a.root,tokenizer,cfg,False,a.index,protocol['inputs']['packed_index_sha256']);metrics,frame=t.evaluate(model,t.build_loader(data,tokenizer,cfg,False),torch.device('cuda'));assert frame.id.tolist()==official.id.tolist();frame.insert(1,'split','test')
 frame.to_csv(folder/'test_predictions.csv',index=False,float_format='%.17g');atomic_json(folder/'test_metrics.json',metrics)
 y=frame.true_label.to_numpy();pred=frame.predicted_label.to_numpy();cm=confusion_matrix(y,pred,labels=range(6));atomic_json(folder/'test_classification_report.json',classification_report(y,pred,labels=range(6),target_names=LABELS,zero_division=0,output_dict=True));atomic_json(folder/'test_confusions.json',{'labels':LABELS,'raw':cm.tolist(),'row_normalized':(cm/cm.sum(1,keepdims=True)).tolist()})
 result=verify(folder,'test',official,'test');result.update(utc=now(),inference_seconds=time.monotonic()-started,selected_epoch=best['epoch'],weights_sha256=best['weights_sha256']);atomic_json(folder/'test_independent_verification.json',result)
 # Preserve original selected validation file; make a labelled final export copy.
 prefix='validation_epoch'+str(best['epoch']);vf=pd.read_csv(folder/(prefix+'_predictions.csv'),dtype={'id':str});vf.insert(1,'split','validation');vf.to_csv(folder/'validation_predictions.csv',index=False,float_format='%.17g')
 import shutil
 for suffix in ['metrics.json','classification_report.json','confusions.json']:shutil.copyfile(folder/(prefix+'_'+suffix),folder/('validation_'+suffix))
 voff=pd.DataFrame([r for r in expected.values() if r['split']=='validation']);atomic_json(folder/'validation_independent_verification.json',verify(folder,'validation',voff,'validation'))
 atomic_json(folder/'final_evaluation_complete.json',{'utc':now(),'test':result,'final_selected_epoch':best['epoch'],'state':'runtime_verified_requires_saved_private_and_local_readback'})
 return result
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--run',required=True,type=Path);p.add_argument('--root',required=True,type=Path);p.add_argument('--index',required=True,type=Path);a=p.parse_args();print(json.dumps(run(a)),flush=True)
