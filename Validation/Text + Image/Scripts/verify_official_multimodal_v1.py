"""Independently recompute full-validation exports and Part1 runtime recovery.

Produces runtime acceptance only. Cloud/local durability and Git receipts are
separate checks; no training or test inference is performed here.
"""
import argparse,csv,json,math
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score,balanced_accuracy_score,f1_score,classification_report,confusion_matrix
from multimodal_recovery_v1 import atomic_json,sha,load_generation

def verify_export(folder,epoch,official):
 prefix='validation_epoch'+str(epoch);p=Path(folder)/(prefix+'_predictions.csv');frame=pd.read_csv(p,dtype={'id':str})
 assert len(frame)==59342 and frame.id.is_unique
 assert frame.id.tolist()==official.id.tolist()
 assert np.array_equal(frame.true_label.to_numpy(),official['6_way_label'].astype(int).to_numpy())
 probs=frame[['p'+str(i) for i in range(6)]].to_numpy();ce=frame.cross_entropy.to_numpy();gold=frame.true_label.to_numpy();pred=frame.predicted_label.to_numpy()
 assert np.isfinite(probs).all() and np.isfinite(ce).all() and (ce>=0).all()
 assert (probs>=0).all() and (probs<=1).all() and np.allclose(probs.sum(1),1,atol=2e-6,rtol=0)
 assert np.array_equal(probs.argmax(1),pred)
 # CE is computed from original logits, so allow float32 softmax/CE rounding.
 gold_probability=probs[np.arange(len(gold)),gold];positive=gold_probability>0
 derived=-np.log(gold_probability[positive])
 assert np.allclose(derived,ce[positive],rtol=2e-5,atol=2e-5)
 # A float32 softmax can underflow to zero for extreme valid logits. The
 # exported CE remains finite; do not manufacture a loss by clipping to1e-308.
 assert (ce[~positive]>=-np.log(np.finfo(np.float32).tiny)).all()
 metrics={'accuracy':float(accuracy_score(gold,pred)),'micro_f1':float(f1_score(gold,pred,average='micro')),'macro_f1':float(f1_score(gold,pred,average='macro',labels=range(6),zero_division=0)),'weighted_f1':float(f1_score(gold,pred,average='weighted',labels=range(6),zero_division=0)),'balanced_accuracy':float(balanced_accuracy_score(gold,pred)),'loss':float(ce.mean()),'samples':len(frame)}
 stored=json.loads((Path(folder)/(prefix+'_metrics.json')).read_text())
 for k,v in metrics.items():assert abs(stored[k]-v)<1e-10,k
 reports=json.loads((Path(folder)/(prefix+'_classification_report.json')).read_text())
 labels=json.loads((Path(folder)/(prefix+'_confusions.json')).read_text())['labels']
 expected=classification_report(gold,pred,labels=range(6),target_names=labels,zero_division=0,output_dict=True)
 def compare(a,b):
  if isinstance(a,dict):
   assert set(a)==set(b)
   for key in a:compare(a[key],b[key])
  else:assert abs(a-b)<1e-10
 compare(reports,expected)
 conf=json.loads((Path(folder)/(prefix+'_confusions.json')).read_text());cm=confusion_matrix(gold,pred,labels=range(6));assert np.array_equal(conf['raw'],cm)
 norm=cm/cm.sum(1,keepdims=True);assert np.allclose(conf['row_normalized'],norm,atol=1e-12,rtol=0)
 return {'epoch':epoch,'metrics':metrics,'predictions_sha256':sha(p)}

def verify_part1(folder,root):
 folder=Path(folder);root=Path(root)
 protocol=json.loads((folder/'protocol.json').read_text());p=protocol['inputs']['tsv_sha256']['multimodal_validate.tsv'];official_path=root/'data/official_multimodal_v2/multimodal_validate.tsv';assert sha(official_path)==p
 assert p=='c70140ec376e083e3780b5b488c96c8933678ca5800139bfb78c92e95df6946e'
 assert protocol['config']['protocol_id']=='OFFICIAL-6W-MM-v1' and protocol['config']['seed']==42 and protocol['config']['planned_epochs']==4
 official=pd.read_csv(official_path,sep='\t',dtype=str,keep_default_na=False)
 payload,recovery=load_generation(folder/'recovery');assert payload['contract']==protocol
 state=payload['state'];assert state['epoch']==3 and state['cursor']==0 and state['phase']=='train';assert [h['epoch'] for h in state['history']]==[1,2]
 expected_boundaries=17625*2;assert state['updates']+state['skips']==expected_boundaries
 values=[verify_export(folder,e,official) for e in [1,2]]
 for stored,actual in zip(state['history'],values):
  for k,v in actual['metrics'].items():assert abs(stored['validation'][k]-v)<1e-10
 selected=max(values,key=lambda x:(x['metrics']['macro_f1'],-x['metrics']['loss'],-x['epoch']))
 assert selected['epoch']==state['best']['epoch']
 assert sha(folder/state['best']['weights_file'])==state['best']['weights_sha256']
 assert not list(folder.glob('test*_predictions.csv')) and not list(folder.glob('test*_metrics.json'))
 artifact_names=['protocol.json','history.json','recovery/generations.json',state['best']['weights_file']]
 for generation in json.loads((folder/'recovery/generations.json').read_text())['generations']:artifact_names.append('recovery/'+generation['file'])
 for epoch in [1,2]:artifact_names.extend('validation_epoch%d_%s'%(epoch,suffix) for suffix in ['predictions.csv','metrics.json','classification_report.json','confusions.json'])
 artifacts={n:{'bytes':(folder/n).stat().st_size,'sha256':sha(folder/n)} for n in artifact_names}
 result={'status':'verified_runtime_only','epochs_trained':2,'epochs_validated':2,'next_epoch':3,'no_test_performed':True,'validation':values,'selected_epoch':selected['epoch'],'recovery':recovery,'artifacts':artifacts,'not_verified':['Private cloud saved-version persistence','Local retrieval of durable recovery','Git backup and all context updates','Actual GPU numerical replay regression']}
 atomic_json(folder/'part1_runtime_verification.json',result);return result

if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--run',type=Path,required=True);ap.add_argument('--root',type=Path,required=True);a=ap.parse_args();print(json.dumps(verify_part1(a.run,a.root),indent=2))
