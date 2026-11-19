"""Independent prediction-only audit; does not load or evaluate a model."""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'testing/text_plus_image'))
sys.path.insert(0, str(ROOT / 'training/text_plus_image/Scripts'))
from verify_multimodal_final_v1 import verify, sha
from usable_cohort_v2 import load_input

BASELINE_SHA = '9b987c5e2699b288dbdf0aabc57f15122776184fda81f1b972039807adce83ec'


def run(a):
    expected, _ = load_input(a.root)
    official = pd.DataFrame([row for row in expected.values() if row['split'] == 'test'])
    if len(official) != 59270:
        raise ValueError('Unexpected official test cohort')
    new = verify(a.run, 'test', official, 'test')
    if sha(a.baseline / 'test_predictions.csv') != BASELINE_SHA:
        raise ValueError('Baseline prediction hash differs')
    old = verify(a.baseline, 'test', official, 'test')
    n = pd.read_csv(a.run / 'test_predictions.csv', dtype={'id': str})
    b = pd.read_csv(a.baseline / 'test_predictions.csv', dtype={'id': str})
    if not np.array_equal(n.id.to_numpy(), b.id.to_numpy()) or not np.array_equal(n.true_label.to_numpy(), b.true_label.to_numpy()):
        raise ValueError('Paired IDs or labels differ')
    nc = n.true_label.to_numpy() == n.predicted_label.to_numpy()
    bc = b.true_label.to_numpy() == b.predicted_label.to_numpy()
    frozen = json.loads((a.run / 'final_selection_frozen.json').read_text())
    start = json.loads((a.run / 'test_start.json').read_text())
    weights = a.run / frozen['selected']['weights_file']
    weight_sha = sha(weights)
    if weight_sha != frozen['selected']['weights_sha256'] or weight_sha != start['weights_sha256'] or sha(a.run / 'final_selection_frozen.json') != start['selection_receipt_sha256']:
        raise ValueError('Frozen checkpoint identity differs')
    result = {'status': 'passed', 'selected_checkpoint_sha256': weight_sha,
              'new': new, 'baseline': old, 'target_89_percent_reached': bool(nc.mean() >= .89),
              'accuracy_difference_percentage_points': float((nc.mean()-bc.mean())*100),
              'paired_counts': {'both_correct': int((nc & bc).sum()), 'new_only_correct': int((nc & ~bc).sum()),
                                'baseline_only_correct': int((~nc & bc).sum()), 'both_wrong': int((~nc & ~bc).sum())}}
    a.output.write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    for name in ('root', 'run', 'baseline', 'output'):
        p.add_argument('--' + name, type=Path, required=True)
    run(p.parse_args())
