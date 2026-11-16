"""Exercise the independent saved-output readback without accessing real test data."""
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
import pandas as pd
import torch

ROOT = Path(__file__).resolve().parents[2]
for folder in ('Model/Image Only', 'Training/Text + Image/Scripts', 'Testing/Image Only'):
    sys.path.insert(0, str(ROOT / folder))

from frozen_image_pair_v1 import export_eval, save_json
from verify_vit_finetune_v1 import LABELS, report, sha, verify


def check(out):
    config = {
        'input_features': ['RGB_pixels'], 'seed': 42, 'encoder_lr': 3e-5,
        'selection': ['accuracy', 'macro_f1', 'lower_cross_entropy', 'earlier_epoch'],
        'pilot_rows': 6, 'expected_no_train_hash_count': 6, 'effective_batch': 2,
        'eval_batch': 6, 'goal_accuracy': .82, 'historical_frozen_vit_accuracy': .656487,
        'historical_resnet_accuracy': .811557, 'model': 'fixture_vit',
        'initialization': 'fixture', 'weight_sha256': 'fixture',
    }
    splits = ('train', 'validation', 'test')
    frames = {}
    for index, split in enumerate(splits):
        # A valid digest can consist entirely of digits. Its leading zeros must survive CSV import.
        frame = pd.DataFrame({
            'id': [f'{split}-{i}' for i in range(6)], 'split': split,
            '6_way_label': list(range(6)),
            'image_sha256': [f'{6 * index + i:064d}' for i in range(6)],
        })
        frames[split] = frame
        frame.to_csv(out / f'{split}_manifest.csv', index=False)
    frames['train'].to_csv(out / 'pilot_train_manifest.csv', index=False)

    (out / 'source').mkdir()
    (out / 'preflight').mkdir()
    timing = out / 'preflight/timing.json'
    save_json(timing, dict(continuation_passed=True, validation_reload_exact=True,
                           encoder_and_head_changed=True))
    plan = dict(id='fixture_full', kind='full', epochs=1, rows=6)
    trial = {**plan, 'lr': config['encoder_lr']}
    registration = out / 'registration.json'
    save_json(registration, dict(
        sources={}, config=config, world_size=1, preflight_sha256=sha(timing),
        cohort_contract=dict(inputs=dict(counts={s: 6 for s in splits}),
                             splits={s: sha(out / f'{s}_manifest.csv')
                                     for s in ('train', 'validation', 'pilot_train')}),
        pilots=[], full=plan, budget={},
    ))
    promotion = out / 'promotion.json'
    save_json(promotion, dict(full_trial=trial))

    trial_dir = out / trial['id']
    trial_dir.mkdir()
    probability = np.full((6, 6), .04)
    np.fill_diagonal(probability, .8)
    loss = -np.log(probability.diagonal())
    metrics = export_eval(trial_dir, 'validation_epoch1', frames['validation'], probability, loss)
    weights = trial_dir / 'best.pt'
    torch.save({'w': torch.ones(1)}, weights)
    best = dict(epoch=1, validation=metrics, updates=3, skips=0,
                class_recall={label: 1. for label in LABELS}, selected_weight=weights.name,
                weight_sha256=sha(weights),
                validation_predictions_sha256=sha(trial_dir / 'validation_epoch1_predictions.csv'))
    progress = dict(epoch=2, cursor=0, updates=3, history=[best], paused=False,
                    stopped_early=False, best=best, segments_seconds=2)
    resume = trial_dir / 'resume.pt'
    torch.save(dict(
        contract=dict(trial=trial, config=config, registration_sha256=sha(registration), world_size=1),
        progress=progress, scheduler=dict(last_epoch=3),
        optimizer=dict(param_groups=[{}], state={0: {}}), scaler=dict(scale=512),
        rng=[[(), (), torch.zeros(1), torch.zeros(1)]], model={'w': torch.ones(1)},
    ), resume)
    save_json(trial_dir / 'resume.json', dict(bytes=resume.stat().st_size,
                                             sha256=sha(resume), progress=progress))
    save_json(trial_dir / 'history.json', [best])
    complete = trial_dir / 'complete.json'
    save_json(complete, {**progress, 'trial': trial, 'resume_sha256': sha(resume)})

    frozen = out / 'selection_frozen.json'
    save_json(frozen, dict(state='frozen_before_test', seed=42, additional_seeds=[],
                           registration_sha256=sha(registration), promotion_sha256=sha(promotion),
                           final_trial=trial, selected=best, complete_sha256=sha(complete), utc='0'))
    release = out / 'fixed_validation_receipt.json'
    save_json(release, dict(state='fresh_process_passed', selection_sha256=sha(frozen),
                            checkpoint_sha256=best['weight_sha256'], rows=6,
                            validation_predictions_sha256=best['validation_predictions_sha256'],
                            probability_max_error=0, probability_atol=.0003,
                            ce_max_error=0, cross_entropy_atol=.002, utc='1'))
    started = out / 'test_started.json'
    save_json(started, dict(selection_sha256=sha(frozen),
                            test_manifest_sha256=sha(out / 'test_manifest.csv'), utc='2'))
    for prefix in ('test', 'test_no_train_hash'):
        export_eval(out, prefix, frames['test'], probability, loss)
    predictions = out / 'test_predictions.csv'
    save_json(out / 'test_saved.json', dict(test_started_sha256=sha(started),
                                           fixed_validation_sha256=sha(release),
                                           test_predictions_sha256=sha(predictions), utc='3'))
    save_json(out / 'sessions.json', [])
    proof = verify(out, official_frames=frames, source_version='fixture')
    assert proof['target_reached'] and proof['test']['metrics']['accuracy'] == 1.
    assert proof['accuracy_byte_group_poisson_bootstrap_95pct'] == [1., 1.]
    assert proof['validation']['fixture_full']['epochs'][0]['metrics'] == metrics
    assert proof['validation']['fixture_full']['epochs'][0]['prediction_sha256'] == best['validation_predictions_sha256']
    assert '| fixture_full | 1 | 100.0000%' in report(proof)

    table = pd.read_csv(predictions)
    table.loc[0, 'true_label'] = 1
    table.to_csv(predictions, index=False)
    try:
        verify(out, official_frames=frames)
    except ValueError as error:
        assert 'gold labels' in str(error)
    else:
        raise AssertionError('Saved readback accepted a changed test label')


if __name__ == '__main__':
    with TemporaryDirectory() as directory:
        check(Path(directory))
    print('Saved checkpoint, full test, overlap subset, and report readback passed with synthetic data.')
