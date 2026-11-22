"""Image-only 83% study, using the historical cohort and resumable training engine."""
# MODEL: Configures image-only ViT/DeiT and DINOv2 classifier variants.
# LOGIC: Sets up study recipes, verified checkpoints, preflight, training, and validation selection.
import argparse
import importlib.metadata
import io
import math
import shutil
import sqlite3
from subprocess import CalledProcessError
import time
from pathlib import Path

from PIL import Image, ImageFile, ImageOps
import torch

# Vision Transformer image-only model: predicts one of six categories from an image.
# The training engine defines ViT-B/16 and DeiT III; this file also defines DINOv2 below.
import train_vit_finetune_v1 as engine
from frozen_image_pair_v1 import load_verified, save_json, require
from packed_image_io_v3 import ArchiveStore, sha
from vit_finetune_cloud_v1 import manifests, runtime
from vit_finetune_control_v1 import fixed_validation, frozen_test

RECIPES = ('crop', 'full_frame', 'layer_decay', 'dinov2')
DINO_REVISION = 'f9e44c814b77203eaa57a6bdbbd535f21ede1415'
DINO = {
    'implementation': 'transformers.Dinov2Model',
    'url': f'https://huggingface.co/facebook/dinov2-base/resolve/{DINO_REVISION}/model.safetensors',
    'revision': DINO_REVISION,
    'sha256': 'd73036b56966966d07975d696bde331762f37297e2f095de8cea0040c3aa0841',
}
BASELINE_VALIDATION_CORRECT = 47592
RESERVE_SECONDS = 6 * 3600
SESSION_MAX = 12 * 3600
READ = engine.read
original_network = engine.network


class FullFrameImages(engine.Images):
    def __getitem__(self, i):
        if self.cfg['framing'] == 'crop':
            return super().__getitem__(i)
        row = self.rows[i]
        require(not ImageFile.LOAD_TRUNCATED_IMAGES, 'Strict decoding required')
        with Image.open(io.BytesIO(self.reader.read(row))) as image:
            image.load()
            rgb = image.convert('RGB')
        # Explicit size calculation also handles extreme aspect ratios.
        scale = 224 / max(rgb.size)
        dims = tuple(max(1, min(224, round(d * scale))) for d in rgb.size)
        resized = rgb.resize(dims, Image.Resampling.BILINEAR)
        tile = Image.new('RGB', (224, 224), (124, 116, 104))
        tile.paste(resized, ((224 - dims[0]) // 2, (224 - dims[1]) // 2))
        return engine.TF.pil_to_tensor(tile), row['id'], int(row['6_way_label'])


def dino_attention_layout(tensors, expected_names):
    """Map legacy Hugging Face projection names to the installed model layout."""
    projection_names = {
        '.attention.attention.query.': '.attention.q_proj.',
        '.attention.attention.key.': '.attention.k_proj.',
        '.attention.attention.value.': '.attention.v_proj.',
        '.attention.output.dense.': '.attention.o_proj.',
    }
    mapped = {}
    for name, tensor in tensors.items():
        target = name
        if name not in expected_names:
            for previous, current in projection_names.items():
                if previous in name:
                    target = name.replace(previous, current)
                    break
        require(target not in mapped, f'Duplicate DINOv2 checkpoint tensor: {target}')
        mapped[target] = tensor
    return mapped


# DINOv2 VISION TRANSFORMER: extracts image features and predicts one of six categories.
class DinoClassifier(torch.nn.Module):
    def __init__(self, cfg, pretrained):
        from safetensors.torch import load_file
        from transformers import Dinov2Config, Dinov2Model

        super().__init__()
        self.encoder = Dinov2Model(Dinov2Config(
            image_size=518, patch_size=14, hidden_size=768, num_hidden_layers=12,
            num_attention_heads=12, mlp_ratio=4, layer_norm_eps=1e-6,
            drop_path_rate=0.0, hidden_dropout_prob=0.0, attention_probs_dropout_prob=0.0,
            layerscale_value=1.0, qkv_bias=True, hidden_act='gelu', use_swiglu_ffn=False))
        if pretrained:
            path = pretrained_path(DINO)
            require(sha(path) == DINO['sha256'], 'DINOv2 checkpoint hash differs')
            tensors = dino_attention_layout(load_file(str(path)), self.encoder.state_dict().keys())
            self.encoder.load_state_dict(tensors, strict=True)
        self.encoder.embeddings.mask_token.requires_grad_(False)
        self.head = torch.nn.Sequential(torch.nn.Dropout(cfg['dropout']), torch.nn.Linear(768, 6))

    def forward(self, x):
        return self.head(self.encoder(pixel_values=x).last_hidden_state[:, 0])


def network(device, cfg, pretrained=False, variant=None):
    if variant == DINO:
        return DinoClassifier(cfg, pretrained).to(device)
    return original_network(device, cfg, pretrained, variant)


def pretrained_path(variant):
    return Path(torch.hub.get_dir()) / 'checkpoints' / f"{variant['sha256']}.safetensors"


def cache_weights(variant):
    path = pretrained_path(variant)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        torch.hub.download_url_to_file(variant['url'], str(path), hash_prefix=variant['sha256'])
    require(sha(path) == variant['sha256'], 'Pinned pretrained checkpoint hash differs')


class RecipeEngine(engine.Engine):
    def __init__(self, device, cfg, plan, initial):
        # The original engine handles DDP, AMP, scheduling, coverage and recovery.
        # DINO uses different parameter paths for the first-block gradient probe.
        if plan.get('variant') == DINO:
            self.initialize_dino(device, cfg, plan, initial)
        else:
            super().__init__(device, cfg, plan, initial)
        if cfg['recipe'] == 'layer_decay':
            groups = {}
            last_block = len(self.raw.blocks) - 1
            for name, parameter in self.raw.named_parameters():
                if name.startswith('head.'):
                    lr = 3e-4
                elif name.startswith('blocks.'):
                    lr = 3e-5 * 0.75 ** (last_block - int(name.split('.')[1]))
                elif name.startswith(('norm.', 'fc_norm.')):
                    lr = 3e-5
                else:
                    lr = 3e-5 * 0.75 ** (last_block + 1)
                decay = cfg['weight_decay'] if parameter.ndim > 1 else 0.0
                groups.setdefault((lr, decay), []).append(parameter)
            schedule = self.sched.lr_lambdas[0]
            self.optim = torch.optim.AdamW(
                [{'params': group, 'lr': lr, 'weight_decay': decay}
                 for (lr, decay), group in groups.items()], fused=True)
            self.sched = torch.optim.lr_scheduler.LambdaLR(self.optim, schedule)

    def initialize_dino(self, device, cfg, plan, initial):
        # Match the inherited engine's plan, with explicit probes for this backbone.
        self.device, self.cfg, self.plan = device, cfg, plan
        engine.seed_all(cfg['seed'])
        self.raw = network(device, cfg, initial, DINO)
        self.model = (engine.DistributedDataParallel(
            self.raw, device_ids=[device.index], gradient_as_bucket_view=True, broadcast_buffers=False)
            if engine.size() > 1 else self.raw)
        groups = {}
        for name, parameter in self.raw.named_parameters():
            if not parameter.requires_grad:
                continue
            lr = plan['lr'] * (cfg['head_lr_ratio'] if name.startswith('head.') else 1)
            decay = cfg['weight_decay'] if parameter.ndim > 1 else 0.0
            groups.setdefault((lr, decay), []).append(parameter)
        self.optim = torch.optim.AdamW(
            [{'params': group, 'lr': lr, 'weight_decay': decay}
             for (lr, decay), group in groups.items()], fused=True)
        total = plan['epochs'] * math.ceil(plan['rows'] / cfg['effective_batch'])
        warm = max(1, math.ceil(total * cfg['warmup_fraction']))

        def schedule(success):
            if success < warm:
                return (success + 1) / warm
            return .5 * (1 + math.cos(math.pi * min(1, (success-warm)/max(1, total-warm-1))))

        self.sched = torch.optim.lr_scheduler.LambdaLR(self.optim, schedule)
        self.scaler = torch.amp.GradScaler('cuda', init_scale=512)
        require(cfg['effective_batch'] % (cfg['microbatch_per_device'] * engine.size()) == 0,
                'Invalid distributed batch')
        self.progress = dict(epoch=1, cursor=0, updates=0, skips=0, train_loss_sum=0.,
                             history=[], best=None, last_accuracy_gain=0, max_accuracy=-1.,
                             paused=False, stopped_early=False, segments_seconds=0.)
        self.probes = {'encoder': self.raw.encoder.encoder.layer[0].mlp.fc1.weight,
                       'head': self.raw.head[1].weight}


def recipe_cfg(cfg, recipe):
    return {**cfg, 'recipe': recipe, 'framing': 'full_frame' if recipe == 'full_frame' else 'crop'}


def run_preflight(buffer, out, cfg, store, frames, device):
    base = READ(buffer/'deit.json')
    for recipe in READ(buffer/'preflight_recipes.json'):
        folder = out/'engineering'/recipe
        if engine.rank() == 0:
            folder.mkdir(parents=True, exist_ok=True)
        engine.barrier()

        def build(device, cfg, plan, initial):
            return RecipeEngine(device, cfg, {**plan, 'variant': DINO if recipe == 'dinov2' else base}, initial)

        engine.Engine = build
        engine.preflight(buffer, folder, recipe_cfg(cfg, recipe), store, frames, device)
        if engine.rank() == 0:
            for path in (folder/'preflight').glob('smoke_resume*'):
                path.unlink()
        engine.barrier()


def launch(mode, source, buffer, out, world):
    import os
    import subprocess
    import sys
    command = [sys.executable]
    if world > 1:
        command += ['-m', 'torch.distributed.run', '--standalone', f'--nproc-per-node={world}']
    subprocess.run([*command, str(source/'vit83.py'), mode, str(buffer), str(out)], check=True,
                   env={**os.environ, 'OMP_NUM_THREADS': '1', 'MKL_NUM_THREADS': '1',
                        'PYTHONUNBUFFERED': '1'})


def cloud(source, out, mode, quota_used_minutes, recovery_sha=None):
    began = time.time()
    require(mode in ('preflight', 'train', 'test'), 'Unknown cloud phase')
    world = 1 if mode == 'test' else 2
    require(torch.cuda.device_count() >= world, 'Required GPU topology unavailable')
    remaining = 30 * 3600 - math.ceil(quota_used_minutes) * 60
    limit = min(SESSION_MAX, remaining - (0 if mode == 'test' else RESERVE_SECONDS))
    require(limit > 1200, 'Insufficient live quota for this session')
    if mode == 'preflight':
        limit = min(limit, 2100)
    deadline = began + limit - 300
    mount = Path('/kaggle/input')
    cfg = {**READ(source/'image_only_vit_finetune_v1.json'), 'goal_accuracy': .83,
           'full_max_epochs': 6, 'early_stop_patience': 99,
           'benchmark_updates': 120, 'benchmark_warmup': 20}
    pins = READ(source/'image_only_vit_resnet_frozen_v1.json')
    base = READ(source/'vit_finetune_candidate_deit3_v1.json')
    source_hashes = {p.name: sha(p) for p in sorted(source.iterdir()) if p.is_file()}
    if mode != 'preflight':
        marker = 'fixed_validation_receipt.json' if mode == 'test' else 'sessions.json'
        require(recovery_sha is not None, 'Exact saved output receipt SHA is required')
        matches = [p for p in mount.glob(f'**/urop_vit83/{marker}') if sha(p) == recovery_sha]
        require(len(matches) == 1, 'Attach the exact saved experiment version')
        recovered = matches[0].parent
        require(not out.exists(), 'Start in a clean saved Kaggle session')
        shutil.copytree(recovered, out)
    out.mkdir(exist_ok=True, parents=True)
    buffer = Path('/tmp/urop_vit83_buffer')
    buffer.mkdir(exist_ok=True)
    root, index, frames, approved = load_verified(mount, pins)
    print('approved_cohort_verified', pins['counts'], approved['excluded_ids_sha256'], flush=True)
    hashes = manifests(frames, out, cfg, buffer, include_test=mode == 'test')
    contract = {'cohort': pins, 'excluded_ids_sha256': approved['excluded_ids_sha256'],
                'excluded_rows': approved['excluded_rows'], 'manifest_hashes':
                {k: v for k, v in hashes.items() if k != 'test'}, 'sources': source_hashes}
    contract_path = out/'cohort_contract.json'
    if contract_path.exists():
        require(READ(contract_path) == contract, 'Saved cohort or bundled source changed')
    else:
        save_json(contract_path, contract)
    env = runtime()
    for package in ('timm', 'safetensors', 'transformers'):
        env['optional_packages'][package] = importlib.metadata.version(package)
    # A single reader stages the exact checked packed archives in local scratch.
    start = time.monotonic()
    store = ArchiveStore(root, index, pins['index_sha256'])
    staging = time.monotonic() - start
    with sqlite3.connect(f'file:{store.index}?mode=ro&immutable=1', uri=True) as db:
        require(db.execute('SELECT COUNT(*) FROM images').fetchone()[0] == sum(pins['counts'].values()),
                'Packed index row count differs')
    save_json(buffer/'storage.json', {'archive_cache': str(store.root), 'local_index': str(store.index),
                                     'index_sha256': pins['index_sha256']})
    save_json(buffer/'config.json', cfg)
    save_json(buffer/'deit.json', base)
    history = out/'sessions.json'
    sessions = READ(history) if history.exists() else []
    session = {'mode': mode, 'state': 'running', 'utc': engine.stamp(),
               'quota_used_minutes_observed': quota_used_minutes, 'duration_cap_seconds': limit,
               'deadline_epoch': deadline, 'world_size': world, 'environment': env,
               'staging_seconds': staging, 'recovery_sha256': recovery_sha}
    sessions.append(session)
    if mode != 'test':
        cache_weights(base)
    if mode == 'preflight':
        require(time.time() < deadline, 'Staging exhausted the preflight window')
        # Check the optional challenger independently so a download failure preserves the DeiT preflight.
        recipes = list(RECIPES)
        try:
            cache_weights(DINO)
        except (OSError, RuntimeError, ValueError) as exc:
            recipes.remove('dinov2')
            save_json(out/'dinov2_unavailable.json', {'reason': str(exc), 'checkpoint': DINO})
        save_json(buffer/'preflight_recipes.json', [r for r in recipes if r != 'dinov2'])
    session['setup_seconds'] = time.time() - began
    save_json(buffer/'session.json', session)
    save_json(history, sessions)
    if mode == 'train':
        from vit83_control import register
        registered = register(out, buffer, cfg, session, base)
        if any(t['variant'] == DINO for t in registered['pilots']):
            cache_weights(DINO)
    launch(mode, source, buffer, out, world)
    if mode == 'preflight' and 'dinov2' in recipes:
        save_json(buffer/'preflight_recipes.json', ['dinov2'])
        try:
            require(time.time() < deadline, 'Preflight window exhausted before the optional DINOv2 check')
            launch(mode, source, buffer, out, world)
        except (CalledProcessError, ValueError) as exc:
            save_json(out/'dinov2_unavailable.json', {'reason': str(exc), 'checkpoint': DINO})
            print('dinov2_unavailable', str(exc), flush=True)
    if mode == 'train' and (out/'selection_frozen.json').exists() and not (out/'fixed_validation_receipt.json').exists():
        launch('reload', source, buffer, out, 1)
    session['state'] = {
        'preflight': 'preflight_complete',
        'test': 'test_saved',
        'train': 'selection_frozen' if (out/'fixed_validation_receipt.json').exists()
                 else 'baseline_retained' if (out/'baseline_retained.json').exists()
                 else 'paused',
    }[mode]
    session['elapsed_seconds'] = time.time() - began
    save_json(history, sessions)
    print(session['state'], 'wall seconds', round(session['elapsed_seconds'], 1), flush=True)
    print('sessions_sha256', sha(history), flush=True)
    if (out/'fixed_validation_receipt.json').exists():
        print('fixed_validation_sha256', sha(out/'fixed_validation_receipt.json'), flush=True)
    if (out/'test_saved.json').exists():
        print('test_receipt_sha256', sha(out/'test_saved.json'), flush=True)


def worker(mode, buffer, out):
    import datetime
    import os
    import signal

    torch.set_num_threads(1)
    device = torch.device('cuda', int(os.environ.get('LOCAL_RANK', 0)))
    torch.cuda.set_device(device)
    if int(os.environ.get('WORLD_SIZE', 1)) > 1:
        engine.dist.init_process_group('nccl', timeout=datetime.timedelta(minutes=90), device_id=device)
    signal.signal(signal.SIGTERM, engine.on_stop)
    signal.signal(signal.SIGINT, engine.on_stop)
    engine.Images, engine.Engine, engine.network = FullFrameImages, RecipeEngine, network
    cfg = READ(buffer/'config.json')
    storage = READ(buffer/'storage.json')
    store = ArchiveStore(storage['archive_cache'], storage['local_index'], storage['index_sha256'])
    frames = engine.frames_from_buffer(buffer)
    if mode == 'preflight':
        run_preflight(buffer, out, cfg, store, frames, device)
    elif mode == 'train':
        from vit83_control import train
        train(buffer, out, cfg, store, frames, device)
    else:
        recipe = READ(out/'selection_frozen.json')['final_trial']['recipe']
        cfg = recipe_cfg(cfg, recipe)
        if mode == 'reload':
            fixed_validation(buffer, out, cfg, store, frames['validation'], device)
        elif mode == 'test':
            frozen_test(buffer, out, cfg, store, frames['train'], device)
    if engine.dist.is_initialized():
        engine.dist.destroy_process_group()


if __name__ == '__main__':
    import sys
    sys.modules['vit83'] = sys.modules[__name__]
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=('preflight', 'train', 'reload', 'test'))
    parser.add_argument('buffer', type=Path)
    parser.add_argument('out', type=Path)
    args = parser.parse_args()
    worker(args.mode, args.buffer, args.out)
