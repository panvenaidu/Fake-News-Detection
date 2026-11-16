"""Owned notebook CPU gate for the completed immutable private Kaggle input.
Runs integrity checks only; no model, training, validation or test inference.
"""
from pathlib import Path
import hashlib
import importlib.util
import json
import os
import platform
import requests
import sys
import time

REVISION = '367b75bd571498c496fed4c51307398f19f2239a'
HASHES = {
    'scripts/verify_usable_image_shards_v2.py': 'f8147134fab8c331dbf2bdf7701a68594c682732bbdd01e0c0083a8e6a399a23',
    'scripts/usable_cohort_v2.py': '22bff1eb0fa14d102ad07786f936c5c1ed1582ec7bd5cee2b8e8dc5eb3520092',
    'collab/prepare_official_images_drive_v1.py': '543c60d78d61182b10052cfd061d90c5bb764f99138a8bc09ae72dbfe93d7354',
}
SLUG = 'urop-faculty-usable-image-transport-v2'
base = Path('/kaggle/working/urop_mm_part1_20261026')
assert Path('/kaggle/input').is_dir(), 'Cloud Kaggle runtime required'
base.mkdir(parents=True, exist_ok=True)
source = base / 'gate_source'
for relative, expected in HASHES.items():
    path = source / relative
    if not path.exists():
        response = requests.get('https://raw.githubusercontent.com/panvenaidu/Fake-News-Detection/' + REVISION + '/' + relative, timeout=45)
        response.raise_for_status()
        assert hashlib.sha256(response.content).hexdigest() == expected
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(response.content)
    assert hashlib.sha256(path.read_bytes()).hexdigest() == expected

candidates = [Path('/kaggle/input') / SLUG,
              Path('/kaggle/input/datasets/rocky62') / SLUG]
roots = [p for p in candidates if (p / 'data/official_paired_v2/paired_manifest.csv').is_file()]
assert len(roots) == 1, 'Expected exactly one attached private faculty input; inspect actual paths'
root = roots[0]
sys.path.insert(0, str(source / 'scripts'))
spec = importlib.util.spec_from_file_location('runtime_image_gate', source / 'scripts/verify_usable_image_shards_v2.py')
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)
receipt = base / 'runtime_image_gate.json'
print(json.dumps({'state': 'full_private_input_gate_started', 'pid': os.getpid(),
                  'utc_epoch': time.time(), 'input_root': str(root),
                  'dataset': 'rocky62/' + SLUG, 'observed_saved_version': 1,
                  'cpus': os.cpu_count(), 'python': platform.python_version(),
                  'required_images': 682170, 'training': False,
                  'test_inference': False}), flush=True)
if receipt.exists():
    prior = json.loads(receipt.read_text())
    assert prior['runtime_root'] == str(root.resolve())
    assert prior['image_gate_passed'] and prior['runtime_image_bytes_verified']
    assert prior['usable'] == 682170 and prior['verifier_sha256'] == HASHES['scripts/verify_usable_image_shards_v2.py']
    assert hashlib.sha256((root / 'data/official_paired_v2/paired_manifest.csv').read_bytes()).hexdigest() == prior['manifest_sha256']
    print('EXISTING_IMMUTABLE_INPUT_GATE_REUSED', flush=True)
else:
    gate.verify_unpacked(root, receipt, workers=min(4, os.cpu_count() or 1))
print('FULL_INPUT_GATE_COMPLETE', flush=True)
