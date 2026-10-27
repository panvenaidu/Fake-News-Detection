"""Collect only the normal Chrome, matching Part2 ZIP; no network or training.

Waits until 22:00 UTC, validates safe members/CRC, preserves archive and extracts
into a new ignored folder. Never overwrites earlier accepted evidence.
"""
from pathlib import Path, PurePosixPath
from datetime import datetime, timezone
import hashlib, json, shutil, stat, time, zipfile

PROJECT = Path('/Users/panveenaidu/Downloads/SEM7/UROP')
DEST = PROJECT / 'data/cloud_recovery/final_saved_output_20261028_362955511'
END = datetime.fromisoformat('2026-10-27T22:00:00+00:00').timestamp()
AFTER = datetime.fromisoformat('2026-10-27T21:10:00+00:00').timestamp()
EXPECTED = '0ebd4b001603802d26c2c48a03bccfa94afd95a6484536c2d14eb6bc5ecb7e26'

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
                    if receipt['state'] != 'runtime_train_validation_test_verified' or receipt['recovery']['loaded']['sha256'] != EXPECTED:
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
    target = DEST / 'results_362955511.zip'
    source.rename(target)
    with zipfile.ZipFile(target) as archive:
        archive.extractall(DEST / 'extracted')
    receipt = {'utc': datetime.now(timezone.utc).isoformat(),
               'method': 'Normal desktop Chrome Kaggle output download; no new credentials or browser security bypass',
               'archive': str(target.relative_to(PROJECT)), 'bytes': target.stat().st_size,
               'sha256': sha(target), 'crc_all_members_passed': True,
               'safe_member_paths': True, 'members': len(members),
               'uncompressed_bytes': sum(m.file_size for m in members),
               'scientific_attempt': str(next((DEST / 'extracted').rglob('part2_runtime_result.json')).parent),
               'independent_tensor_prediction_verification': 'pending'}
    (PROJECT / 'results/MM_FINAL_DOWNLOAD_READBACK_20261028.json').write_text(json.dumps(receipt, indent=2)+'\n')
    print(json.dumps(receipt), flush=True)

if __name__ == '__main__':
    run()
