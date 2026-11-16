"""One bounded one-hour CPU continuation over approved original shards.

Transport v4 retains the one-hour cap and adds failure evidence fallback.
Print original failure first; a disconnected Drive must not hide the cause.
All registered image bytes, cohort, hashes, model and scientific budgets stay fixed.
Existing closed packs are rehashed by the shared packer before any new copy.
"""
import fcntl
import json
import os
import sys
import tarfile
import traceback
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from usable_cohort_v2 import REGISTRATION, REGISTRATION_SHA, COHORT, load_cohort
from repack_usable_images_v2 import run as repack, prep
from verify_usable_image_shards_v2 import prepare

ROOT = Path('/content/drive/MyDrive/UROP/official_images_v1')


def publish_failure(failure, drive_path, scratch_root=Path('/content/urop_transport_evidence')):
    """Retain the original exception when Drive itself cannot save a report.

    Notebook output is first. Scratch is NOT durable across runtime loss;
    durability is true only for a successful private Drive write.
    """
    print(json.dumps(failure, allow_nan=False), flush=True)
    writes = {'job_id': failure['job_id'], 'state': 'transport_failure_evidence',
              'drive_saved': False, 'scratch_saved': False,
              'scratch_is_durable': False}
    try:
        scratch_root = Path(scratch_root)
        scratch_root.mkdir(parents=True, exist_ok=True)
        scratch = scratch_root / (failure['job_id'] + '_failure.json')
        prep.record(scratch, failure)
        writes.update(scratch_saved=True, scratch_file=str(scratch),
                      scratch_sha256=prep.sha(scratch))
    except Exception as error:
        writes['scratch_write_error'] = str(error)
    try:
        prep.record(drive_path, failure)
        writes.update(drive_saved=True, drive_file=str(drive_path),
                      drive_sha256=prep.sha(drive_path))
    except Exception as error:
        writes['drive_write_error'] = str(error)
    print(json.dumps(writes, allow_nan=False), flush=True)
    return writes


def run():
    job = 'CPU_USABLE_TRANSPORT_' + uuid.uuid4().hex
    started = False
    with open('/content/urop_stream_image_prep_v2.lock', 'a+') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            prep.require_drive(ROOT)
            guard = ROOT / 'USABLE_V2_TRANSPORT_JOB.json'
            if guard.exists():
                raise RuntimeError('Existing usable transport job guard: inspect real terminal output before any resume')
            reg = json.loads((ROOT / REGISTRATION).read_text())
            report = ROOT / reg['extraction_report_file']
            expected, reg = load_cohort(ROOT, ROOT / REGISTRATION, report, ROOT / reg['approval_file'])
            original = json.loads((ROOT / 'CPU_STREAM_PREP_87f54da6a55c47349ba79a6f6ab33747_result.json').read_text())
            if original.get('result') != json.loads(report.read_text()):
                raise ValueError('Exact original source terminal result differs')
            launch = {'utc': prep.now(), 'state': 'approved_usable_transport_started',
                      'job_id': job, 'pid': os.getpid(), 'cohort_id': COHORT,
                      'cohort_registration_sha256': REGISTRATION_SHA,
                      'required': len(expected), 'max_pack_seconds': 3600,
                      'source_originals_retained': True, 'training': False,
                      'test_inference': False,
                      'checkpoint': 'Closed immutable original-byte TARs and per-image SHA receipts; open orphans never trusted',
                      'recovery': 'Inspect exact terminal receipt/PID; verify original committed packs before an explicitly recorded bounded continuation',
                      'source_file_sha256': prep.sha(__file__)}
            prep.record(guard, launch)
            prep.record(ROOT / (job + '_launch.json'), launch)
            started = True
            print(json.dumps(launch), flush=True)
            packed = ROOT / 'kaggle_packed_usable_v2'
            result = repack(ROOT, packed, report, max_seconds=3600)
            metadata_done = False
            if result.get('complete'):
                metadata = ROOT / 'usable_metadata_v2'
                prepare(packed, metadata, packed / report.name, layout='kaggle-tar')
                transport = ROOT / 'usable_transfer_v2'
                transport.mkdir(exist_ok=True)
                for name in ['data', 'results']:
                    destination = transport / (name + '.tar')
                    if destination.exists():
                        raise ValueError('Existing metadata transport archive: preserve and verify before reuse')
                    with tarfile.open(destination, 'x') as archive:
                        for path in sorted((metadata / name).rglob('*')):
                            if path.is_file(): archive.add(path, arcname=str(path.relative_to(metadata / name)), recursive=False)
                    with destination.open('rb') as stream: os.fsync(stream.fileno())
                    prep.record(destination.with_suffix('.receipt.json'), {
                        'file': destination.name, 'bytes': destination.stat().st_size,
                        'sha256': prep.sha(destination), 'cohort_id': COHORT})
                metadata_done = True
            terminal = {'utc': prep.now(), 'state': 'approved_usable_transport_terminal',
                        'job_id': job, 'result': result, 'metadata_prepared': metadata_done,
                        'runtime_image_gate_passed': False, 'training': False, 'test_inference': False}
            prep.record(ROOT / (job + '_result.json'), terminal)
            print(json.dumps(terminal), flush=True)
        except Exception as error:
            failure = {'utc': prep.now(), 'state': 'approved_usable_transport_failed',
                       'job_id': job, 'started': started, 'error': str(error),
                       'traceback': traceback.format_exc(), 'runtime_image_gate_passed': False,
                       'recovery': 'Preserve original shards and every closed pack/receipt. Diagnose exact terminal cause; never restart extraction.'}
            if started:
                publish_failure(failure, ROOT / (job + '_failure.json'))
            else:
                print(json.dumps(failure), flush=True)
        finally:
            if started:
                from google.colab import drive
                try:
                    drive.flush_and_unmount(timeout_ms=600000)
                    print(json.dumps({'utc': prep.now(), 'state': 'usable_transport_drive_flush_completed', 'job_id': job}), flush=True)
                except Exception as error:
                    print(json.dumps({'utc': prep.now(), 'state': 'usable_transport_flush_unverified', 'job_id': job, 'error': str(error)}), flush=True)


if __name__ == '__main__':
    run()
