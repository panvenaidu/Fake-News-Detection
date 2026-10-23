"""Prepare private input metadata, then verify the actual unpacked cloud input.

Preparing metadata NEVER passes the image gate. Only verify-unpacked can issue
a passing runtime coverage receipt after every expected file is hashed/decoded.
No models, CUDA allocation, downloads, authentication or test inference.
"""
import argparse
import csv
import hashlib
import importlib.util
import io
import json
import os
import shutil
import uuid
from collections import Counter, defaultdict
from pathlib import Path, PurePosixPath

from PIL import Image

_spec = importlib.util.spec_from_file_location(
    'imageprep', Path(__file__).resolve().parents[1] / 'collab/prepare_official_images_drive_v1.py')
prep = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(prep)

ARCHIVE_BYTES = 113623359224
REQUIRED = 682661
COUNTS = {'train': 564000, 'validation': 59342, 'test': 59319}
COLUMNS = ['id', 'split', 'clean_title', '6_way_label', 'image_path',
           'image_sha256', 'bytes', 'source_shard', 'source_member']


def digest_valid(value):
    return isinstance(value, str) and len(value) == 64 and all(c in '0123456789abcdef' for c in value)


def safe_path(root, relative):
    root = Path(root).resolve()
    relative = PurePosixPath(relative)
    if relative.is_absolute() or '..' in relative.parts:
        raise ValueError('Absolute/traversing input path')
    result = (root / str(relative)).resolve()
    if not result.is_relative_to(root):
        raise ValueError('Input path escapes root')
    return result


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.tmp-' + uuid.uuid4().hex)
    with temporary.open('x') as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def receipt_rows(source, expected):
    """Strict semantic joins; existing TAR bytes are verified in the runtime."""
    rows = {}
    shards = []
    for path in sorted((Path(source) / 'shards').glob('*.receipt.json')):
        receipt = json.loads(path.read_text())
        archive = safe_path(Path(source) / 'shards', receipt['archive'])
        if archive.name != receipt['archive'] or archive.suffix != '.tar':
            raise ValueError('Unexpected shard path')
        if not archive.is_file() or archive.stat().st_size != receipt['bytes']:
            raise ValueError('Committed shard missing/size mismatch: ' + archive.name)
        if not digest_valid(receipt['sha256']):
            raise ValueError('Invalid shard checksum')
        for row in receipt['images']:
            ident = row['id']
            if ident not in expected or ident in rows:
                raise ValueError('Unexpected/duplicate committed ID: ' + ident)
            for key in ['split', 'clean_title', '6_way_label']:
                if row[key] != expected[ident][key]:
                    raise ValueError('Official metadata mismatch for ' + ident + ': ' + key)
            member = PurePosixPath(row['member'])
            original = PurePosixPath(row['source_member'])
            if (member.parent != PurePosixPath('images') or member.stem != ident
                    or original.parent != PurePosixPath('public_image_set')
                    or original.name != member.name):
                raise ValueError('Unexpected image member/source path: ' + ident)
            if not digest_valid(row['image_sha256']) or not 0 < row['bytes'] <= 512 * 1024**2:
                raise ValueError('Invalid image checksum/size: ' + ident)
            rows[ident] = {**expected[ident], 'image_path': str(member),
                           'image_sha256': row['image_sha256'], 'bytes': row['bytes'],
                           'source_shard': archive.name, 'source_member': str(original)}
        shards.append({'file': archive.name, 'bytes': receipt['bytes'],
                       'sha256': receipt['sha256'], 'images': len(receipt['images']),
                       'receipt_sha256': prep.sha(path)})
    if set(rows) != set(expected):
        missing = sorted(set(expected) - set(rows))
        raise ValueError('Incomplete committed cohort: %d missing; first IDs %s' % (len(missing), missing[:20]))
    return rows, shards


def prepare(source, output, extraction_report):
    source, output = Path(source).resolve(), Path(output).resolve()
    if source == output or source.is_relative_to(output) or output.is_relative_to(source):
        raise ValueError('Metadata output must be separate from original source/shards')
    expected = prep.expected_rows(source)
    if len(expected) != REQUIRED or dict(Counter(r['split'] for r in expected.values())) != COUNTS:
        raise ValueError('Wrong official input cohort')
    extraction_report = Path(extraction_report)
    complete = json.loads(extraction_report.read_text())
    if (complete.get('image_gate_passed') is not True or complete.get('required') != REQUIRED
            or complete.get('usable') != REQUIRED or complete.get('missing_ids')
            or complete.get('decode_failures') or complete.get('compressed_archive_bytes') != ARCHIVE_BYTES
            or not digest_valid(complete.get('compressed_archive_sha256'))):
        raise ValueError('Complete archive CRC/hash/coverage evidence required')
    rows, shards = receipt_rows(source, expected)
    # Original archive is not copied into the private training input.
    output.mkdir(parents=True, exist_ok=True)
    tsvdir = output / 'data/official_multimodal_v2'
    tsvdir.mkdir(parents=True, exist_ok=True)
    provenance = []
    for split, name, fileid, digest, count in prep.TSVS:
        destination = tsvdir / name
        if destination.exists() and prep.sha(destination) != digest:
            raise ValueError('Existing official TSV conflict: ' + name)
        if not destination.exists():
            shutil.copyfile(source / name, destination)
        assert prep.sha(destination) == digest
        provenance.append({'filename': name, 'sha256': digest, 'rows': count,
                           'split': split, 'source_id': fileid})
    pairdir = output / 'data/official_paired_v1'
    pairdir.mkdir(parents=True, exist_ok=True)
    manifest = pairdir / 'paired_manifest.csv'
    temporary = manifest.with_name(manifest.name + '.tmp-' + uuid.uuid4().hex)
    with temporary.open('x', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=COLUMNS)
        writer.writeheader()
        for ident in expected:
            writer.writerow(rows[ident])
        stream.flush()
        os.fsync(stream.fileno())
    if manifest.exists() and prep.sha(manifest) != prep.sha(temporary):
        raise ValueError('Existing paired manifest conflict; preserve both generations')
    os.replace(temporary, manifest)
    content = defaultdict(list)
    for row in rows.values():
        content[row['image_sha256']].append({'id': row['id'], 'split': row['split']})
    cross_split = {digest: group for digest, group in content.items()
                   if len({r['split'] for r in group}) > 1}
    write_json(pairdir / 'cross_split_content_duplicates.json', cross_split)
    write_json(output / 'results/official_dataset_provenance.json', {
        'utc': prep.now(), 'files': provenance,
        'faculty_dataset': 'https://drive.google.com/drive/folders/1DuH0YaEox08ZwzZDpRMOaFpMCeRyxiEF',
        'source_archive_sha256': complete['compressed_archive_sha256'],
        'source_archive_bytes': ARCHIVE_BYTES,
        'extraction_report_sha256': prep.sha(extraction_report),
        'source_script_sha256': prep.sha(Path(__file__).resolve().parents[1] / 'collab/prepare_official_images_drive_v1.py'),
    })
    receipt = {
        'utc': prep.now(), 'image_gate_passed': False,
        'shard_metadata_gate_passed': True, 'runtime_image_bytes_verified': False,
        'required': REQUIRED, 'split_counts': COUNTS, 'manifest_sha256': prep.sha(manifest),
        'shards': shards, 'image_bytes': sum(row['bytes'] for row in rows.values()),
        'cross_split_content_duplicate_groups': len(cross_split),
        'exclusions_or_resampling': False,
        'status': 'Metadata prepared only. Upload shards plus this metadata privately, then verify actual unpacked input before training.',
    }
    write_json(output / 'results/official_image_coverage_v1.json', receipt)
    print(json.dumps({k: v for k, v in receipt.items() if k != 'shards'}, indent=2))
    return receipt


def verify_unpacked(root, output):
    root = Path(root).resolve()
    if Path(output).resolve().is_relative_to(root):
        raise ValueError('Runtime receipt must be outside immutable private dataset input')
    source = root / 'data/official_multimodal_v2'
    expected = prep.expected_rows(source)
    if len(expected) != REQUIRED:
        raise ValueError('Wrong official row count')
    coverage = json.loads((root / 'results/official_image_coverage_v1.json').read_text())
    if coverage.get('shard_metadata_gate_passed') is not True:
        raise ValueError('Complete metadata preparation required')
    manifest = root / 'data/official_paired_v1/paired_manifest.csv'
    if prep.sha(manifest) != coverage['manifest_sha256']:
        raise ValueError('Runtime manifest checksum mismatch')
    seen = set()
    counts = Counter()
    with manifest.open(newline='') as stream:
        for row in csv.DictReader(stream):
            ident = row['id']
            if ident not in expected or ident in seen:
                raise ValueError('Wrong/duplicate runtime image ID: ' + ident)
            for key in ['split', 'clean_title', '6_way_label']:
                if str(row[key]) != str(expected[ident][key]):
                    raise ValueError('Official runtime metadata mismatch: ' + ident)
            path = safe_path(root, row['image_path'])
            member = PurePosixPath(row['image_path'])
            if member.parent != PurePosixPath('images') or member.stem != ident:
                raise ValueError('Invalid image path: ' + ident)
            if not path.is_file() or path.stat().st_size != int(row['bytes']):
                raise ValueError('Missing/size-mismatched runtime image: ' + ident)
            raw = path.read_bytes()
            if hashlib.sha256(raw).hexdigest() != row['image_sha256']:
                raise ValueError('Runtime image checksum mismatch: ' + ident)
            with Image.open(io.BytesIO(raw)) as image:
                image.load()
                image.convert('RGB').load()
            seen.add(ident)
            counts[row['split']] += 1
            if len(seen) % 10000 == 0:
                print(json.dumps({'utc': prep.now(), 'state': 'verifying_unpacked_input',
                                  'verified': len(seen), 'required': REQUIRED}), flush=True)
    if seen != set(expected) or dict(counts) != COUNTS:
        raise ValueError('Incomplete runtime image cohort')
    receipt = {**coverage, 'utc': prep.now(), 'image_gate_passed': True,
               'runtime_image_bytes_verified': True, 'runtime_root': str(root),
               'usable': len(seen), 'split_counts': dict(counts),
               'verifier_sha256': prep.sha(__file__),
               'status': 'Every official paired runtime image hashed and decoded; no model inference'}
    write_json(output, receipt)
    print(json.dumps({k: v for k, v in receipt.items() if k != 'shards'}, indent=2))
    return receipt


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest='mode', required=True)
    metadata = subparsers.add_parser('prepare-metadata')
    metadata.add_argument('--source-root', type=Path, required=True)
    metadata.add_argument('--output-root', type=Path, required=True)
    metadata.add_argument('--extraction-report', type=Path, required=True)
    runtime = subparsers.add_parser('verify-unpacked')
    runtime.add_argument('--root', type=Path, required=True)
    runtime.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.mode == 'prepare-metadata':
        prepare(args.source_root, args.output_root, args.extraction_report)
    else:
        verify_unpacked(args.root, args.output)
