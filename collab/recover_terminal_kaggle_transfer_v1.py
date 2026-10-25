"""Reconcile failed private checkpoint write after a proven terminal worker.
Only in the same CPU runtime, with the exact previously observed Python PID.
Never copies secrets out of private runtime/Drive storage or restarts a job.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import time
import google.auth
from google.auth.transport.requests import AuthorizedSession
from drive_api_storage_v1 import DriveStore
from pack_usable_images_api_v1 import SOURCE_FOLDER
from transfer_verified_packs_to_kaggle_v1 import STATE_NAME, INDEX_SHA, validate_index, validate_uri

parser = argparse.ArgumentParser()
parser.add_argument('--terminal-pid', type=int, required=True)
args = parser.parse_args()
assert args.terminal_pid > 1 and not Path('/proc/' + str(args.terminal_pid)).exists()
assert subprocess.run(['pgrep', '-f', '[p]ython.*transfer_verified_packs_to_kaggle_v1.py'],
                      stdout=subprocess.DEVNULL).returncode == 1
local = json.loads(Path('/content/urop_kaggle_transfer_v1/PRIVATE_TRANSFER_STATE.json').read_text())
assert local['index_sha256'] == INDEX_SHA and local['phase'] == 'stopped_recoverable'
credentials, _ = google.auth.default()
with AuthorizedSession(credentials) as session:
    store = DriveStore(session)
    parent = store.meta(SOURCE_FOLDER)['parents']
    assert len(parent) == 1
    control = store.folder(parent[0], 'api_transport_v1')
    meta = store.children(control)[STATE_NAME]
    raw = store.read_small(meta)
    remote = json.loads(raw)
    assert remote['index_sha256'] == INDEX_SHA and remote['dataset'] == local['dataset']
    assert remote['phase'] in ('running', 'stopped_recoverable')
    assert remote.get('source_sha256') == local.get('source_sha256')
    index = validate_index(store.read_small(store.children(control)['KAGGLE_TRANSFER_MANIFEST_V2.json']))
    expected = {e['name']: e for e in index['files']}
    for name, item in local['files'].items():
        assert item['sha256'] == expected[name]['sha256'] and item['bytes'] == expected[name]['bytes']
        if item.get('uri'):
            validate_uri(item['uri'])
    for name, item in remote['files'].items():
        candidate = local['files'][name]
        assert all(candidate.get(k) == v for k, v in item.items()
                   if k not in ('offset', 'complete', 'uri', 'token'))
        assert candidate.get('offset', 0) >= item.get('offset', 0)
        assert not item.get('complete') or candidate.get('complete')
        for key in ('uri', 'token'):
            assert not item.get(key) or candidate.get(key) == item[key]
    remote['files'] = local['files']
    proof = {'state': 'same_runtime_terminal_checkpoint_reconciled',
             'terminal_python_pid': args.terminal_pid,
             'boot_id': Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
             'previous_private_state_sha256': hashlib.sha256(raw).hexdigest(),
             'completed': sum(bool(x.get('complete')) for x in remote['files'].values()),
             'utc_epoch': time.time(), 'training': False}
    remote['phase'] = 'stopped_recoverable'
    remote['terminal_recovery'] = proof
    remote['last_error_type'] = local.get('last_error_type')
    saved = store.put_json(control, STATE_NAME, remote, meta)
    assert json.loads(store.read_small(saved))['phase'] == 'stopped_recoverable'
    print(json.dumps(proof), flush=True)
