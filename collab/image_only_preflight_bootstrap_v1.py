"""Prepare exact source for an image-only preflight in an owned Kaggle notebook.

Requires SOURCE_COMMIT and SOURCE_HASHES supplied by the generated notebook.
"""
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import subprocess
import sys
import requests


def main(commit, hashes, audit):
    base = Path('/kaggle/working/urop_image_only_preflight_v1')
    source = base / 'source'
    base.mkdir(parents=True, exist_ok=False)
    for relative, digest in hashes.items():
        target = source / relative
        response = requests.get('https://raw.githubusercontent.com/panvenaidu/Fake-News-Detection/' + commit + '/' + relative, timeout=60)
        response.raise_for_status()
        assert hashlib.sha256(response.content).hexdigest() == digest, relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(response.content)
    # Restore the already used research dependency if the Kaggle base differs.
    if importlib.metadata.version('transformers') != '4.48.3':
        subprocess.run([sys.executable, '-m', 'pip', '-q', 'install', 'transformers==4.48.3'], check=True, timeout=600)
    def matching(name, digest):
        matches = [p for p in Path('/kaggle/input').rglob(name) if p.is_file() and hashlib.sha256(p.read_bytes()).hexdigest() == digest]
        assert matches, 'Missing exact ' + name
        return min(matches, key=lambda p: (len(p.parts), str(p)))
    coverage = matching('packed_runtime_coverage.json', 'afe8c723f91fe74f791908e0c16fab94d919af64c7cb7c9b5a37e676361d95e5')
    index = matching('packed_image_index.sqlite', 'fc8dc03a4f773da5762891c8392375add5fb8087251b527f3b37a880308e6018')
    meta = json.loads(coverage.read_text())
    root = Path(meta['runtime_root'])
    assert root.is_dir() and meta['dataset_version'] == 1
    audit_path = base / 'startup_audit.json'
    audit_path.write_text(json.dumps(audit, indent=2) + '\n')
    environment = dict(os.environ, CUDA_VISIBLE_DEVICES='0', CUBLAS_WORKSPACE_CONFIG=':4096:8',
                       PYTHONPATH=str(source / 'scripts'), PYTHONDONTWRITEBYTECODE='1')
    command = [sys.executable, '-u', str(source / 'collab/image_only_gpu_preflight_v1.py'),
               '--root', str(root), '--coverage', str(coverage), '--index', str(index),
               '--config', str(source / 'configs/image_only_usable_6way_v1.json'),
               '--output', str(base / 'evidence'), '--audit', str(audit_path)]
    print('IMAGE_ONLY_PREFLIGHT_LAUNCH', json.dumps({'source_commit': commit, 'command': command}), flush=True)
    subprocess.run(command, env=environment, check=True, timeout=6000)
    print('PRIVATE_PREFLIGHT_READY_FOR_SAVED_READBACK', flush=True)
