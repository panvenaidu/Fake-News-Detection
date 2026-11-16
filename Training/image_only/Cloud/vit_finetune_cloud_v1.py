"""Private notebook controller: stage pinned images and launch a saved top-to-bottom job."""
import importlib.metadata
import io
import json
import os
import platform
import shutil
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

import pandas as pd
from PIL import Image, ImageDraw, ImageOps
import torch
import torchvision
from torchvision.models import ViT_B_16_Weights
from frozen_image_pair_v1 import FIELDS, load_verified, require, sampled, save_json
from packed_image_io_v3 import ArchiveStore, sha
from train_vit_finetune_v1 import read, stamp


def manifests(frames, out, cfg, buffer, include_test=False):
    hashes = {}
    for split in ('train', 'validation', 'test') if include_test else ('train', 'validation'):
        f = frames[split]
        f[FIELDS].to_csv(buffer/f'{split}.csv', index=False)
        path = out/f'{split}_manifest.csv'
        content = f[['id', 'split', '6_way_label', 'image_sha256']].to_csv(index=False).encode()
        if path.exists():
            require(path.read_bytes() == content, f'{split} manifest differs from saved run')
        else:
            path.write_bytes(content)
        hashes[split] = sha(path)
    path = out/'pilot_train_manifest.csv'
    content = sampled(frames['train'], cfg['pilot_rows'], cfg['seed'])[
        ['id', 'split', '6_way_label', 'image_sha256']].to_csv(index=False).encode()
    if path.exists():
        require(path.read_bytes() == content, 'Pilot cohort differs')
    else:
        path.write_bytes(content)
    hashes['pilot_train'] = sha(path)
    return hashes


def label_conflicts(frame):
    by_label = frame.groupby(['image_sha256', '6_way_label'], sort=False).size()
    group = by_label.groupby(level=0, sort=False)
    excess = int(len(frame)-group.max().sum())
    return {'rows':len(frame), 'identical_byte_groups':len(group),
            'conflicting_duplicate_groups':int((group.size()>1).sum()),
            'incompatible_rows':excess, 'within_split_ceiling':1-excess/len(frame)}


def crop_audit(frames, store, out, cfg):
    """Retain privately: three rows per class/split, selected before looking."""
    from torchvision.transforms import functional as F
    from torchvision.transforms import InterpolationMode
    out.mkdir(exist_ok=True)
    for split in ('train','validation'):
        frame=frames[split]
        selected=pd.concat([g.sample(3,random_state=cfg['seed']+int(label))
                            for label,g in frame.groupby('6_way_label',sort=True)])
        grid=Image.new('RGB',(3*220, len(selected)*165),'white')
        draw=ImageDraw.Draw(grid)
        rows=[]
        for n,row in enumerate(selected.to_dict('records')):
            with Image.open(io.BytesIO(store.read(row))) as im:
                im.load()
                rgb=im.convert('RGB')
            resized=F.resize(rgb,256,InterpolationMode.BILINEAR,antialias=True)
            cropped=F.center_crop(resized,[224,224])
            padded=ImageOps.pad(rgb,(224,224),Image.Resampling.BILINEAR,(124,116,104))
            for i,(name,view) in enumerate(zip(('Original','Current center crop','Full-frame pad'),(rgb,cropped,padded))):
                grid.paste(ImageOps.contain(view,(211,140)),(i*220+4,n*165+20))
                draw.text((i*220+4,n*165+3),f"{name} | class {row['6_way_label']}",fill='black')
            rows.append({'label':row['6_way_label'],'id':row['id'],'sha256':row['image_sha256'],
                         'width':rgb.width,'height':rgb.height,
                         'crop_fraction_of_resized_frame':224**2/(resized.width*resized.height)})
        grid.save(out/f'{split}_crop_private.jpg', quality=89)
        save_json(out/f'{split}_sampling_receipt.json',rows)


def runtime():
    packages = {p:importlib.metadata.version(p) for p in
                ('torch', 'torchvision', 'numpy', 'pandas', 'Pillow', 'scikit-learn')}
    optional = {}
    for name in ('timm','safetensors'):
        try:
            optional[name]=importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            pass
    return {'python':platform.python_version(), 'packages':packages, 'optional_packages':optional,
            'cuda':torch.version.cuda,
            'cudnn':torch.backends.cudnn.version(),
            'nvidia_smi':subprocess.check_output(['nvidia-smi','--query-gpu=name,driver_version,memory.total',
                                                    '--format=csv,noheader'], text=True).splitlines(),
            'cpus_available':len(os.sched_getaffinity(0)),
            'free_bytes_working':shutil.disk_usage('/kaggle/working').free,
            'free_bytes_scratch':shutil.disk_usage('/tmp').free}


def invoke(mode, source, buffer, out, world):
    trainer = str(source/'train_vit_finetune_v1.py')
    prefix = [sys.executable, '-m', 'torch.distributed.run', '--standalone',
              f'--nproc-per-node={world}'] if world>1 else [sys.executable]
    subprocess.run([*prefix, trainer, mode, str(buffer), str(out)], check=True,
                   env={**os.environ, 'OMP_NUM_THREADS':'1', 'MKL_NUM_THREADS':'1',
                        'PYTHONUNBUFFERED':'1'})


def start(source, out, mode='preflight', world=2, quota_used_minutes=0,
          recovery=None, stop_after_seconds=None, accounting_multiplier=1,
          expected_recovery_sha256=None):
    source, out = Path(source), Path(out)
    began = time.time()
    cfg = read(source/'image_only_vit_finetune_v1.json')
    pinned = read(source/'image_only_vit_resnet_frozen_v1.json')
    max_session = cfg['session_limit_seconds']
    require(0 < world <= torch.cuda.device_count(), 'Registered GPU topology unavailable')
    remaining = cfg['initial_quota_hours']*3600 - quota_used_minutes*60
    require(accounting_multiplier in (1, 2) and remaining > 0, 'Invalid live quota')
    reserve = cfg['initial_quota_hours']*3600*cfg['reserve_fraction'] if mode in ('preflight','train') else 0
    duration = min(max_session, (remaining-reserve)/accounting_multiplier)
    require(duration>900, 'Live quota does not support this phase plus its reserve')
    if stop_after_seconds is not None:
        duration = min(duration, stop_after_seconds)
    # Stop before Kaggle termination; prioritize completing saved outputs.
    deadline = began + duration - min(1800, max(120, duration*.1))
    if mode in ('train','test'):
        require(recovery is not None or out.is_dir(), 'Mount the registered saved output before continuing')
    if recovery is not None and not out.exists():
        if recovery == 'auto':
            if mode=='test':
                marker='fixed_validation_receipt.json'
            else:
                marker='preflight/timing.json'
            matches=[p for p in Path('/kaggle/input').glob(f'**/urop_vit_finetune/{marker}')
                     if expected_recovery_sha256 is None or sha(p)==expected_recovery_sha256]
            require(len(matches)==1, f'Attach exactly one matching saved ViT recovery output; found {len(matches)}')
            recovery = matches[0].parent.parent if mode!='test' else matches[0].parent
        # Copy only from mounted saved output; never publish or replace the input.
        recovery = Path(recovery).resolve()
        require(recovery.is_relative_to(Path('/kaggle/input')) and recovery.is_dir(),
                'Recovery must be a private saved Notebook input')
        # The engineering smoke checkpoint is evidence in its own saved
        # version. The measured receipt is sufficient to start a new run.
        def omit_smoke(folder, names):
            if Path(folder).name == 'preflight':
                return [name for name in names if name.startswith('smoke_resume')]
            return []
        if expected_recovery_sha256 is not None:
            marker='fixed_validation_receipt.json' if mode=='test' else 'preflight/timing.json'
            require(sha(recovery/marker)==expected_recovery_sha256,'Mounted recovery receipt changed')
        shutil.copytree(recovery, out, ignore=omit_smoke)
    out.mkdir(exist_ok=True, parents=True)
    buffer = Path('/tmp/urop_vit_finetune_buffer')
    buffer.mkdir(exist_ok=True)
    shutil.copytree(source, out/'source', dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns('__pycache__'))
    try:
        env = runtime()
        hashes = {p.name:sha(p) for p in sorted(source.iterdir()) if p.is_file()}
        input_root, index, frames, registration = load_verified(Path('/kaggle/input'), pinned)
        print('registered_input_verified', pinned['counts'], 'gpu', env['nvidia_smi'], flush=True)
        begin_stage = time.monotonic()
        reader = ArchiveStore(input_root, index, pinned['index_sha256'])
        staging = time.monotonic()-begin_stage
        save_json(buffer/'storage.json', {'archive_cache':str(reader.root), 'local_index':str(reader.index),
                                          'index_sha256':pinned['index_sha256']})
        with sqlite3.connect(f'file:{reader.index}?mode=ro&immutable=1', uri=True) as db:
            require(db.execute('SELECT COUNT(*) FROM images').fetchone()[0] == sum(pinned['counts'].values()),
                    'Retained packed index row count differs')
        if mode == 'test':
            require((out/'selection_frozen.json').is_file(), 'A completed validation-only release must be mounted')
        save_json(buffer/'config.json', cfg)
        split_hashes = manifests(frames, out, cfg, buffer, include_test=mode=='test')
        source_pin = ViT_B_16_Weights.IMAGENET1K_V1
        if mode in ('preflight', 'train'):
            pretrained = Path(torch.hub.get_dir())/'checkpoints'/source_pin.url.rsplit('/', 1)[-1]
            if not pretrained.exists():
                pretrained.parent.mkdir(exist_ok=True, parents=True)
                torch.hub.download_url_to_file(source_pin.url, str(pretrained), hash_prefix=cfg['weight_sha256'])
            require(sha(pretrained)==cfg['weight_sha256'], 'Pretrained tensor hash differs')
        history = out/'sessions.json'
        sessions = read(history) if history.exists() else []
        session = {'mode':mode, 'utc':stamp(), 'environment':env, 'world_size':world,
                   'quota_used_minutes_observed':quota_used_minutes, 'accounting_multiplier':accounting_multiplier,
                   'duration_cap_seconds':duration, 'deadline_epoch':deadline, 'staging_seconds':staging,
                   'setup_seconds':time.time()-began, 'state':'running'}
        sessions.append(session)
        save_json(history,sessions)
        save_json(buffer/'session.json',session)
        if mode=='preflight':
            source_record = {'config':cfg,'inputs':pinned,'hashes':hashes,'splits':split_hashes,
                             'initialization_url':source_pin.url, 'cohort_registration':registration['cohort_id'],
                             'holdout_policy':'No test decode or inference before validation freeze',
                             'diagnostics':{s:label_conflicts(frames[s]) for s in ('train','validation')}}
            save_json(out/'preflight_contract.json',source_record)
            invoke(mode, source, buffer, out, world)
            session['state']='preflight_complete'
        elif mode in ('train','test'):
            previous = read(out/'preflight_contract.json')
            # Source for the real run is registered separately; initial immutable recipe and data must match.
            require(previous['config']==cfg and previous['inputs']==pinned
                    and all(split_hashes[k]==v for k,v in previous['splits'].items()),
                    'Preflight config or approved split differs')
            if mode=='train':
                from vit_finetune_control_v1 import register
                alt = read(source/'vit_finetune_candidate_deit3_v1.json')
                reg = register(out, cfg, session, previous, hashes, alt)
                if not (out/'crop_audit/validation_sampling_receipt.json').is_file():
                    crop_audit(frames, reader, out/'crop_audit', cfg)
                alt_failed = out/'alternative_unavailable.json'
                if reg.get('alternative') and not alt_failed.exists():
                    dest = Path(torch.hub.get_dir())/'checkpoints'/f"{alt['sha256']}.safetensors"
                    try:
                        if not dest.exists():
                            torch.hub.download_url_to_file(alt['url'],str(dest),hash_prefix=alt['sha256'])
                        require(sha(dest)==alt['sha256'],'Pinned DeiT III weights SHA differs')
                    except (OSError, ValueError, RuntimeError) as exc:
                        require(not (out/reg['alternative']['id']).exists(),
                                'Previously started alternative requires its pinned weights for recovery')
                        save_json(alt_failed, {'utc':stamp(), 'reason':str(exc),
                                              'trial':reg['alternative'], 'state':'not_started'})
                        print('optional_alternative_unavailable',str(exc),flush=True)
                invoke('train',source,buffer,out,world)
                if (out/'selection_frozen.json').is_file() and not (out/'fixed_validation_receipt.json').exists():
                    invoke('fixed-validation',source,buffer,out,1)
                session['state'] = 'selection_frozen' if (out/'fixed_validation_receipt.json').exists() else 'paused'
            else:
                invoke('test',source,buffer,out,1)
                session['state']='test_saved'
        else:
            raise ValueError(mode)
        session['elapsed_seconds'] = time.time()-began
        save_json(history,sessions)
        print(session['state'], 'wall seconds', round(session['elapsed_seconds'],1), flush=True)
    except Exception as exc:
        save_json(out/'status.json', {'state':'failed','mode':mode,'utc':stamp(),'reason':str(exc),
                                    'elapsed_seconds':time.time()-began})
        raise
