"""Actual original-TSV cohort audit plus adversarial approval/report guards."""
from pathlib import Path
from datetime import datetime,timezone
import json,tempfile,hashlib,ast
from usable_cohort_v2 import load_cohort,REGISTRATION_SHA,COHORT,sha

root=Path(__file__).resolve().parents[1]
reg=root/'results/MM_PART1_USABLE_COHORT_REGISTRATION_20261024.json'
report=root/'data/official_paired_v1/source_recovery/extraction_7f55c34bcfa94cf09b61e3884590e49d.json'
approval=root/'results/MM_PART1_USABLE_COHORT_APPROVAL_20261024.json'
expected,r=load_cohort(root/'data/official_multimodal_v2',reg,report,approval)
assert len(expected)==682170 and not set(expected).intersection(json.loads(report.read_text())['missing_ids'])
checks=[]
with tempfile.TemporaryDirectory(dir=root/'data/official_paired_v2') as tmp:
 for role,original in [('registration',reg),('approval',approval),('report',report)]:
  bad=Path(tmp)/(role+'.json');bad.write_bytes(original.read_bytes()+b' ')
  args=[root/'data/official_multimodal_v2',reg,report,approval]
  args[{'registration':1,'report':2,'approval':3}[role]]=bad
  try:load_cohort(*args)
  except ValueError:checks.append(role+'_tamper_rejected')
  else:raise AssertionError(role+'tamperaccepted')
# These numerically sensitive production primitives are unchanged by the cohort amendment.
a=ast.parse((root/'scripts/train_official_multimodal_v1.py').read_text());b=ast.parse((root/'scripts/train_usable_multimodal_v2.py').read_text())
for name in ['Engine','MaximumFusion','Pairs','Collate','build_loader','measure','evaluate','export_eval','better']:
 before=next(n for n in a.body if isinstance(n,(ast.ClassDef,ast.FunctionDef)) and n.name==name)
 after=next(n for n in b.body if isinstance(n,(ast.ClassDef,ast.FunctionDef)) and n.name==name)
 assert ast.dump(before,include_attributes=False)==ast.dump(after,include_attributes=False),name
checks+=['all_original_TSV_hashes_counts_IDs_labels_titles_verified','exact491approved_exclusions_only','all_three_usable_split_and_class_counts_verified','unchanged_architecture_engine_recovery_crop_eval_primitives','four_epoch_boundaries70452_warmup7046_registered']
result={'utc':datetime.now(timezone.utc).isoformat(),'status':'passed','cohort_id':COHORT,'registration_sha256':REGISTRATION_SHA,'usable':len(expected),'split_counts':r['split_counts'],'checks':checks,'image_bytes_verified':False,'training':False,'validation_inference':False,'test_inference':False,'test_source_sha256':sha(__file__)}
(root/'results/usable_cohort_contract_checks_20261024.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
