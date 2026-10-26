"""CPU-only full faculty-image gate for the packed private Kaggle input.

Run as the code of the approved private Kaggle notebook after attaching the
immutable private packed dataset. No model, GPU allocation, or test inference.
"""
import hashlib
import json
import os
from pathlib import Path
import platform
import requests
import subprocess
import sys
import time

REVISION = 'b4378dd4213dec255a82f5400fb26bb4426f59d7'
HASHES = {
    'scripts/verify_packed_usable_input_v3.py': 'ef7ebb081ca33c1a56638a46e112d3099af373bfd0cbc18a9b0b453985c40a2d',
    'scripts/packed_image_io_v3.py': 'ce570b906d8f5bb0c3d1b2d8b7e07f8654589bae3557ed91c9e84cde484cdc30',
    'scripts/usable_cohort_v2.py': '22bff1eb0fa14d102ad07786f936c5c1ed1582ec7bd5cee2b8e8dc5eb3520092',
}
SLUG = 'urop-faculty-usable-packed-input-v3'
BASE = Path('/kaggle/working/urop_mm_packed_gate_20261026')
assert Path('/kaggle/input').is_dir(), 'Kaggle cloud runtime required'
BASE.mkdir(parents=True, exist_ok=True)
SOURCE = BASE / 'gate_source'
for relative, digest in HASHES.items():
    target = SOURCE / relative
    if not target.exists():
        response = requests.get('https://raw.githubusercontent.com/panvenaidu/Fake-News-Detection/' +
                                REVISION + '/' + relative, timeout=45)
        response.raise_for_status()
        if hashlib.sha256(response.content).hexdigest() != digest:
            raise ValueError('Released source SHA mismatch')
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(response.content)
    if hashlib.sha256(target.read_bytes()).hexdigest() != digest:
        raise ValueError('Existing source differs from released version')

candidates = [Path('/kaggle/input') / SLUG,
              Path('/kaggle/input/datasets/rocky62') / SLUG]
roots = [p for p in candidates if (p / 'data/official_paired_v2/paired_manifest.csv').is_file()]
if len(roots) != 1:
    raise ValueError('Exactly one private packed input required; inspect actual mount')
root = roots[0]
print(json.dumps({'state': 'packed_full_image_gate_started', 'input_root': str(root),
                  'source_revision': REVISION, 'required_images': 682170,
                  'cpus': os.cpu_count(), 'python': platform.python_version(),
                  'gpu_training': False, 'test_inference': False}), flush=True)
command = [sys.executable, str(SOURCE / 'scripts/verify_packed_usable_input_v3.py'),
           '--root', str(root), '--output', str(BASE), '--dataset-version', '1']
with (BASE / 'packed_gate_console.log').open('a') as log:
    process = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT)
    while process.poll() is None:
        tail = (BASE / 'packed_gate_console.log').stat().st_size
        print(json.dumps({'state': 'packed_gate_process_alive', 'pid': process.pid,
                          'log_bytes': tail, 'utc_epoch': time.time(),
                          'training': False}), flush=True)
        time.sleep(30)
if process.returncode:
    raise RuntimeError('Packed full gate failed; preserve index/log and inspect failure')
receipt = json.loads((BASE / 'packed_runtime_coverage.json').read_text())
assert receipt['image_gate_passed'] and receipt['usable'] == 682170
print(json.dumps({'state': 'packed_full_image_gate_complete',
                  'index_sha256': receipt['packed_index_sha256'],
                  'verified_images': receipt['usable'], 'training': False}), flush=True)
