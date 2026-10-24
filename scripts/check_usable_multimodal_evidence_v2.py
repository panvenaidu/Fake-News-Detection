"""Verifier regression using synthetic exports only; no research scores reported."""
import tempfile,json
from pathlib import Path
import numpy as np
import pandas as pd
from train_usable_multimodal_v2 import export_eval,measure
from verify_usable_multimodal_v2 import verify_export

def main():
 n=59299;y=np.arange(n)%6;probs=np.full((n,6),.05);probs[np.arange(n),y]=.75
 ce=-np.log(probs[np.arange(n),y]);official=pd.DataFrame({'id':['synthetic_'+str(i) for i in range(n)],'6_way_label':y.astype(str)})
 frame=pd.DataFrame({'id':official.id,'true_label':y,'predicted_label':y,'cross_entropy':ce,**{'p'+str(i):probs[:,i] for i in range(6)}})
 with tempfile.TemporaryDirectory(dir='data/official_paired_v2',prefix='evidence-check-') as temp:
  folder=Path(temp);export_eval(folder,1,measure(y,y,ce),frame);verify_export(folder,1,official)
  path=folder/'validation_epoch1_predictions.csv'
  for change in ['probability','duplicate_id','gold_label','loss']:
   bad=frame.copy()
   if change=='probability':bad.loc[0,'p0']=.8
   elif change=='duplicate_id':bad.loc[0,'id']=bad.loc[1,'id']
   elif change=='gold_label':bad.loc[0,'true_label']=1
   else:bad.loc[0,'cross_entropy']=0
   bad.to_csv(path,index=False,float_format='%.17g')
   try:verify_export(folder,1,official)
   except AssertionError:pass
   else:raise AssertionError('Corruption accepted: '+change)
 result={'status':'passed','scope':'Synthetic59299-row export verification only; no faculty data inference, no task metrics','checks':['Complete IDs/labels/supports and all requested metrics independently recomputed','All-six probabilities, loss, reports and confusions checked','Invalid probability rejected','Duplicate ID rejected','Altered gold label rejected','Altered per-row CE rejected']}
 Path('results/usable_multimodal_evidence_checks_20261024.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
