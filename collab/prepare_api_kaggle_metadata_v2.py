"""Versioned API archive audit -> small Kaggle metadata packages.

Run only AFTER complete API packing. Never opens the actual-image runtime gate,
never modifies the transport STATE, never deletes sources or runs a model.
Uses existing authorization, no DriveFS. Output is a new private generation.
"""
import argparse
import gc
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tarfile
import uuid

sys.path[:0] = [str(Path(__file__).resolve().parent), str(Path(__file__).resolve().parents[1] / 'scripts')]
from drive_api_storage_v1 import DriveStore, hashes, atomic_json, safe_error
from pack_usable_images_api_v1 import SOURCE_FOLDER, INDEX_SHA, SCHEMA, COHORT, emit
from usable_cohort_v2 import REGISTRATION, REGISTRATION_SHA
import verify_usable_image_shards_v2 as verifier

JOB_NAME = 'METADATA_JOB_V2.json'


def metadata_job(store, control, state_raw):
    """One recoverable generation per exact completed transport control."""
    files = store.children(control)
    existing = files.get(JOB_NAME)
    old = json.loads(store.read_small(existing)) if existing else None
    digest = hashlib.sha256(state_raw).hexdigest()
    if old:
        if old['transport_control_sha256'] != digest:
            raise ValueError('Preserve metadata job for different transport generation')
        if old['adapter_sha256'] != hashes(__file__)[0] or old['verifier_sha256'] != hashes(verifier.__file__)[0]:
            raise ValueError('Metadata source changed; audit existing generation before resuming')
        return old, existing
    generation = store.folder(control, 'METADATA_' + uuid.uuid4().hex, create=True)
    value = {'phase':'preparing', 'generation':generation, 'created_utc':verifier.prep.now(),
             'transport_control_sha256':digest, 'adapter_sha256':hashes(__file__)[0],
             'verifier_sha256':hashes(verifier.__file__)[0], 'packages':{}, 'archive_proofs':{}}
    return value, store.put_json(control, JOB_NAME, value)


def current_proof(archive, cached, receipt, receipt_sha):
    """Check durable mapping; a changed version requires a fresh full remote SHA."""
    if (not cached or cached.get('id') != archive['id'] or cached.get('name') != archive['name']
            or cached.get('bytes') != int(archive['size']) or cached.get('sha256') != receipt['sha256']
            or cached.get('md5Checksum') != archive['md5Checksum'] or not archive.get('version')
            or int(archive['size']) != receipt['bytes']):
        raise ValueError('Archive must be fully hash-audited at its current Drive version')
    return {**cached, 'version': archive['version'],
            'verified_current_metadata': cached.get('version') == archive['version'],
            'receipt_sha256': receipt_sha}


def full_remote_proof(store, archive, mapped, receipt, receipt_sha):
    """Bind an actual full remote SHA/MD5 pass to a stable Drive version."""
    checked = store.verify_remote(archive, receipt['sha256'])
    after = store.meta(archive['id'])
    for key in ('id', 'name', 'size', 'md5Checksum', 'version'):
        if str(after.get(key)) != str(archive.get(key)):
            raise ValueError('Archive changed during full remote hash audit')
    if any(checked.get(key) != mapped.get(key) for key in ('id', 'name', 'bytes', 'sha256', 'md5Checksum', 'version')):
        raise ValueError('Full remote hash differs from committed mapping')
    return {**mapped, 'verified_current_metadata': True, 'receipt_sha256': receipt_sha,
            'proof_source': 'full_remote_sha256_md5'}


def prepare_api(store, scratch):
    scratch = Path(scratch)
    if not str(scratch.resolve()).startswith('/content/') or not Path('/var/colab/hostname').exists():
        raise ValueError('Cloud CPU scratch required; no image staging on laptop')
    root = store.meta(SOURCE_FOLDER)['parents']
    if len(root) != 1: raise ValueError('Ambiguous original root')
    root = root[0]
    control = store.folder(root, 'api_transport_v1')
    state_meta = store.children(control)['STATE.json']
    state_raw = store.read_small(state_meta)
    state = json.loads(state_raw)
    if (state.get('schema') != SCHEMA or state.get('cohort') != COHORT or state.get('index_sha256') != INDEX_SHA
            or state.get('phase') != 'complete' or state.get('pending') is not None
            or state.get('committed_images') != 682170):
        raise ValueError('Transport must be complete and terminal before metadata publication')
    controls = store.children(control)
    terminal_name = state['job_id'] + '_terminal.json'
    terminal = json.loads(store.read_small(controls[terminal_name]))
    if (terminal.get('job_id') != state['job_id'] or terminal.get('phase') != 'complete'
            or terminal.get('prior_pack_audit_complete') is not True
            or terminal.get('images_committed') != 682170
            or terminal.get('packed_shards') != state['packed_shards']):
        raise ValueError('Completed transport terminal and prior full audit not proven')
    job, job_meta = metadata_job(store, control, state_raw)
    if job['phase'] == 'complete':
        raw = store.read_small(store.meta(job['receipt_meta']['id']), job['receipt_sha256'])
        result = json.loads(raw)
        for package in result['packages']:
            current = store.meta(package['private_file']['id'])
            if int(current['size']) != package['bytes'] or current['md5Checksum'] != package['md5Checksum']:
                raise ValueError('Completed metadata package changed')
        emit(state='api_kaggle_metadata_already_complete', images=682170, image_gate_passed=False)
        return result
    source = scratch / 'metadata_source'
    originals = store.children(root)
    regpath = store.download(originals[REGISTRATION], source / REGISTRATION, REGISTRATION_SHA)
    reg = json.loads(regpath.read_text())
    originals_to_copy = [(reg['approval_file'], reg['approval_sha256']),
                         (reg['extraction_report_file'], reg['extraction_report_sha256'])]
    originals_to_copy += [(item['filename'], item['sha256']) for item in reg['original_files']]
    for name, sha in originals_to_copy:
        # Reuse the original packer's verified cloud cache, if still present.
        cache = Path('/content/urop_api_transport_v1/original_metadata') / name
        target = source / name
        if cache.is_file() and hashes(cache)[0] == sha:
            target.parent.mkdir(parents=True, exist_ok=True)
            if not target.exists(): shutil.copyfile(cache, target)
        store.download(originals[name], target, sha)
    packed = store.folder(store.folder(root, 'kaggle_packed_usable_v2'), 'shards')
    files = store.children(packed)
    receipts = sorted((m for name, m in files.items() if name.endswith('.receipt.json')), key=lambda m: m['name'])
    if len(receipts) != state['packed_shards'] or len(receipts) > 47:
        raise ValueError('Transport receipt/archive count changed')
    proofs = {}
    for n, meta in enumerate(receipts, 1):
        raw = store.read_small(meta)
        receipt = json.loads(raw)
        name = receipt['archive']
        if meta['name'] != name.replace('.tar', '.receipt.json') or name in proofs:
            raise ValueError('Unexpected/duplicate receipt filename')
        archive = store.meta(files[name]['id'])
        receipt_sha = hashlib.sha256(raw).hexdigest()
        mapped = current_proof(archive, state['archive_checks'].get(archive['id']), receipt, receipt_sha)
        committed_name = name.replace('.tar', '_committed.json')
        committed = json.loads(store.read_small(controls[committed_name]))
        if (committed.get('archive_sha256') != receipt['sha256']
                or committed.get('archive', {}).get('id') != archive['id']
                or committed.get('receipt', {}).get('id') != meta['id']):
            raise ValueError('Committed archive provenance differs')
        prior = job['archive_proofs'].get(name)
        if prior:
            if any(prior.get(key) != mapped.get(key) for key in
                   ('id', 'name', 'bytes', 'sha256', 'md5Checksum', 'version', 'receipt_sha256')):
                raise ValueError('Saved full archive proof differs from current Drive version')
            proof = prior
        elif committed['job_id'] == state['job_id'] or mapped['verified_current_metadata'] is False:
            proof = full_remote_proof(store, archive, mapped, receipt, receipt_sha)
        else:
            # The current terminal's audit_packs() full-hashed every prior pack
            # or reused a same-version proof from a previous full remote read.
            proof = {**mapped, 'proof_source': 'completed_transport_prior_pack_full_audit'}
        proofs[name] = proof
        if not prior:
            job['archive_proofs'][name] = proof
            job_meta = store.put_json(control, JOB_NAME, job, job_meta)
        target = source / 'shards' / meta['name']
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists() and target.read_bytes() != raw:
            raise ValueError('Preserve conflicting metadata receipt')
        target.write_bytes(raw)
        emit(state='api_metadata_archive_proof_verified', archives=n, required=len(receipts))
    # Detect an intervening pack/control writer before making a derived generation.
    if store.read_small(store.meta(state_meta['id'])) != state_raw:
        raise ValueError('Transport control changed during metadata audit')
    output = scratch / 'prepared'
    coverage = verifier.prepare(source, output, source / reg['extraction_report_file'],
                                layout='kaggle-tar', archive_proofs=proofs)
    assert coverage['image_gate_passed'] is False and coverage['runtime_image_bytes_verified'] is False
    # Preserve exact bytes across interrupted regeneration, including JSON timestamps.
    for relative in ['results/usable_image_coverage_v2.json', 'results/official_dataset_provenance.json']:
        path = output / relative
        value = json.loads(path.read_text()); value['utc'] = job['created_utc']
        atomic_json(path, value)
    gc.collect()
    generation = job['generation']
    packages = []
    for name in ['data', 'results']:
        path = scratch / (name + '.tar')
        # Preserve any interrupted build; a fresh derived name avoids erasing it.
        building = path.with_suffix('.tar.building-' + uuid.uuid4().hex)
        with tarfile.open(building, 'x', format=tarfile.PAX_FORMAT) as archive:
            for member in sorted((output / name).rglob('*')):
                if not member.is_file(): continue
                info = archive.gettarinfo(str(member), str(member.relative_to(output / name)))
                info.mtime = 0; info.uid = 0; info.gid = 0; info.uname = ''; info.gname = ''; info.mode = 0o644
                with member.open('rb') as stream: archive.addfile(info, stream)
        if path.exists():
            if hashes(path) != hashes(building): raise ValueError('Preserve conflicting metadata package generations')
            building.unlink()  # Exact duplicate of this derived scratch build only.
        else: building.rename(path)
        sha, md5 = hashes(path)
        prior = job['packages'].get(name, {})
        if prior and (prior['sha256'] != sha or prior['bytes'] != path.stat().st_size):
            raise ValueError('Regenerated metadata package differs from durable upload state')
        def save_upload(value):
            nonlocal job_meta
            job['packages'][name] = {'sha256':sha,'bytes':path.stat().st_size,'upload':value}
            job_meta = store.put_json(control, JOB_NAME, job, job_meta)
        meta = store.upload_file(path, generation, path.name, prior.get('upload'), save_upload)
        store.verify_remote(meta, sha)
        packages.append({'name':path.name, 'sha256':sha, 'md5Checksum':md5,
                         'bytes':path.stat().st_size, 'private_file':meta})
    result = {'state':'api_kaggle_metadata_prepared', 'transport_job':state['job_id'],
              'transport_control_sha256':hashlib.sha256(state_raw).hexdigest(),
              'images':682170, 'archives':len(proofs), 'manifest_sha256':coverage['manifest_sha256'],
              'image_gate_passed':False, 'training':False, 'test_inference':False,
              'packages':packages, 'verifier_sha256':hashes(verifier.__file__)[0],
              'adapter_sha256':hashes(__file__)[0]}
    existing_receipt = store.children(generation).get('METADATA_RECEIPT.json')
    receipt_meta = store.put_json(generation, 'METADATA_RECEIPT.json', result, existing_receipt)
    job.update(phase='complete', receipt_meta=receipt_meta,
               receipt_sha256=hashlib.sha256(store.read_small(receipt_meta)).hexdigest())
    job_meta = store.put_json(control, JOB_NAME, job, job_meta)
    atomic_json(scratch / 'metadata_receipt.json', result)
    emit(state=result['state'], images=682170, archives=len(proofs), manifest_sha256=coverage['manifest_sha256'],
         image_gate_passed=False, training=False, test_inference=False)
    return result


if __name__ == '__main__':
    import google.auth
    from google.auth.transport.requests import AuthorizedSession
    p = argparse.ArgumentParser()
    p.add_argument('--scratch', type=Path, required=True)
    args = p.parse_args()
    credentials, _ = google.auth.default()
    try:
        with AuthorizedSession(credentials) as session:
            prepare_api(DriveStore(session), args.scratch)
    except Exception as error:
        emit(state='api_kaggle_metadata_failed', error_type=type(error).__name__,
             error=safe_error(error), training=False, test_inference=False)
        sys.exit(1)
