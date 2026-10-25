"""Read-only, bounded diagnosis of the completed private image transport.

Run in the already authorized Colab notebook. Never print Drive IDs, tokens,
resumable upload URIs, or contents of private control files.
"""
import hashlib
import json
import signal
from contextlib import contextmanager
from datetime import datetime, timezone

import google.auth
from google.auth.transport.requests import AuthorizedSession

SOURCE_FOLDER = '1tY3NP96gcuHQwGUponsxRlqLD-sfXo9U'
API = 'https://www.googleapis.com/drive/v3/files'
FIELDS = 'id,name,size,md5Checksum,version,mimeType,parents'


@contextmanager
def deadline(seconds=240):
    def expire(*_):
        raise TimeoutError('Bounded read-only Drive inspection expired')
    old = signal.signal(signal.SIGALRM, expire)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old)


def main():
    credentials, _ = google.auth.default()
    with deadline(), AuthorizedSession(credentials) as session:
        def metadata(ident):
            response = session.get(API + '/' + ident, params={'fields': FIELDS}, timeout=30)
            response.raise_for_status()
            return response.json()

        def children(parent):
            response = session.get(API, params={
                'q': "'" + parent + "' in parents and trashed = false",
                'pageSize': 1000,
                'fields': 'nextPageToken,files(' + FIELDS + ')',
            }, timeout=30)
            response.raise_for_status()
            data = response.json()
            if data.get('nextPageToken'):
                raise ValueError('Unexpected pagination in bounded diagnosis')
            files = data['files']
            if len(files) != len({item['name'] for item in files}):
                raise ValueError('Ambiguous private folder names')
            return {item['name']: item for item in files}

        def read_small(item):
            if int(item['size']) > 32 * 1024**2:
                raise ValueError('Control exceeds read-only bound')
            response = session.get(API + '/' + item['id'], params={'alt': 'media'}, timeout=30)
            response.raise_for_status()
            raw = response.content
            if len(raw) != int(item['size']) or hashlib.md5(raw).hexdigest() != item['md5Checksum']:
                raise ValueError('Private control readback mismatch')
            return raw

        root = metadata(SOURCE_FOLDER)['parents']
        if len(root) != 1:
            raise ValueError('Ambiguous source root')
        folders = children(root[0])
        control = children(folders['api_transport_v1']['id'])
        state_raw = read_small(control['STATE.json'])
        state = json.loads(state_raw)
        job = json.loads(read_small(control['METADATA_JOB.json'])) if 'METADATA_JOB.json' in control else {}
        packed_root = children(folders['kaggle_packed_usable_v2']['id'])
        packed = children(packed_root['shards']['id'])
        checked = state.get('archive_checks', {})
        mismatches = []
        receipt_count = 0
        for name, receipt_meta in sorted(packed.items()):
            if not name.endswith('.receipt.json'):
                continue
            receipt_count += 1
            receipt = json.loads(read_small(receipt_meta))
            archive = metadata(packed[receipt['archive']]['id'])
            cached = checked.get(archive['id'], {})
            failures = []
            if cached.get('id') != archive['id']: failures.append('id')
            if cached.get('name') != archive['name']: failures.append('name')
            if cached.get('bytes') != int(archive['size']): failures.append('size')
            if cached.get('sha256') != receipt['sha256']: failures.append('sha256_mapping')
            if cached.get('md5Checksum') != archive['md5Checksum']: failures.append('md5')
            if not cached.get('version') or cached['version'] != archive.get('version'): failures.append('version')
            if int(archive['size']) != receipt['bytes']: failures.append('receipt_size')
            if failures: mismatches.append({'archive': archive['name'], 'fields': failures})
        result = {
            'utc': datetime.now(timezone.utc).isoformat(),
            'state': 'read_only_api_metadata_diagnosis',
            'transport_phase': state.get('phase'),
            'transport_images': state.get('committed_images'),
            'transport_archives': state.get('packed_shards'),
            'pending_exists': state.get('pending') is not None,
            'receipt_count': receipt_count,
            'cached_archive_checks': len(checked),
            'metadata_phase': job.get('phase'),
            'metadata_control_sha_matches': job.get('transport_control_sha256') == hashlib.sha256(state_raw).hexdigest(),
            'mismatch_count': len(mismatches),
            'mismatches': mismatches,
            'training': False,
            'test_inference': False,
        }
        print(json.dumps(result, sort_keys=True), flush=True)


if __name__ == '__main__':
    main()
