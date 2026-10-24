"""Disposable cloud-only train-path timing; never validation/test inference.

Run only after full immutable input verification and the actual CUDA recovery
fixture. Discard this model: the registered scientific run starts separately
from the approved text warm start. No preflight scores select a model.
"""
import argparse
import hashlib
import importlib.metadata
import json
import math
import os
from pathlib import Path
import sys
import time

os.environ.setdefault('CUDA_VISIBLE_DEVICES', '0')
os.environ.setdefault('CUBLAS_WORKSPACE_CONFIG', ':4096:8')
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
TRAINER_SHA = '88412d918b77f8a54569b25a8c469618c028ebaeeeb0b6050385dc55bd20ac1e'
RECOVERY_SHA = '2f5f67ce79289c69279040d21b483e28535895f5c99c63e0021da3eee6d3d1c8'
CONFIG_SHA = 'ad8f86f86b1fef453ae3bccda0aeb13cc50b298dc0d5d502f87c9ac4b041b483'


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda: f.read(4 * 1024**2), b''):
            h.update(b)
    return h.hexdigest()


def verify_request(root, output, seconds, evaluation_seconds, fixture, config):
    if not Path(root).resolve().is_relative_to(Path('/kaggle/input')):
        raise ValueError('Actual immutable Kaggle input required; no laptop run')
    work = Path('/kaggle/working')
    out = Path(output).resolve()
    if out == work or not out.is_relative_to(work) or out.exists():
        raise ValueError('New dedicated disposable Kaggle working folder required')
    if not 600 <= seconds <= 900 or not 60 <= evaluation_seconds <= 120:
        raise ValueError('Bounded 600–900s training /60–120s train-image eval timing required')
    if sha(config) != CONFIG_SHA:
        raise ValueError('Registered config checksum mismatch')
    for name, digest in [('train_usable_multimodal_v2.py', TRAINER_SHA),
                         ('multimodal_recovery_v1.py', RECOVERY_SHA)]:
        if sha(ROOT / 'scripts' / name) != digest:
            raise ValueError('Production source checksum mismatch: ' + name)
    if sha(ROOT/'scripts/usable_cohort_v2.py') != '22bff1eb0fa14d102ad07786f936c5c1ed1582ec7bd5cee2b8e8dc5eb3520092':
        raise ValueError('Approved cohort loader source differs')
    proof = json.loads(Path(fixture).read_text())
    if (proof.get('status') != 'passed_cuda_engineering_fixture'
            or proof.get('trainer_sha256') != TRAINER_SHA
            or proof.get('recovery_sha256') != RECOVERY_SHA):
        raise ValueError('Actual production CUDA recovery fixture required')
    return out, proof


def run(args):
    out, fixture = verify_request(args.root, args.output, args.seconds,
                                  args.eval_seconds, args.cuda_fixture, args.config)
    import train_usable_multimodal_v2 as t
    import torch
    from torch import nn
    import numpy as np
    import random
    if (not torch.cuda.is_available() or torch.cuda.device_count() != 1
            or torch.__version__ != fixture['torch']
            or torch.version.cuda != fixture['cuda']
            or torch.cuda.get_device_name(0) != fixture['device']):
        raise ValueError('Repeat recovery fixture for this actual CUDA environment')
    cfg = json.loads(args.config.read_text())
    # This repeats the production exact-ID/title/label/hash gate. Test files are
    # checked for integrity only; only the train frame reaches any model loader.
    frames, inputs = t.verified_frames(args.root, args.coverage)
    if sha(args.warmstart) != cfg['warmstart_sha256']:
        raise ValueError('Selected text warm-start checksum mismatch')
    out.mkdir(parents=True, exist_ok=False)
    t.atomic_json(out / 'preflight_state.json', {
        'state': 'disposable_preflight_started', 'utc': t.utc(),
        'scientific_training': False, 'train_only': True,
        'registered_attempt_recovery': False})
    random.seed(cfg['seed']); np.random.seed(cfg['seed'])
    torch.manual_seed(cfg['seed']); torch.cuda.manual_seed_all(cfg['seed'])
    torch.backends.cudnn.benchmark = False
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.use_deterministic_algorithms(True, warn_only=True)
    tokenizer = t.AutoTokenizer.from_pretrained(cfg['bert_checkpoint'], revision=cfg['bert_revision'])
    text = t.BertModel(t.AutoConfig.from_pretrained(cfg['bert_checkpoint'],
                                                  revision=cfg['bert_revision']), add_pooling_layer=False)
    mapping = t.map_text_encoder(torch.load(args.warmstart, map_location='cpu', weights_only=True), text)
    image = t.resnet50(weights=t.ResNet50_Weights.IMAGENET1K_V2)
    image.fc = nn.Identity()
    model = t.MaximumFusion(text, image).cuda()
    groups = {}
    for name, p in model.named_parameters():
        family = 'bert' if name.startswith('text.') else 'image' if name.startswith('image.') else 'head'
        decay = 0. if p.ndim <= 1 else cfg['image_decay' if family == 'image' else 'bert_head_decay']
        groups.setdefault((cfg[family + '_lr'], decay), []).append(p)
    opt = torch.optim.AdamW([{'params': p, 'lr': lr, 'weight_decay': decay}
                            for (lr, decay), p in groups.items()], betas=(.9, .999), eps=1e-8)
    budget = math.ceil(math.ceil(len(frames['train']) / cfg['micro_batch']) / cfg['accumulation']) * cfg['planned_epochs']
    scheduler = t.get_linear_schedule_with_warmup(opt, math.ceil(budget * cfg['warmup_fraction']), budget)
    scaler = torch.amp.GradScaler('cuda')
    contract = {'purpose': 'disposable_train_only_preflight_not_scientific_run',
                'inputs': inputs, 'config_sha256': CONFIG_SHA, 'trainer_sha256': TRAINER_SHA}
    engine = t.Engine(model, opt, scheduler, scaler, cfg, out, torch.device('cuda'), contract)
    data = t.Pairs(frames['train'], args.root, tokenizer, cfg, True)
    loader = t.build_loader(data, tokenizer, cfg, True)
    # Prime CUDA/data workers and optimizer state outside the timed interval.
    engine.train_epoch(loader, len(data),
                       on_boundary=lambda current, ids, boundaries:
                       current.state['updates'] >= 2 or boundaries >= 32)
    if engine.state['updates'] < 1:
        raise RuntimeError('Warmup produced no successful optimizer update')
    start_cursor = engine.state['cursor']; start_updates = engine.state['updates']
    torch.cuda.synchronize(); torch.cuda.reset_peak_memory_stats()
    started = time.monotonic()
    timing = {}

    def timed_batches(source, counters):
        iterator = iter(source)
        while True:
            wait_start = time.monotonic()
            try:
                batch = next(iterator)
            except StopIteration:
                return
            counters['loader_wait_seconds'] = counters.get('loader_wait_seconds', 0.) + time.monotonic() - wait_start
            yield batch

    def stop_at_boundary(current, ids, boundaries):
        torch.cuda.synchronize()
        elapsed = time.monotonic() - started
        if elapsed < args.seconds:
            return False
        timing.update(seconds=elapsed, examples=current.state['cursor'] - start_cursor)
        return True

    # The unchanged production loop checkpoints at its normal intervals; those
    # costs remain inside timing, giving a conservative throughput estimate.
    engine.train_epoch(timed_batches(t.build_loader(data, tokenizer, cfg, True, start_cursor), timing),
                       len(data), on_boundary=stop_at_boundary)
    if timing.get('seconds', 0) < 600 or engine.state['updates'] <= start_updates:
        raise RuntimeError('Insufficient measured successful training')
    torch.cuda.synchronize()
    checkpoint_start = time.monotonic()
    generation = engine.save()
    payload, recovered = t.load_generation(out / 'recovery')
    checkpoint_seconds = time.monotonic() - checkpoint_start
    if payload['cursor'] != engine.state['cursor'] or payload['contract'] != contract:
        raise ValueError('Preflight full-state checkpoint roundtrip failed')
    del payload
    # Measure the production evaluation preprocessing/inference path on TRAIN
    # images only. No validation/test model inference, probabilities or scores.
    eval_data = t.Pairs(frames['train'], args.root, tokenizer, cfg, False)
    model.eval(); count = 0
    eval_loader = t.build_loader(eval_data, tokenizer, cfg, False)
    torch.cuda.synchronize(); eval_start = time.monotonic()
    eval_timing = {}
    with torch.inference_mode():
        for batch in timed_batches(eval_loader, eval_timing):
            batch.pop('ids'); labels = batch.pop('labels').cuda(non_blocking=True)
            with torch.autocast('cuda', dtype=torch.float16):
                logits = model(**{k: v.cuda(non_blocking=True) for k, v in batch.items()})
            ce = nn.functional.cross_entropy(logits.float(), labels, reduction='none')
            if not torch.isfinite(ce).all():
                raise ValueError('Nonfinite train-only evaluation-path loss')
            # Include the production CPU probability/loss transfer overhead.
            logits.float().softmax(-1).cpu().tolist(); ce.cpu().tolist()
            count += len(labels)
            torch.cuda.synchronize()
            if time.monotonic() - eval_start >= args.eval_seconds:
                break
    eval_elapsed = time.monotonic() - eval_start
    if eval_elapsed < args.eval_seconds or count == 0:
        raise RuntimeError('Incomplete evaluation-path timing')
    versions = {n: importlib.metadata.version(n) for n in ['torch', 'torchvision', 'transformers', 'numpy', 'Pillow']}
    result = {'utc': t.utc(), 'status': 'passed_measured_multimodal_preflight',
              'train_only': True, 'measurement_seconds': timing['seconds'],
              'training_examples': timing['examples'],
              'train_loader_wait_seconds': timing['loader_wait_seconds'],
              'train_examples_per_second': timing['examples'] / timing['seconds'],
              'eval_path_examples_per_second': count / eval_elapsed,
              'eval_path_measurement_seconds': eval_elapsed, 'eval_path_train_examples': count,
              'eval_path_loader_wait_seconds': eval_timing['loader_wait_seconds'],
              'checkpoint_seconds': checkpoint_seconds, 'checkpoint': generation,
              'checkpoint_roundtrip': recovered, 'config_sha256': CONFIG_SHA,
              'trainer_sha256': TRAINER_SHA, 'recovery_sha256': RECOVERY_SHA,
              'preflight_source_sha256': sha(__file__), 'inputs': inputs,
              'cuda_fixture_sha256': sha(args.cuda_fixture), 'warmstart_mapping': mapping,
              'torch': torch.__version__, 'cuda': torch.version.cuda,
              'device': torch.cuda.get_device_name(0), 'used_devices': 1,
              'versions': versions, 'peak_gpu_bytes': torch.cuda.max_memory_allocated(),
              'successful_updates': engine.state['updates'], 'amp_skips': engine.state['skips'],
              'scientific_epochs_completed': 0, 'full_validations_completed': 0,
              'test_performed': False, 'disposition': 'Discard this model; scientific run starts from approved warm start'}
    t.atomic_json(out / 'measured_preflight.json', result)
    print(json.dumps(result), flush=True)
    return result


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    for name in ['root', 'coverage', 'config', 'output', 'warmstart', 'cuda-fixture']:
        ap.add_argument('--' + name, type=Path, required=True)
    ap.add_argument('--seconds', type=int, default=600)
    ap.add_argument('--eval-seconds', type=int, default=60)
    run(ap.parse_args())
