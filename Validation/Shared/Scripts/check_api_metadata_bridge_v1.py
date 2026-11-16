"""Offline tests for API proof guards, never authorizes a model runtime gate."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'collab'))
import prepare_api_kaggle_metadata_v1 as adapter
import verify_usable_image_shards_v2 as verifier


def reject(fn):
    try: fn()
    except ValueError: return
    raise AssertionError('Unsafe metadata accepted')


def main():
    count = 0
    class FakeControl:
        value = None
        folders = 0
        def children(self, parent):return {'METADATA_JOB.json':{'id':'control'}} if self.value else {}
        def read_small(self, meta):return json.dumps(self.value).encode()
        def folder(self, parent, name, create):self.folders+=1;return 'generation'
        def put_json(self, parent, name, value):self.value=copy.deepcopy(value);return {'id':'control'}
    store=FakeControl()
    first,_=adapter.metadata_job(store,'control-folder',b'completed-transport')
    second,_=adapter.metadata_job(store,'control-folder',b'completed-transport')
    assert first==second and store.folders==1;count+=1
    reject(lambda:adapter.metadata_job(store,'control-folder',b'different-transport'));count+=1
    store.value['adapter_sha256']='0'*64
    reject(lambda:adapter.metadata_job(store,'control-folder',b'completed-transport'));count+=1
    with tempfile.TemporaryDirectory(dir='data/official_paired_v2', prefix='api-metadata-') as temp:
        root = Path(temp)
        (root / 'shards').mkdir()
        row = {'id':'synthetic', 'split':'train', 'clean_title':'line one\nline two, comma', '6_way_label':3,
               'member':'images/synthetic.jpg', 'source_member':'public_image_set/synthetic.jpg',
               'image_sha256':'1'*64, 'bytes':42}
        receipt = {'archive':'images_pack_synthetic.tar', 'bytes':10240, 'sha256':'2'*64, 'images':[row]}
        path = root / 'shards/images_pack_synthetic.receipt.json'
        path.write_text(json.dumps(receipt))
        archive = {'id':'synthetic-file', 'name':receipt['archive'], 'size':'10240', 'version':'7', 'md5Checksum':'3'*32}
        cached = {**archive, 'bytes':10240, 'sha256':receipt['sha256']}
        expected = {row['id']:{k:row[k] for k in ['id','split','clean_title','6_way_label']}}
        proof = adapter.current_proof(archive, cached, receipt, verifier.prep.sha(path))
        rows, shards = verifier.receipt_rows(root, expected, 'kaggle-tar', {archive['name']:proof})
        assert rows['synthetic']['image_path'] == 'images_pack_synthetic/images/synthetic.jpg'
        assert len(shards) == 1 and not (root/'shards'/archive['name']).exists()
        count += 1
        reject(lambda: verifier.receipt_rows(root, expected, 'kaggle-tar')); count += 1
        for key, value in [('version','8'),('md5Checksum','0'*32),('size','10241')]:
            changed = {**archive,key:value}
            reject(lambda: adapter.current_proof(changed, cached, receipt, verifier.prep.sha(path))); count += 1
        for key, value in [('sha256','0'*64),('receipt_sha256','0'*64),('verified_current_metadata',False),('version',None)]:
            badproof = {**proof,key:value}
            reject(lambda: verifier.receipt_rows(root, expected, 'kaggle-tar', {archive['name']:badproof})); count += 1
        reject(lambda: verifier.receipt_rows(root, expected, 'kaggle-tar', {archive['name']:proof,'extra':proof})); count += 1
        changed = copy.deepcopy(receipt); changed['images'][0]['6_way_label'] = 4
        path.write_text(json.dumps(changed))
        updated = {**proof, 'receipt_sha256':verifier.prep.sha(path)}
        reject(lambda: verifier.receipt_rows(root, expected, 'kaggle-tar', {archive['name']:updated})); count += 1
        path.write_text(json.dumps(receipt))
        reject(lambda: verifier.receipt_rows(root, {**expected,'missing':expected['synthetic']},
                                             'kaggle-tar', {archive['name']:proof})); count += 1
    result = {'utc':verifier.prep.now(),'state':'passed','cases':count,'scope':'Synthetic API metadata-proof guards only; no network, images, model or runtime gate',
              'adapter_sha256':hashlib.sha256(Path(adapter.__file__).read_bytes()).hexdigest(),
              'verifier_sha256':hashlib.sha256(Path(verifier.__file__).read_bytes()).hexdigest(),
              'limitations':['Adapter is not yet cloud executed','Full image SHA/decode runtime gate remains mandatory']}
    Path('results/api_metadata_bridge_checks_20261025.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))

if __name__ == '__main__': main()
