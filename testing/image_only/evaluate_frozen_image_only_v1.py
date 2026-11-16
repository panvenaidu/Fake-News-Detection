"""One full image-only test after a sealed, completed validation selection."""
import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd
import torch
import train_image_only_v1 as t
from multimodal_recovery_v1 import atomic_json, sha
from usable_cohort_v2 import load_input
from verify_multimodal_final_v1 import verify


def run(args):
    folder = Path(args.run)
    frozen = t.freeze(folder)
    contract, selected = frozen['contract'], frozen['selected']
    cfg = contract['config']
    if t.source_hashes() != contract['sources']:
        raise ValueError('Frozen source changed')
    t.configure(cfg['seed'])
    if t.environment() != contract['versions']:
        raise ValueError('Frozen environment changed')
    expected, _ = load_input(args.root)
    official = pd.DataFrame([r for r in expected.values() if r['split'] == 'test'])
    assert len(official) == 59270
    if (folder / 'test_metrics.json').exists():
        result = verify(folder, 'test', official, 'test')
        atomic_json(folder / 'test_independent_verification.json', result)
        return result
    if (folder / 'test_start.json').exists():
        raise ValueError('Interrupted frozen test requires explicit replay receipt')
    weights = folder / selected['weights_file']
    assert sha(weights) == selected['weights_sha256']
    network = t.model().cuda().eval()
    state = torch.load(weights, map_location='cpu', weights_only=True)
    network.load_state_dict(state, strict=True)
    manifest_path = Path(args.root) / 'data/official_paired_v2/paired_manifest.csv'
    assert sha(manifest_path) == contract['inputs']['manifest_sha256']
    manifest = pd.read_csv(manifest_path, dtype=str, keep_default_na=False)
    from packed_image_io_v3 import ArchiveStore
    store = ArchiveStore(args.root, args.index, contract['inputs']['packed_index_sha256'])
    validation = manifest[manifest.split.eq('validation')].iloc[:32].copy()
    probe = next(iter(t.loader(t.Images(validation, args.root, cfg, False, store), cfg, False)))['images'].cuda()
    with torch.inference_mode(), torch.autocast('cuda', dtype=torch.float16):
        before = network(probe)
        network.load_state_dict(state, strict=True)
        after = network(probe)
    assert torch.equal(before, after)
    atomic_json(folder / 'selected_weight_roundtrip.json', {'utc': t.shared.utc(), 'strict_load': True,
                'weights_sha256': sha(weights), 'validation_probe_rows': 32, 'maximum_logit_delta': 0.0})
    del state, probe, before, after
    test = manifest[manifest.split.eq('test')].set_index('id').loc[official.id].reset_index()
    assert np.array_equal(test['6_way_label'].astype(int), official['6_way_label'])
    atomic_json(folder / 'test_start.json', {'utc': t.shared.utc(), 'weights_sha256': sha(weights),
                'freeze_sha256': sha(folder / 'final_selection_frozen.json'), 'expected_rows': 59270})
    metrics, predictions = t.shared.evaluate(network, t.loader(t.Images(test, args.root, cfg, False, store), cfg, False), torch.device('cuda'))
    assert predictions.id.tolist() == official.id.tolist()
    t.export(folder, 'test', metrics, predictions, 'test')
    result = verify(folder, 'test', official, 'test')
    atomic_json(folder / 'test_independent_verification.json', result)
    atomic_json(folder / 'final_evaluation_complete.json', {'utc': t.shared.utc(), 'selected': selected,
                'test': result, 'status': 'runtime_verified_requires_private_saved_readback'})
    print(json.dumps(result), flush=True)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    for key in ['run', 'root', 'index']:
        parser.add_argument('--' + key, type=Path, required=True)
    run(parser.parse_args())
