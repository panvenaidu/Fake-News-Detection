"""Bounded read-only sanitized receipt for the private Kaggle transfer."""
import hashlib
import json
import google.auth
from google.auth.transport.requests import AuthorizedSession
from drive_api_storage_v1 import DriveStore
from pack_usable_images_api_v1 import SOURCE_FOLDER
from transfer_verified_packs_to_kaggle_v1 import STATE_NAME, INDEX_SHA, validate_index

credentials, _ = google.auth.default()
with AuthorizedSession(credentials) as session:
    store = DriveStore(session)
    root = store.meta(SOURCE_FOLDER)['parents']
    assert len(root) == 1
    files = store.children(store.folder(root[0], 'api_transport_v1'))
    index = validate_index(store.read_small(files['KAGGLE_TRANSFER_MANIFEST_V2.json']))
    state = json.loads(store.read_small(files[STATE_NAME]))
    assert state['index_sha256'] == INDEX_SHA
    expected = {e['name']: e for e in index['files']}
    completed = []
    for name, item in state['files'].items():
        entry = expected[name]
        assert item['sha256'] == entry['sha256'] and item['bytes'] == entry['bytes']
        if item.get('complete'):
            assert item['offset'] == entry['bytes'] and item.get('token') and item.get('uri')
            completed.append(name)
    print(json.dumps({'state': 'private_transfer_recovery_readback_verified',
                      'phase': state['phase'], 'completed': len(completed),
                      'completed_bytes': sum(expected[n]['bytes'] for n in completed),
                      'files': 41, 'heartbeat': state.get('heartbeat'),
                      'source_sha256': state.get('source_sha256'),
                      'dataset': state['dataset'], 'index_sha256': INDEX_SHA,
                      'runtime_image_gate_passed': False, 'training': False}), flush=True)
