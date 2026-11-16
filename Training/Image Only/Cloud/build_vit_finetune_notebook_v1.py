"""Build a source-pinned Kaggle cell and importable notebook without credentials."""
import argparse
import ast
import base64
import hashlib
import json
from pathlib import Path
import zlib

ROOT = Path(__file__).resolve().parents[3]
FILES = [
    'Configuration/Image Only/image_only_vit_finetune_v1.json',
    'Configuration/Image Only/image_only_vit_resnet_frozen_v1.json',
    'Configuration/Image Only/vit_finetune_candidate_deit3_v1.json',
    'Model/Image Only/train_vit_finetune_v1.py',
    'Model/Image Only/frozen_image_pair_v1.py',
    'Training/Image Only/Cloud/vit_finetune_cloud_v1.py',
    'Training/Image Only/Cloud/vit_finetune_control_v1.py',
    'Training/Text + Image/Scripts/packed_image_io_v3.py',
    'Training/Text + Image/Scripts/usable_cohort_v2.py',
]
ENTRY = """from pathlib import Path
import base64, hashlib, json, sys, zlib
source = Path('/tmp/urop_vit_finetune_source')
source.mkdir(exist_ok=True)
for name, (digest, body) in json.loads(zlib.decompress(base64.b64decode(PAYLOAD))).items():
    raw=base64.b64decode(body)
    if hashlib.sha256(raw).hexdigest()!=digest:
        raise RuntimeError('Embedded source hash changed: '+name)
    (source/name).write_bytes(raw)
sys.path.insert(0, str(source))
from vit_finetune_cloud_v1 import start
start(source, Path('/kaggle/working/urop_vit_finetune'), **SETTINGS)
"""


def read_locked_payload(notebook_path):
    """Read and verify the embedded source without executing notebook cells."""
    notebook = json.loads(notebook_path.read_text())
    code = [cell for cell in notebook['cells'] if cell['cell_type'] == 'code']
    if len(code) != 1:
        raise ValueError('Expected the registered single-cell ViT notebook')
    tree = ast.parse(''.join(code[0]['source']))
    payload = [node.value for node in tree.body if isinstance(node, ast.Assign)
               and any(isinstance(t, ast.Name) and t.id == 'PAYLOAD' for t in node.targets)]
    if len(payload) != 1:
        raise ValueError('Expected one literal source payload')
    encoded = ast.literal_eval(payload[0])
    sources = json.loads(zlib.decompress(base64.b64decode(encoded)))
    if set(sources) != {Path(name).name for name in FILES}:
        raise ValueError('Registered notebook source inventory differs')
    for name, (digest, body) in sources.items():
        if hashlib.sha256(base64.b64decode(body)).hexdigest() != digest:
            raise ValueError(f'Registered source hash differs for {name}')
    return encoded


RECOVERY_GUARD = """# Verify the paused training state before the controller copies any input.
from pathlib import Path
import hashlib
import json

matches = [
    path for path in Path('/kaggle/input').glob('**/urop_vit_finetune/sessions.json')
    if hashlib.sha256(path.read_bytes()).hexdigest() == SESSIONS_SHA
]
if len(matches) != 1:
    raise RuntimeError('Mount the checkpointed training version identified by its session receipt')
recovery = matches[0].parent
sessions = json.loads(matches[0].read_text())
if (sessions[-1]['state'] != 'paused' or not (recovery/'registration.json').is_file()
        or not any(recovery.glob('*/resume.pt'))):
    raise RuntimeError('Mounted output is missing the paused training registration or checkpoints')
SETTINGS['recovery'] = str(recovery)
"""


def build(settings, source_notebook=None, recovery_version_id=None, sessions_sha=None):
    if sessions_sha and (settings['mode'] != 'train' or source_notebook is None
                         or recovery_version_id is None):
        raise ValueError('A paused continuation requires train mode, the locked notebook, and the saved version ID')
    if source_notebook is not None:
        data = read_locked_payload(source_notebook)
    else:
        sources = {}
        for rel in FILES:
            path = ROOT / rel
            body = path.read_bytes()
            sources[path.name] = (hashlib.sha256(body).hexdigest(), base64.b64encode(body).decode())
        data = base64.b64encode(zlib.compress(json.dumps(sources).encode(), 9)).decode()
    inputs = [{'sourceType': 'datasetVersion', 'sourceId': 21277535},
              {'sourceType': 'kernelVersion', 'sourceId': 362643633}]
    if recovery_version_id is not None:
        inputs.append({'sourceType': 'kernelVersion', 'sourceId': recovery_version_id})
    recovery_guard = f'SESSIONS_SHA = {sessions_sha!r}\n' + RECOVERY_GUARD if sessions_sha else ''
    cell = ('# Private UROP ViT-B/16; immutable source and invocation settings.\n'
            + f'SETTINGS = {settings!r}\nPAYLOAD = (\n'
            + ''.join(f'    {data[i:i+1024]!r}\n' for i in range(0,len(data),1024)) + ')\n'+recovery_guard+ENTRY)
    compile(cell,'<kaggle-v1>','exec')
    notebook={'cells':[{'cell_type':'code','metadata':{},'source':cell.splitlines(True),
                        'execution_count':None,'outputs':[]}],
              'metadata':{'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'},
                          'kaggle':{'accelerator':'nvidiaTeslaT4','isInternetEnabled':True,
                                    'language':'python','sourceType':'notebook',
                                    'dataSources': inputs}},
              'nbformat':4,'nbformat_minor':4}
    return cell,notebook


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--mode',choices=['preflight','train','test'],default='preflight')
    p.add_argument('--world',type=int,default=2)
    p.add_argument('--quota-used-minutes',type=float,default=0)
    p.add_argument('--accounting-multiplier',type=int,default=1)
    p.add_argument('--stop-after-seconds',type=int)
    p.add_argument('--recovery')
    p.add_argument('--expected-recovery-sha256')
    p.add_argument('--source-notebook', type=Path)
    p.add_argument('--recovery-version-id', type=int)
    p.add_argument('--paused-sessions-sha256')
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    d=vars(a).copy()
    output=d.pop('output')
    source_notebook = d.pop('source_notebook')
    recovery_version_id = d.pop('recovery_version_id')
    sessions_sha = d.pop('paused_sessions_sha256')
    cell,notebook=build(d, source_notebook, recovery_version_id, sessions_sha)
    output.write_text(json.dumps(notebook,indent=1)+'\n')
    output.with_suffix('.txt').write_text(cell)
