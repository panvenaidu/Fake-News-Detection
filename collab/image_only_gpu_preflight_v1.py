"""Bounded GPU release check on training IDs only. Never starts scientific training."""
import argparse
import gc
import importlib.metadata
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path


def run(args):
    import torch
    import train_image_only_v1 as t
    from multimodal_recovery_v1 import atomic_json, sha
    from check_image_only_v1 import fixture
    from packed_image_io_v3 import ArchiveStore
    started = time.monotonic()
    assert os.environ.get('CUDA_VISIBLE_DEVICES') == '0' and torch.cuda.is_available()
    assert torch.cuda.device_count() == 1 and torch.cuda.get_device_name(0) == 'Tesla T4'
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=False)
    audit = json.loads(Path(args.audit).read_text())
    age = (t.shared.datetime.now(t.shared.timezone.utc) - t.shared.datetime.fromisoformat(audit['utc'])).total_seconds()
    assert 0 <= age < 3600 and audit['active_events'] == 0 and audit['account'] == 'rocky62'
    assert audit['gpu_hours_remaining'] >= 12 and audit['private'] is True
    assert shutil.disk_usage('/kaggle/working').free > 12 * 1024**3
    assert shutil.disk_usage('/tmp').free > 120 * 1024**3
    cfg = json.loads(Path(args.config).read_text())
    t.configure(cfg['seed'])
    metadata = {'utc': t.shared.utc(), 'environment': t.environment(), 'audit': audit,
                'config_sha256': sha(args.config), 'sources': t.source_hashes(),
                'device_memory_bytes': torch.cuda.get_device_properties(0).total_memory,
                'driver': subprocess.check_output(['nvidia-smi', '--query-gpu=driver_version', '--format=csv,noheader'], text=True).strip(),
                'scratch_bytes_free': shutil.disk_usage('/tmp').free}
    atomic_json(out / 'preflight_start.json', metadata)
    print(json.dumps({'state': 'checking_registered_inputs', **metadata}), flush=True)
    frames, inputs = t.validated_inputs(args.root, args.coverage, args.index)
    assert len(frames['train']) == 563601 and len(frames['validation']) == 59299
    store = ArchiveStore(args.root, args.index, inputs['packed_index_sha256'])
    stage_seconds = time.monotonic() - started
    # Download and hash the official ImageNet artifact, then discard this model.
    initial = t.model(pretrained=True)
    weights = Path(torch.hub.get_dir()) / 'checkpoints/resnet50-11ad3fa6.pth'
    pretrained_sha = sha(weights)
    assert pretrained_sha.startswith('11ad3fa6')
    torch.save(initial.state_dict(), out / 'initial_imagenet_with_fresh_head.pt')
    del initial
    print('INPUTS_AND_INITIALIZATION_PASSED', flush=True)
    checks = fixture(argparse.Namespace(output=out / 'cuda_fixture', config=args.config, device='cuda'))
    assert checks['AMP_skip'] == 'passed_scheduler_did_not_advance'
    gc.collect(); torch.cuda.empty_cache()
    t.configure(42)
    network = t.model(pretrained=True).cuda()
    optimizer, scheduler, scaler = t.optimization(network, cfg, torch.device('cuda'))
    train_data = t.Images(frames['train'], args.root, cfg, True, store)
    timing = {}
    for phase in ['train', 'eval']:
        data = train_data if phase == 'train' else t.Images(frames['train'], args.root, cfg, False, store)
        stream = iter(t.loader(data, cfg, phase == 'train'))
        network.train(phase == 'train')
        def step():
            wait_started = time.monotonic()
            batch = next(stream)
            wait = time.monotonic() - wait_started
            images, labels = batch['images'].cuda(non_blocking=True), batch['labels'].cuda(non_blocking=True)
            if phase == 'train':
                optimizer.zero_grad(set_to_none=True)
                with torch.autocast('cuda', dtype=torch.float16):
                    logits = network(images)
                    loss = torch.nn.functional.cross_entropy(logits.float(), labels)
                scaler.scale(loss).backward(); scaler.unscale_(optimizer)
                torch.nn.utils.clip_grad_norm_(network.parameters(), 1.)
                scale = scaler.get_scale(); scaler.step(optimizer); scaler.update()
                if scaler.get_scale() >= scale:
                    scheduler.step()
                optimizer.zero_grad(set_to_none=True)
            else:
                with torch.inference_mode(), torch.autocast('cuda', dtype=torch.float16):
                    logits = network(images)
                    loss = torch.nn.functional.cross_entropy(logits.float(), labels)
                    probabilities = logits.float().softmax(-1)
                    probabilities.cpu(); loss.cpu()
            assert torch.isfinite(loss)
            return len(labels), wait
        for _ in range(3):
            step()
        torch.cuda.synchronize(); torch.cuda.reset_peak_memory_stats()
        clock = time.monotonic(); count = 0; waited = 0.
        while time.monotonic() - clock < 120:
            n, wait = step(); count += n; waited += wait
        torch.cuda.synchronize(); elapsed = time.monotonic() - clock
        timing[phase] = {'rows': count, 'seconds': elapsed, 'pairs_per_second': count / elapsed,
                         'loader_wait_fraction': waited / elapsed,
                         'peak_allocated_bytes': torch.cuda.max_memory_allocated()}
        del stream
        print(json.dumps({'state': 'throughput_measured', 'phase': phase, **timing[phase]}), flush=True)
    total_compute = 4 * (563601 / timing['train']['pairs_per_second'] + 59299 / timing['eval']['pairs_per_second']) + 59270 / timing['eval']['pairs_per_second']
    result = {**metadata, 'utc': t.shared.utc(), 'status': 'gpu_preflight_passed_requires_saved_readback',
              'inputs': inputs, 'checks': checks, 'timing': timing, 'staging_seconds': stage_seconds,
              'estimated_four_epoch_validation_test_compute_seconds': total_compute,
              'pretrained_weights_sha256': pretrained_sha, 'elapsed_seconds': time.monotonic() - started,
              'scientific_training': False, 'test_inference': False}
    atomic_json(out / 'PRIVATE_PREFLIGHT_RESULT.json', result)
    members = {str(p.relative_to(out)): {'bytes': p.stat().st_size, 'sha256': sha(p)}
               for p in out.rglob('*') if p.is_file()}
    atomic_json(out / 'PRIVATE_PREFLIGHT_MANIFEST.json', {'utc': t.shared.utc(), 'files': members})
    print(json.dumps(result), flush=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    for key in ['root', 'coverage', 'index', 'config', 'output', 'audit']:
        p.add_argument('--' + key, type=Path, required=True)
    run(p.parse_args())
