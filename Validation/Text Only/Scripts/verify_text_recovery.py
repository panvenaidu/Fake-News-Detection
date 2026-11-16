"""Verify OUR original Colab checkpoint ZIP after it is placed in UROP.

This loads trusted project-authored tensor checkpoints, not arbitrary downloaded
pickle files. No training, original data edits, or source changes are performed.
"""
import argparse
import gc
import hashlib
import json
import stat
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ATTEMPT = 'OFFICIAL-6W-TEXT-v2_seed42_20261008T095827Z'
SOURCE_SHA = 'a13c0e5d97b2fe7661ce6a228d43d853f1aca703314cfa48688825b7b01701f9'


def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()


def main():
    import torch
    parser=argparse.ArgumentParser();parser.add_argument('archive');args=parser.parse_args()
    archive=Path(args.archive).resolve()
    assert archive.is_relative_to(ROOT), 'Place the downloaded project archive inside UROP first'
    dest=ROOT/'data/cloud_recovery'/ATTEMPT;dest.mkdir(parents=True,exist_ok=True)
    archive_sha=digest(archive)
    with zipfile.ZipFile(archive) as z:
        for member in z.infolist():
            assert (dest/member.filename).resolve().is_relative_to(dest.resolve())
            assert not stat.S_ISLNK(member.external_attr>>16), 'Unexpected archive symlink'
        bad=z.testzip();assert bad is None, ('Corrupt archive member',bad)
        z.extractall(dest)
    checkpoints=list(dest.rglob('resume_checkpoint.pt'));assert len(checkpoints)==1
    checkpoint=checkpoints[0];folder=checkpoint.parent
    assert digest(folder/'train_official_text.py')==SOURCE_SHA
    # Trusted: our source, our private Drive attempt, transferred through Chrome.
    q=torch.load(checkpoint,map_location='cpu',weights_only=False)
    assert tuple(q['model']['classifier.weight'].shape)==(6,768)
    assert tuple(q['model']['classifier.bias'].shape)==(6,)
    assert q['epoch'] in range(1,7) and q['step_in_epoch'] in range(0,17626)
    if q['epoch_finished']:assert q['step_in_epoch']==17625
    history=json.loads((ROOT/'results/experiments/official_text'/ATTEMPT/'bert-base/history.json').read_text())
    assert q['history']==history[:len(q['history'])]
    assert all(k in q for k in ['optimizer','scheduler','scaler','loader_rng','python_rng','numpy_rng','torch_rng','cuda_rng','sampler_start'])
    assert q['updates']+q['skips']==(q['epoch']-1)*17625+q['step_in_epoch']
    assert all(bool(torch.isfinite(t).all()) for t in q['model'].values() if t.is_floating_point())
    best=torch.load(folder/'best_weights.pt',map_location='cpu',weights_only=True)
    assert set(best)==set(q['model']) and tuple(best['classifier.weight'].shape)==(6,768)
    if q['best']['epoch']==q['epoch'] and q['epoch_finished']:
        assert all(torch.equal(best[k],q['model'][k]) for k in best)
    proof={'attempt':ATTEMPT,'verified_utc':datetime.now(timezone.utc).isoformat(),
        'archive_filename':archive.name,'archive_sha256':archive_sha,
        'checkpoint_sha256':digest(checkpoint),'best_weights_sha256':digest(folder/'best_weights.pt'),
        'source_sha256':SOURCE_SHA,'epoch':q['epoch'],'step_in_epoch':q['step_in_epoch'],
        'epoch_finished':q['epoch_finished'],'epochs_validated':len(q['history']),
        'optimizer_updates':q['updates'],'skipped_updates':q['skips'],'best':q['best'],
        'torch_verification_version':torch.__version__,'status':'verified',
        'note':'CPU integrity/recovery-state inspection only; no training or final test performed'}
    del q,best;gc.collect()
    (ROOT/'data/cloud_recovery/recovery_verification.json').write_text(json.dumps(proof,indent=2)+'\n')
    (ROOT/'results/bert_recovery_verification.json').write_text(json.dumps(proof,indent=2)+'\n')
    print(json.dumps(proof,indent=2))


if __name__=='__main__':main()
