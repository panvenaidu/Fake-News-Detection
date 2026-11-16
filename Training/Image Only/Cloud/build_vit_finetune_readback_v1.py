"""CPU readback notebook for a specific completed private Kaggle version."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import zlib

from build_vit_finetune_notebook_v1 import ROOT

FILES = [
    'Testing/Image Only/verify_vit_finetune_v1.py',
    'Model/Image Only/frozen_image_pair_v1.py',
    'Configuration/Image Only/image_only_vit_resnet_frozen_v1.json',
    'Training/Text + Image/Scripts/usable_cohort_v2.py',
    'Training/Text + Image/Scripts/packed_image_io_v3.py',
]
ENTRY = """
import base64, hashlib, json, sys, zlib
from pathlib import Path
source=Path('/tmp/urop_vit_finetune_readback_source')
source.mkdir(exist_ok=True)
for name,(digest,body) in json.loads(zlib.decompress(base64.b64decode(PAYLOAD))).items():
    raw=base64.b64decode(body)
    if hashlib.sha256(raw).hexdigest()!=digest:
        raise RuntimeError('Readback source hash changed: '+name)
    (source/name).write_bytes(raw)
sys.path.insert(0,str(source))
from verify_vit_finetune_v1 import report, verify, require
from frozen_image_pair_v1 import load_verified
from packed_image_io_v3 import sha
mount=Path('/kaggle/input')
frozen=[path for path in mount.glob('**/urop_vit_finetune/test_saved.json')
        if TEST_RECEIPT_SHA is None or sha(path)==TEST_RECEIPT_SHA]
require(len(frozen)==1,'Attach exactly the registered completed test output')
_, _, frames, _ = load_verified(mount,json.loads((source/'image_only_vit_resnet_frozen_v1.json').read_text()))
baselines=[]
if COMPARE_HISTORICAL_RESNET:
    digest='ca2c8afb877146b2ae892e60a03f114acd8cb184d2d6e1cd861c2f65b5eb41d3'
    matches=[p for p in mount.glob('**/OFFICIAL-6W-IMAGE-USABLE-v1_seed42_20261102T145600Z/run/test_predictions.csv')
             if sha(p)==digest]
    require(len(matches)==1,'Mount the privately saved historical ResNet-50 version 364917396')
    baselines.append(('Historical ResNet-50', matches[0], digest, .8115572802429559))
if COMPARE_FROZEN_VIT:
    digest='f18c3c15732de40b034047b788a04420b71a68cff315125df45a71177561e6b3'
    matches=[p for p in mount.glob('**/urop_frozen_pair/vit/test_predictions.csv')
             if sha(p)==digest]
    require(len(matches)==1,'Mount the privately saved frozen ViT version 369302248')
    baselines.append(('Frozen ViT-B/16', matches[0], digest, .6564872616838198))
proof=verify(frozen[0].parent,baseline_specs=baselines,official_frames=frames,source_version=str(VERSION_ID))
out=Path('/kaggle/working')
(out/'VIT_FINETUNE_REOPENED_VERIFICATION.json').write_text(json.dumps(proof,indent=2,allow_nan=False)+'\\n')
(out/'VIT_FINETUNE_REOPENED_REPORT.md').write_text(report(proof))
print(json.dumps({'source_version':VERSION_ID,'test':proof['test']['metrics'],
                  'no_train_hash':proof['no_train_hash']['metrics'],
                  'target_reached':proof['target_reached']},indent=2),flush=True)
"""

if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('version_id',type=int)
    ap.add_argument('output',type=Path)
    ap.add_argument('--test-receipt-sha256')
    ap.add_argument('--notebook-output',type=Path)
    ap.add_argument('--compare-historical-resnet', action='store_true')
    ap.add_argument('--compare-frozen-vit', action='store_true')
    a=ap.parse_args()
    sources={}
    for f in FILES:
        body=(ROOT/f).read_bytes()
        sources[Path(f).name]=(hashlib.sha256(body).hexdigest(),base64.b64encode(body).decode())
    data=base64.b64encode(zlib.compress(json.dumps(sources).encode(),9)).decode()
    cell=(f'VERSION_ID = {a.version_id}\nTEST_RECEIPT_SHA = {a.test_receipt_sha256!r}\n'
          f'COMPARE_HISTORICAL_RESNET = {a.compare_historical_resnet!r}\n'
          f'COMPARE_FROZEN_VIT = {a.compare_frozen_vit!r}\nPAYLOAD = (\n')+''.join(f'    {data[i:i+1024]!r}\n' for i in range(0,len(data),1024))+')\n'+ENTRY
    compile(cell,'<readback>','exec')
    a.output.write_text(cell)
    if a.notebook_output:
        versions = [362643633, a.version_id]
        if a.compare_historical_resnet:
            versions.append(364917396)
        if a.compare_frozen_vit:
            versions.append(369302248)
        inputs = [{'sourceType':'datasetVersion','sourceId':21277535}]
        inputs.extend({'sourceType':'kernelVersion','sourceId':v} for v in versions)
        notebook = {
            'cells':[{'cell_type':'code','metadata':{},'execution_count':None,
                      'outputs':[],'source':cell.splitlines(keepends=True)}],
            'metadata':{
                'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'},
                'kaggle':{'accelerator':'none','isInternetEnabled':False,'language':'python',
                          'sourceType':'notebook','dataSources':inputs},
            },
            'nbformat':4,'nbformat_minor':4,
        }
        a.notebook_output.write_text(json.dumps(notebook,indent=1)+'\n')
