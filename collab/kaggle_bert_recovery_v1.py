# TEXT-COMPLETE-v1: only the verified BERT recovery; no ModernBERT/pilot launch.
from pathlib import Path
import gc, hashlib, json, os, shutil, stat, subprocess, sys, traceback, zipfile
work=Path('/kaggle/working/UROP_BERT_RECOVERY_V1');work.mkdir(exist_ok=True)
inputs=Path('/kaggle/input');roots=[inputs]
attempt_name='OFFICIAL-6W-TEXT-v2_seed42_20261008T095827Z'

def digest(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()

def unpack(z,dst):
    dst.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(z) as archive:
        for member in archive.infolist():
            assert (dst/member.filename).resolve().is_relative_to(dst.resolve())
            assert not stat.S_ISLNK(member.external_attr>>16)
        archive.extractall(dst)
    roots.append(dst)

def find(name):return [p for r in roots for p in r.rglob(name)]
def unique(name):
    files=find(name);assert len(files)==1,(name,[str(p) for p in files]);return files[0]

try:
    official=list(inputs.rglob('official_training_inputs.zip'))
    if official:
        assert len(official)==1 and digest(official[0])=='c7b62f7943a11f8f6d9e45cdf7954488faefd54118b2850aad3856cd71d36d46'
        unpack(official[0],work/'official_inputs')
    original=list(inputs.rglob('bert-base-20261008T133126Z-1-001.zip'))
    if original:
        assert len(original)==1 and digest(original[0])=='369610b47f755e0bda9b09b51d546970da284e51fe245d2c2349e1d95094ff87'
        unpack(original[0],work/'original_checkpoint')
    packages=list(inputs.rglob('bert_recovery_v1_payload.zip'))
    if packages:
        assert len(packages)==1 and digest(packages[0])=='f4c4a64d4535116dd1c21c08ebc8ca21dd1f89d94aae8b4a8514db621e876c9d'
        unpack(packages[0],work/'recovery_payload')
    proof=json.loads(unique('recovery_verification.json').read_text())
    assert proof['status']=='verified' and proof['attempt']==attempt_name
    checkpoint=unique('resume_checkpoint.pt')
    assert digest(checkpoint)==proof['checkpoint_sha256']
    assert digest(checkpoint.parent/'best_weights.pt')==proof['best_weights_sha256']
    assert digest(checkpoint.parent/'train_official_text.py')=='a13c0e5d97b2fe7661ce6a228d43d853f1aca703314cfa48688825b7b01701f9'
    cfg=unique('text_official_6way_v2.json')
    assert digest(cfg)=='b203b3ea15c247c8174bbd67733501e304a31c7b681c720a4ed61bbe05f57689'
    data=unique('multimodal_train.tsv').parent
    for info in json.loads(cfg.read_text())['splits'].values():assert digest(data/info['filename'])==info['sha256']
    manifest_path=unique('recovery_payload_manifest.json')
    assert digest(manifest_path)=='025362937e9326a3b3b4cd9495cab83bfc1aca83556d0aa686d198ec51df056d'
    payload=manifest_path.parent;manifest=json.loads(manifest_path.read_text())
    for name,info in manifest['files'].items():assert digest(payload/name)==info['sha256']
    source_dir=payload/'scripts'
    attempt=work/'official_text_runs'/attempt_name
    if not attempt.exists():
        attempt.mkdir(parents=True)
        original_root=unique('text_attempt')
        for p in original_root.iterdir():
            if p.is_file():shutil.copy2(p,attempt/p.name)
        shutil.copy2(cfg,attempt/'protocol.json')
        shutil.copytree(checkpoint.parent,attempt/'bert-base')
        shutil.copytree(payload/'historical_colab_snapshot',attempt/'historical_colab_snapshot')
        (attempt/'migration_verification.json').write_text(json.dumps(proof,indent=2)+'\n')
    deployed=work/'recovery_source';shutil.copytree(source_dir,deployed,dirs_exist_ok=True)
    shutil.copy2(manifest_path,attempt/manifest_path.name)
    # Keep Kaggle Torch installed, match the original Hugging Face version.
    subprocess.run([sys.executable,'-m','pip','install','--quiet','transformers==5.18.0'],check=True)
    env=dict(os.environ,CUDA_VISIBLE_DEVICES='0',TOKENIZERS_PARALLELISM='false')
    print('VERIFIED INPUTS; running installed-Torch CPU recovery gates',flush=True)
    subprocess.run([sys.executable,'-u',str(deployed/'check_text_recovery_v1.py'),
        '--checkpoint',str(checkpoint),'--output',str(attempt/'installed_torch_recovery_checks.json')],env=env,check=True)
    import torch
    assert torch.cuda.is_available(),'Cloud CUDA GPU required'
    assert shutil.disk_usage(work).free>8*1024**3,'Insufficient disk for recoverable outputs'
    print('PREFLIGHT GPU:',torch.cuda.get_device_name(0),'Torch:',torch.__version__,'BERT ONLY',flush=True)
    subprocess.run([sys.executable,'-u',str(deployed/'train_official_text_recovery_v1.py'),
        '--config',str(cfg),'--data',str(data),'--output',str(attempt.parent),
        '--resume-attempt',str(attempt)],env=env,check=True)
    print((attempt/'results_summary.json').read_text(),flush=True)
    print('OUTPUT EVIDENCE:',attempt/'text_results_evidence.zip',flush=True)
    print('OUTPUT WEIGHTS:',attempt/'bert_final_weights.zip',flush=True)
except Exception:
    (work/'bootstrap_error.txt').write_text(traceback.format_exc())
    with zipfile.ZipFile(work/'bootstrap_failure_evidence.zip','w',zipfile.ZIP_DEFLATED) as z:
        for p in work.rglob('*'):
            if p.is_file() and p.suffix in ['.json','.txt','.py','.log'] and p.stat().st_size<10*1024**2:
                z.write(p,p.relative_to(work))
    raise
