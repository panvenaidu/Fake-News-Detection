"""Independent local CPU readback of a saved private image-only job.

No inference, optimization, network or cloud allocation. Large inputs remain private.
"""
import argparse
import gc
import hashlib
import json
import math
from pathlib import Path
from datetime import datetime, timezone
import numpy as np
import pandas as pd
import torch
import train_image_only_v1 as t
from multimodal_recovery_v1 import load_generation, sha, order, atomic_json
from usable_cohort_v2 import load_cohort, registration, REGISTRATION, COUNTS
from verify_multimodal_final_v1 import verify


def verify_saved(folder, project, allow_partial=False):
    folder, project = Path(folder).resolve(), Path(project).resolve()
    manifest_path = folder / 'PRIVATE_ARTIFACT_MANIFEST.json'
    manifest = json.loads(manifest_path.read_text())
    for relative, item in manifest['files'].items():
        path = (folder / relative).resolve()
        assert path.is_relative_to(folder) and path.is_file(), relative
        assert path.stat().st_size == item['bytes'] and sha(path) == item['sha256'], relative
    result = json.loads((folder / 'IMAGE_JOB_RESULT.json').read_text())
    run = folder / 'run'
    protocol = json.loads((run / 'protocol.json').read_text())
    cfg = protocol['config']
    assert cfg['protocol_id'] == t.PROTOCOL and cfg['seed'] == 42 and cfg['planned_epochs'] == 4
    assert protocol['attempt'] == result['attempt']
    assert sha(folder / 'source/configs/image_only_usable_6way_v1.json') == protocol['config_sha256']
    assert sha(folder / 'release.json') == protocol['preflight_release_sha256']
    for name, digest in protocol['sources'].items():
        assert sha(folder / 'source/scripts' / name) == digest
        assert sha(project / 'scripts' / name) == digest
    reg_path = project / 'results' / REGISTRATION
    reg = registration(reg_path)
    expected, _ = load_cohort(project / 'data/official_multimodal_v2', reg_path,
                              project / 'data/official_paired_v1/source_recovery' / reg['extraction_report_file'],
                              project / 'results' / reg['approval_file'])
    validation = pd.DataFrame([row for row in expected.values() if row['split'] == 'validation'])
    test = pd.DataFrame([row for row in expected.values() if row['split'] == 'test'])
    del expected; gc.collect()
    payload, recovery = load_generation(run / 'recovery')
    assert payload['contract'] == protocol and payload['gradients_cleared']
    state = payload['state']
    assert state == result['state']
    assert state['cursor'] == state['seen'] == payload['cursor'] and 0 <= state['cursor'] <= COUNTS['train']
    assert state['cursor'] % 32 == 0 or state['cursor'] == COUNTS['train']
    assert state['updates'] + state['skips'] == len(state['history']) * 17613 + math.ceil(state['cursor'] / 32)
    assert payload['scheduler']['last_epoch'] == state['updates']
    assert len(payload['rng']['cuda']) == 1 and set(payload['rng']) == {'python', 'numpy', 'torch', 'cuda'}
    assert payload['optimizer']['state'] and payload['scaler']['scale'] > 0
    network = t.model()
    network.load_state_dict(payload['model'], strict=True)
    optimizer, scheduler, scaler = t.optimization(network, cfg, torch.device('cpu'))
    optimizer.load_state_dict(payload['optimizer']); scheduler.load_state_dict(payload['scheduler'])
    cpu_scaler = torch.amp.GradScaler('cpu')
    cpu_scaler.load_state_dict(payload['scaler'])
    assert cpu_scaler.state_dict() == payload['scaler']
    for value in network.state_dict().values():
        if value.is_floating_point():
            assert torch.isfinite(value).all()
    sampler = json.loads((folder / 'SAMPLER_RECOVERY_PROOF.json').read_text())
    permutation = order(42, state['epoch'], COUNTS['train'])
    assert sampler['epoch'] == state['epoch'] and sampler['cursor'] == state['cursor']
    assert sampler['permutation_sha256'] == hashlib.sha256(permutation.numpy().tobytes()).hexdigest()
    assert sampler['next_positions'] == permutation[state['cursor']:state['cursor'] + 32].tolist()
    del optimizer, scheduler, cpu_scaler, payload, permutation; gc.collect()
    validations = []
    for entry in state['history']:
        check = verify(run, 'validation_epoch' + str(entry['epoch']), validation, 'validation')
        assert check['metrics'] == entry['validation']
        validations.append({'epoch': entry['epoch'], **check})
    winner = max(state['history'], key=lambda h: (h['validation']['macro_f1'], -h['validation']['loss'], -h['epoch'])) if state['history'] else None
    selected = state['best']
    if selected is not None:
        assert selected['epoch'] == winner['epoch']
        weights = run / selected['weights_file']
        assert sha(weights) == selected['weights_sha256']
        network.load_state_dict(torch.load(weights, map_location='cpu', weights_only=True), strict=True)
        for value in network.state_dict().values():
            if value.is_floating_point():
                assert torch.isfinite(value).all()
    complete = state['epoch'] > 4 or state['early_stopped']
    test_proof = None
    if not allow_partial:
        assert complete and len(validations) >= 3 and result['test_complete']
        frozen = json.loads((run / 'final_selection_frozen.json').read_text())
        start = json.loads((run / 'test_start.json').read_text())
        assert frozen['selected'] == selected and frozen['contract'] == protocol
        assert frozen['protocol_sha256'] == sha(run / 'protocol.json')
        assert start['freeze_sha256'] == sha(run / 'final_selection_frozen.json')
        assert start['weights_sha256'] == selected['weights_sha256']
        assert datetime.fromisoformat(frozen['utc']) <= datetime.fromisoformat(start['utc'])
        assert len(state['history']) == 4 or state['early_stopped']
        test_proof = verify(run, 'test', test, 'test')
        assert test_proof['metrics'] == result['test']['metrics']
    return {'utc': datetime.now(timezone.utc).isoformat(), 'status': 'accepted_complete' if test_proof else 'accepted_partial',
            'attempt': result['attempt'], 'training_complete': complete, 'epochs_completed': len(state['history']),
            'full_validations': len(validations), 'selected': selected, 'validations': validations, 'test': test_proof,
            'recovery': recovery, 'updates': state['updates'], 'skips': state['skips'],
            'next_epoch': state['epoch'], 'cursor': state['cursor'], 'phase': state['phase'],
            'manifest_sha256': sha(manifest_path), 'job_result_sha256': sha(folder / 'IMAGE_JOB_RESULT.json'),
            'protocol_sha256': sha(run / 'protocol.json'), 'source_hashes': protocol['sources'],
            'strict_model_optimizer_scheduler_scaler_readback': True, 'sampler_and_RNG_state_verified': True,
            'validation_and_test_CSV_independently_recomputed': True, 'private_folder': str(folder),
            'verification_environment': {'torch': torch.__version__, 'numpy': np.__version__, 'CPU_only': True},
            'runtime_environment': protocol['versions'], 'run_history': state['history']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--folder', required=True, type=Path)
    parser.add_argument('--project', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--allow-partial', action='store_true')
    args = parser.parse_args()
    outcome = verify_saved(args.folder, args.project, args.allow_partial)
    atomic_json(args.output, outcome)
    print(json.dumps(outcome, indent=2), flush=True)
