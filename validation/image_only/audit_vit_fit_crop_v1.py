"""Private visual audit of train/validation RGBs with exact hash-matching local files."""
import argparse
import csv
import hashlib
import json
import sqlite3
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageOps, ImageDraw
from torchvision.transforms import functional as TF
from torchvision.transforms import InterpolationMode

root=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(root/'Training/Text + Image/Scripts'))
from usable_cohort_v2 import load_cohort, sha

p=argparse.ArgumentParser()
p.add_argument('output',type=Path)
a=p.parse_args()
a.output.mkdir(exist_ok=True,parents=True,mode=0o700)
data=root/'Pre-processing/Data'
regfile=root/'Metrics/Results/MM_PART1_USABLE_COHORT_REGISTRATION_20261024.json'
reg=json.loads(regfile.read_text())
expected,_=load_cohort(data/'official_multimodal_v2',regfile,
                       data/'official_paired_v1/source_recovery'/reg['extraction_report_file'],
                       root/'Metrics/Results'/reg['approval_file'])
cfg=json.loads((root/'Configuration/Image Only/image_only_vit_resnet_frozen_v1.json').read_text())
index=data/'cloud_recovery/KAGGLE_PACKED_GATE_v2_362643633/urop_mm_packed_gate_20261026/packed_image_index.sqlite'
assert sha(index)==cfg['index_sha256']
with sqlite3.connect(f'file:{index}?mode=ro&immutable=1',uri=True) as db:
    index_rows=dict(db.execute('SELECT id,sha256 FROM images'))
rng=np.random.default_rng(42)
legacy=data/'Legacy Paired Images/images'
records=[]
page=Image.new('RGB',(3*184,12*150),'white')
draw=ImageDraw.Draw(page)
for split in ('train','validation'):
    for cls in range(6):
        ids=np.array([k for k,e in expected.items() if e['split']==split and e['6_way_label']==cls])
        for ix in rng.permutation(len(ids)):
            ident=str(ids[ix])
            source=legacy/(ident+'.jpg')
            if not source.is_file() or sha(source)!=index_rows[ident]:
                continue
            with Image.open(source) as f:
                f.load()
                rgb=f.convert('RGB')
            target=TF.resize(rgb,256,InterpolationMode.BILINEAR)
            crop=TF.center_crop(target,[224,224])
            variants=(rgb,crop,ImageOps.pad(rgb,(224,224),method=Image.Resampling.BILINEAR,color=(124,116,104)))
            for col,im in enumerate(variants):
                page.paste(ImageOps.contain(im,(176,126)),(col*184+4,len(records)*150+19))
            draw.text((4,len(records)*150+2),f'{split} | class {cls} | {rgb.width}x{rgb.height}',fill='black')
            draw.text((190,len(records)*150+2),'256 + center crop',fill='black')
            draw.text((374,len(records)*150+2),'Full-frame pad',fill='black')
            records.append({'split':split,'label':cls,'id':ident,'sha256':index_rows[ident],
                            'width':rgb.width,'height':rgb.height})
            break
page.crop((0,0,page.width,max(150,len(records)*150))).save(a.output/'private_train_val_contact_sheet.png')
with (a.output/'sample_sha256_receipts.csv').open('w',newline='') as stream:
    writer=csv.DictWriter(stream,fieldnames=('split','label','id','sha256','width','height'))
    writer.writeheader()
    writer.writerows(records)
print(json.dumps({'exact_byte_matches_visualized':len(records),'counts':{
    s:sum(x['split']==s for x in records) for s in ('train','validation')}}))
