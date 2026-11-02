"""Disposable local/CUDA release checks. No scientific results or test inference."""
import argparse
import copy
import json
import shutil
import time
from pathlib import Path
import numpy as np
import pandas as pd
from PIL import Image
import torch
from torch import nn
import train_image_only_v1 as t
from multimodal_recovery_v1 import atomic_json, load_generation, sha, crop, capture_rng


def equal(left, right, path='root'):
    if isinstance(left, torch.Tensor):
        assert torch.equal(left.cpu(), right.cpu()), path
    elif isinstance(left, np.ndarray):
        assert np.array_equal(left, right), path
    elif isinstance(left, dict):
        assert set(left) == set(right), path
        for key in left:
            equal(left[key], right[key], path + '.' + str(key))
    elif isinstance(left, (list, tuple)):
        assert len(left) == len(right), path
        for index, (a, b) in enumerate(zip(left, right)):
            equal(a, b, path + '.' + str(index))
    else:
        assert left == right, path


def fixture(args):
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=False)
    cfg = json.loads(Path(args.config).read_text())
    cfg.update(micro_batch=4, accumulation=2, eval_batch=4, workers=0, checkpoint_updates=100000)
    device = torch.device(args.device)
    if device.type == 'cpu':
        torch.set_num_threads(2)
    t.configure(42)
    arrays = np.random.default_rng(42)
    rows = []
    for index in range(17):
        mode = ['RGB', 'L', 'RGBA'][index % 3]
        shape = (241, 257, len(mode)) if mode != 'L' else (241, 257)
        path = output / ('fixture_' + str(index) + '.png')
        Image.fromarray(arrays.integers(0, 256, shape, dtype=np.uint8)).save(path)
        rows.append({'id': 'fixture' + str(index), 'image_path': path.name, 'image_sha256': sha(path),
                     'split': 'train', '6_way_label': index % 6, 'clean_title': 'discarded text'})
    frame = pd.DataFrame(rows)
    data = t.Images(frame, output, cfg, True)
    assert 'clean_title' not in data.frame
    first = data[0]['images']
    with Image.open(output / frame.iloc[0].image_path) as image:
        rgb = image.convert('RGB')
        top, left, h, w = crop(rgb, 42, 1, 'fixture0')
        expected = t.F.normalize(t.F.to_tensor(t.F.resized_crop(rgb, top, left, h, w, [224, 224],
                                  t.T.InterpolationMode.BILINEAR, antialias=True)), [.485, .456, .406], [.229, .224, .225])
    assert torch.equal(first, expected) and first.shape == (3, 224, 224)
    changed = frame.copy(); changed['clean_title'] = 'changed metadata'
    assert torch.equal(t.Images(changed, output, cfg, True)[0]['images'], first)
    for ident in range(17):
        assert data[ident]['images'].shape == (3, 224, 224)
    assert [len(b['ids']) for b in t.loader(data, cfg, True)] == [4, 4, 4, 4, 1]
    tail_cfg = dict(cfg, micro_batch=32, accumulation=1)
    assert [len(b['ids']) for b in t.loader(data, tail_cfg, True)] == [17]
    assert 563601 % 32 == 17
    duplicate = pd.concat([frame, frame.iloc[:1]])
    try:
        t.Images(duplicate, output, cfg, True)
        raise AssertionError('Duplicate accepted')
    except ValueError:
        pass
    broken = frame.iloc[:1].copy(); broken['image_path'] = 'missing.png'
    try:
        t.Images(broken, output, cfg, False)[0]
        raise AssertionError('Missing image accepted')
    except RuntimeError:
        pass
    bad = output / 'corrupt.png'; bad.write_bytes(b'<html>not an image</html>')
    broken['image_path'] = bad.name; broken['image_sha256'] = sha(bad)
    try:
        t.Images(broken, output, cfg, False)[0]
        raise AssertionError('Corrupt image accepted')
    except RuntimeError:
        pass
    t.configure(42)
    visual = t.model().to(device)
    assert all(p.requires_grad for p in visual.parameters())
    visual.eval()
    pixels = torch.stack([data[0]['images'], data[1]['images']]).to(device)
    with torch.no_grad():
        logits = visual(pixels)
        assert logits.shape == (2, 6) and torch.isfinite(logits).all()
        assert torch.equal(logits, visual(pixels))
        assert not torch.equal(logits, visual(pixels + .1))
    visual.train()
    loss = nn.functional.cross_entropy(visual(pixels), torch.tensor([0, 1], device=device))
    loss.backward()
    assert visual.encoder.conv1.weight.grad.abs().sum() > 0 and visual.encoder.fc[1].weight.grad.abs().sum() > 0
    old = visual.encoder.fc[1].weight.detach().clone()
    opt = torch.optim.SGD(visual.parameters(), lr=.01); opt.step()
    assert not torch.equal(old, visual.encoder.fc[1].weight)
    del opt, visual, pixels, logits, loss
    if device.type == 'cuda':
        torch.cuda.empty_cache()
    # Full real ResNet on CUDA; compact BN/dropout network on CPU for recovery mechanics.
    def make_model():
        if device.type == 'cuda':
            return t.model().to(device)
        class Tiny(nn.Sequential):
            def forward(self, images):
                return super().forward(images)
        return Tiny(nn.Conv2d(3, 4, 3), nn.BatchNorm2d(4), nn.AdaptiveAvgPool2d(1),
                    nn.Flatten(), nn.Dropout(.2), nn.Linear(4, 6)).to(device)
    contract = {'protocol_id': t.PROTOCOL, 'disposable': True, 'device': str(device)}
    t.configure(42)
    continuous = t.engine(make_model(), cfg, output / 'continuous', device, contract)
    assert continuous.train_epoch(t.loader(data, cfg, True), 17)
    final = {'model': copy.deepcopy(continuous.model.state_dict()),
             'optimizer': copy.deepcopy(continuous.optimizer.state_dict()),
             'scheduler': copy.deepcopy(continuous.scheduler.state_dict()),
             'scaler': copy.deepcopy(continuous.scaler.state_dict()),
             'state': copy.deepcopy(continuous.state), 'rng': capture_rng()}
    del continuous
    t.configure(42)
    interrupted = t.engine(make_model(), cfg, output / 'replayed', device, contract)
    assert not interrupted.train_epoch(t.loader(data, cfg, True), 17, lambda e, ids, b: b == 1)
    assert interrupted.state['cursor'] == 8
    del interrupted
    t.configure(999)
    resumed = t.engine(make_model(), cfg, output / 'replayed', device, contract)
    resumed.resume()
    assert resumed.train_epoch(t.loader(data, cfg, True, resumed.state['cursor']), 17)
    got = {'model': resumed.model.state_dict(), 'optimizer': resumed.optimizer.state_dict(),
           'scheduler': resumed.scheduler.state_dict(), 'scaler': resumed.scaler.state_dict(),
           'state': resumed.state, 'rng': capture_rng()}
    equal(final, got)
    resumed.save()
    pointer = json.loads((output / 'replayed/recovery/generations.json').read_text())
    (output / 'replayed/recovery' / pointer['generations'][0]['file']).write_bytes(b'corrupt disposable newest')
    previous, fallback = load_generation(output / 'replayed/recovery')
    assert fallback['fallback_errors'] and previous['cursor'] == 17
    # Selection and patience are distinct; a <.001 improvement can win selection.
    selected = {'metrics': {'macro_f1': .8, 'loss': 1.}}
    assert t.shared.better({'macro_f1': .8005, 'loss': 2.}, selected)
    assert not t.shared.better({'macro_f1': .8, 'loss': 1.}, selected)
    assert t.shared.better({'macro_f1': .8, 'loss': .9}, selected)
    # Full exported metrics and the independent verifier must reject damaged rows.
    from verify_multimodal_final_v1 import verify
    y = np.arange(6)
    probabilities = np.full((6, 6), .02)
    probabilities[y, y] = .9
    ce = -np.log(probabilities[y, y])
    predictions = pd.DataFrame({'id': ['metric' + str(i) for i in y], 'true_label': y,
        'predicted_label': y, 'cross_entropy': ce, **{'p' + str(i): probabilities[:, i] for i in y}})
    official = pd.DataFrame({'id': predictions.id, '6_way_label': y})
    metrics = t.shared.measure(y, y, ce)
    t.export(output, 'validation_epoch0', metrics, predictions, 'validation')
    verify(output, 'validation_epoch0', official, 'validation')
    path = output / 'validation_epoch0_predictions.csv'
    saved = path.read_bytes()
    damaged = pd.read_csv(path); damaged.loc[0, 'id'] = 'incorrect'
    damaged.to_csv(path, index=False)
    try:
        verify(output, 'validation_epoch0', official, 'validation')
        raise RuntimeError('Damaged predictions accepted')
    except AssertionError:
        pass
    path.write_bytes(saved)
    amp_skip = 'not_applicable_CPU'
    if device.type == 'cuda':
        t.configure(42)
        skip = t.engine(make_model(), cfg, output / 'amp_skip', device, contract)
        handle = next(skip.model.parameters()).register_hook(lambda grad: torch.full_like(grad, float('inf')))
        assert not skip.train_epoch(t.loader(data, cfg, True), 17, lambda e, ids, b: b == 1)
        handle.remove()
        assert skip.state['skips'] == 1 and skip.state['updates'] == 0 and skip.scheduler.last_epoch == 0
        amp_skip = 'passed_scheduler_did_not_advance'
    result = {'utc': t.shared.utc(), 'status': 'passed_disposable_checks', 'device': str(device),
              'scientific_training': False, 'test_inference': False,
              'image_shape_RGB_modes_hash_corruption_duplicate_checks': True,
              'encoder_head_gradients_parameter_update': True, 'pixels_only_metadata_invariance': True,
              'registered_transform_exact_parity': True, 'short_tail_retained': 17,
              'interrupted_resume_exact_tensors_optimizer_scheduler_scaler_RNG_BN_cursor': True,
              'corrupt_newest_fallback': True, 'selection_tie_rules': True, 'independent_verifier_rejects_corruption': True, 'AMP_skip': amp_skip,
              'resume_absolute_tolerance': 0.0, 'environment': t.environment()}
    atomic_json(output / 'fixture_result.json', result)
    print(json.dumps(result), flush=True)
    return result


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--config', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--device', choices=['cpu', 'cuda'], default='cpu')
    fixture(p.parse_args())
