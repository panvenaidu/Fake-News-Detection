"""Build a private Kaggle preflight package; never submits or starts a job."""
import base64
import hashlib
import json
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
FILES = [
    'model/text_plus_image/bert_deit3/model.py',
    'model/text_plus_image/bert_deit3/train.py',
    'model/text_plus_image/bert_deit3/preflight.py',
    'training/text_plus_image/Scripts/usable_cohort_v2.py',
    'training/text_plus_image/Scripts/multimodal_recovery_v1.py',
    'training/text_plus_image/Scripts/packed_image_io_v3.py',
    'configs/text_plus_image/bert_deit3/experiment.json',
]


def build(destination):
    payload = {}
    for name in FILES:
        raw = (ROOT / name).read_bytes()
        payload[name] = {'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': base64.b64encode(raw).decode()}
    encoded = base64.b64encode(zlib.compress(json.dumps(payload).encode(), 9)).decode()
    source = f'''# Private engineering preflight. No scientific training or held-out inference.
import base64, hashlib, json, os, subprocess, sys, zlib
from pathlib import Path

bundle = json.loads(zlib.decompress(base64.b64decode({encoded!r})))
root = Path('/tmp/urop_bert_deit3_source')
for name, item in bundle.items():
    target = root / name
    target.parent.mkdir(parents=True, exist_ok=True)
    raw = base64.b64decode(item['bytes'])
    if hashlib.sha256(raw).hexdigest() != item['sha256']:
        raise ValueError('Bundled source checksum mismatch: ' + name)
    target.write_bytes(raw)

def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(4 * 1024**2), b''):
            digest.update(block)
    return digest.hexdigest()

def unique(pattern, digest=None):
    matches = list(Path('/kaggle/input').glob(pattern))
    if digest is not None:
        matches = [p for p in matches if sha(p) == digest]
    if len(matches) != 1:
        raise ValueError(f'Expected one mounted input for {{pattern}}; found {{len(matches)}}')
    return matches[0]

manifest = unique('**/urop-faculty-usable-packed-input-v3/data/official_paired_v2/paired_manifest.csv',
                  '96c84e9453401cc4a24999c41cdbeb182dafd08771383cf1c75feea9c3001caf')
data_root = manifest.parents[2]
coverage = unique('**/urop_mm_packed_gate_20261026/packed_runtime_coverage.json',
                  'afe8c723f91fe74f791908e0c16fab94d919af64c7cb7c9b5a37e676361d95e5')
index = coverage.with_name('packed_image_index.sqlite')
if sha(index) != 'fc8dc03a4f773da5762891c8392375add5fb8087251b527f3b37a880308e6018':
    raise ValueError('Packed index hash differs')
text = unique('**/urop-text-only-final-results/**/bert-base/best_weights.pt',
              '870bea50fa608dddd20421c21fd1786e244b1323e22734093214b87023666753')
image = unique('**/urop-image-only-vit-83-training/urop_vit83/full_full_frame/best_epoch3.pt',
               '97cb89e986c2481d65dd61ff4f2570a907898c885c34ea2e9460385ce01ae300')
output = Path('/kaggle/working/urop_bert_deit3_preflight')
output.mkdir(exist_ok=False)
command = [sys.executable, '-u', str(root/'model/text_plus_image/bert_deit3/preflight.py'),
           '--root', str(data_root), '--coverage', str(coverage), '--packed-index', str(index),
           '--config', str(root/'configs/text_plus_image/bert_deit3/experiment.json'),
           '--text', str(text), '--image', str(image), '--output', str(output/'preflight.json'),
           '--scratch', '/tmp', '--benchmark-seconds', '180']
print('Starting disposable preflight; no held-out inference', flush=True)
subprocess.run(command, check=True, env={{**os.environ, 'TOKENIZERS_PARALLELISM': 'false',
                                       'CUBLAS_WORKSPACE_CONFIG': ':4096:8', 'OMP_NUM_THREADS': '1'}})
print('PREFLIGHT_RECEIPT_SHA256', sha(output/'preflight.json'), flush=True)
'''
    compile(source, '<bert-deit3-preflight>', 'exec')
    notebook = {'nbformat': 4, 'nbformat_minor': 5,
                'metadata': {'kernelspec': {'display_name': 'Python 3', 'language': 'python', 'name': 'python3'}},
                'cells': [{'cell_type': 'code', 'execution_count': None, 'metadata': {}, 'outputs': [],
                           'source': source.splitlines(True)}]}
    metadata = {'id': 'rocky62/urop-bert-deit3-preflight', 'title': 'UROP BERT DeiT III preflight',
                'code_file': 'preflight.ipynb', 'language': 'python', 'kernel_type': 'notebook',
                'is_private': True, 'enable_gpu': True, 'enable_tpu': False, 'enable_internet': True,
                'dataset_sources': ['rocky62/urop-faculty-usable-packed-input-v3'],
                'kernel_sources': ['rocky62/urop-text-only-final-results/1',
                                   'rocky62/urop-images-quality-check/2',
                                   'rocky62/urop-image-only-vit-83-training/1'],
                'competition_sources': [], 'model_sources': [], 'machine_shape': 'NvidiaTeslaT4'}
    destination.mkdir(parents=True, exist_ok=False)
    (destination/'preflight.ipynb').write_text(json.dumps(notebook, indent=1)+'\n')
    (destination/'kernel-metadata.json').write_text(json.dumps(metadata, indent=2)+'\n')
    (destination/'source_hashes.json').write_text(json.dumps({k: v['sha256'] for k, v in payload.items()}, indent=2)+'\n')
    print(json.dumps({'package': str(destination), 'notebook_sha256': hashlib.sha256((destination/'preflight.ipynb').read_bytes()).hexdigest(), 'submitted': False}))


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('destination', type=Path)
    build(parser.parse_args().destination)
