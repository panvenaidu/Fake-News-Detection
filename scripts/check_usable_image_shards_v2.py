"""Synthetic six-image checks for private input metadata/runtime gate separation."""
import csv
import io
import json
import shutil
import tarfile
import tempfile
from pathlib import Path
from unittest.mock import patch

from PIL import Image

import verify_usable_image_shards_v2 as verifier


def rejected(function, contains):
    try:
        function()
    except (ValueError, OSError) as error:
        assert contains in str(error), str(error)
    else:
        raise AssertionError('Invalid input accepted: ' + contains)


def main():
    fixture_parent = Path('data/official_paired_v2')
    fixture_parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=fixture_parent, prefix='input-gate-') as temporary:
        base = Path(temporary).resolve()
        source, metadata = base / 'source', base / 'metadata'
        source.mkdir()
        expected, definitions = {}, []
        names = ['multimodal_train.tsv', 'multimodal_validate.tsv', 'multimodal_test_public.tsv']
        for index, (split, name) in enumerate(zip(['train', 'validation', 'test'], names)):
            rows = []
            for offset in range(2):
                number = 2 * index + offset
                row = {'id': 's' + str(number), 'split': split,
                       'clean_title': 'synthetic, title\n' + str(number), '6_way_label': number}
                expected[row['id']] = row
                rows.append(row)
            with (source / name).open('w', newline='') as stream:
                writer = csv.DictWriter(stream, fieldnames=['id', 'split', 'clean_title', '6_way_label'], delimiter='\t')
                writer.writeheader()
                writer.writerows(rows)
            definitions.append((split, name, 'synthetic-file', verifier.prep.sha(source / name), 2))
        archive = source / 'public_images.tar.bz2'
        with tarfile.open(archive, 'w:bz2') as output:
            for index, ident in enumerate(expected):
                content = io.BytesIO()
                image = Image.new(['RGB', 'L', 'P', 'RGBA'][index % 4], (22, 18))
                image.save(content, format='PNG')
                raw = content.getvalue()
                entry = tarfile.TarInfo('public_image_set/' + ident + '.png')
                entry.size = len(raw)
                output.addfile(entry, io.BytesIO(raw))
        counts = {'train': 2, 'validation': 2, 'test': 2}
        with patch.object(verifier.prep, 'TSVS', definitions), patch.object(verifier, 'REQUIRED', 6), patch.object(verifier, 'COUNTS', counts), patch.object(verifier, 'ARCHIVE_BYTES', archive.stat().st_size):
            complete = verifier.prep.extract(source, expected)
            report = next(source.glob('extraction_*.json'))
            assert complete['image_gate_passed']
            reg={'approval_file':'approval.json','extraction_report_file':report.name,'extraction_report_sha256':verifier.prep.sha(report),'excluded_ids_sha256':'0'*64}
            (source/verifier.REGISTRATION).write_text('{}');(source/'approval.json').write_text('{}')
            policy_patches=[patch.object(verifier,'registration',return_value=reg),patch.object(verifier,'load_cohort',return_value=(expected,reg)),patch.object(verifier,'load_input',return_value=(expected,reg))]
            for policy_patch in policy_patches:policy_patch.start()
            prepared = verifier.prepare(source, metadata, report)
            assert prepared['image_gate_passed'] is False and prepared['shard_metadata_gate_passed'] is True
            assert not (metadata / 'images').exists(), 'Metadata prep unexpectedly materialized images'
            for receipt in (source / 'shards').glob('*.receipt.json'):
                item = json.loads(receipt.read_text())
                with tarfile.open(source / 'shards' / item['archive']) as shard:
                    for row in item['images']:
                        destination = verifier.safe_path(metadata, Path(item['archive']).stem + '/' + row['member'])
                        destination.parent.mkdir(parents=True, exist_ok=True)
                        destination.write_bytes(shard.extractfile(row['member']).read())
            result = verifier.verify_unpacked(metadata, base / 'runtime_receipt.json')
            assert result['image_gate_passed'] is True and result['usable'] == 6 and result['split_counts'] == counts
            first = next(metadata.glob('images_*/images/s0.png'))
            original = first.read_bytes()
            first.write_bytes(b'X' * len(original))
            rejected(lambda: verifier.verify_unpacked(metadata, base / 'corrupt.json'), 'checksum mismatch: s0')
            first.unlink()
            rejected(lambda: verifier.verify_unpacked(metadata, base / 'missing.json'), 'Missing/size-mismatched runtime image: s0')
            external = base / 'outside.png'
            external.write_bytes(original)
            first.symlink_to(external)
            rejected(lambda: verifier.verify_unpacked(metadata, base / 'escape.json'), 'escapes root')
            first.unlink()
            first.write_bytes(original)
            rejected(lambda: verifier.verify_unpacked(metadata, metadata / 'mutable.json'), 'outside immutable')
            receipt = next((source / 'shards').glob('*.receipt.json'))
            saved = receipt.read_text()
            tampered = json.loads(saved)
            tampered['images'][0]['6_way_label'] = 5
            receipt.write_text(json.dumps(tampered))
            rejected(lambda: verifier.receipt_rows(source, expected), 'Official metadata mismatch')
            receipt.write_text(saved)
            bad_report = json.loads(report.read_text())
            bad_report['image_gate_passed'] = False
            (base / 'incomplete.json').write_text(json.dumps(bad_report))
            rejected(lambda: verifier.prepare(source, base / 'not-ready', base / 'incomplete.json'), 'Original failed gate proof')
            for policy_patch in policy_patches:policy_patch.stop()
    result = {
        'utc': verifier.prep.now(),
        'status': 'passed', 'scope': 'Six synthetic images test metadata/runtime-byte guards; policy loader is mocked ONLY here and separately checked against all real TSVs; no model inference',
        'verifier_sha256': verifier.prep.sha(Path(verifier.__file__)),
        'test_sha256': verifier.prep.sha(__file__),
        'input_layout_tested': 'kaggle-tar',
        'checks': ['Metadata preparation never opens image gate',
                   'Actual unpacked images all hashed/decoded before runtime gate',
                   'RGB, grayscale, palette and RGBA decode',
                   'Official title/label/split joins including multiline CSV text',
                   'Corrupt/missing image and symlink escape rejected',
                   'Runtime receipt cannot mutate immutable input',
                   'Altered receipt labels and incomplete extraction rejected'],
        'limitations': ['Real full-cohort manifest/private Kaggle import still pending'],
    }
    Path('results/usable_image_shard_verifier_checks_20261024.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
