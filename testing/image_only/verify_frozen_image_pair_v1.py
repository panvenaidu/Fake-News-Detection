"""Independent readback of prediction CSVs and selected weight hashes."""
import json
from pathlib import Path

import numpy as np
import pandas as pd
from packed_image_io_v3 import sha
from verify_multimodal_final_v1 import verify

ARMS = ('vit', 'resnet50')
SCORES = ('accuracy', 'macro_f1', 'balanced_accuracy')


def read(path):
    return json.loads(path.read_text())


def verify_run(folder):
    folder = Path(folder)
    resolved_path = folder / 'resolved.json'
    resolved = read(resolved_path)
    freeze_path = folder / 'selection_frozen.json'
    freeze = read(freeze_path)
    assert freeze['resolved_sha256'] == sha(resolved_path)
    assert freeze['backbones'] == resolved['backbones']
    assert freeze['test_manifest_sha256'] == resolved['manifests']['test']
    manifests = {}
    for split, digest in resolved['manifests'].items():
        path = folder / f'{split}_manifest.csv'
        assert sha(path) == digest
        frame = pd.read_csv(path, dtype={'id': str})
        assert len(frame) == resolved['scope']['counts'][split]
        assert frame.id.is_unique and frame.split.eq(split).all()
        assert set(frame['6_way_label']) == set(range(6))
        manifests[split] = frame
    assert pd.concat(list(manifests.values())).id.is_unique
    test = manifests['test']
    mask = ~test.image_sha256.isin(set(manifests['train'].image_sha256))
    subset = test.loc[mask].reset_index(drop=True)
    if resolved['scope']['mode'] == 'full':
        assert len(subset) == 56052

    arms = {}
    cols = ['id', 'true_label', 'predicted_label', 'cross_entropy'] + [f'p{i}' for i in range(6)]
    for arm in ARMS:
        d = folder / arm
        history = read(d / 'history.json')
        assert [row['epoch'] for row in history] == list(range(1, resolved['config']['epochs'] + 1))
        epochs = {}
        for row in history:
            epoch = row['epoch']
            proof = verify(d, f'validation_epoch{epoch}', manifests['validation'], 'validation')
            assert all(abs(proof['metrics'][k] - v) < 1e-10 for k, v in row['validation'].items())
            assert row['weight_sha256'] == sha(d / f'epoch{epoch}.pt')
            epochs[str(epoch)] = proof
        best = max(history, key=lambda r: (r['validation']['macro_f1'], -r['validation']['loss'], -r['epoch']))
        assert freeze['selected'][arm] == best and best['weight_sha256'] == sha(d / 'selected.pt')
        saved = read(d / 'test_saved.json')
        assert saved['freeze_sha256'] == sha(freeze_path)
        test_result = verify(d, 'test', test, 'test')
        assert saved['test_predictions_sha256'] == test_result['prediction_sha256']
        overlap_result = verify(d, 'test_no_train_hash', subset, 'test')
        full_csv = pd.read_csv(d / 'test_predictions.csv', dtype={'id': str}, usecols=cols)
        sub_csv = pd.read_csv(d / 'test_no_train_hash_predictions.csv', dtype={'id': str}, usecols=cols)
        assert full_csv.loc[mask, cols].reset_index(drop=True).equals(sub_csv[cols])
        arms[arm] = {'epoch': best['epoch'], 'checkpoint_sha256': best['weight_sha256'],
                     'validation': epochs, 'test': test_result, 'test_no_train_hash': overlap_result}
    delta = {name: {k: arms['vit'][name]['metrics'][k] - arms['resnet50'][name]['metrics'][k]
                    for k in SCORES} for name in ('test', 'test_no_train_hash')}
    return {'status': 'passed', 'scope': resolved['scope'], 'test_posts': len(test),
            'no_train_hash_posts': len(subset), 'arms': arms, 'differences': delta,
            'frozen_selection_sha256': sha(freeze_path), 'resolved_sha256': sha(resolved_path)}


def report(folder, proof):
    scope = proof['scope']
    resolved = read(folder / 'resolved.json')
    lines = ['# Frozen ViT-B/16 versus ResNet-50', '', f"Scope: {scope['mode']}; "
             + ', '.join(f"{split}: {count:,}" for split, count in scope['counts'].items()) + '.',
             f"Latest run session: {read(folder / 'runtime.json')['current_session_seconds']/60:.1f} minutes.",
             '', '| Held-out split | Model | Accuracy | Macro-F1 | Balanced accuracy |',
             '|---|---|---:|---:|---:|']
    for key, name, n in [('test', 'All selected test posts', proof['test_posts']),
                          ('test_no_train_hash', 'Exact bytes absent from training', proof['no_train_hash_posts'])]:
        for arm, info in proof['arms'].items():
            m = info[key]['metrics']
            lines.append(f"| {name} ({n:,}) | {arm} | {m['accuracy']:.4%} | {m['macro_f1']:.6f} | {m['balanced_accuracy']:.4%} |")
        m = proof['differences'][key]
        lines.append(f"| {name} ({n:,}) | ViT − ResNet-50 | {100*m['accuracy']:+.4f} pp | {m['macro_f1']:+.6f} | {100*m['balanced_accuracy']:+.4f} pp |")
    for arm in ARMS:
        lines += ['', f"## {arm} (epoch {proof['arms'][arm]['epoch']})", '',
                  '| Test cohort | Class | Precision | Recall | F1 | Support |',
                  '|---|---|---:|---:|---:|---:|']
        for prefix in ('test', 'test_no_train_hash'):
            items = read(folder / arm / f'{prefix}_classification_report.json')
            for label, m in items.items():
                if isinstance(m, dict) and label not in ('macro avg', 'weighted avg', 'micro avg'):
                    lines.append(f"| {prefix} | {label} | {m['precision']:.6f} | {m['recall']:.6f} | {m['f1-score']:.6f} | {int(m['support']):,} |")
    lines += ['', 'Exact image hashes identify byte-for-byte repeats only. The main comparison is against the matched frozen ResNet-50.',
              'The historical fine-tuned ResNet-50 scored 81.1557% accuracy and 0.661796 macro-F1 under its original protocol.',
              'The backbone pretraining recipes differ. This single-seed result does not establish run-to-run variability.',
              f"Runtime hardware: {', '.join(resolved['runtime']['devices'])}.", '']
    return '\n'.join(lines)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('folder', type=Path)
    args = parser.parse_args()
    result = verify_run(args.folder)
    receipt = args.folder / 'independent_verification.json'
    if receipt.is_file():
        assert result == read(receipt), 'Saved verification receipt changed'
    print(json.dumps(result, indent=2))
