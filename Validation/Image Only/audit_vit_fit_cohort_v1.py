"""Local train/validation audit from exact registered index and original cohort files."""
import json
import sqlite3
import sys
from pathlib import Path

import pandas as pd

root=Path(__file__).resolve().parents[2]
for p in ('Training/Text + Image/Scripts','Training/Image Only/Cloud','Model/Image Only'):
    sys.path.insert(0,str(root/p))
from packed_image_io_v3 import sha
from usable_cohort_v2 import load_cohort
from vit_finetune_cloud_v1 import label_conflicts
from frozen_image_pair_v1 import sampled

regfile=root/'Metrics/Results/MM_PART1_USABLE_COHORT_REGISTRATION_20261024.json'
config=json.loads((root/'Configuration/Image Only/image_only_vit_resnet_frozen_v1.json').read_text())
data=root/'Pre-processing/Data'
gate=data/'cloud_recovery/KAGGLE_PACKED_GATE_v2_362643633/urop_mm_packed_gate_20261026'
index=gate/'packed_image_index.sqlite'
assert sha(index)==config['index_sha256']
assert sha(gate/'packed_runtime_coverage.json')==config['coverage_sha256']
reg=json.loads(regfile.read_text())
expected,_=load_cohort(data/'official_multimodal_v2',regfile,
                       data/'official_paired_v1/source_recovery'/reg['extraction_report_file'],
                       root/'Metrics/Results'/reg['approval_file'])
with sqlite3.connect(f'file:{index}?mode=ro&immutable=1',uri=True) as db:
    index_rows=dict(db.execute('SELECT id,sha256 FROM images'))
assert set(index_rows)==expected.keys()
result={}
for split in ('train','validation'):
    frame=pd.DataFrame.from_records((ident,row['6_way_label'],index_rows[ident])
                                    for ident,row in expected.items() if row['split']==split)
    frame.columns=['id','6_way_label','image_sha256']
    result[split]=label_conflicts(frame)
    if split=='train':
        subset=sampled(frame,30000,42)
        result['pilot_class_counts']={int(k):int(v) for k,v in subset['6_way_label'].value_counts().items()}
print(json.dumps(result,indent=2))
