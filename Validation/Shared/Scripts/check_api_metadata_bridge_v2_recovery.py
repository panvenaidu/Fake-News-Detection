"""Offline checks for resuming the first v2 metadata job after legacy-pack error."""
import copy
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'collab'))
import prepare_api_kaggle_metadata_v2 as adapter
from drive_api_storage_v1 import hashes


class Store:
    def __init__(self, job):
        self.job = copy.deepcopy(job)

    def children(self, control):
        return {adapter.JOB_NAME: {'id': adapter.JOB_NAME}}

    def read_small(self, meta):
        return json.dumps(self.job).encode()


def reject(job, state_raw):
    try:
        adapter.metadata_job(Store(job), 'control', state_raw)
    except ValueError:
        return
    raise AssertionError('Unsafe metadata job migration accepted')


def main():
    state_raw = b'exact-completed-transport'
    proof = {'name': 'existing.tar', 'sha256': 'a' * 64, 'version': '7',
             'receipt_sha256': 'b' * 64, 'proof_source': 'full_remote_sha256_md5'}
    job = {'phase': 'preparing', 'generation': 'existing-private-generation',
           'transport_control_sha256': hashlib.sha256(state_raw).hexdigest(),
           'adapter_sha256': adapter.PREDECESSOR_ADAPTER_SHA,
           'verifier_sha256': hashes(adapter.verifier.__file__)[0],
           'archive_proofs': {'existing.tar': proof}, 'packages': {}}
    migrated, meta = adapter.metadata_job(Store(job), 'control', state_raw)
    assert meta['id'] == adapter.JOB_NAME
    assert migrated['generation'] == job['generation']
    assert migrated['archive_proofs'] == job['archive_proofs']
    assert migrated['adapter_predecessor_sha256'] == job['adapter_sha256']
    assert migrated['adapter_sha256'] == hashes(adapter.__file__)[0]
    reject(job, b'different-transport')
    reject({**job, 'phase': 'complete'}, state_raw)
    reject({**job, 'adapter_sha256': '0' * 64}, state_raw)
    reject({**job, 'verifier_sha256': '0' * 64}, state_raw)
    result = {'state': 'passed', 'cases': 6,
              'scope': 'same-generation v2 source migration; preserve archive proofs; reject unrelated state',
              'adapter_sha256': hashes(adapter.__file__)[0], 'training': False}
    Path('results/api_metadata_bridge_v2_recovery_checks_20261025.json').write_text(
        json.dumps(result, indent=2) + '\n')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
