"""Build an importable private Kaggle notebook with a hash-checked source bundle."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import zlib

ROOT = Path(__file__).resolve().parents[3]
LOCAL = Path(__file__).resolve().parent
SOURCES = (
    'Configuration/Image Only/image_only_vit_finetune_v1.json',
    'Configuration/Image Only/image_only_vit_resnet_frozen_v1.json',
    'Configuration/Image Only/vit_finetune_candidate_deit3_v1.json',
    'Model/Image Only/train_vit_finetune_v1.py',
    'Model/Image Only/frozen_image_pair_v1.py',
    'Training/Image Only/Cloud/vit_finetune_cloud_v1.py',
    'Training/Image Only/Cloud/vit_finetune_control_v1.py',
    'Training/Text + Image/Scripts/packed_image_io_v3.py',
    'Training/Text + Image/Scripts/usable_cohort_v2.py',
)
ENTRY = """
import base64, hashlib, json, sys, zlib
from pathlib import Path

source = Path('/tmp/urop_vit83_source')
source.mkdir(exist_ok=True)
for name, (digest, body) in json.loads(zlib.decompress(base64.b64decode(PAYLOAD))).items():
    raw = base64.b64decode(body)
    if hashlib.sha256(raw).hexdigest() != digest:
        raise ValueError(f'Embedded source hash differs for {name}')
    (source/name).write_bytes(raw)
sys.path.insert(0, str(source))
"""
TRAIN = """
from vit83 import cloud
cloud(source, Path('/kaggle/working/urop_vit83'), **SETTINGS)
"""
VERIFY = """
from vit83_verify import verify_retained, verify_saved
verify = verify_retained if SETTINGS.pop('validation_only') else verify_saved
verify(source, Path('/kaggle/input'), Path('/kaggle/working'), **SETTINGS)
"""


def build(mode, quota_used_minutes, recovery_version, recovery_sha):
    sources = [ROOT / name for name in SOURCES]
    cpu = mode in ('verify', 'verify-retained')
    if cpu:
        sources += [LOCAL/'vit83_verify.py', ROOT/'Testing/Image Only/verify_vit_finetune_v1.py']
    else:
        sources += [LOCAL/'vit83.py', LOCAL/'vit83_control.py']
    bundle = {}
    for file in sources:
        raw = file.read_bytes()
        bundle[file.name] = [hashlib.sha256(raw).hexdigest(), base64.b64encode(raw).decode()]
    encoded = base64.b64encode(zlib.compress(json.dumps(bundle).encode(), 9)).decode()
    payload = ''.join(f'    {encoded[i:i+1024]!r}\n' for i in range(0, len(encoded), 1024))
    settings = ({'mode': mode, 'quota_used_minutes': quota_used_minutes, 'recovery_sha': recovery_sha}
                if not cpu else {'version': recovery_version, 'receipt_sha': recovery_sha,
                                 'validation_only': mode == 'verify-retained'})
    cell = f'# UROP private image-only 83% Vision Transformer study\nSETTINGS = {settings!r}\nPAYLOAD = (\n{payload})\n'
    cell += ENTRY + (VERIFY if cpu else TRAIN)
    compile(cell, '<kaggle-vit83>', 'exec')
    versions = [362643633]
    if recovery_version:
        versions.append(recovery_version)
    if mode == 'verify':
        versions.extend([364917396, 369892645])
    inputs = [{'sourceType': 'datasetVersion', 'sourceId': 21277535},
              *[{'sourceType': 'kernelVersion', 'sourceId': v} for v in versions]]
    notebook = {'cells': [{'cell_type': 'code', 'metadata': {}, 'source': cell.splitlines(True),
                           'outputs': [], 'execution_count': None}],
                'metadata': {'kernelspec': {'display_name': 'Python 3', 'language': 'python', 'name': 'python3'},
                             'kaggle': {'accelerator': 'none' if cpu else 'nvidiaTeslaT4',
                                        'isInternetEnabled': mode in ('preflight', 'train'),
                                        'language': 'python', 'sourceType': 'notebook', 'dataSources': inputs}},
                'nbformat': 4, 'nbformat_minor': 4}
    return notebook, cell


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('mode', choices=('preflight', 'train', 'test', 'verify', 'verify-retained'))
    p.add_argument('output', type=Path)
    p.add_argument('--quota-used-minutes', type=float)
    p.add_argument('--recovery-version', type=int)
    p.add_argument('--recovery-sha')
    args = p.parse_args()
    if args.mode != 'preflight' and not (args.recovery_version and args.recovery_sha):
        p.error('Supply the exact saved version and receipt hash')
    if args.mode in ('preflight', 'train', 'test') and args.quota_used_minutes is None:
        p.error('Supply the observed free GPU quota usage in minutes')
    notebook, cell = build(args.mode, args.quota_used_minutes, args.recovery_version, args.recovery_sha)
    args.output.write_text(json.dumps(notebook, indent=1) + '\n')
    args.output.with_suffix('.txt').write_text(cell)
