"""Pinned user-approved available-image cohort; originals remain unchanged.

This verifies row membership only. It never certifies image bytes or runs models.
"""
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

REGISTRATION = 'MM_PART1_USABLE_COHORT_REGISTRATION_20261024.json'
REGISTRATION_SHA = '3fe0b622958a1eee6732789d4f7acf6b450c0e3bda87312e5cbb6500fb405ce5'
COHORT = 'FACULTY-6W-USABLE-682170-v1'
PROTOCOL = 'OFFICIAL-6W-MM-USABLE-v2'
COUNTS = {'train': 563601, 'validation': 59299, 'test': 59270}
REQUIRED = 682170


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda: f.read(4 * 1024**2), b''):
            h.update(b)
    return h.hexdigest()


def registration(path):
    if sha(path) != REGISTRATION_SHA:
        raise ValueError('Approved cohort registration hash mismatch')
    value = json.loads(Path(path).read_text())
    if (value.get('approved') is not True or value.get('cohort_id') != COHORT
            or value.get('protocol_id') != PROTOCOL or value.get('usable_rows') != REQUIRED
            or value.get('split_counts') != COUNTS):
        raise ValueError('Wrong approved cohort')
    return value


def load_cohort(tsv_dir, registration_path, extraction_path, approval_path):
    reg = registration(registration_path)
    if sha(approval_path) != reg['approval_sha256']:
        raise ValueError('User approval receipt mismatch')
    if json.loads(Path(approval_path).read_text()).get('status') != 'approved_by_user':
        raise ValueError('User approval missing')
    if sha(extraction_path) != reg['extraction_report_sha256']:
        raise ValueError('Original extraction report hash mismatch')
    report = json.loads(Path(extraction_path).read_text())
    if (report.get('source_id') != reg['archive_source_id']
            or report.get('compressed_archive_sha256') != reg['archive_sha256']
            or report.get('compressed_archive_bytes') != reg['archive_bytes']
            or report.get('source_crc_consumed') is not True
            or report.get('required') != reg['original_rows']
            or report.get('usable') != REQUIRED
            or report.get('image_gate_passed') is not False):
        raise ValueError('Original all-row source evidence differs; never rewrite its failed gate')
    failures = report['decode_failures']
    excluded = {row['id'] for row in failures}
    fingerprint = hashlib.sha256(('\n'.join(sorted(excluded)) + '\n').encode()).hexdigest()
    if (len(failures) != len(excluded) or len(excluded) != reg['excluded_rows']
            or set(report['missing_ids']) != excluded or fingerprint != reg['excluded_ids_sha256']):
        raise ValueError('Exclusions differ from exact approved 491 IDs')
    all_ids, found, expected = set(), set(), {}
    counts, failed_counts, failed_classes = Counter(), Counter(), Counter()
    classes = {key: Counter() for key in COUNTS}
    for item in reg['original_files']:
        path = Path(tsv_dir) / item['filename']
        if sha(path) != item['sha256']:
            raise ValueError('Original faculty TSV hash mismatch: ' + item['filename'])
        count = 0
        with path.open(newline='') as stream:
            for row in csv.DictReader(stream, delimiter='\t'):
                ident = row['id']; label = int(row['6_way_label']); count += 1
                if ident in all_ids or not ident.isalnum() or label not in range(6) or not row['clean_title'].strip():
                    raise ValueError('Invalid/duplicate original row')
                all_ids.add(ident)
                split = item['split']
                if ident in excluded:
                    found.add(ident); failed_counts[split] += 1; failed_classes[str(label)] += 1
                else:
                    expected[ident] = {'id': ident, 'split': split,
                                       'clean_title': row['clean_title'], '6_way_label': label}
                    counts[split] += 1; classes[split][str(label)] += 1
        if count != item['rows']:
            raise ValueError('Original row count mismatch')
    if (len(all_ids) != reg['original_rows'] or found != excluded or len(expected) != REQUIRED
            or dict(counts) != COUNTS or dict(failed_counts) != reg['excluded_split_counts']
            or dict(failed_classes) != reg['excluded_class_counts']
            or {key: dict(value) for key, value in classes.items()} != reg['class_counts']):
        raise ValueError('Approved cohort membership/count/label audit failed')
    return expected, reg


def load_input(root):
    root = Path(root)
    reg = registration(root / 'results' / REGISTRATION)
    return load_cohort(root / 'data/official_multimodal_v2', root / 'results' / REGISTRATION,
                       root / 'results' / reg['extraction_report_file'],
                       root / 'results' / reg['approval_file'])
