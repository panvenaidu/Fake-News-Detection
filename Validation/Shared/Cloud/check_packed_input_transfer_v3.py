"""Sanitized private checkpoint readback; never prints tokens or Drive IDs."""
import json
import google.auth
from google.auth.transport.requests import AuthorizedSession
from drive_api_storage_v1 import DriveStore
from pack_usable_images_api_v1 import SOURCE_FOLDER
import transfer_packed_input_v3 as packed

credentials, _ = google.auth.default()
with AuthorizedSession(credentials) as session:
    store = DriveStore(session)
    parent = store.meta(SOURCE_FOLDER)['parents']
    assert len(parent) == 1
    files = store.children(store.folder(parent[0], 'api_transport_v1'))
    index = packed.transport.validate_index(store.read_small(files['KAGGLE_TRANSFER_MANIFEST_V2.json']))
    state = json.loads(store.read_small(files[packed.transport.STATE_NAME]))
    assert state['index_sha256'] == packed.transport.INDEX_SHA
    assert state['dataset'] == 'rocky62/urop-faculty-usable-packed-input-v3'
    expected = {e['name']: e for e in index['files']}
    completed = []
    for name, item in state['files'].items():
        entry = expected[name]
        assert item['sha256'] == entry['sha256'] and item['bytes'] == entry['bytes']
        destination = name[:-4] + '.bin' if name.startswith('images_pack_') else name
        if item.get('uri'):
            assert item['destination_name'] == destination and item['storage_adapter_sha256'] == packed.ADAPTER_SHA
        if item.get('complete'):
            assert item['offset'] == entry['bytes'] and item.get('token') and item.get('uri')
            completed.append(name)
    print(json.dumps({'state': 'packed_private_recovery_readback_verified', 'phase': state['phase'],
                      'completed': len(completed), 'completed_bytes': sum(expected[n]['bytes'] for n in completed),
                      'files': 41, 'heartbeat': state.get('heartbeat'),
                      'engine_sha256': state.get('source_sha256'), 'adapter_sha256': packed.ADAPTER_SHA,
                      'dataset': state['dataset'], 'destination_mapping_verified': True,
                      'training': False}), flush=True)
