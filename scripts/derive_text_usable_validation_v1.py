"""Same-ID validation comparison from completed text predictions; no inference.

Keep original text results intact. Only validation predictions reach scoring; all TSVs are checked for integrity.
Confidence of the predicted class cannot reconstruct gold-class CE loss.
"""
import datetime,json
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score,balanced_accuracy_score,f1_score,classification_report,confusion_matrix
from usable_cohort_v2 import load_cohort,registration,REGISTRATION,sha

root=Path(__file__).resolve().parents[1]
reg=registration(root/'results'/REGISTRATION)
expected,_=load_cohort(root/'data/official_multimodal_v2',root/'results'/REGISTRATION,
    root/'data/official_paired_v1/source_recovery'/reg['extraction_report_file'],root/'results'/reg['approval_file'])
folder=root/'results/experiments/official_text/OFFICIAL-6W-TEXT-v2_seed42_20261008T095827Z/KAGGLE_RECOVERY_v1_20261009_356721456'
source=folder/'raw_evidence/bert-base/validation_predictions.csv'
proof=json.loads((folder/'local_prediction_verification.json').read_text())
assert sha(source)==proof['splits']['validation']['prediction_sha256']
p=pd.read_csv(source,dtype={'id':str});assert len(p)==59342 and p.id.is_unique
official=pd.DataFrame([r for r in expected.values() if r['split']=='validation'])
assert len(official)==59299
p=p.set_index('id').loc[official.id].reset_index()
assert p.id.tolist()==official.id.tolist() and np.array_equal(p.true_label.to_numpy(),official['6_way_label'].to_numpy())
gold,pred=p.true_label.to_numpy(),p.predicted_label.to_numpy()
names=['True','Satire/Parody','Misleading Content','Imposter Content','False Connection','Manipulated Content']
cm=confusion_matrix(gold,pred,labels=range(6))
result={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'state':'verified_derived_text_validation_same_usable_ids',
    'cohort_id':reg['cohort_id'],'validation_samples':len(p),'original_text_validation_samples':59342,
    'excluded_validation_ids':43,'source_predictions_file':str(source.relative_to(root)),'source_predictions_sha256':sha(source),
    'selected_text_epoch':proof['selected_epoch'],'selected_text_weights_sha256':proof['selected_weight_sha256'],
    'metrics':{'accuracy':float(accuracy_score(gold,pred)),'micro_f1':float(f1_score(gold,pred,average='micro')),
        'macro_f1':float(f1_score(gold,pred,average='macro',labels=range(6),zero_division=0)),
        'weighted_f1':float(f1_score(gold,pred,average='weighted',labels=range(6),zero_division=0)),
        'balanced_accuracy':float(balanced_accuracy_score(gold,pred)),'loss':None},
    'loss_status':'Not reconstructible for this filtered cohort from saved predicted-label confidence; do not reuse full-cohort loss',
    'classification_report':classification_report(gold,pred,labels=range(6),target_names=names,output_dict=True,zero_division=0),
    'confusions':{'labels':names,'raw':cm.tolist(),'row_normalized':(cm/cm.sum(1,keepdims=True)).tolist()},
    'no_model_inference':True,'test_prediction_file_read':False,'test_inference_performed':False,'all_split_tsv_integrity_checked':True,'original_text_results_modified':False,
    'limitation':'Same validation cohort only: original text training used564000 rows; multimodal training uses563601 usable rows'}
out=root/'results/MM_TEXT_SAME_USABLE_VALIDATION_20261027.json';out.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:result[k] for k in ['state','validation_samples','metrics','no_model_inference','test_prediction_file_read']}))
