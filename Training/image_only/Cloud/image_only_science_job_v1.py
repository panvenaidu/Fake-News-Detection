"""A bounded private Kaggle job for the single approved image-only experiment.

Read back saved preflight and prior recovery before release. Never duplicate a trainer.
Source/config are copied from the accepted preflight, without scientific edits.
"""
import gc
import hashlib
import importlib.metadata
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        while block := stream.read(4 * 1024**2):
            h.update(block)
    return h.hexdigest()


def write(path, value):
    temporary = Path(path).with_suffix('.tmp')
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')
    os.replace(temporary, path)


def matching(name, digest=None):
    paths = [p for p in Path('/kaggle/input').rglob(name) if p.is_file() and (digest is None or sha(p) == digest)]
    assert paths, 'Missing verified saved input ' + name
    if digest is None:
        assert len({sha(p) for p in paths}) == 1, 'Ambiguous saved input ' + name
    return min(paths, key=lambda p: (len(p.parts), str(p)))


def check_manifest(root, manifest):
    for relative, record in manifest['files'].items():
        file = (root / relative).resolve()
        assert file.is_relative_to(root.resolve()) and file.is_file()
        assert file.stat().st_size == record['bytes'] and sha(file) == record['sha256'], relative


def run(audit, attempt, preflight_result_sha256=None, previous_result_sha256=None):
    started = time.monotonic()
    observed = datetime.fromisoformat(audit['utc'])
    assert 0 <= (datetime.now(timezone.utc) - observed).total_seconds() < 1200
    assert audit['account'] == 'rocky62' and audit['active_events'] == 0 and audit['private']
    assert audit['gpu_hours_remaining'] >= 2 and audit['session_cap_seconds'] <= 43200
    assert os.environ.get('CUDA_VISIBLE_DEVICES') == '0'
    assert not any('train_image_only_v1.py' in p for p in subprocess.check_output(['ps', '-eo', 'args'], text=True).splitlines())
    base = Path('/kaggle/working') / attempt
    assert not base.exists(), 'Existing job output must be reconciled, never overwritten'
    base.mkdir()
    if importlib.metadata.version('transformers') != '4.48.3':
        subprocess.run([sys.executable, '-m', 'pip', '-q', 'install', 'transformers==4.48.3'], check=True, timeout=600)
    preflight = matching('PRIVATE_PREFLIGHT_RESULT.json', preflight_result_sha256)
    saved = json.loads(preflight.read_text())
    assert saved['status'] == 'gpu_preflight_passed_requires_saved_readback'
    assert saved['utc'] == '2026-11-02T14:29:27.279798+00:00'
    assert saved['config_sha256'] == '91e9e7722297730f280ca2e92a0af91482da78795953b076bf69b47ade9161f6'
    assert saved['sources'] == {'train_image_only_v1.py': '8496d5fe91f6ad58ae2ea63fa6fa4b120dd55a831b90426f0c52766fec827866', 'train_usable_multimodal_v2.py': '7f7fb90deb08a5901d1ca8343b780f6d82dd42b3e278d51f333568435becee0e', 'multimodal_recovery_v1.py': '2f5f67ce79289c69279040d21b483e28535895f5c99c63e0021da3eee6d3d1c8', 'usable_cohort_v2.py': '22bff1eb0fa14d102ad07786f936c5c1ed1582ec7bd5cee2b8e8dc5eb3520092', 'packed_image_io_v3.py': 'a29e66d9c2962eb5bdfdce9abab02866fc77ad44aa5711ec8009a09dda7bb60d', 'verify_multimodal_final_v1.py': '2167e194447eacbcfd2c45cd70f07c524e8996b87fd1e702a9b4900de615065b', 'evaluate_frozen_image_only_v1.py': '178ee95e0f9f40584b3cf05e2979d0d94ee5a5c354b1ac9d1eaa6e3f4b6544bf', 'check_image_only_v1.py': 'bd5f4df242529499545da110e65c8d7138b79c45fdcbceeeec3fd791b244320e'}
    assert saved['scientific_training'] is False and saved['test_inference'] is False
    assert saved['checks']['AMP_skip'] == 'passed_scheduler_did_not_advance'
    manifest = json.loads(preflight.with_name('PRIVATE_PREFLIGHT_MANIFEST.json').read_text())
    check_manifest(preflight.parent, manifest)
    source = base / 'source'
    shutil.copytree(preflight.parent.parent / 'source', source)
    for name, digest in saved['sources'].items():
        assert sha(source / 'scripts' / name) == digest
    config = source / 'configs/image_only_usable_6way_v1.json'
    assert sha(config) == saved['config_sha256']
    sys.path.insert(0, str(source / 'scripts'))
    import torch
    import train_image_only_v1 as t
    from multimodal_recovery_v1 import load_generation
    t.configure(42)
    assert torch.cuda.device_count() == 1 and torch.cuda.get_device_name(0) == 'Tesla T4'
    assert t.environment() == saved['environment'], 'Saved runtime environment changed'
    output = base / 'run'
    release_path = base / 'release.json'
    previous = None
    if previous_result_sha256 is not None:
        previous = matching('IMAGE_JOB_RESULT.json', previous_result_sha256)
        meta = json.loads(previous.read_text())
        assert meta['attempt'] == attempt
        check_manifest(previous.parent, json.loads(previous.with_name('PRIVATE_ARTIFACT_MANIFEST.json').read_text()))
        shutil.copytree(previous.parent / 'run', output)
        shutil.copyfile(previous.parent / 'release.json', release_path)
        assert not (output / 'trainer.lock').exists()
        payload, proof = load_generation(output / 'recovery')
        assert payload['contract']['attempt'] == attempt and payload['gradients_cleared']
        assert payload['scheduler']['last_epoch'] == payload['state']['updates']
        assert payload['state']['cursor'] == payload['cursor'] == payload['state']['seen']
        assert all(k in payload for k in ['optimizer', 'scheduler', 'scaler', 'rng', 'model'])
        assert payload['contract']['sources'] == saved['sources']
        # The stop marker belongs only to this verified copied job.
        stop = output / 'STOP_REQUESTED'
        if stop.exists():
            stop.rename(output / ('STOP_ACKNOWLEDGED_' + str(time.time_ns())))
        write(base / 'PRIOR_RECOVERY_READBACK.json', {'utc': datetime.now(timezone.utc).isoformat(), 'recovery': proof,
              'epoch': payload['state']['epoch'], 'cursor': payload['cursor'], 'prior_result_sha256': sha(previous)})
        del payload; gc.collect()
    else:
        release = dict(saved, status='accepted_saved_preflight_readback',
                       saved_preflight_sha256=sha(preflight), saved_preflight_manifest_sha256=sha(preflight.with_name('PRIVATE_PREFLIGHT_MANIFEST.json')))
        write(release_path, release)
    coverage = matching('packed_runtime_coverage.json', saved['inputs']['coverage_sha256'])
    index = matching('packed_image_index.sqlite', saved['inputs']['packed_index_sha256'])
    root = Path(json.loads(coverage.read_text())['runtime_root'])
    assert root.is_dir()
    per_epoch = 563601 / saved['timing']['train']['pairs_per_second'] + 59299 / saved['timing']['eval']['pairs_per_second']
    safety = max(1800., per_epoch * .2)
    cap = min(audit['session_cap_seconds'], int(audit['gpu_hours_remaining'] * 3600) - 900)
    # Leave at least a full validation plus saving margin after the training safe boundary.
    validation_reserve = 59299 / saved['timing']['eval']['pairs_per_second'] * 1.5 + safety
    training_seconds = int(cap - (time.monotonic() - started) - saved['staging_seconds'] * 1.5 - validation_reserve)
    assert training_seconds >= 600, 'Insufficient measured safe runtime headroom'
    write(base / 'RELEASE_RECORD.json', {'utc': datetime.now(timezone.utc).isoformat(), 'attempt': attempt,
          'source_hashes': saved['sources'], 'config_sha256': saved['config_sha256'], 'audit': audit,
          'preflight_result_sha256': sha(preflight), 'resuming': previous is not None,
          'estimated_seconds_per_epoch': per_epoch, 'bounded_training_seconds': training_seconds,
          'test_policy': 'only frozen selection after completed registered training'})
    environment = dict(os.environ, PYTHONPATH=str(source / 'scripts'), PYTHONDONTWRITEBYTECODE='1')
    command = [sys.executable, '-u', str(source / 'scripts/train_image_only_v1.py'), '--root', str(root),
               '--coverage', str(coverage), '--index', str(index), '--config', str(config), '--output', str(output),
               '--release', str(release_path), '--attempt', attempt, '--stop-after-epoch', '4',
               '--wall-seconds', str(training_seconds)]
    if previous is not None:
        command.append('--resume')
    with (base / 'training_console.log').open('x') as stream:
        process = subprocess.Popen(command, stdout=stream, stderr=subprocess.STDOUT, env=environment)
        while process.poll() is None:
            status_path = output / 'status.json'
            status = json.loads(status_path.read_text()) if status_path.exists() else {'state': 'verified_input_staging_or_model_initialization'}
            heartbeat = {'utc': datetime.now(timezone.utc).isoformat(), 'pid': process.pid,
                         'trainer_alive': True, 'status': status, 'elapsed_seconds': time.monotonic() - started}
            write(base / 'heartbeat.json', heartbeat)
            print(json.dumps(heartbeat), flush=True)
            if time.monotonic() - started > cap - 600:
                (output / 'STOP_REQUESTED').touch()
            if time.monotonic() - started > cap - 150:
                process.terminate(); process.wait(timeout=120)
                break
            time.sleep(30)
    assert process.returncode == 0, 'Trainer failed; preserve log and recovery'
    payload, proof = load_generation(output / 'recovery')
    state = payload['state']
    assert payload['contract']['attempt'] == attempt
    assert payload['scheduler']['last_epoch'] == state['updates']
    assert payload['cursor'] == state['cursor'] == state['seen']
    order = t.order(42, state['epoch'], 563601)
    sampler_proof = {'epoch': state['epoch'], 'cursor': state['cursor'], 'permutation_sha256': hashlib.sha256(order.numpy().tobytes()).hexdigest(),
                     'next_positions': order[state['cursor']:state['cursor'] + 32].tolist()}
    write(base / 'SAMPLER_RECOVERY_PROOF.json', sampler_proof)
    complete = state['epoch'] > 4 or state['early_stopped']
    del payload, order; gc.collect()
    result = {'utc': datetime.now(timezone.utc).isoformat(), 'attempt': attempt,
              'training_complete': complete, 'full_validations': len(state['history']),
              'state': state, 'recovery': proof, 'test_complete': False, 'elapsed_seconds': time.monotonic() - started}
    write(base / 'IMAGE_JOB_RESULT.json', result)
    test_reserve = 59270 / saved['timing']['eval']['pairs_per_second'] * 1.5 + 900
    if complete and cap - (time.monotonic() - started) > test_reserve:
        command = [sys.executable, '-u', str(source / 'scripts/evaluate_frozen_image_only_v1.py'),
                   '--run', str(output), '--root', str(root), '--index', str(index)]
        with (base / 'test_console.log').open('x') as stream:
            subprocess.run(command, stdout=stream, stderr=subprocess.STDOUT, env=environment, check=True,
                           timeout=max(60, int(cap - (time.monotonic() - started) - 600)))
        result['test_complete'] = True
        result['test'] = json.loads((output / 'test_independent_verification.json').read_text())
        result['elapsed_seconds'] = time.monotonic() - started
        write(base / 'IMAGE_JOB_RESULT.json', result)
    files = {str(p.relative_to(base)): {'bytes': p.stat().st_size, 'sha256': sha(p)}
             for p in base.rglob('*') if p.is_file()}
    write(base / 'PRIVATE_ARTIFACT_MANIFEST.json', {'utc': datetime.now(timezone.utc).isoformat(), 'files': files})
    print('IMAGE_JOB_DURABLE_OUTPUT_READY', json.dumps(result), flush=True)
    return result
