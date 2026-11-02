"""Create image-only reports only from independently accepted saved artifacts."""
import argparse
import json
import shutil
from pathlib import Path

LABELS = ['True', 'Satire/Parody', 'Misleading Content', 'Imposter Content', 'False Connection', 'Manipulated Content']
METRICS = ['accuracy', 'micro_f1', 'macro_f1', 'weighted_f1', 'balanced_accuracy', 'loss']
NAMES = ['Accuracy', 'Micro-F1', 'Macro-F1', 'Weighted-F1', 'Balanced accuracy', 'Loss']


def cell(metric, value):
    return f'{value * 100:.4f}%' if metric in ['accuracy', 'balanced_accuracy'] else f'{value:.6f}'


def build(verification, project, job_url, version, archive_record):
    project, verification = Path(project).resolve(), Path(verification).resolve()
    accepted = json.loads(verification.read_text())
    assert accepted['status'] == 'accepted_complete' and accepted['test'] is not None
    private = Path(accepted['private_folder'])
    run = private / 'run'
    result = json.loads((private / 'IMAGE_JOB_RESULT.json').read_text())
    assert result['training_complete'] and result['test_complete']
    selected = accepted['selected']
    cfg = json.loads((run / 'protocol.json').read_text())['config']
    prefix = 'validation_epoch' + str(selected['epoch'])
    vm = json.loads((run / (prefix + '_metrics.json')).read_text())
    tm = accepted['test']['metrics']
    assert vm['samples'] == 59299 and tm['samples'] == 59270
    date = accepted['utc'][:10].replace('-', '')
    evidence = project / 'results/experiments/image_only' / accepted['attempt'] / ('final_' + str(version))
    evidence.mkdir(parents=True, exist_ok=False)
    for history in accepted['validations']:
        stem = 'validation_epoch' + str(history['epoch'])
        for suffix in ['metrics.json', 'classification_report.json', 'confusions.json', 'verified.json']:
            shutil.copyfile(run / (stem + '_' + suffix), evidence / (stem + '_' + suffix))
    for suffix in ['metrics.json', 'classification_report.json', 'confusions.json', 'independent_verification.json']:
        shutil.copyfile(run / ('test_' + suffix), evidence / ('test_' + suffix))
    shutil.copyfile(verification, evidence / 'independent_saved_verification.json')
    for name in ['final_selection_frozen.json', 'protocol.json', 'environment.json', 'selected_weight_roundtrip.json']:
        if (run / name).exists():
            shutil.copyfile(run / name, evidence / name)
    shutil.copyfile(private / 'RELEASE_RECORD.json', evidence / 'release_record.json')
    # Selection receipt includes history/hashes, never raw predictions or tensors.
    metrics_table = '| Metric | Selected validation | Final public test | Paper validation | Paper test |\n|---|---:|---:|---:|---:|\n'
    for key, name in zip(METRICS, NAMES):
        paper = ('75.29%', '75.49%') if key == 'accuracy' else ('not reported', 'not reported')
        metrics_table += f'| {name} | {cell(key, vm[key])} | {cell(key, tm[key])} | {paper[0]} | {paper[1]} |\n'
    history_table = '| Epoch | Train loss | Val accuracy | Micro-F1 | Macro-F1 | Weighted-F1 | Balanced accuracy | Val loss | Cumulative updates / AMP skips |\n|---:|---:|---:|---:|---:|---:|---:|---:|---:|\n'
    for h in accepted['run_history']:
        val = h['validation']
        history_table += f"| {h['epoch']} | {h['train_loss']:.6f} | {cell('accuracy', val['accuracy'])} | {val['micro_f1']:.6f} | {val['macro_f1']:.6f} | {val['weighted_f1']:.6f} | {cell('balanced_accuracy', val['balanced_accuracy'])} | {val['loss']:.6f} | {h['updates']} / {h['skips']} |\n"
    class_text = ''
    for split, stem in [('Validation', prefix), ('Public test', 'test')]:
        report = json.loads((run / (stem + '_classification_report.json')).read_text())
        confusions = json.loads((run / (stem + '_confusions.json')).read_text())
        class_text += f'\n### {split}\n\n| Class | Precision | Recall | F1 | Support |\n|---|---:|---:|---:|---:|\n'
        for label in LABELS:
            row = report[label]
            class_text += f"| {label} | {row['precision']:.6f} | {row['recall']:.6f} | {row['f1-score']:.6f} | {int(row['support'])} |\n"
        class_text += '\nConfusion rows are gold labels and columns are predictions, in label order0–5.\n\n| Gold / Pred | 0 | 1 | 2 | 3 | 4 | 5 |\n|---|---:|---:|---:|---:|---:|---:|\n'
        for index, row in enumerate(confusions['raw']):
            class_text += '| ' + str(index) + ' | ' + ' | '.join(str(v) for v in row) + ' |\n'
        class_text += '\nRow-normalized confusion percentages\n\n| Gold / Pred | 0 | 1 | 2 | 3 | 4 | 5 |\n|---|---:|---:|---:|---:|---:|---:|\n'
        for index, row in enumerate(confusions['row_normalized']):
            class_text += '| ' + str(index) + ' | ' + ' | '.join(f'{v * 100:.2f}%' for v in row) + ' |\n'
    test_classes = json.loads((run / 'test_classification_report.json').read_text())
    weakest = sorted(LABELS, key=lambda label: test_classes[label]['f1-score'])[:2]
    cm = json.loads((run / 'test_confusions.json').read_text())['raw']
    conf_pairs = sorted(((cm[i][j], i, j) for i in range(6) for j in range(6) if i != j), reverse=True)[:3]
    confusion_summary = ', '.join(f'{LABELS[i]} → {LABELS[j]} ({count} posts)' for count, i, j in conf_pairs)
    validation_delta, test_delta = vm['accuracy'] * 100 - 75.29, tm['accuracy'] * 100 - 75.49
    release = json.loads((private / 'release.json').read_text())
    report = f'''# Image-only ResNet-50 results

One seed42 experiment on the dataset (provided by the faculty), using the frozen usable-image cohort. {accepted['epochs_completed']} complete training epochs and {accepted['full_validations']} full validations. The registered maximum was four epochs. Selection used full validation Macro-F1, then lower loss, then earlier epoch. Epoch{selected['epoch']} won. One frozen59,270-row public-test evaluation completed and passed independent saved-CSV verification.

## Results

{metrics_table}
Validation accuracy is numerically {validation_delta:+.4f} percentage points against the paper image-only ResNet-50 value. Public-test accuracy is {test_delta:+.4f} points. The +1-point aspirations were76.29%validation/76.49%test. Validation target {'met' if validation_delta >= 1 else 'not met'}. Test target {'met' if test_delta >= 1 else 'not met'}.

The paper uses fixed ImageNet features and a different downstream feature/training pipeline. This run fine-tunes ResNet-50V2 end-to-end. The approved usable cohort excludes491 original decoding failures. The paper/release335-row discrepancy and3,561 cross-split image-byte duplicate groups remain limitations. This single-seed numerical comparison does not establish controlled superiority, significance or state of the art. [Original paper, Table4](https://arxiv.org/html/1911.03854v2).

## Training and checkpoint selection

{history_table}
Epoch counts are passes within one experiment. Training accuracy/F1 were not exported. Training loss is sample-weighted during optimization. Validation and test loss come from per-row FP32 cross-entropy. A higher accuracy epoch can lose to higher Macro-F1 under the registered rule. Small Macro-F1 gains may win selection without resetting the separate0.001 patience reference.

## Model and protocol

Pixels → strict RGB decoding → registered224×224 transform → ImageNet1KV2 ResNet-50 →2,048 pooled image features →dropout0.2→six-logit linear head. All layers fine-tuned. No text encoder, titles, OCR, captions, source metadata, projections or fusion enter the predictor. AdamW1e-4, weight decay1e-4 on matrices/convolutions and zero on bias/normalization, clip1.0, FP16AMP with FP32 parameters. Effective batch32, physical batch{cfg['micro_batch']}; config is authoritative. Linear warmup7,046 successful steps, decay over70,452 planned boundaries; scheduler advances only on successful updates. Early-stop evaluation begins after epoch3, patience2, delta0.001.

Official usable membership remains563,601train/59,299validation/59,270test. Original TSVs, IDs, split assignments and six-class labels are unchanged. The491 exclusions are399train/43validation/49test, comprising489False Connection and2Satire/Parody. Image-only starts from ImageNet, without the supervised fusion-trained encoder. The research categories are0True,1Satire/Parody,2Misleading Content,3Imposter Content,4False Connection and5Manipulated Content. A prediction describes a research-defined category and does not independently establish factual truth.

## Per-class evaluation and confusions
{class_text}
Paper per-class F1, precision, recall, balanced accuracy and loss are not reported. Table6 error counts are not F1. Lowest test F1 classes are{', '.join(weakest)}. Largest off-diagonal confusions are{confusion_summary}. Image-only evidence cannot directly establish a headline–image mismatch.

## Other completed modalities

The completed text-only BERT result used the original full released title cohort and selected epoch4. Its test accuracy is82.3901% and Macro-F1.774566. The completed text+image result uses the same usable-image cohort as this experiment and selected epoch4. Its test accuracy is88.1458%, Macro-F1.826415. These runs have different optimization and initialization. Fusion also used a supervised text warm start, so the descriptive differences do not isolate the effect of adding text.

## Verification, runtime and artifacts

Independent CPU readback checked all saved manifest members, model/optimizer/scheduler/scaler state, RNG/sampler/cursor, every complete validation export and the complete held-out test export. Exact IDs/golds/order/supports, six normalized probabilities, argmax, per-row CE, all aggregate/class metrics and raw/normalized confusions passed. Selected weights strict-loaded from saved private bytes. The separate evaluator starts in a fresh process after the pre-test freeze receipt and performs a validation-only logit reload check. CUDA recovery was independently exercised before release.

Kaggle job [{version}]({job_url}). Actual runtime versions are recorded in the resolved protocol. The model used{accepted['runtime_environment']['gpu']}device0 from aT4×2 allocation. Controller-measured training/evaluation wall time was{result['elapsed_seconds']:.1f}seconds, excluding initial notebook startup and final saved-output transfer. Preflight speeds were{release['timing']['train']['pairs_per_second']:.2f}train/{release['timing']['eval']['pairs_per_second']:.2f}evaluation images/s, with their measured batch/environment. These are preflight measurements.

Attempt `{accepted['attempt']}`. Selected epoch{selected['epoch']}, weights SHA-256 `{selected['weights_sha256']}`. Latest recovery SHA-256 `{accepted['recovery']['loaded']['sha256']}`. Private manifest SHA-256 `{accepted['manifest_sha256']}`. Private archive/readback record `{archive_record}`. Small numerical evidence `{evidence.relative_to(project)}`. Independent verification `{verification.relative_to(project)}`. Large predictions, raw images and tensors remain in ignored private storage and the private saved Kaggle version.

GitHub backup is pending until the intended results commit is pushed and independently read back. The completion receipt records the final verified backup. The existing main workflow/progress/comparison pages must use this new receipt when their image-only status is updated.
'''
    path = project / 'results' / ('IMAGE_ONLY_FINAL_REPORT_' + date + '.md')
    assert not path.exists(), 'Preserve an existing final report'
    path.write_text(report)
    receipt = {'utc': accepted['utc'], 'status': 'scientific_results_verified_backup_pending',
               'attempt': accepted['attempt'], 'selected_epoch': selected['epoch'],
               'epochs_trained': accepted['epochs_completed'], 'full_validations': accepted['full_validations'],
               'validation_metrics': vm, 'test_metrics': tm, 'selected_weights_sha256': selected['weights_sha256'],
               'recovery': accepted['recovery'], 'independent_verification': str(verification.relative_to(project)),
               'report': str(path.relative_to(project)), 'small_evidence': str(evidence.relative_to(project)),
               'private_archive_record': archive_record, 'job_url': job_url, 'script_version_id': version,
               'github_backup_verified': False, 'source_hashes': accepted['source_hashes']}
    (project / 'results' / ('IMAGE_ONLY_FINAL_COMPLETION_RECEIPT_' + date + '.json')).write_text(json.dumps(receipt, indent=2) + '\n')
    print(path)


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--verification', type=Path, required=True)
    p.add_argument('--project', type=Path, required=True)
    p.add_argument('--job-url', required=True)
    p.add_argument('--version', type=int, required=True)
    p.add_argument('--archive-record', required=True)
    args = p.parse_args()
    build(args.verification, args.project, args.job_url, args.version, args.archive_record)
