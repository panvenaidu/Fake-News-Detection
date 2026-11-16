"""Approved CPU-only Drive -> private Kaggle transport, one pinned file at a time.

Secrets come from runtime environment only. Private resumable URLs/blob tokens
are saved only in the existing private Drive control folder. No model execution.
Official SDK protocol: github.com/Kaggle/kagglehub (gcs_upload, datasets_helpers).
"""
import argparse
import base64
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import time
from urllib.parse import urlparse

import requests
from drive_api_storage_v1 import DriveStore, hashes, atomic_json
from pack_usable_images_api_v1 import SOURCE_FOLDER

INDEX_SHA = '5608291805e241d662d24db576d860a129d995e45b7a31b3651130f1a73780ee'
COHORT = 'FACULTY-6W-USABLE-682170-v1'
STATE_NAME = 'KAGGLE_PRIVATE_TRANSFER_V1.json'
OWNER = 'rocky62'
SLUG = 'urop-faculty-usable-image-transport-v2'
TITLE = 'UROP faculty usable image transport v2'
CHUNK = 32 * 1024**2


def emit(**value):
    print(json.dumps(value, allow_nan=False), flush=True)


def validate_index(raw):
    if hashlib.sha256(raw).hexdigest() != INDEX_SHA:
        raise ValueError('Pinned transfer index checksum mismatch')
    value = json.loads(raw)
    entries = value['files']
    if value['cohort'] != COHORT or len(entries) != 41 or sum(e['bytes'] for e in entries) != 80584734720:
        raise ValueError('Pinned cohort/file/byte totals mismatch')
    if len({e['name'] for e in entries}) != 41:
        raise ValueError('Duplicate transfer names')
    for e in entries:
        if Path(e['name']).name != e['name'] or not e['name'].endswith('.tar'):
            raise ValueError('Unsafe transfer filename')
    return value


def validate_uri(uri):
    p = urlparse(uri)
    allowed = p.hostname in ('storage.googleapis.com', 'www.googleapis.com') or (
        p.hostname and p.hostname.endswith('.storage.googleapis.com'))
    if p.scheme != 'https' or not allowed or p.username or p.password or p.fragment:
        raise ValueError('Unexpected private Kaggle blob upload destination')


def source_metadata_status(meta, entry):
    # Drive version is a metadata revision counter, not a content hash. A
    # version-only change requires the full pinned SHA/MD5 download readback
    # below; changed name/size/MD5 is a hard stop. Never rewrite the index.
    if any(str(meta[k]) != str(entry[v]) for k, v in
           [('name', 'name'), ('size', 'bytes'), ('md5Checksum', 'md5Checksum')]):
        raise ValueError('Pinned Drive source content metadata changed')
    return str(meta['version']) != str(entry['version'])


def response_offset(response, size):
    if response.status_code in (200, 201):
        return size, True
    if response.status_code != 308:
        raise RuntimeError('Kaggle blob upload HTTP ' + str(response.status_code))
    match = re.fullmatch(r'bytes=0-(\d+)', response.headers.get('Range', ''))
    offset = int(match[1]) + 1 if match else 0
    if response.headers.get('Range') and not match or not 0 <= offset < size:
        raise ValueError('Invalid incomplete upload range')
    return offset, False


def verify_complete(response, entry):
    # Server MD5 is supplementary; exact local SHA is always mandatory and the
    # independent Kaggle runtime must rehash all archives/images before training.
    try:
        body = response.json()
    except ValueError:
        body = {}
    if isinstance(body, dict):
        if body.get('size') is not None and int(body['size']) != entry['bytes']:
            raise ValueError('Completed server size mismatch')
        if body.get('md5Hash') and base64.b64decode(body['md5Hash']).hex() != entry['md5Checksum']:
            raise ValueError('Completed server MD5 mismatch')


def upload_file(path, entry, item, save, deadline):
    from kagglehub.clients import build_kaggle_client
    from kagglesdk.blobs.types.blob_api_service import ApiBlobType, ApiStartBlobUploadRequest
    if not item.get('uri'):
        r = ApiStartBlobUploadRequest()
        r.type = ApiBlobType.DATASET
        r.name = entry['name']
        r.content_length = entry['bytes']
        r.last_modified_epoch_seconds = int(path.stat().st_mtime)
        with build_kaggle_client() as client:
            result = client.blobs.blob_api_client.start_blob_upload(r)
        validate_uri(result.create_url)
        item.update(uri=result.create_url, token=result.token, offset=0, complete=False)
        save()
    validate_uri(item['uri'])
    with requests.Session() as session, path.open('rb') as stream:
        failures = 0
        last_saved = time.monotonic()
        # Query first, including after a lost response or a resumed runtime.
        while not item.get('complete'):
            if time.monotonic() >= deadline:
                raise TimeoutError('Bounded CPU transfer reached safe stopping boundary')
            try:
                with session.put(item['uri'], data=b'', headers={
                        'Content-Length': '0', 'Content-Range': f"bytes */{entry['bytes']}"},
                        timeout=(15, 90), allow_redirects=False) as response:
                    offset, complete = response_offset(response, entry['bytes'])
                    if complete:
                        verify_complete(response, entry)
                        item.update(offset=offset, complete=True, completed_utc=time.time())
                        save()
                        break
                stream.seek(offset)
                block = stream.read(min(CHUNK, entry['bytes'] - offset))
                if not block:
                    raise ValueError('Unexpected local archive EOF')
                end = offset + len(block) - 1
                with session.put(item['uri'], data=block, headers={
                        'Content-Type': 'application/octet-stream',
                        'Content-Range': f"bytes {offset}-{end}/{entry['bytes']}"},
                        timeout=(15, 180), allow_redirects=False) as response:
                    received, complete = response_offset(response, entry['bytes'])
                    if received != end + 1 or complete != (received == entry['bytes']):
                        raise ValueError('Upload acknowledgement differs from sent range')
                    if complete:
                        verify_complete(response, entry)
                    item.update(offset=received, complete=complete)
                    # The persisted session URI is sufficient to query the exact
                    # server offset after a crash. Avoid a Drive write per32MiB.
                    if complete or time.monotonic() - last_saved >= 60:
                        save()
                        last_saved = time.monotonic()
                emit(state='kaggle_blob_progress', file=entry['name'], bytes=item['offset'], total=entry['bytes'])
                failures = 0
            except (requests.ConnectionError, requests.Timeout):
                failures += 1
                save()
                if failures >= 5:
                    raise RuntimeError('Repeated network failure; private upload checkpoint preserved') from None
                time.sleep(min(2**failures, 10))


def run(args):
    if not os.environ.get('KAGGLE_API_TOKEN', '').startswith('KGAT_'):
        raise ValueError('Approved runtime-only Kaggle token required')
    if not 0 < args.max_seconds <= 14400 or not 1 <= args.max_files <= 41:
        raise ValueError('Bounded transfer arguments required')
    import google.auth
    from google.auth.transport.requests import AuthorizedSession
    credentials, _ = google.auth.default()
    scratch = Path(args.scratch)
    if not str(scratch.resolve()).startswith('/content/urop_kaggle_transfer_v1'):
        raise ValueError('Dedicated cloud CPU scratch required')
    scratch.mkdir(parents=True, exist_ok=True)
    lock = (scratch / 'transfer.lock').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    deadline = time.monotonic() + args.max_seconds
    with AuthorizedSession(credentials) as session:
        store = DriveStore(session)
        with session.get('https://www.googleapis.com/drive/v3/about',
                         params={'fields': 'user(emailAddress)'}, timeout=30) as response:
            response.raise_for_status()
            if response.json()['user']['emailAddress'] != 'panvee62@gmail.com':
                raise ValueError('Wrong approved Google account')
        root = store.meta(SOURCE_FOLDER)['parents']
        if len(root) != 1:
            raise ValueError('Ambiguous existing private source root')
        control = store.folder(root[0], 'api_transport_v1')
        files = store.children(control)
        index = validate_index(store.read_small(files['KAGGLE_TRANSFER_MANIFEST_V2.json']))
        existing = files.get(STATE_NAME)
        state = json.loads(store.read_small(existing)) if existing else {
            'schema': 'UROP_PRIVATE_KAGGLE_TRANSFER_V1', 'index_sha256': INDEX_SHA,
            'dataset': OWNER + '/' + SLUG, 'files': {}, 'phase': 'initialized'}
        if state['index_sha256'] != INDEX_SHA or state['dataset'] != OWNER + '/' + SLUG:
            raise ValueError('Private recovery state belongs to another transfer')
        if state.get('phase') == 'running' and time.time() - state.get('heartbeat', 0) < 900:
            raise ValueError('A recent cloud transfer may still be active; inspect before resuming')
        if state.get('phase') in ('create_submitted', 'created', 'create_ambiguous'):
            raise ValueError('Dataset creation already submitted; inspect its version before any retry')

        def save():
            nonlocal existing
            state['heartbeat'] = time.time()
            atomic_json(scratch / 'PRIVATE_TRANSFER_STATE.json', state)
            # Updating an existing control ID is idempotent. A first create is
            # never blindly retried: its result can be ambiguous after a timeout.
            for attempt in range(3):
                try:
                    existing = store.put_json(control, STATE_NAME, state, existing)
                    break
                except (requests.ConnectionError, requests.Timeout, requests.HTTPError) as error:
                    response = getattr(error, 'response', None)
                    transient = response is None or response.status_code in (429, 500, 502, 503, 504)
                    if existing is None or not transient or attempt == 2:
                        raise
                    time.sleep(2 ** attempt)

        state['phase'] = 'running'
        state['source_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
        save()
        emit(state='private_transfer_started', completed=sum(bool(x.get('complete')) for x in state['files'].values()),
             files=41, gpu=False, training=False)
        try:
            # Small metadata packages first provide a bounded real upload check.
            entries = sorted(index['files'], key=lambda e: (not e['name'] in ('results.tar', 'data.tar'), e['name']))
            processed = 0
            for entry in entries:
                if time.monotonic() >= deadline or processed >= args.max_files:
                    break
                item = state['files'].setdefault(entry['name'], {'sha256': entry['sha256'], 'bytes': entry['bytes']})
                if item['sha256'] != entry['sha256'] or item['bytes'] != entry['bytes']:
                    raise ValueError('Blob state identity mismatch')
                if item.get('complete'):
                    continue
                if shutil.disk_usage(scratch).free < entry['bytes'] + 8 * 1024**3:
                    raise ValueError('Need one pinned archive plus8GiB cloud scratch margin')
                meta = store.meta(entry['id'])
                version_changed = source_metadata_status(meta, entry)
                emit(state='downloading_pinned_file', file=entry['name'], bytes=entry['bytes'])
                path = store.download(meta, scratch / entry['name'], entry['sha256'])
                if hashes(path) != (entry['sha256'], entry['md5Checksum']):
                    raise ValueError('Independent scratch checksum mismatch')
                current = store.meta(entry['id'])
                source_metadata_status(current, entry)
                item['source_readback'] = {'pinned_index_version': entry['version'],
                    'observed_version': current['version'], 'version_changed': version_changed,
                    'full_sha256': entry['sha256'], 'md5Checksum': entry['md5Checksum'],
                    'bytes': entry['bytes']}
                save()
                if version_changed:
                    emit(state='source_version_change_full_pinned_bytes_reverified', file=entry['name'])
                upload_file(path, entry, item, save, deadline)
                if not item.get('complete'):
                    raise ValueError('No successful server upload receipt')
                save()
                # Delete only this regenerated, verified CPU scratch copy.
                path.unlink()
                processed += 1
                emit(state='private_blob_committed', file=entry['name'], completed=sum(bool(x.get('complete')) for x in state['files'].values()), files=41)
            done = len(state['files']) == 41 and all(x.get('complete') for x in state['files'].values())
            state['phase'] = 'blobs_ready' if done else 'stopped_recoverable'
            save()
            if done and args.finalize:
                from kagglehub.clients import build_kaggle_client
                from kagglehub.gcs_upload import UploadDirectoryInfo
                from kagglesdk.datasets.types.dataset_api_service import ApiCreateDatasetRequest
                proto = UploadDirectoryInfo(name='root', files=[state['files'][e['name']]['token'] for e in index['files']]).to_proto()
                request = ApiCreateDatasetRequest()
                request.owner_slug, request.slug = OWNER, SLUG
                request.title = TITLE
                request.files, request.directories, request.is_private = proto.files, proto.directories, True
                state['phase'] = 'create_submitted'
                save()
                try:
                    with build_kaggle_client() as client:
                        client.datasets.dataset_api_client.create_dataset(request)
                except Exception:
                    state['phase'] = 'create_ambiguous'
                    save()
                    raise RuntimeError('Inspect existing private Kaggle dataset before retrying creation') from None
                state['phase'] = 'created'
                save()
            emit(state=state['phase'], completed=sum(bool(x.get('complete')) for x in state['files'].values()),
                 files=41, runtime_image_gate_passed=False, training=False)
        except BaseException as error:
            if state['phase'] == 'running':
                state['phase'] = 'stopped_recoverable'
            state['last_error_type'] = type(error).__name__
            save()
            raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--scratch', default='/content/urop_kaggle_transfer_v1')
    parser.add_argument('--max-seconds', type=int, default=3600)
    parser.add_argument('--max-files', type=int, default=41)
    parser.add_argument('--finalize', action='store_true')
    try:
        run(parser.parse_args())
    except BaseException as error:
        # SDK exception messages can include private signed URLs/tokens.
        emit(state='transfer_stopped', error_type=type(error).__name__, private_recovery=True, training=False)
        raise SystemExit(1) from None
