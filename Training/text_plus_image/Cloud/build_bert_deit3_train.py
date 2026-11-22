"""Build an immutable, bounded Kaggle training notebook; never submit it here."""
import argparse
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
    'model/text_plus_image/bert_deit3/bert-base-assets/config.json',
    'model/text_plus_image/bert_deit3/bert-base-assets/tokenizer/tokenizer.json',
    'model/text_plus_image/bert_deit3/bert-base-assets/tokenizer/tokenizer_config.json',
    'training/text_plus_image/Scripts/usable_cohort_v2.py',
    'training/text_plus_image/Scripts/multimodal_recovery_v1.py',
    'training/text_plus_image/Scripts/packed_image_io_v3.py',
    'configs/text_plus_image/bert_deit3/experiment.json',
]
def build(destination, quota_minutes, seconds, stop_epoch, previous_receipt):
    if not 0 < quota_minutes < 30*60 or not 900 <= seconds <= 12*3600-1800:
        raise ValueError('Invalid quota/session bound')
    if seconds + 3600 > (30*60-quota_minutes)*60:
        raise ValueError('Keep at least one hour of free GPU quota after this session')
    if stop_epoch not in (1, 2, 3, 4) or (stop_epoch > 2 and not previous_receipt):
        raise ValueError('Continuation beyond epoch 2 requires an exact predecessor receipt')
    bundle = {}
    for name in FILES:
        raw = (ROOT/name).read_bytes(); digest = hashlib.sha256(raw).hexdigest()
        bundle[name] = {'sha256': digest, 'bytes': base64.b64encode(raw).decode()}
    payload = base64.b64encode(zlib.compress(json.dumps(bundle).encode(), 9)).decode()
    source = f'''# BERT + DeiT III: one bounded, resumable scientific training session; no test.
import base64, hashlib, json, os, shutil, signal, subprocess, sys, time, zlib
from pathlib import Path

STARTED = time.monotonic()
SESSION_SECONDS = {seconds!r}
STOP_EPOCH = {stop_epoch!r}
PREVIOUS_RECEIPT = {previous_receipt!r}
QUOTA_USED_MINUTES = {quota_minutes!r}
bundle = json.loads(zlib.decompress(base64.b64decode({payload!r})))
source = Path('/tmp/urop_bert_deit3_source')
for name, item in bundle.items():
    target = source/name; target.parent.mkdir(parents=True, exist_ok=True)
    raw = base64.b64decode(item['bytes'])
    if hashlib.sha256(raw).hexdigest() != item['sha256']:
        raise ValueError('Bundled source hash mismatch: '+name)
    target.write_bytes(raw)

def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(4*1024**2), b''): h.update(block)
    return h.hexdigest()

def unique(pattern, digest):
    matches = [p for p in Path('/kaggle/input').glob(pattern) if sha(p) == digest]
    if len(matches) != 1: raise ValueError(f'Expected exactly one verified {{pattern}}, found {{len(matches)}}')
    return matches[0]

manifest = unique('**/urop-faculty-usable-packed-input-v3/data/official_paired_v2/paired_manifest.csv',
                  '96c84e9453401cc4a24999c41cdbeb182dafd08771383cf1c75feea9c3001caf')
data_root = manifest.parents[2]
coverage = unique('**/urop_mm_packed_gate_20261026/packed_runtime_coverage.json',
                  'afe8c723f91fe74f791908e0c16fab94d919af64c7cb7c9b5a37e676361d95e5')
index = coverage.with_name('packed_image_index.sqlite')
if sha(index) != 'fc8dc03a4f773da5762891c8392375add5fb8087251b527f3b37a880308e6018': raise ValueError('Index differs')
text = unique('**/urop-text-only-final-results/**/bert-base/best_weights.pt',
              '870bea50fa608dddd20421c21fd1786e244b1323e22734093214b87023666753')
image = unique('**/urop-image-only-vit-83-training/urop_vit83/full_full_frame/best_epoch3.pt',
               '97cb89e986c2481d65dd61ff4f2570a907898c885c34ea2e9460385ce01ae300')
preflight = Path('/kaggle/working/urop_bert_deit3_retry_preflight.json')
if preflight.exists(): raise ValueError('Preserve existing retry preflight; use a fresh session')
preflight_cmd = [sys.executable, '-u', str(source/'model/text_plus_image/bert_deit3/preflight.py'),
                 '--root', str(data_root), '--coverage', str(coverage), '--packed-index', str(index),
                 '--config', str(source/'configs/text_plus_image/bert_deit3/experiment.json'),
                 '--text', str(text), '--image', str(image), '--output', str(preflight),
                 '--scratch', '/tmp', '--benchmark-seconds', '180']
print('OFFLINE_LOCAL_ASSET_PREFLIGHT_START', flush=True)
subprocess.run(preflight_cmd, check=True, env={{**os.environ, 'TOKENIZERS_PARALLELISM':'false',
                                               'CUBLAS_WORKSPACE_CONFIG':':4096:8', 'OMP_NUM_THREADS':'1'}})
receipt = json.loads(preflight.read_text())
if receipt['status'] != 'passed' or receipt['device'] != 'cuda': raise ValueError('Preflight did not pass')
if receipt['estimated_epoch_seconds_excluding_checkpoint'] <= 0: raise ValueError('Bad throughput receipt')
import torch
if not torch.cuda.is_available() or torch.cuda.get_device_name(0) != receipt['gpu']:
    raise ValueError('Different or unavailable GPU; repeat preflight')
output = Path('/kaggle/working/urop_bert_deit3_training_retry1')
if output.exists(): raise ValueError('Preserve existing output; do not duplicate a run')
if PREVIOUS_RECEIPT:
    previous = unique('**/urop_bert_deit3_training/session_receipt.json', PREVIOUS_RECEIPT)
    old = json.loads(previous.read_text())
    if old['state'] not in ('stopped_at_boundary', 'stage_complete'): raise ValueError('Predecessor not terminal')
    shutil.copytree(previous.parent, output)
    (output/'session_receipt.json').unlink()
    if (output/'trainer.lock').exists(): raise ValueError('Preserve predecessor lock for investigation')
stage = 'part1' if STOP_EPOCH <= 2 else 'part2'
cmd = [sys.executable, '-u', str(source/'model/text_plus_image/bert_deit3/train.py'),
       '--root', str(data_root), '--coverage', str(coverage), '--packed-index', str(index),
       '--config', str(source/'configs/text_plus_image/bert_deit3/experiment.json'),
       '--output', str(output), '--warmstart', str(text), '--image-warmstart', str(image),
       '--preflight', str(preflight), '--stage', stage, '--stop-after-epoch', str(STOP_EPOCH)]
if PREVIOUS_RECEIPT: cmd += ['--resume']
env = {{**os.environ, 'CUDA_VISIBLE_DEVICES':'0', 'CUBLAS_WORKSPACE_CONFIG':':4096:8',
        'TOKENIZERS_PARALLELISM':'false', 'OMP_NUM_THREADS':'1', 'MKL_NUM_THREADS':'1'}}
print('TRAINING_SESSION_REGISTERED', json.dumps({{'quota_used_minutes':QUOTA_USED_MINUTES,
      'session_seconds': SESSION_SECONDS,'stop_after_epoch':STOP_EPOCH,'previous_receipt':PREVIOUS_RECEIPT,
      'preflight_sha256':sha(preflight),'no_test':True}}), flush=True)
proc = subprocess.Popen(cmd, env=env)
stop_sent = False
while proc.poll() is None:
    if time.monotonic()-STARTED >= SESSION_SECONDS-1200 and not stop_sent:
        proc.send_signal(signal.SIGTERM); stop_sent = True
        print('STOP_REQUESTED checkpoint boundary', flush=True)
    if time.monotonic()-STARTED >= SESSION_SECONDS-120 and proc.poll() is None:
        proc.kill(); proc.wait(); raise RuntimeError('No clean stop; preserve this run for inspection')
    time.sleep(10)
if proc.returncode != 0: raise RuntimeError(f'Trainer failed with exit code {{proc.returncode}}')
sys.path.insert(0,str(source/'training/text_plus_image/Scripts'))
from multimodal_recovery_v1 import load_generation
payload, proof = load_generation(output/'recovery')
state = payload['state']
if state['cursor'] != payload['cursor']: raise ValueError('Recovery cursor mismatch')
complete = len(state['history']) >= STOP_EPOCH
summary = {{'state':'stage_complete' if complete else 'stopped_at_boundary', 'stop_after_epoch':STOP_EPOCH,
           'history_epochs':len(state['history']), 'phase':state['phase'], 'epoch':state['epoch'],
           'cursor':state['cursor'], 'recovery':proof, 'best':state['best'],
           'protocol_sha256':sha(output/'protocol.json'), 'preflight_sha256':sha(preflight),
           'elapsed_seconds':time.monotonic()-STARTED, 'no_test':True}}
tmp = output/'session_receipt.tmp'; tmp.write_text(json.dumps(summary,indent=2)+'\\n'); os.replace(tmp,output/'session_receipt.json')
print('TRAINING_SESSION_RECEIPT',json.dumps(summary),flush=True)
print('SESSION_RECEIPT_SHA256',sha(output/'session_receipt.json'),flush=True)
'''
    compile(source, '<bert-deit3-training>', 'exec')
    notebook = {'nbformat':4, 'nbformat_minor':5,
                'metadata':{'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'}},
                'cells':[{'cell_type':'code','execution_count':None,'metadata':{},'outputs':[], 'source':source.splitlines(True)}]}
    destination.mkdir(parents=True, exist_ok=False)
    path = destination/'training.ipynb'; path.write_text(json.dumps(notebook,indent=1)+'\n')
    (destination/'bundle_hashes.json').write_text(json.dumps({k:v['sha256'] for k,v in bundle.items()},indent=2)+'\n')
    print(json.dumps({'notebook':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                      'quota_minutes':quota_minutes,'session_seconds':seconds,'stop_epoch':stop_epoch,
                      'previous_receipt':previous_receipt,'submitted':False}))


if __name__ == '__main__':
    p=argparse.ArgumentParser(); p.add_argument('destination',type=Path)
    p.add_argument('--quota-used-minutes',type=float,required=True); p.add_argument('--session-seconds',type=int,required=True)
    p.add_argument('--stop-epoch',type=int,choices=range(1,5),required=True); p.add_argument('--previous-receipt')
    a=p.parse_args(); build(a.destination,a.quota_used_minutes,a.session_seconds,a.stop_epoch,a.previous_receipt)
