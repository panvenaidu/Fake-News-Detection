"""Independent CSV-only verification for a frozen multimodal validation/test.
No model, inference, training or network access. Output is a returned dict.
"""
from pathlib import Path
import hashlib,json
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score,f1_score,balanced_accuracy_score,classification_report,confusion_matrix
LABELS=['True','Satire/Parody','Misleading Content','Imposter Content','False Connection','Manipulated Content']
def sha(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  for b in iter(lambda:f.read(4*1024**2),b''):h.update(b)
 return h.hexdigest()
def verify(folder,prefix,official,split):
 folder=Path(folder);frame=pd.read_csv(folder/(prefix+'_predictions.csv'),dtype={'id':str})
 assert len(frame)==len(official) and frame.id.is_unique and frame.id.tolist()==official.id.tolist()
 assert frame['split'].eq(split).all()
 y=frame.true_label.to_numpy();p=frame.predicted_label.to_numpy();ce=frame.cross_entropy.to_numpy();probs=frame[['p'+str(i) for i in range(6)]].to_numpy()
 assert np.array_equal(y,official['6_way_label'].astype(int).to_numpy())
 assert np.isfinite(probs).all() and np.isfinite(ce).all() and (ce>=0).all() and (probs>=0).all() and (probs<=1).all()
 assert np.allclose(probs.sum(1),1,atol=2e-6,rtol=0) and np.array_equal(probs.argmax(1),p)
 gold=probs[np.arange(len(y)),y];positive=gold>0
 assert np.allclose(-np.log(gold[positive]),ce[positive],rtol=2e-5,atol=2e-5)
 assert (ce[~positive]>=-np.log(np.finfo(np.float32).tiny)).all()
 metrics={'accuracy':float(accuracy_score(y,p)),'micro_f1':float(f1_score(y,p,average='micro')),'macro_f1':float(f1_score(y,p,average='macro',labels=range(6),zero_division=0)),'weighted_f1':float(f1_score(y,p,average='weighted',labels=range(6),zero_division=0)),'balanced_accuracy':float(balanced_accuracy_score(y,p)),'loss':float(ce.mean()),'samples':len(frame)}
 def compare(a,b):
  if isinstance(a,dict):
   assert set(a)==set(b)
   for k in a:compare(a[k],b[k])
  else:assert abs(a-b)<1e-10
 compare(json.loads((folder/(prefix+'_metrics.json')).read_text()),metrics)
 compare(json.loads((folder/(prefix+'_classification_report.json')).read_text()),classification_report(y,p,labels=range(6),target_names=LABELS,output_dict=True,zero_division=0))
 cm=confusion_matrix(y,p,labels=range(6));conf=json.loads((folder/(prefix+'_confusions.json')).read_text());assert conf['labels']==LABELS and np.array_equal(conf['raw'],cm)
 norm=np.divide(cm,cm.sum(1,keepdims=True),out=np.zeros_like(cm,dtype=float),where=cm.sum(1,keepdims=True)!=0)
 assert np.allclose(conf['row_normalized'],norm,atol=1e-12,rtol=0)
 return {'status':'passed_independent_csv_verification','split':split,'metrics':metrics,'prediction_sha256':sha(folder/(prefix+'_predictions.csv')),'exact_order_ids_labels':True,'probability_ce_confusion_checks':True}
