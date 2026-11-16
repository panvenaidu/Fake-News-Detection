"""Standalone approved pixels-only baseline. Science requires a released CUDA run.

Reuse the tested multimodal recovery loop and metrics, never its model/tokenizer.
The image experiment is isolated by its immutable protocol, attempt and contract.
"""
import argparse
import io
import json
import math
import os
import random
import signal
import sys
import time
from pathlib import Path
os.environ.setdefault('CUBLAS_WORKSPACE_CONFIG', ':4096:8')
import numpy as np
import pandas as pd
import PIL
from PIL import Image
import torch
import torchvision
from torch import nn
from torch.utils.data import Dataset, DataLoader, Subset
from torchvision import transforms as T
from torchvision.transforms import functional as F
from torchvision.models import resnet50, ResNet50_Weights
import train_usable_multimodal_v2 as shared
from multimodal_recovery_v1 import atomic_json, sha, crop, order, stable_seed, load_generation
from usable_cohort_v2 import COHORT, COUNTS, REGISTRATION_SHA

PROTOCOL = 'OFFICIAL-6W-IMAGE-USABLE-v1'
SOURCE_NAMES = ['train_image_only_v1.py', 'train_usable_multimodal_v2.py',
                'multimodal_recovery_v1.py', 'usable_cohort_v2.py', 'packed_image_io_v3.py',
                'verify_multimodal_final_v1.py', 'evaluate_frozen_image_only_v1.py', 'check_image_only_v1.py']
PIXEL_FIELDS = ['id', 'split', '6_way_label', 'source_shard', 'bytes', 'image_sha256', 'image_path']

def configure(seed):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.deterministic = True
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    torch.use_deterministic_algorithms(True)


def image_tensor(image, seed, epoch, ident, training):
    image = image.convert('RGB')
    if training:
        top, left, height, width = crop(image, seed, epoch, ident)
        image = F.resized_crop(image, top, left, height, width, [224, 224],
                               T.InterpolationMode.BILINEAR, antialias=True)
    else:
        image = F.center_crop(F.resize(image, 232, T.InterpolationMode.BILINEAR,
                                      antialias=True), [224, 224])
    return F.normalize(F.to_tensor(image), [.485, .456, .406], [.229, .224, .225])


class Images(Dataset):
    def __init__(self, frame, root, cfg, training, store=None):
        self.frame = frame.loc[:, [k for k in PIXEL_FIELDS if k in frame]].reset_index(drop=True)
        if self.frame.id.duplicated().any():
            raise ValueError('Duplicate image IDs')
        self.root, self.cfg, self.training, self.store = Path(root).resolve(), cfg, training, store
        self.epoch = 1

    def __len__(self):
        return len(self.frame)

    def __getitem__(self, index):
        row = self.frame.iloc[index]
        try:
            if self.store is None:
                source = (self.root / row.image_path).resolve()
                if not source.is_relative_to(self.root) or not source.is_file():
                    raise ValueError('Missing/escaping image')
                if 'image_sha256' in row and sha(source) != row.image_sha256:
                    raise ValueError('Image bytes differ')
            else:
                source = io.BytesIO(self.store.read(row))
            with Image.open(source) as image:
                image.load()
                tensor = image_tensor(image, self.cfg['seed'], self.epoch, row.id, self.training)
        except Exception as exc:
            raise RuntimeError('Image failure for ' + row.id) from exc
        return {'images': tensor, 'labels': int(row['6_way_label']), 'id': row.id}


def collate(rows):
    return {'images': torch.stack([row['images'] for row in rows]),
            'labels': torch.tensor([row['labels'] for row in rows]),
            'ids': [row['id'] for row in rows]}


def loader(data, cfg, training, cursor=0):
    selected = Subset(data, order(cfg['seed'], data.epoch, len(data))[cursor:].tolist()) if training else data
    generator = torch.Generator().manual_seed(stable_seed(cfg['seed'], data.epoch, 'workers-' + str(cursor)))
    return DataLoader(selected, batch_size=cfg['micro_batch'] if training else cfg['eval_batch'],
                      shuffle=False, num_workers=cfg['workers'], generator=generator,
                      collate_fn=collate, pin_memory=torch.cuda.is_available(), persistent_workers=False)


class ImageOnly(nn.Module):
    def __init__(self, pretrained=False):
        super().__init__()
        self.encoder = resnet50(weights=ResNet50_Weights.IMAGENET1K_V2 if pretrained else None)
        self.encoder.fc = nn.Sequential(nn.Dropout(.2), nn.Linear(2048, 6))

    def forward(self, images):
        return self.encoder(images)


def model(pretrained=False):
    return ImageOnly(pretrained)


def optimization(network, cfg, device):
    groups = {True: [], False: []}
    for parameter in network.parameters():
        groups[parameter.ndim > 1].append(parameter)
    optimizer = torch.optim.AdamW([
        {'params': groups[True], 'weight_decay': cfg['weight_decay']},
        {'params': groups[False], 'weight_decay': 0.}], lr=cfg['learning_rate'], betas=(.9, .999), eps=1e-8)
    def multiplier(step):
        if step < cfg['warmup_boundaries']:
            return step / max(1, cfg['warmup_boundaries'])
        return max(0., (cfg['planned_update_boundaries'] - step) /
                   (cfg['planned_update_boundaries'] - cfg['warmup_boundaries']))
    scheduler = torch.optim.lr_scheduler.LambdaLR(optimizer, multiplier)
    scaler = torch.amp.GradScaler(device.type, enabled=device.type == 'cuda')
    return optimizer, scheduler, scaler


def environment():
    import sklearn, transformers
    return {'python': sys.version, 'torch': torch.__version__, 'torchvision': torchvision.__version__,
            'numpy': np.__version__, 'pillow': PIL.__version__, 'sklearn': sklearn.__version__,
            'transformers': transformers.__version__, 'cuda': torch.version.cuda,
            'gpu': torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU fixture',
            'cuda_visible_devices': os.environ.get('CUDA_VISIBLE_DEVICES'),
            'deterministic_algorithms': torch.are_deterministic_algorithms_enabled(),
            'cudnn_benchmark': torch.backends.cudnn.benchmark,
            'cudnn_deterministic': torch.backends.cudnn.deterministic,
            'allow_tf32': torch.backends.cuda.matmul.allow_tf32}


def source_hashes():
    return {name: sha(Path(__file__).with_name(name)) for name in SOURCE_NAMES}


def validated_inputs(root, coverage, index):
    if sha(coverage) != 'afe8c723f91fe74f791908e0c16fab94d919af64c7cb7c9b5a37e676361d95e5':
        raise ValueError('Unrecognized saved image coverage')
    if sha(index) != 'fc8dc03a4f773da5762891c8392375add5fb8087251b527f3b37a880308e6018':
        raise ValueError('Unrecognized saved image index')
    frames, proof = shared.verified_frames(root, coverage, index)
    return {split: frame[PIXEL_FIELDS].copy() for split, frame in frames.items()}, proof


def export(folder, prefix, metrics, frame, split):
    frame = frame.copy()
    frame.insert(1, 'split', split)
    # Write in an owned staging directory, then publish metrics last as completion marker.
    temporary = Path(folder) / ('.export-' + prefix)
    temporary.mkdir(exist_ok=False)
    epoch = int(prefix.removeprefix('validation_epoch')) if prefix.startswith('validation_epoch') else 0
    proof = shared.export_eval(temporary, epoch, metrics, frame)
    generated = 'validation_epoch' + str(epoch)
    for suffix in ['predictions.csv', 'classification_report.json', 'confusions.json', 'metrics.json']:
        destination = Path(folder) / (prefix + '_' + suffix)
        if destination.exists():
            raise ValueError('Preserve existing completed export ' + str(destination))
        os.replace(temporary / (generated + '_' + suffix), destination)
    temporary.rmdir()
    return {'predictions_file': prefix + '_predictions.csv',
            'predictions_sha256': sha(Path(folder) / (prefix + '_predictions.csv')),
            'metrics': metrics, 'epoch': epoch}


def engine(network, cfg, output, device, contract):
    return shared.Engine(network, *optimization(network, cfg, device), cfg, output, device, contract)


def freeze(folder):
    folder = Path(folder)
    payload, proof = load_generation(folder / 'recovery')
    state, contract = payload['state'], payload['contract']
    if contract['config']['protocol_id'] != PROTOCOL or not (state['epoch'] > 4 or state['early_stopped']):
        raise ValueError('Registered training/early stop incomplete')
    if len(state['history']) < 3:
        raise ValueError('At least three complete validations required')
    if state['updates'] + state['skips'] != 17613 * len(state['history']):
        raise ValueError('Training schedule counts do not reconcile')
    winner = max(state['history'], key=lambda h: (h['validation']['macro_f1'], -h['validation']['loss'], -h['epoch']))
    best = state['best']
    if winner['epoch'] != best['epoch'] or sha(folder / best['weights_file']) != best['weights_sha256']:
        raise ValueError('Validation selection/weights mismatch')
    frozen = {'utc': shared.utc(), 'state': 'frozen_before_test', 'protocol_sha256': sha(folder / 'protocol.json'),
              'selected': best, 'history': state['history'], 'contract': contract, 'recovery': proof,
              'training_complete': True, 'test_rows': COUNTS['test']}
    path = folder / 'final_selection_frozen.json'
    if path.exists():
        old = json.loads(path.read_text())
        if old['selected'] != best or old['protocol_sha256'] != frozen['protocol_sha256']:
            raise ValueError('Frozen selection changed')
        return old
    atomic_json(path, frozen)
    return frozen


def run(args):
    if not torch.cuda.is_available() or os.environ.get('CUDA_VISIBLE_DEVICES') != '0':
        raise RuntimeError('One approved cloud CUDA device required')
    cfg = json.loads(Path(args.config).read_text())
    if cfg['protocol_id'] != PROTOCOL or cfg['planned_epochs'] != 4 or cfg['seed'] != 42:
        raise ValueError('Approved protocol mismatch')
    frames, inputs = validated_inputs(args.root, args.coverage, args.index)
    release = json.loads(Path(args.release).read_text())
    if (release['status'] != 'accepted_saved_preflight_readback' or release['sources'] != source_hashes()
            or release['config_sha256'] != sha(args.config)):
        raise ValueError('Saved verified GPU release required')
    configure(cfg['seed'])
    versions = environment()
    if versions != release['environment']:
        raise ValueError('Registered environment changed')
    folder = Path(args.output)
    if (folder / 'training_runtime_complete.json').exists():
        freeze(folder)
        print('TRAINING_ALREADY_COMPLETE', flush=True)
        return
    folder.mkdir(parents=True, exist_ok=args.resume)
    lock = folder / 'trainer.lock'
    fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    os.write(fd, str(os.getpid()).encode()); os.close(fd)
    try:
        contract = {'config': cfg, 'config_sha256': sha(args.config), 'inputs': inputs,
                    'versions': versions, 'sources': source_hashes(), 'attempt': args.attempt,
                    'preflight_release_sha256': sha(args.release),
                    'pretrained_weights_sha256': release['pretrained_weights_sha256']}
        path = folder / 'protocol.json'
        if path.exists() and json.loads(path.read_text()) != contract:
            raise ValueError('Immutable run contract changed')
        if args.resume and not path.exists():
            raise ValueError('Resume contract missing')
        atomic_json(path, contract)
        network = model(pretrained=not args.resume).cuda()
        if not args.resume:
            weight_path = Path(torch.hub.get_dir()) / 'checkpoints/resnet50-11ad3fa6.pth'
            if sha(weight_path) != release['pretrained_weights_sha256']:
                raise ValueError('Initial ImageNet weights differ')
        runner = engine(network, cfg, folder, torch.device('cuda'), contract)
        if args.resume:
            atomic_json(folder / 'last_resume_verification.json', runner.resume())
        else:
            runner.save()
        from packed_image_io_v3 import ArchiveStore
        store = ArchiveStore(args.root, args.index, inputs['packed_index_sha256'])
        data = {split: Images(frame, args.root, cfg, split == 'train', store) for split, frame in frames.items()}
        for sig in [signal.SIGTERM, signal.SIGINT]:
            signal.signal(sig, shared.request_stop)
        deadline = time.monotonic() + args.wall_seconds
        def bounded_boundary(current, ids, boundaries):
            return time.monotonic() >= deadline
        from verify_multimodal_final_v1 import verify
        while runner.state['epoch'] <= args.stop_after_epoch and not runner.state['early_stopped']:
            if shared.STOP or (folder / 'STOP_REQUESTED').exists():
                runner.save(); return
            epoch = runner.state['epoch']
            data['train'].epoch = epoch
            start = time.monotonic()
            if runner.state['phase'] == 'train':
                if not runner.train_epoch(loader(data['train'], cfg, True, runner.state['cursor']),
                                          len(data['train']), bounded_boundary):
                    atomic_json(folder / 'bounded_stop.json', {'utc': shared.utc(), 'state': runner.state})
                    return
            metrics, predictions = shared.evaluate(network, loader(data['validation'], cfg, False), torch.device('cuda'))
            if predictions.id.tolist() != frames['validation'].id.tolist():
                raise ValueError('Validation IDs/order mismatch')
            prefix = 'validation_epoch' + str(epoch)
            if (folder / (prefix + '_metrics.json')).exists():
                proof = {'predictions_file': prefix + '_predictions.csv', 'metrics': metrics, 'epoch': epoch,
                         'predictions_sha256': sha(folder / (prefix + '_predictions.csv'))}
                old = json.loads((folder / (prefix + '_metrics.json')).read_text())
                if old != metrics:
                    raise ValueError('Replayed validation differs from saved export')
            else:
                proof = export(folder, prefix, metrics, predictions, 'validation')
            verification = verify(folder, prefix, frames['validation'], 'validation')
            atomic_json(folder / (prefix + '_verified.json'), verification)
            runner.finish_validation(metrics, proof)
            print(json.dumps({'state': 'full_validation_accepted', 'epoch': epoch, 'metrics': metrics,
                              'elapsed_seconds': time.monotonic() - start, 'selected': runner.state['best']}), flush=True)
            if time.monotonic() >= deadline:
                return
        if runner.state['epoch'] > 4 or runner.state['early_stopped']:
            frozen = freeze(folder)
            atomic_json(folder / 'training_runtime_complete.json', {'utc': shared.utc(), 'frozen': frozen,
                        'status': 'training_validation_complete_test_pending', 'no_test_performed': True})
    finally:
        lock.unlink(missing_ok=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    for name in ['root', 'coverage', 'index', 'config', 'output', 'release']:
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--attempt', required=True)
    parser.add_argument('--resume', action='store_true')
    parser.add_argument('--stop-after-epoch', type=int, choices=[1, 2, 3, 4], default=4)
    parser.add_argument('--wall-seconds', type=int, default=36000)
    run(parser.parse_args())
