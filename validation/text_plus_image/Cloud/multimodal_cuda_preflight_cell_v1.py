"""Short disposable CUDA engineering check through authorized Chrome notebook.
No faculty data, Drive mount, credentials, paid services, or scientific training.
Stop the GPU session through the notebook UI after retrieving the receipt.
"""
import hashlib
import importlib.metadata
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import urllib.request

SOURCE_COMMIT = '1c2634d5008437a7e697759ed462c0ebd087d366'
SOURCE_FILES = {'scripts/train_official_multimodal_v1.py': 'e0e2ace518f8232ca250c7185b89b56a645c12125666630cace4a2876e520026', 'scripts/multimodal_recovery_v1.py': '2f5f67ce79289c69279040d21b483e28535895f5c99c63e0021da3eee6d3d1c8', 'scripts/check_multimodal_cuda_v1.py': 'cb8bf1c28d1d2bee547eb9bfbb27f9a8171cbf6e1f684444eb59e3a98c665244', 'configs/multimodal_official_6way_v1.json': '19e3c78288aa7a5eb7ee657900583a3cb2984637354fc43b742302816aea049b'}
ROOT = (Path('/kaggle/working') if Path('/kaggle/working').is_dir() else Path('/content')) / 'urop_mm_preflight'
ROOT.mkdir(parents=True, exist_ok=True)
os.environ['CUDA_VISIBLE_DEVICES'] = '0'
for relative, digest in SOURCE_FILES.items():
    target = ROOT / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    data = urllib.request.urlopen('https://raw.githubusercontent.com/panvenaidu/Fake-News-Detection/' + SOURCE_COMMIT + '/' + relative, timeout=60).read()
    if hashlib.sha256(data).hexdigest() != digest:
        raise RuntimeError('Pinned source checksum mismatch: ' + relative)
    target.write_bytes(data)
try:
    transformers_version = importlib.metadata.version('transformers')
except importlib.metadata.PackageNotFoundError:
    transformers_version = None
if transformers_version != '4.48.3':
    subprocess.check_call([sys.executable, '-m', 'pip', '-q', 'install', 'transformers==4.48.3'])
for package, module in [('pandas', 'pandas'), ('scikit-learn', 'sklearn')]:
    if importlib.util.find_spec(module) is None:
        subprocess.check_call([sys.executable, '-m', 'pip', '-q', 'install', package])
import torch
if not torch.cuda.is_available():
    raise RuntimeError('CUDA unavailable: stop here, do not run a CPU substitute')
print(json.dumps({'state': 'synthetic_cuda_engineering_check_started', 'gpu': torch.cuda.get_device_name(0), 'used_devices': 1, 'torch': torch.__version__, 'source_commit': SOURCE_COMMIT, 'official_data_used': False}), flush=True)
receipt = ROOT / 'cuda_engineering_receipt.json'
subprocess.check_call([sys.executable, str(ROOT / 'scripts/check_multimodal_cuda_v1.py'), '--config', str(ROOT / 'configs/multimodal_official_6way_v1.json'), '--output', str(receipt)], cwd=ROOT)
print('UROP_CUDA_RECEIPT_BEGIN', flush=True)
print(receipt.read_text(), flush=True)
print('UROP_CUDA_RECEIPT_END', flush=True)
