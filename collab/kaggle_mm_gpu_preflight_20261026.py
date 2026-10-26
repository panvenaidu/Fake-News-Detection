"""Actual registered-source CUDA fixture and600s train-only timing, no experiment.

Execute only after the CPU full-image receipt has been independently preserved
and this notebook is allocated a GPU. Never launches scientific training/test.
"""
from pathlib import Path
import hashlib
import importlib.metadata
import json
import os
import requests
import subprocess
import sys
import time

os.environ['CUDA_VISIBLE_DEVICES'] = '0'
os.environ['CUBLAS_WORKSPACE_CONFIG'] = ':4096:8'
import torch
assert torch.cuda.is_available() and torch.cuda.device_count() == 1, 'One used cloud CUDA device required'
BASE = Path('/kaggle/working/urop_mm_part1_20261026')
COVERAGE = BASE / 'runtime_image_gate.json'
coverage = json.loads(COVERAGE.read_text())
assert coverage['image_gate_passed'] and coverage['runtime_image_bytes_verified'] and coverage['usable'] == 682170
ROOT = Path(coverage['runtime_root'])
assert ROOT.is_relative_to('/kaggle/input') and ROOT.is_dir()
SOURCE = BASE / 'registered_source'
COMMIT = '5aa5c87a2620b3c7763401e845dad45a935dd621'
HASHES = {
    'scripts/train_usable_multimodal_v2.py': '88412d918b77f8a54569b25a8c469618c028ebaeeeb0b6050385dc55bd20ac1e',
    'scripts/multimodal_recovery_v1.py': '2f5f67ce79289c69279040d21b483e28535895f5c99c63e0021da3eee6d3d1c8',
    'scripts/usable_cohort_v2.py': '22bff1eb0fa14d102ad07786f936c5c1ed1582ec7bd5cee2b8e8dc5eb3520092',
    'scripts/verify_usable_multimodal_v2.py': 'bc314502833835a42bba8bab2d069074018bafc807106a3eb503386e2671139b',
    'scripts/check_usable_multimodal_cuda_v2.py': '0317d959710522a6b69f97f059ea78b23f41042e5c0500f934f3f0d4a048e8f6',
    'configs/multimodal_usable_6way_v2.json': 'ad8f86f86b1fef453ae3bccda0aeb13cc50b298dc0d5d502f87c9ac4b041b483',
    'collab/measure_usable_multimodal_preflight_v2.py': 'e8a3b4f4826d9de2549b369588ce578d71a79fa9fb51a87a0e75c0a782fd4dab',
}


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(4 * 1024**2), b''):
            digest.update(block)
    return digest.hexdigest()


for relative, expected in HASHES.items():
    path = SOURCE / relative
    if not path.exists():
        response = requests.get('https://raw.githubusercontent.com/panvenaidu/Fake-News-Detection/' + COMMIT + '/' + relative, timeout=45)
        response.raise_for_status()
        assert hashlib.sha256(response.content).hexdigest() == expected
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(response.content)
    assert sha(path) == expected, 'Preserve conflicting scientific source'

try:
    transformers_version = importlib.metadata.version('transformers')
except importlib.metadata.PackageNotFoundError:
    transformers_version = None
if transformers_version != '4.48.3':
    subprocess.run([sys.executable, '-m', 'pip', '-q', 'install', 'transformers==4.48.3'], check=True, timeout=600)

config = SOURCE / 'configs/multimodal_usable_6way_v2.json'
text_roots = [Path('/kaggle/input/urop-official-six-way-text-recovery'),
              Path('/kaggle/input/notebooks/rocky62/urop-official-six-way-text-recovery')]
weights = [p for parent in text_roots if parent.is_dir() for p in parent.rglob('best_weights.pt')]
assert len(weights) == 1, 'Inspect the attached completed text output; never substitute another checkpoint'
warmstart = weights[0]
assert sha(warmstart) == '870bea50fa608dddd20421c21fd1786e244b1323e22734093214b87023666753'
print(json.dumps({'state': 'actual_gpu_preflight_started', 'gpu': torch.cuda.get_device_name(0),
                  'torch': torch.__version__, 'cuda': torch.version.cuda,
                  'warmstart_verified': True, 'scientific_training': False}), flush=True)

fixture = BASE / 'actual_cuda_fixture.json'
command = [sys.executable, str(SOURCE / 'scripts/check_usable_multimodal_cuda_v2.py'),
           '--config', str(config), '--output', str(fixture)]
with (BASE / 'actual_cuda_fixture.log').open('a') as log:
    subprocess.run(command, cwd=SOURCE, stdout=log, stderr=subprocess.STDOUT, check=True, timeout=1800)
assert json.loads(fixture.read_text())['status'] == 'passed_cuda_engineering_fixture'
print('ACTUAL_CUDA_RECOVERY_FIXTURE_PASSED', flush=True)

preflight = BASE / ('disposable_preflight_' + str(int(time.time())))
command = [sys.executable, str(SOURCE / 'collab/measure_usable_multimodal_preflight_v2.py'),
           '--root', str(ROOT), '--coverage', str(COVERAGE), '--config', str(config),
           '--output', str(preflight), '--warmstart', str(warmstart),
           '--cuda-fixture', str(fixture), '--seconds', '600', '--eval-seconds', '60']
with (BASE / 'measured_gpu_preflight.log').open('a') as log:
    subprocess.run(command, cwd=SOURCE, stdout=log, stderr=subprocess.STDOUT, check=True, timeout=7200)
result = json.loads((preflight / 'measured_preflight.json').read_text())
assert result['status'] == 'passed_measured_multimodal_preflight'
epoch = 563601 / result['train_examples_per_second'] + 59299 / result['eval_path_examples_per_second'] + result['checkpoint_seconds']
summary = {'state': 'gpu_preflight_verified', 'fixture': str(fixture),
           'fixture_sha256': sha(fixture), 'throughput': str(preflight / 'measured_preflight.json'),
           'throughput_sha256': sha(preflight / 'measured_preflight.json'),
           'coverage': str(COVERAGE), 'coverage_sha256': sha(COVERAGE),
           'input_root': str(ROOT), 'warmstart': str(warmstart),
           'estimated_epoch_seconds': epoch,
           'estimated_two_epochs_with20percent_margin_seconds': 2.4 * epoch,
           'versions': result['versions'], 'gpu': result['device'],
           'scientific_epochs_completed': 0, 'full_validations_completed': 0,
           'test_performed': False}
(BASE / 'GPU_PREFLIGHT_SUMMARY.json').write_text(json.dumps(summary, indent=2) + '\n')
print(json.dumps(summary), flush=True)
