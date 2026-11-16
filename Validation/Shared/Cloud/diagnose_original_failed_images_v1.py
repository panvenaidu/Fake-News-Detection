"""Bounded CPU inspection of a few failed ORIGINAL archive members.

No dataset changes, alternate URLs, relaxed decoder flags, model inference or
full archive download. Raw specimens and full diagnostics stay private on Drive.
"""
import bz2
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import tarfile
import time
import uuid

ROOT = Path('/content/drive/MyDrive/UROP/official_images_v1')
REPORT = 'extraction_7f55c34bcfa94cf09b61e3884590e49d.json'
REPORT_SHA = '262a40e9e04629cda8c13388478a112016ba17ef42ed2d423bc517dc8911ebe0'
STREAM_SHA = '5b9be91021d4d397d8f3bd74c0354d0496b7cfb685723cf2c3c3ee24ea6266e6'


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for value in iter(lambda: f.read(1024**2), b''):
            h.update(value)
    return h.hexdigest()


def payload_kind(raw):
    prefix = raw[:4096].lstrip().lower()
    if prefix.startswith(b'<!doctype html') or prefix.startswith(b'<html'):
        return 'HTML document, not a raster image'
    if prefix.startswith(b'<?xml') or prefix.startswith(b'<svg'):
        return 'XML/SVG document; inspect privately before any conversion'
    for signature, name in [(b'\xff\xd8\xff', 'JPEG'), (b'\x89PNG\r\n\x1a\n', 'PNG'),
                            (b'GIF87a', 'GIF'), (b'GIF89a', 'GIF'), (b'%PDF-', 'PDF')]:
        if raw.startswith(signature):
            return name
    if raw.startswith(b'RIFF') and raw[8:12] == b'WEBP':
        return 'WebP'
    if raw[4:8] == b'ftyp':
        return 'ISO base-media container; codec not inferred'
    return 'Unknown signature'


class DiagnosticBoundary(Exception):
    pass


class LimitedReader:
    def __init__(self, reader, byte_budget, deadline):
        self.reader = reader
        self.budget = byte_budget
        self.deadline = deadline

    def read(self, size=-1):
        if time.monotonic() >= self.deadline or self.reader.pos >= self.budget:
            raise DiagnosticBoundary('Bounded time/byte limit reached; no full source scan')
        remaining = self.budget - self.reader.pos
        return self.reader.read(min(size if size >= 0 else 1024**2, remaining))

    def readable(self):
        return True

    def seekable(self):
        return False


def run(max_bytes=512*1024**2, max_seconds=180, max_specimens=3):
    if not 0 < max_bytes <= 512*1024**2 or not 0 < max_seconds <= 300 or max_specimens not in [1, 2, 3]:
        raise ValueError('Small bounded CPU diagnostic only')
    if not Path('/content/drive/MyDrive').is_dir():
        raise RuntimeError('Mount the same already-approved Drive first')
    if sha(ROOT / REPORT) != REPORT_SHA:
        raise ValueError('Original failure report checksum differs')
    script = ROOT / 'prepare_official_images_stream_v2.py'
    if sha(script) != STREAM_SHA:
        raise ValueError('Original source reader checksum differs')
    spec = importlib.util.spec_from_file_location('original_stream_diagnostic', script)
    source = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(source)
    source.prep.require_drive(ROOT)
    report = json.loads((ROOT / REPORT).read_text())
    targets = [x['id'] for x in report['decode_failures'] if 'cannot identify' in x['error']][:max_specimens]
    if not targets:
        raise ValueError('No registered unrecognized specimens to inspect')
    folder = ROOT / 'failed_payload_diagnostics_v1' / ('sample_' + uuid.uuid4().hex)
    folder.mkdir(parents=True, exist_ok=False)
    records = []
    started = time.monotonic()
    stopped = 'requested specimens captured'
    with source.PublicArchiveReader() as reader:
        limited = LimitedReader(reader, max_bytes, started + max_seconds)
        try:
            with bz2.BZ2File(limited, 'rb') as expanded, tarfile.open(fileobj=expanded, mode='r|') as archive:
                for member in archive:
                    if not member.isfile() or Path(member.name).stem not in targets:
                        continue
                    ident = Path(member.name).stem
                    if member.size > 32*1024**2:
                        raise ValueError('Specimen exceeds32MiB diagnostic cap')
                    raw = archive.extractfile(member).read()
                    destination = folder / Path(member.name).name
                    with destination.open('xb') as f:
                        f.write(raw); f.flush(); os.fsync(f.fileno())
                    from PIL import Image
                    try:
                        with Image.open(io.BytesIO(raw)) as image:
                            image.load(); image.convert('RGB').load()
                            decoded = {'strict_decode': True, 'format': image.format, 'size': list(image.size)}
                    except Exception as error:
                        decoded = {'strict_decode': False, 'error_type': type(error).__name__, 'error': str(error)}
                    value = {'id': ident, 'original_member': member.name,
                             'private_file': str(destination), 'bytes': len(raw),
                             'sha256': sha(destination), 'kind': payload_kind(raw), **decoded}
                    records.append(value)
                    print(json.dumps({'state': 'original_failed_specimen_preserved', 'id': ident,
                                      'bytes': len(raw), 'kind': value['kind'], 'strict_decode': value['strict_decode']}), flush=True)
                    targets.remove(ident)
                    if not targets:
                        break
        except DiagnosticBoundary as error:
            stopped = str(error)
        result = {'utc': source.prep.now(), 'state': 'bounded_original_specimen_diagnostic_finished',
                  'requested': max_specimens, 'captured': len(records), 'uncaptured_ids': targets,
                  'stop_reason': stopped, 'compressed_bytes_consumed': reader.pos,
                  'byte_budget': max_bytes, 'elapsed_seconds': time.monotonic() - started,
                  'source_id': source.SOURCE_ID, 'parent_full_archive_sha256': report['compressed_archive_sha256'],
                  'this_diagnostic_consumed_full_source_crc': False,
                  'source_failure_report_sha256': REPORT_SHA, 'diagnostic_source_sha256': sha(__file__),
                  'specimens': records, 'raw_data_private': True,
                  'dataset_modified': False, 'decoder_policy_changed': False,
                  'image_gate_passed': False, 'training': False, 'test_inference': False}
        source.prep.record(folder / 'diagnostic.json', result)
        print(json.dumps(result), flush=True)
    from google.colab import drive
    drive.flush_and_unmount(timeout_ms=600000)
    print(json.dumps({'utc': source.prep.now(), 'state': 'specimen_diagnostic_drive_flush_completed',
                      'private_report': str(folder / 'diagnostic.json')}), flush=True)
    return result


if __name__ == '__main__':
    run()
