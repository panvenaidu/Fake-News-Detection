# Run only on the authorized private Kaggle GPU notebook with our input dataset.
from pathlib import Path
import hashlib, json, shutil, subprocess, sys, zipfile

work = Path('/kaggle/working/UROP'); work.mkdir(exist_ok=True)
inputs = Path('/kaggle/input')

def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(1048576), b''): h.update(b)
    return h.hexdigest()

archives={'official_training_inputs.zip':'c7b62f7943a11f8f6d9e45cdf7954488faefd54118b2850aad3856cd71d36d46',
          'pilot_inputs.zip':'0e38e9138dd6117d1e58a6646809c738ef75ec6e04ba27934d0f783bdf92f853'}
search_roots=[inputs]
for filename, expected in archives.items():
    matches=list(inputs.rglob(filename))
    if matches:
        assert len(matches)==1 and digest(matches[0])==expected
        dst=work/'input_unpacked'/filename.removesuffix('.zip'); dst.mkdir(parents=True,exist_ok=True)
        with zipfile.ZipFile(matches[0]) as archive:
            for name in archive.namelist():
                assert (dst/name).resolve().is_relative_to(dst.resolve()), 'Unsafe archive path'
            archive.extractall(dst)
        search_roots.append(dst)

def find(name):
    return [p for root in search_roots for p in root.rglob(name)]

sources=find('train_multimodal_pilot.py')
assert len(sources)==1, [('source',str(p)) for p in sources]
source_root=sources[0].parent
assert digest(sources[0])=='793b0867e3f3f672a2b1ba9787826cdacdc515d5301f22d9084aea1b8aed50f1'
assert digest(source_root/'train_official_text.py')=='a13c0e5d97b2fe7661ce6a228d43d853f1aca703314cfa48688825b7b01701f9'
cfgs=find('multimodal_pilot_6way_v1.json'); assert len(cfgs)==1
assert digest(cfgs[0])=='80c28c353e92528af2cef01e5bb00a60bdc8bc48bc5bc81b346765d779583743'
manifests=[p for p in find('pilot_manifest.csv') if (p.parent/'images').is_dir()]
assert len(manifests)==1, [('manifest',str(p)) for p in manifests]
assert digest(manifests[0])=='b8e0ee632cd847b60ec00ca7f253a0456602fd70b95c541fddd378bf66d7e4bd'
evidence_candidates=[p for p in find('dataset_evidence.json')
                     if json.loads(p.read_text()).get('pilot_manifest.csv_sha256')=='b8e0ee632cd847b60ec00ca7f253a0456602fd70b95c541fddd378bf66d7e4bd']
assert evidence_candidates
pilot=work/'pilot_input'; pilot.mkdir(exist_ok=True)
shutil.copy2(manifests[0],pilot/'pilot_manifest.csv')
shutil.copy2(evidence_candidates[0],pilot/'dataset_evidence.json')
if not (pilot/'images').exists(): (pilot/'images').symlink_to(manifests[0].parent/'images',target_is_directory=True)
source=work/'source'; source.mkdir(exist_ok=True)
for name in ['train_multimodal_pilot.py','train_official_text.py']: shutil.copy2(source_root/name,source/name)
cfg=work/'multimodal_pilot_6way_v1.json'; shutil.copy2(cfgs[0],cfg)

# Keep Kaggle's installed CUDA torch/torchvision; pin only the HF API used by the original text run.
subprocess.run([sys.executable,'-m','pip','install','--quiet','transformers==5.18.0'],check=True)
import torch
assert torch.cuda.is_available(), 'Cloud GPU required'
print('PRIVATE GPU PILOT: 2000/300/300 rows, six classes, ORIGINAL split membership',flush=True)
print('GPU:',torch.cuda.get_device_name(0),'source:',digest(source/'train_multimodal_pilot.py'),flush=True)
out=work/'MM-PILOT-6W-v1_seed42_20261009'
if (out/'result.json').exists():
    print('PRESERVING COMPLETED PILOT', (out/'result.json').read_text())
else:
    command=[sys.executable,'-u',str(source/'train_multimodal_pilot.py'),'--config',str(cfg),'--input',str(pilot),'--output',str(out)]
    if out.exists():
        assert (out/'resume_checkpoint.pt').exists(), 'Partial initialization present; inspect error before new attempt'
        command.append('--resume')
    subprocess.run(command,check=True)
print('PILOT ORIGINAL RESULT:',(out/'result.json').read_text(),flush=True)
with zipfile.ZipFile(work/'multimodal_pilot_evidence.zip','w',zipfile.ZIP_DEFLATED) as bundle:
    for p in out.rglob('*'):
        if p.is_file() and p.suffix not in ['.pt','.tmp']:
            bundle.write(p,p.relative_to(out))
print('Save a Kaggle version WITH current outputs to preserve the result and checkpoints.',flush=True)
