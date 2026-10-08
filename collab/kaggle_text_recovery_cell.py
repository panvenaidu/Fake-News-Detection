# Requires the private official input dataset PLUS our verified BERT checkpoint dataset.
from pathlib import Path
import json,hashlib,shutil,subprocess,sys,zipfile,os
work=Path('/kaggle/working/UROP_TEXT');work.mkdir(exist_ok=True)
inputs=Path('/kaggle/input');search_roots=[inputs]
attempt_name='OFFICIAL-6W-TEXT-v2_seed42_20261008T095827Z'

def digest(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda:f.read(1048576),b''):h.update(block)
    return h.hexdigest()

def unpack(archive,dest):
    dest.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(archive) as z:
        assert all((dest/n).resolve().is_relative_to(dest.resolve()) for n in z.namelist())
        z.extractall(dest)
    search_roots.append(dest)

for z in inputs.rglob('official_training_inputs.zip'):
    assert digest(z)=='c7b62f7943a11f8f6d9e45cdf7954488faefd54118b2850aad3856cd71d36d46'
    unpack(z,work/'official_inputs')
for z in inputs.rglob('bert-base*.zip'):
    unpack(z,work/'checkpoint_input')

def find(name):return [p for r in search_roots for p in r.rglob(name)]
proofs=find('recovery_verification.json');assert len(proofs)==1,'Attach verified original recovery files first'
proof=json.loads(proofs[0].read_text());assert proof['status']=='verified' and proof['attempt']==attempt_name
checkpoints=find('resume_checkpoint.pt');assert len(checkpoints)==1
checkpoint=checkpoints[0];assert digest(checkpoint)==proof['checkpoint_sha256']
assert digest(checkpoint.parent/'best_weights.pt')==proof['best_weights_sha256']
sources=find('train_official_text.py')
source=next(p for p in sources if digest(p)=='a13c0e5d97b2fe7661ce6a228d43d853f1aca703314cfa48688825b7b01701f9')
cfgs=find('text_official_6way_v2.json');assert len(cfgs)==1
cfg=cfgs[0];assert digest(cfg)=='b203b3ea15c247c8174bbd67733501e304a31c7b681c720a4ed61bbe05f57689'
trains=find('multimodal_train.tsv');assert len(trains)==1
data=trains[0].parent
for info in json.loads(cfg.read_text())['splits'].values():assert digest(data/info['filename'])==info['sha256']
attempt=work/'official_text_runs'/attempt_name
if not attempt.exists():
    attempt.mkdir(parents=True)
    # Preserve original Colab environment/provenance alongside new resume records.
    original_roots=find('text_attempt')
    assert len(original_roots)==1, 'Original Colab attempt metadata missing'
    for original in original_roots[0].iterdir():
        if original.is_file():shutil.copy2(original,attempt/original.name)
    shutil.copy2(cfg,attempt/'protocol.json')
    shutil.copytree(checkpoint.parent,attempt/'bert-base')
    (attempt/'migration_verification.json').write_text(json.dumps(proof,indent=2)+'\n')
script=work/'train_official_text.py';shutil.copy2(source,script)
subprocess.run([sys.executable,'-m','pip','install','--quiet','transformers==5.18.0'],check=True)
env=dict(os.environ,CUDA_VISIBLE_DEVICES='0')
print('RESUMING original six-way BERT checkpoint, then ModernBERT; unchanged official data/protocol',flush=True)
subprocess.run([sys.executable,'-u',str(script),'--config',str(cfg),'--data',str(data),
                '--output',str(attempt.parent),'--resume-attempt',str(attempt)],env=env,check=True)
print((attempt/'results_summary.json').read_text(),flush=True)
