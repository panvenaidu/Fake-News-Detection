"""Run only AFTER the current source job terminates and Drive is remounted.

One bounded CPU transport-pack job. No download, GPU or model execution. Never
queue/run this in parallel with the source extraction. An incomplete source
result or missing approved Drive mount fails before any packing.
"""
from pathlib import Path
import fcntl
import hashlib
import json
import os
import subprocess
import sys
import traceback
import uuid
import zipfile

ROOT = Path('/content/drive/MyDrive/UROP/official_images_v1')
SOURCE_JOB = 'CPU_STREAM_PREP_87f54da6a55c47349ba79a6f6ab33747'
BUNDLE = 'UROP_MM_PART1_SOURCE_BUNDLE_20261024.zip'
BUNDLE_SHA = 'e52dc84c4f05ec8f712bedd0fdc624d00c3fc32cd659e869e11749d8a972aa20'
RUN_JOB = None


def checksum(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for data in iter(lambda: stream.read(4 * 1024**2), b''):
            h.update(data)
    return h.hexdigest()


def complete_source(result):
    value = result.get('result', {})
    if (result.get('job_id') != SOURCE_JOB
            or value.get('image_gate_passed') is not True
            or value.get('required') != 682661 or value.get('usable') != 682661
            or value.get('compressed_archive_bytes') != 113623359224
            or value.get('source_id') != '1cjY6HsHaSZuLVHywIxD5xQqng33J5S2b'
            or value.get('source_crc_consumed') is not True
            or value.get('missing_ids') or value.get('decode_failures')
            or len(value.get('compressed_archive_sha256', '')) != 64
            or any(c not in '0123456789abcdef' for c in value['compressed_archive_sha256'])):
        raise ValueError('Original complete source CRC/SHA/682661 coverage required')
    return value


def run():
    global RUN_JOB
    if not Path('/content/drive/MyDrive').is_dir():
        raise RuntimeError('Remount the existing approved Drive through Colab first')
    # Keep the exact source attempt immutable while deriving transport copies.
    with open('/content/urop_stream_image_prep_v2.lock', 'a+') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        result = json.loads((ROOT / (SOURCE_JOB + '_result.json')).read_text())
        outcome = complete_source(result)
        matches = [p for p in ROOT.glob('extraction_*.json')
                   if json.loads(p.read_text()) == outcome]
        if len(matches) != 1:
            raise ValueError('Require the unique actual source extraction report')
        bundle = ROOT / BUNDLE
        if checksum(bundle) != BUNDLE_SHA:
            raise ValueError('Owned source bundle checksum mismatch')
        deployed = ROOT / ('owned_source_' + BUNDLE_SHA[:16])
        with zipfile.ZipFile(bundle) as archive:
            manifest = json.loads(archive.read('SOURCE_MANIFEST.json'))
            expected = {x['path']: x for x in manifest['files']}
            if set(archive.namelist()) != set(expected) | {'SOURCE_MANIFEST.json'}:
                raise ValueError('Unexpected bundle members')
            for relative, item in expected.items():
                path = (deployed / relative).resolve()
                if not path.is_relative_to(deployed.resolve()):
                    raise ValueError('Unsafe source bundle path')
                data = archive.read(relative)
                if len(data) != item['bytes'] or hashlib.sha256(data).hexdigest() != item['sha256']:
                    raise ValueError('Source member checksum mismatch')
                if path.exists() and checksum(path) != item['sha256']:
                    raise ValueError('Existing deployment differs; preserve it')
                path.parent.mkdir(parents=True, exist_ok=True)
                if not path.exists():
                    with path.open('xb') as target:
                        target.write(data); target.flush(); os.fsync(target.fileno())
        sys.path.insert(0, str(deployed / 'collab'))
        import prepare_official_images_drive_v1 as prep
        prep.require_drive(ROOT)
        job = 'CPU_TRANSPORT_PACK_' + uuid.uuid4().hex
        RUN_JOB = job
        launch = {'utc': prep.now(), 'job_id': job, 'source_job': SOURCE_JOB,
                  'source_result_sha256': checksum(ROOT / (SOURCE_JOB + '_result.json')),
                  'extraction_report': matches[0].name, 'extraction_report_sha256': checksum(matches[0]),
                  'bundle_sha256': BUNDLE_SHA, 'max_pack_seconds': 3600,
                  'scientific_training': False, 'test_inference': False}
        prep.record(ROOT / (job + '_launch.json'), launch)
        print(json.dumps(launch), flush=True)
        packed = ROOT / 'kaggle_packed_v1'
        log = ROOT / (job + '_console.jsonl')
        with log.open('x') as stream:
            subprocess.run([sys.executable, '-u', str(deployed / 'collab/repack_official_images_kaggle_v1.py'),
                            '--source-root', str(ROOT), '--output-root', str(packed),
                            '--extraction-report', str(matches[0]), '--max-seconds', '3600'],
                           check=True, stdout=stream, stderr=subprocess.STDOUT)
        lines = log.read_text().strip().splitlines()
        packed_result = json.loads(lines[-1])
        if packed_result.get('complete'):
            metadata = ROOT / 'prepared_kaggle_metadata_v1'
            subprocess.run([sys.executable, '-u', str(deployed / 'scripts/verify_official_image_shards_v1.py'),
                            'prepare-metadata', '--source-root', str(packed), '--output-root', str(metadata),
                            '--extraction-report', str(packed / matches[0].name), '--layout', 'kaggle-tar'],
                           check=True)
        value = {'utc': prep.now(), 'job_id': job, 'result': packed_result,
                 'metadata_prepared': bool(packed_result.get('complete')),
                 'actual_training_runtime_image_gate': False,
                 'source_originals_preserved': True,
                 'next': 'Verify Drive flush, retrieve pack/metadata receipts and exact bytes, then private full-input upload/runtime audit. No training yet.'}
        prep.record(ROOT / (job + '_result.json'), value)
        print(json.dumps(value), flush=True)
    from google.colab import drive
    drive.flush_and_unmount(timeout_ms=600000)
    print(json.dumps({'utc': prep.now(), 'state': 'transport_pack_drive_flush_completed', 'job_id': job}), flush=True)


if __name__ == '__main__':
    try:
        run()
    except Exception as error:
        failure = {'state': 'transport_pack_failed', 'job_id': RUN_JOB,
                   'error': str(error), 'traceback': traceback.format_exc(),
                   'recovery': 'Preserve all committed receipts and untrusted orphans. Diagnose exact failure before resuming; no source extraction restart implied.',
                   'actual_training_runtime_image_gate': False}
        if ROOT.is_dir():
            try:
                with (ROOT / ('transport_failure_' + uuid.uuid4().hex + '.json')).open('x') as stream:
                    json.dump(failure, stream, indent=2); stream.flush(); os.fsync(stream.fileno())
            except Exception as save_error:
                failure['failure_receipt_write_error'] = str(save_error)
        print(json.dumps(failure), flush=True)
        # A failed pack may still have closed shards awaiting Drive upload.
        # Flush them when possible; a successful flush does not fix the failure.
        if RUN_JOB is not None and Path('/content/drive/MyDrive').is_dir():
            try:
                from google.colab import drive
                drive.flush_and_unmount(timeout_ms=600000)
                print(json.dumps({'state': 'failed_pack_pending_writes_flushed', 'job_id': RUN_JOB}), flush=True)
            except Exception as flush_error:
                print(json.dumps({'state': 'failed_pack_flush_unverified', 'error': str(flush_error)}), flush=True)
