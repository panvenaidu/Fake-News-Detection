"""Verify every approved faculty image in Kaggle's immutable packed input.

The source TAR bytes are unchanged. This CPU gate checks the official join,
full archive SHA, every member SHA and strict decode before issuing coverage.
The SQLite index resumes at fully committed archive boundaries.
"""
import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path, PurePosixPath

from packed_image_io_v3 import create_index, packed_name, sha
from usable_cohort_v2 import load_input, COHORT, REGISTRATION_SHA

COUNTS = {'train': 563601, 'validation': 59299, 'test': 59270}
REQUIRED = sum(COUNTS.values())


def verify(root, output, dataset_version):
    root, output = Path(root).resolve(), Path(output).resolve()
    if output.is_relative_to(root):
        raise ValueError('Gate output must be outside immutable input')
    expected, registration = load_input(root)
    if len(expected) != REQUIRED or dict(Counter(r['split'] for r in expected.values())) != COUNTS:
        raise ValueError('Wrong approved cohort')
    meta = root / 'results/usable_image_coverage_v2.json'
    coverage = json.loads(meta.read_text())
    if (coverage.get('cohort_id') != COHORT or
            coverage.get('cohort_registration_sha256') != REGISTRATION_SHA or
            coverage.get('required') != REQUIRED or
            coverage.get('split_counts') != COUNTS or
            coverage.get('shard_metadata_gate_passed') is not True):
        raise ValueError('Wrong approved source metadata')
    shards = coverage['shards']
    if len(shards) != 39 or sum(int(s['images']) for s in shards) != REQUIRED:
        raise ValueError('Wrong archive membership count')
    names = {s['file'] for s in shards}
    if len(names) != len(shards):
        raise ValueError('Duplicate archive name')
    if any(not (root / packed_name(s['file'])).is_file() for s in shards):
        raise ValueError('Missing packed Kaggle source archive')
    manifest = root / 'data/official_paired_v2/paired_manifest.csv'
    if sha(manifest) != coverage['manifest_sha256']:
        raise ValueError('Packed input manifest checksum mismatch')
    rows, seen, counts = [], set(), Counter()
    with manifest.open(newline='') as stream:
        for row in csv.DictReader(stream):
            ident = row['id']
            if ident not in expected or ident in seen:
                raise ValueError('Unexpected or duplicate paired ID')
            seen.add(ident)
            if any(str(row[k]) != str(expected[ident][k]) for k in
                   ['split', 'clean_title', '6_way_label']):
                raise ValueError('Paired title/label/split differs from official TSV')
            archive = row['source_shard']
            member = PurePosixPath(row['image_path'])
            if (archive not in names or member.parent != PurePosixPath(Path(archive).stem) / 'images'
                    or member.stem != ident or int(row['bytes']) <= 0):
                raise ValueError('Paired image path/size differs from approved layout')
            rows.append(row)
            counts[row['split']] += 1
    if seen != set(expected) or dict(counts) != COUNTS:
        raise ValueError('Incomplete approved image cohort')
    output.mkdir(parents=True, exist_ok=True)
    index = output / 'packed_image_index.sqlite'
    receipt = output / 'packed_runtime_coverage.json'
    if index.exists() or receipt.exists():
        if not index.exists() or not receipt.exists():
            raise ValueError('Existing index/receipt mismatch; preserve for inspection')
        prior = json.loads(receipt.read_text())
        if (prior.get('image_gate_passed') is not True or prior.get('dataset_version') != dataset_version
                or prior.get('runtime_root') != str(root) or prior.get('manifest_sha256') != sha(manifest)
                or prior.get('packed_index_sha256') != sha(index)):
            raise ValueError('Existing packed gate cannot be reused')
        return prior
    result = create_index(root, shards, rows, index)
    value = {**coverage, 'image_gate_passed': True, 'runtime_image_bytes_verified': True,
             'usable': REQUIRED, 'split_counts': dict(counts), 'runtime_root': str(root),
             'dataset_version': dataset_version, 'input_layout': 'kaggle-packed-bin',
             'packed_index': str(index), 'packed_index_sha256': result['index_sha256'],
             'packed_adapter_sha256': sha(Path(__file__).with_name('packed_image_io_v3.py')),
             'gate_source_sha256': sha(__file__), 'metadata_sha256': sha(meta),
             'official_input_registration_sha256': REGISTRATION_SHA,
             'status': 'Every approved image decoded and hashed from exact pinned TAR bytes; no inference'}
    temporary = receipt.with_suffix('.json.tmp')
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')
    temporary.replace(receipt)
    print(json.dumps({'state': 'packed_runtime_image_gate_passed', 'usable': REQUIRED,
                      'dataset_version': dataset_version, 'index_sha256': result['index_sha256'],
                      'training': False, 'test_inference': False}), flush=True)
    return value


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--root', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--dataset-version', type=int, required=True)
    a = p.parse_args()
    verify(a.root, a.output, a.dataset_version)
