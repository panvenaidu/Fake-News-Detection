"""Collect only the human-initiated, matching Part2 ZIP; no network or training.

Waits until 20:01 UTC, validates safe members/CRC, preserves archive and extracts
into a new ignored folder. Never overwrites earlier accepted evidence.
"""
from pathlib import Path, PurePosixPath
from datetime import datetime, timezone
import hashlib, json, shutil, stat, time, zipfile

PROJECT = Path('/Users/panveenaidu/Downloads/SEM7/UROP')
DEST = PROJECT / 'data/cloud_recovery/part2_saved_output_20261027_362859423'
END = datetime.fromisoformat('2026-10-27T20:01:00+00:00').timestamp()
AFTER = datetime.fromisoformat('2026-10-27T19:37:00+00:00').timestamp()
EXPECTED = '6c7747e08f482d6e504e05fb6c7e1a8c4e1fe3bce7154961f9380ed7e3e6f68e'

def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(4 * 1024**2), b''):
            h.update(block)
    return h.hexdigest()

def run():
    assert not DEST.exists(), 'Preserve existing collection; inspect before retry'
    source = None
    while time.time() < END:
        candidates = [p for root in [Path('/Users/panveenaidu/Downloads'),
                                     PROJECT / 'data/cloud_recovery']
                      for p in root.glob('*.zip') if p.stat().st_mtime >= AFTER]
        for p in candidates:
            try:
                with zipfile.ZipFile(p) as archive:
                    names = [n for n in archive.namelist()
                             if n.endswith('/part2_runtime_result.json')]
                    if len(names) != 1:
                        continue
                    receipt = json.loads(archive.read(names[0]))
                    if receipt['recovery']['loaded']['sha256'] != EXPECTED:
                        continue
                    source = p
                    break
            except zipfile.BadZipFile:
                continue
        if source:
            break
        time.sleep(10)
    if source is None:
        print(json.dumps({'state': 'matching_manual_download_not_complete_by_collection_deadline'}), flush=True)
        return
    with zipfile.ZipFile(source) as archive:
        members = archive.infolist()
        assert sum(m.file_size for m in members) < 12 * 1024**3
        assert shutil.disk_usage(PROJECT).free > sum(m.file_size for m in members) + 4 * 1024**3
        assert len({m.filename for m in members}) == len(members)
        for m in members:
            path = PurePosixPath(m.filename)
            assert not path.is_absolute() and '..' not in path.parts
            assert not stat.S_ISLNK(m.external_attr >> 16)
        assert archive.testzip() is None, 'Archive CRC failure; retain original'
    DEST.mkdir()
    target = DEST / 'results_362859423.zip'
    source.rename(target)
    with zipfile.ZipFile(target) as archive:
        archive.extractall(DEST / 'extracted')
    receipt = {'utc': datetime.now(timezone.utc).isoformat(),
               'method': 'Human initiated normal Chrome download after security-block handoff; agent did not bypass block',
               'archive': str(target.relative_to(PROJECT)), 'bytes': target.stat().st_size,
               'sha256': sha(target), 'crc_all_members_passed': True,
               'safe_member_paths': True, 'members': len(members),
               'uncompressed_bytes': sum(m.file_size for m in members),
               'scientific_attempt': str(next((DEST / 'extracted').rglob('part2_runtime_result.json')).parent),
               'independent_tensor_prediction_verification': 'pending'}
    (PROJECT / 'results/MM_PART2_MANUAL_DOWNLOAD_READBACK_20261027.json').write_text(json.dumps(receipt, indent=2)+'\n')
    print(json.dumps(receipt), flush=True)

if __name__ == '__main__':
    run()
