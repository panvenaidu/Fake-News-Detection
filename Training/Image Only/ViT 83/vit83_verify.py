"""Reopen immutable test outputs on CPU and independently recompute the metrics."""
import math

import numpy as np
import pandas as pd

from frozen_image_pair_v1 import load_verified, sampled, save_json
from packed_image_io_v3 import sha
from verify_vit_finetune_v1 import match, paired, prediction_file, read, require, selection, wilson

BASELINES = (
    ('ResNet-50', '**/OFFICIAL-6W-IMAGE-USABLE-v1_seed42_20261102T145600Z/run/test_predictions.csv',
     'ca2c8afb877146b2ae892e60a03f114acd8cb184d2d6e1cd861c2f65b5eb41d3', .8115572802429559),
    ('DeiT III B/16', '**/urop_vit_finetune/test_predictions.csv',
     '57a5848380c26f9446e949297af8acf51b01d81c3c3aef4b99c9c1a94de2c6b0', .803948),
)
ORDER = ('crop', 'full_frame', 'layer_decay', 'dinov2')
GOAL_CORRECT = 49195
VALIDATION_CORRECT = 47592
MANIFEST_COLUMNS = ['id', 'split', '6_way_label', 'image_sha256']


def exact_artifact(mount, glob, digest):
    matches = [path for path in mount.glob(glob) if sha(path) == digest]
    require(len(matches) == 1, f'Expected one exact saved artifact for {glob}')
    return matches[0]


def check_run(folder, trial, validation):
    run_folder = folder/trial['id']
    complete = read(run_folder/'complete.json')
    require(complete['trial'] == trial and len(complete['history']) == trial['epochs'],
            f'Trial inventory differs for {trial["id"]}')
    for epoch, entry in enumerate(complete['history'], 1):
        _, metrics = prediction_file(run_folder, f'validation_epoch{epoch}', validation)
        match(entry['validation'], metrics['metrics'], f'{trial["id"]} validation epoch {epoch}')
        require(entry['epoch'] == epoch and metrics['prediction_sha256'] == entry['validation_predictions_sha256']
                and entry['updates'] + entry['skips'] == epoch * math.ceil(trial['rows']/64),
                f'Validation or optimizer update accounting differs for {trial["id"]} epoch {epoch}')
    best = max(complete['history'], key=selection)
    require(best == complete['best'] and sha(run_folder/best['selected_weight']) == best['weight_sha256'],
            f'Validation checkpoint selection differs for {trial["id"]}')
    return best


def verify_validation(folder, registration, promotion, validation):
    chosen_pilots = registration['pilots']
    require([t['recipe'] for t in chosen_pilots] == sorted((t['recipe'] for t in chosen_pilots), key=ORDER.index)
            and all(t['rows'] == 30000 and t['epochs'] == 2 and t['kind'] == 'pilot' for t in chosen_pilots),
            'Pilot registration differs')
    pilot_ranking = [{'trial': t['id'], 'best': check_run(folder, t, validation)} for t in chosen_pilots]
    pilot_ranking.sort(key=lambda item: selection(item['best']), reverse=True)
    require(pilot_ranking == promotion['pilot_ranking'], 'Independent pilot ranking differs')
    alternatives = [r for r in pilot_ranking if r['trial'] != 'pilot_crop']
    count = 1
    if registration['budget']['full_trial_cap'] == 2 and len(alternatives) > 1:
        a, b = [round(x['best']['validation']['accuracy']*len(validation)) for x in alternatives[:2]]
        count += int(400 * (a-b) <= len(validation))
    scheduled = [next(t for t in chosen_pilots if t['id'] == r['trial']) for r in alternatives[:count]]
    expected_full = [{**t, 'id': f"full_{t['recipe']}", 'kind': 'full',
                      'epochs': registration['budget']['epoch_cap'], 'rows': 563601} for t in scheduled]
    require(promotion['full_trials'] == expected_full, 'Independent promotion differs')
    finalists = {}
    for t in expected_full:
        best = check_run(folder, t, validation)
        finalists[t['id']] = {'trial': t, 'selected': best, 'complete_sha256': sha(folder/t['id']/'complete.json')}
    winner = max(finalists.values(), key=lambda r: (*selection(r['selected']), -ORDER.index(r['trial']['recipe'])))
    val_correct = round(winner['selected']['validation']['accuracy'] * len(validation))
    return pilot_ranking, finalists, winner, val_correct


def verify_retained(source, mount, out, version, receipt_sha):
    result_path = exact_artifact(mount, '**/urop_vit83/baseline_retained.json', receipt_sha)
    folder = result_path.parent
    result = read(result_path)
    registration = read(folder/'registration.json')
    promotion = read(folder/'promotion.json')
    require(result['state'] == 'baseline_retained'
            and sha(folder/'registration.json') == result['registration_sha256']
            and sha(folder/'promotion.json') == result['promotion_sha256']
            and sha(folder/'cohort_contract.json') == registration['cohort_sha256'],
            'Saved validation and baseline decision receipt chain differs')
    pin = read(source/'image_only_vit_resnet_frozen_v1.json')
    _, _, frames, approval = load_verified(mount, pin)
    cohort = read(folder/'cohort_contract.json')
    require(cohort['cohort'] == pin and cohort['excluded_ids_sha256'] == approval['excluded_ids_sha256'],
            'Validation input cohort differs')
    validation = frames['validation']
    pilots, finalists, winner, correct = verify_validation(folder, registration, promotion, validation)
    require(result['finalists'] == finalists and result['selected'] == winner['selected']
            and result['final_trial'] == winner['trial']
            and result['complete_sha256'] == winner['complete_sha256']
            and result['validation_correct'] == correct <= VALIDATION_CORRECT
            and result['prior_validation_correct'] == VALIDATION_CORRECT,
            'Independent baseline decision differs')
    save_json(out/'VIT83_CPU_VALIDATION.json',
              {'source_version': version, 'receipt_sha256': receipt_sha, 'pilot_ranking': pilots,
               'finalists': finalists, 'winner': winner, 'correct': correct, 'total': len(validation),
               'prior_validation_correct': VALIDATION_CORRECT, 'budget': registration['budget'],
               'cohort_contract': cohort})
    print(f'verified_validation {correct}/{len(validation)} {correct/len(validation):.6%}', flush=True)


def verify_saved(source, mount, out, version, receipt_sha):
    receipt_path = exact_artifact(mount, '**/urop_vit83/test_saved.json', receipt_sha)
    folder = receipt_path.parent
    test_receipt = read(receipt_path)
    gate = read(folder/'test_started.json')
    reload = read(folder/'fixed_validation_receipt.json')
    freeze = read(folder/'selection_frozen.json')
    promotion = read(folder/'promotion.json')
    registration = read(folder/'registration.json')
    cohort_contract = read(folder/'cohort_contract.json')
    require(freeze['state'] == 'frozen_before_test'
            and reload['state'] == 'fresh_process_passed'
            and sha(folder/'test_started.json') == test_receipt['test_started_sha256']
            and sha(folder/'fixed_validation_receipt.json') == test_receipt['fixed_validation_sha256']
            and sha(folder/'selection_frozen.json') == gate['selection_sha256'] == reload['selection_sha256']
            and sha(folder/'registration.json') == freeze['registration_sha256']
            and sha(folder/'promotion.json') == freeze['promotion_sha256']
            and sha(folder/'cohort_contract.json') == registration['cohort_sha256'],
            'Freeze, reload, or test receipt chain differs')
    pin = read(source/'image_only_vit_resnet_frozen_v1.json')
    _, _, frames, approval = load_verified(mount, pin)
    require(cohort_contract['cohort'] == pin
            and cohort_contract['excluded_ids_sha256'] == approval['excluded_ids_sha256'],
            'Registered cohort or exclusion hash changed')
    manifest_frames = {**frames, 'pilot_train': sampled(frames['train'], 30000, 42)}
    for split, data in manifest_frames.items():
        p = folder/f'{split}_manifest.csv'
        manifest = pd.read_csv(p, dtype={'id': str})
        expected = gate['test_manifest_sha256'] if split == 'test' else cohort_contract['manifest_hashes'][split]
        require(sha(p) == expected and manifest.equals(data[MANIFEST_COLUMNS]), f'Manifest differs for {split}')

    validation = frames['validation']
    pilot_ranking, finalists, winner, val_correct = verify_validation(folder, registration, promotion, validation)
    require(freeze['finalists'] == finalists, 'Frozen finalists differ')
    require(freeze['final_trial'] == winner['trial'] and freeze['selected'] == winner['selected']
            and freeze['validation_correct'] == val_correct > VALIDATION_CORRECT
            and freeze['prior_validation_correct'] == VALIDATION_CORRECT
            and freeze['complete_sha256'] == winner['complete_sha256']
            and reload['checkpoint_sha256'] == winner['selected']['weight_sha256']
            and reload['validation_predictions_sha256'] == winner['selected']['validation_predictions_sha256'],
            'Independent frozen selection differs')

    test = frames['test']
    table, full = prediction_file(folder, 'test', test)
    require(full['prediction_sha256'] == test_receipt['test_predictions_sha256'],
            'Frozen test prediction hash differs')
    keep = ~test.image_sha256.isin(set(frames['train'].image_sha256))
    require(int(keep.sum()) == 56052 and len(test) == 59270, 'Exact-image subset differs')
    subset_table, subset = prediction_file(folder, 'test_no_train_hash', test[keep].reset_index(drop=True))
    require(subset_table.equals(table[keep].reset_index(drop=True)), 'Saved subset rows differ from full predictions')
    paired_results = {name: paired(exact_artifact(mount, pattern, digest), table, digest, acc,
                                   test.image_sha256)
                      for name, pattern, digest, acc in BASELINES}
    correct = int(np.count_nonzero(table.true_label == table.predicted_label))
    accuracy = correct / len(test)
    proof = {'source_version': version, 'test_receipt_sha256': receipt_sha, 'winner': winner,
             'correct': correct, 'total': len(test), 'target_correct': GOAL_CORRECT,
             'target_reached': correct >= GOAL_CORRECT, 'gap_pp': (accuracy-.83)*100,
             'correct_shortfall': max(0, GOAL_CORRECT - correct),
             'wilson_95pct': wilson(correct, len(test)), 'pilot_ranking': pilot_ranking,
             'budget': registration['budget'], 'cohort_contract': cohort_contract,
             'test_manifest_sha256': gate['test_manifest_sha256'],
             'full': full, 'no_exact_training_match': subset,
             'paired': paired_results}
    save_json(out/'VIT83_CPU_VERIFICATION.json', proof)
    report = [
        '# UROP image-only Vision Transformer 83% experiment', '',
        f'Frozen recipe **{winner["trial"]["recipe"]}**, epoch {winner["selected"]["epoch"]}, seed 42.',
        f'Full validation accuracy {val_correct/len(validation):.4%} ({val_correct:,}/{len(validation):,}).',
        f'Independent full-test accuracy **{accuracy:.4%}** ({correct:,}/{len(test):,}).',
        f'Difference from 83.00% {proof["gap_pp"]:+.4f} percentage points. '
        f'Additional correct predictions needed {proof["correct_shortfall"]:,}.', '',
        '| Cohort | Accuracy | Macro-F1 | Balanced accuracy | Imposter Content recall |',
        '|---|---:|---:|---:|---:|',
    ]
    for title, result in [('Full official test', full), ('No exact training byte match', subset)]:
        m = result['metrics']
        rare = result['classes']['Imposter Content']['recall']
        report.append(f'| {title} ({m["samples"]:,}) | {m["accuracy"]:.4%} | '
                      f'{m["macro_f1"]:.6f} | {m["balanced_accuracy"]:.4%} | {rare:.4%} |')
    report += ['', '| Baseline | Paired difference (pp) | Correct only for new model | Correct only for baseline |',
               '|---|---:|---:|---:|']
    for name, delta in paired_results.items():
        report.append(f'| {name} | {100*delta["paired_delta"]:+.4f} | {delta["better"]:,} | {delta["worse"]:,} |')
    report += ['', 'The CPU verification JSON includes raw and normalized confusion matrices, per-class metrics, '
               'paired bootstrap intervals, and cohort and prediction hashes.',
               'The prior models used this official test as well. No separate holdout was registered.', '']
    (out/'VIT83_REPORT.md').write_text('\n'.join(report))
    print(f'verified_test {correct}/{len(test)} {accuracy:.6%} gap {proof["gap_pp"]:+.4f} pp', flush=True)
