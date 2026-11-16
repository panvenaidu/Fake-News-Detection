"""Offline regression for the metadata audit missed by transport v1."""
import copy
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'collab'))
import prepare_api_kaggle_metadata_v2 as adapter


def reject(call):
    try:
        call()
    except ValueError:
        return
    raise AssertionError('Changed or unaudited remote archive accepted')


def main():
    class Store:
        def __init__(self):
            self.jobs = {'METADATA_JOB.json': {'phase': 'failed', 'id': 'old'}}
            self.archive = {'id': 'example-id', 'name': 'images_pack_example.tar',
                            'size': '10240', 'md5Checksum': '3' * 32, 'version': '7'}
            self.hash_reads = 0
            self.changed_after_read = False

        def children(self, parent):
            return {name: {'id': name} for name in self.jobs}

        def folder(self, parent, name, create=False):
            return 'new-generation'

        def put_json(self, parent, name, value, existing=None):
            self.jobs[name] = copy.deepcopy(value)
            return {'id': name}

        def read_small(self, meta):
            return json.dumps(self.jobs[meta['id']]).encode()

        def verify_remote(self, archive, expected_sha):
            self.hash_reads += 1
            return {'id': archive['id'], 'name': archive['name'],
                    'bytes': int(archive['size']), 'sha256': expected_sha,
                    'md5Checksum': archive['md5Checksum'], 'version': archive['version']}

        def meta(self, ident):
            result = copy.deepcopy(self.archive)
            if self.changed_after_read: result['version'] = '8'
            return result

    store = Store()
    job, _ = adapter.metadata_job(store, 'control', b'completed-transport')
    assert job['archive_proofs'] == {} and 'METADATA_JOB.json' in store.jobs
    assert 'METADATA_JOB_V2.json' in store.jobs and store.jobs['METADATA_JOB.json']['phase'] == 'failed'
    receipt = {'bytes': 10240, 'sha256': '2' * 64}
    mapped = {'id': store.archive['id'], 'name': store.archive['name'], 'bytes': 10240,
              'sha256': receipt['sha256'], 'md5Checksum': store.archive['md5Checksum'],
              'version': store.archive['version']}
    assert adapter.current_proof(store.archive, mapped, receipt, '4' * 64)['verified_current_metadata']
    proof = adapter.full_remote_proof(store, store.archive, mapped, receipt, '4' * 64)
    assert proof['proof_source'] == 'full_remote_sha256_md5' and store.hash_reads == 1
    store.changed_after_read = True
    reject(lambda: adapter.full_remote_proof(store, store.archive, mapped, receipt, '4' * 64))
    store.changed_after_read = False
    changed = {**mapped, 'sha256': '0' * 64}
    reject(lambda: adapter.full_remote_proof(store, store.archive, changed, receipt, '4' * 64))
    moved = {**store.archive, 'version': '8'}
    stale = adapter.current_proof(moved, mapped, receipt, '4' * 64)
    assert stale['verified_current_metadata'] is False and stale['version'] == '8'
    store.archive = moved
    refreshed = adapter.full_remote_proof(store, moved, stale, receipt, '4' * 64)
    assert refreshed['verified_current_metadata'] is True and refreshed['version'] == '8'
    result = {'state': 'passed', 'cases': 7,
              'scope': 'v2 metadata proof/version and separate recovery generation; offline synthetic only',
              'adapter_sha256': hashlib.sha256(Path(adapter.__file__).read_bytes()).hexdigest(),
              'runtime_image_gate_passed': False, 'training': False}
    Path('results/api_metadata_bridge_v2_checks_20261025.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
