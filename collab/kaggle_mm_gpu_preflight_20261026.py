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
print(json.dumps({'state': 'cuda_runtime_observation', 'torch': torch.__version__,
                  'cuda': torch.version.cuda, 'visible_devices': os.environ['CUDA_VISIBLE_DEVICES'],
                  'available': torch.cuda.is_available(), 'visible_count': torch.cuda.device_count()}), flush=True)
assert torch.cuda.is_available() and torch.cuda.device_count() == 1, 'One used cloud CUDA device required'
BASE = Path('/kaggle/working/urop_mm_part1_20261026')
COVERAGE_CANDIDATES = list(Path('/kaggle/input').rglob('packed_runtime_coverage.json'))
assert len(COVERAGE_CANDIDATES) == 1, 'Attach exactly one saved full packed-image gate output'
COVERAGE = COVERAGE_CANDIDATES[0]
coverage = json.loads(COVERAGE.read_text())
assert coverage['image_gate_passed'] and coverage['runtime_image_bytes_verified'] and coverage['usable'] == 682170 and coverage['input_layout'] == 'kaggle-packed-bin'
PACKED_INDEX = COVERAGE.with_name('packed_image_index.sqlite')
assert PACKED_INDEX.is_file()
ROOT = Path(coverage['runtime_root'])
assert ROOT.is_relative_to('/kaggle/input') and ROOT.is_dir()
SOURCE = BASE / 'registered_source'
COMMIT = '1b22467fc4d404e172e3d938f44e7d37e345e4bc'
HASHES = {
    'scripts/train_usable_multimodal_v2.py': '7f7fb90deb08a5901d1ca8343b780f6d82dd42b3e278d51f333568435becee0e',
    'scripts/packed_image_io_v3.py': '2a661546aab7969ae80329eff66d9667496c4e5db91d7b20993d168f70ee0b57',
    'scripts/multimodal_recovery_v1.py': '2f5f67ce79289c69279040d21b483e28535895f5c99c63e0021da3eee6d3d1c8',
    'scripts/usable_cohort_v2.py': '22bff1eb0fa14d102ad07786f936c5c1ed1582ec7bd5cee2b8e8dc5eb3520092',
    'scripts/verify_usable_multimodal_v2.py': 'bc314502833835a42bba8bab2d069074018bafc807106a3eb503386e2671139b',
    'scripts/check_usable_multimodal_cuda_v2.py': '0317d959710522a6b69f97f059ea78b23f41042e5c0500f934f3f0d4a048e8f6',
    'configs/multimodal_usable_6way_v2.json': 'ad8f86f86b1fef453ae3bccda0aeb13cc50b298dc0d5d502f87c9ac4b041b483',
    'collab/measure_usable_multimodal_preflight_v2.py': '65f1a8dac090bb867b3e5abec16ac1c44a8c7c7bd96ae1bb6483aa80ff5e48d3',
}


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(4 * 1024**2), b''):
            digest.update(block)
    return digest.hexdigest()


assert sha(PACKED_INDEX) == coverage['packed_index_sha256'], 'Packed index changed after full gate'
assert sha(PACKED_INDEX) == 'fc8dc03a4f773da5762891c8392375add5fb8087251b527f3b37a880308e6018', 'Wrong saved gate index'
assert sha(COVERAGE) == 'afe8c723f91fe74f791908e0c16fab94d919af64c7cb7c9b5a37e676361d95e5', 'Attach verified saved gate version 362643633'


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
prior_fixture = Path('/kaggle/input/notebooks/rocky62/urop-mm-part1-packed-gpu-20261026/urop_mm_part1_20261026/actual_cuda_fixture.json')
assert sha(prior_fixture) == '8b0f6399d249cdf1e4263923c2515a1e99abcceb9d3a5a066a1034a964a26c63'
proof = json.loads(prior_fixture.read_text())
assert proof['torch'] == torch.__version__ and proof['cuda'] == torch.version.cuda and proof['device'] == torch.cuda.get_device_name(0)
fixture.write_bytes(prior_fixture.read_bytes())
assert json.loads(fixture.read_text())['status'] == 'passed_cuda_engineering_fixture'
print('ACTUAL_CUDA_RECOVERY_FIXTURE_PASSED', flush=True)

preflight = BASE / ('disposable_preflight_' + str(int(time.time())))
command = [sys.executable, str(SOURCE / 'collab/measure_usable_multimodal_preflight_v2.py'),
           '--root', str(ROOT), '--coverage', str(COVERAGE), '--packed-index', str(PACKED_INDEX), '--config', str(config),
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
           'packed_index': str(PACKED_INDEX), 'packed_index_sha256': sha(PACKED_INDEX),
           'input_root': str(ROOT), 'warmstart': str(warmstart),
           'estimated_epoch_seconds': epoch,
           'estimated_two_epochs_with20percent_margin_seconds': 2.4 * epoch,
           'versions': result['versions'], 'gpu': result['device'],
           'runtime_reader_sha256': HASHES['scripts/packed_image_io_v3.py'],
           'index_cache_policy': 'Exact SHA local index and in-memory metadata; retain all39 verified archive handles; raw byte SHA checked on every image',
           'scientific_epochs_completed': 0, 'full_validations_completed': 0,
           'test_performed': False}
(BASE / 'GPU_PREFLIGHT_SUMMARY.json').write_text(json.dumps(summary, indent=2) + '\n')
print(json.dumps(summary), flush=True)
