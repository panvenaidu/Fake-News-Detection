"""Disposable CUDA/AMP recovery regression, never a faculty-data experiment.

Uses the production Engine/MaximumFusion, a tiny random BERT and a random full
ResNet50. Requires CUDA. Saves only an engineering receipt; fixture checkpoints
are temporary. No official examples, model downloads or test inference.
"""
import argparse
import copy
import json
import random
import tempfile
from pathlib import Path

import numpy as np
import torch
from torch import nn
from torch.utils.data import DataLoader, Dataset, Subset
from torchvision.models import resnet50
from transformers import BertConfig, BertModel, get_linear_schedule_with_warmup

from train_usable_multimodal_v2 import Engine, MaximumFusion, evaluate, utc
from multimodal_recovery_v1 import atomic_json, order, sha


class Fixture(Dataset):
    def __len__(self):
        return 13

    def __getitem__(self, index):
        generator = torch.Generator().manual_seed(700 + index)
        return {
            'input_ids': torch.randint(0, 64, (8,), generator=generator),
            'attention_mask': torch.ones(8, dtype=torch.long),
            'images': torch.rand(3, 224, 224, generator=generator),
            'labels': torch.tensor(index % 6),
            'id': 'synthetic-' + str(index),
        }


def collate(rows):
    return {**{key: torch.stack([row[key] for row in rows])
               for key in ['input_ids', 'attention_mask', 'images', 'labels']},
            'ids': [row['id'] for row in rows]}


class OverflowOnce(torch.amp.GradScaler):
    """Real CUDA GradScaler with one reproducible infinite-gradient injection."""
    def __init__(self):
        super().__init__('cuda', init_scale=128.)
        self.boundaries = 0

    def unscale_(self, optimizer):
        self.boundaries += 1
        if self.boundaries == 2:
            # Loss stays finite; real GradScaler must detect/skip this update.
            parameter = next(p for group in optimizer.param_groups
                             for p in group['params'] if p.grad is not None)
            parameter.grad.view(-1)[0] = float('inf')
        return super().unscale_(optimizer)

    def state_dict(self):
        return {**super().state_dict(), 'fixture_boundaries': self.boundaries}

    def load_state_dict(self, state):
        state = dict(state)
        self.boundaries = state.pop('fixture_boundaries')
        super().load_state_dict(state)


def loader(epoch, cursor=0, validation=False):
    fixture = Fixture()
    rows = fixture if validation else Subset(fixture, order(42, epoch, len(fixture))[cursor:].tolist())
    # Dedicated loader RNG must not consume the model's restored RNG.
    return DataLoader(rows, batch_size=2 if not validation else 4,
                      num_workers=0, collate_fn=collate,
                      generator=torch.Generator().manual_seed(991 + cursor))


def make(output, config):
    random.seed(42)
    np.random.seed(42)
    torch.manual_seed(42)
    torch.cuda.manual_seed_all(42)
    text = BertModel(BertConfig(vocab_size=64, hidden_size=32,
                     num_hidden_layers=1, num_attention_heads=4,
                     intermediate_size=48, attn_implementation='eager'),
                     add_pooling_layer=False)
    image = resnet50(weights=None)
    image.fc = nn.Identity()
    model = MaximumFusion(text, image).cuda()
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-4)
    scheduler = get_linear_schedule_with_warmup(optimizer, 1, 12)
    return Engine(model, optimizer, scheduler, OverflowOnce(), config, output,
                  torch.device('cuda'), {'fixture': 'CUDA-ENGINE-RECOVERY-v1'})


def simulate(engine, interrupted):
    snapshots = []
    while engine.state['epoch'] <= 2:
        epoch = engine.state['epoch']
        if interrupted:
            # Two interruptions per epoch, then finish the remaining suffix.
            for _ in range(2):
                if engine.state['cursor'] >= len(Fixture()):
                    break
                engine.train_epoch(loader(epoch, engine.state['cursor']), len(Fixture()),
                                   on_boundary=lambda *_: True)
                snapshots.append((epoch, engine.state['cursor'],
                                  engine.state['updates'], engine.state['skips']))
                # Consume all RNGs before restore to catch missing RNG recovery.
                torch.rand(19, device='cuda')
                torch.rand(7)
                np.random.rand(3)
                random.random()
                engine.resume()
        if engine.state['phase'] == 'train':
            assert engine.train_epoch(loader(epoch, engine.state['cursor']), len(Fixture()))
        # Repeated validation-pending restore must not retrain the epoch.
        if interrupted:
            engine.save()
            engine.resume()
        metrics, predictions = evaluate(engine.model, loader(epoch, validation=True),
                                        torch.device('cuda'))
        assert predictions.id.tolist() == ['synthetic-' + str(i) for i in range(13)]
        assert predictions.shape[0] == 13
        engine.finish_validation(metrics, {'epoch': epoch, 'metrics': metrics})
    return snapshots


def compare(left, right, path='state', maxima=None):
    if maxima is None:
        maxima = {}
    if torch.is_tensor(left):
        assert torch.is_tensor(right) and left.shape == right.shape, path
        if left.is_floating_point():
            torch.testing.assert_close(left, right, rtol=1e-4, atol=1e-5,
                                       equal_nan=False, msg=path)
            if left.numel():
                maxima[path] = float((left.double() - right.double()).abs().max())
        else:
            assert torch.equal(left, right), path
    elif isinstance(left, dict):
        assert set(left) == set(right), path
        for key in left:
            compare(left[key], right[key], path + '/' + str(key), maxima)
    elif isinstance(left, (list, tuple)):
        assert len(left) == len(right), path
        for index, (a, b) in enumerate(zip(left, right)):
            compare(a, b, path + '/' + str(index), maxima)
    elif isinstance(left, float):
        assert abs(left - right) <= 1e-5 + 1e-4 * abs(left), path
    else:
        assert left == right, path
    return maxima


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if not torch.cuda.is_available():
        raise SystemExit('CUDA required; no local CPU substitute or research training was run')
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.deterministic = True
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    torch.use_deterministic_algorithms(True, warn_only=True)
    config = json.loads(args.config.read_text())
    config.update(micro_batch=2, accumulation=3, workers=0,
                  checkpoint_updates=100, checkpoint_seconds=99999)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='cuda-recovery-', dir=args.output.parent) as temporary:
        base = Path(temporary)
        direct = make(base / 'direct', config)
        parameter_names = ['text.embeddings.word_embeddings.weight',
                           'image.conv1.weight', 'classifier.0.weight']
        before = {name: direct.model.state_dict()[name].detach().cpu().clone()
                  for name in parameter_names}
        simulate(direct, False)
        branch_changes = {
            name: float((direct.model.state_dict()[name].detach().cpu() - initial).abs().max())
            for name, initial in before.items()
        }
        assert all(delta > 0 for delta in branch_changes.values()), 'An encoder/head received no effective updates'
        # Keep only CPU state between runs, avoiding two full models/optimizers on GPU.
        final_direct = copy.deepcopy({
            'model': {k: v.cpu() for k, v in direct.model.state_dict().items()},
            'optimizer': direct.optimizer.state_dict(),
            'scheduler': direct.scheduler.state_dict(),
            'scaler': direct.scaler.state_dict(),
            'history': direct.state['history'],
        })
        def to_cpu(value):
            if torch.is_tensor(value):
                return value.cpu()
            if isinstance(value, dict):
                return {k: to_cpu(v) for k, v in value.items()}
            if isinstance(value, list):
                return [to_cpu(v) for v in value]
            return value
        final_direct = to_cpu(final_direct)
        del direct
        torch.cuda.empty_cache()
        resumed = make(base / 'resumed', config)
        interruptions = simulate(resumed, True)
        final_resumed = to_cpu({
            'model': resumed.model.state_dict(), 'optimizer': resumed.optimizer.state_dict(),
            'scheduler': resumed.scheduler.state_dict(), 'scaler': resumed.scaler.state_dict(),
            'history': resumed.state['history'],
        })
        maxima = compare(final_direct, final_resumed)
        assert resumed.state['updates'] == 5 and resumed.state['skips'] == 1
        assert resumed.scheduler.last_epoch == 5 and resumed.state['epoch'] == 3
        assert len(list((base / 'resumed/recovery').glob('*.pt'))) == 2
        receipt = {
            'utc': utc(), 'status': 'passed_cuda_engineering_fixture',
            'torch': torch.__version__, 'cuda': torch.version.cuda,
            'device': torch.cuda.get_device_name(0), 'allocated_devices': torch.cuda.device_count(),
            'source_sha256': sha(__file__),
            'trainer_sha256': sha(Path(__file__).with_name('train_usable_multimodal_v2.py')),
            'recovery_sha256': sha(Path(__file__).with_name('multimodal_recovery_v1.py')),
            'fixture': 'Random tiny BERT + full random ResNet50, 13 synthetic examples, two epochs',
            'interruptions': interruptions, 'successful_updates': 5, 'actual_amp_skips': 1,
            'scheduler_updates': 5, 'tolerance': {'rtol': 1e-4, 'atol': 1e-5},
            'maximum_state_absolute_difference': max(maxima.values(), default=0.),
            'encoder_and_head_max_parameter_changes': branch_changes,
            'checks': ['Production Engine with real CUDA fp16 GradScaler',
                       'Repeated mid-epoch and validation-pending restoration',
                       'Next-epoch model, BatchNorm, optimizer, scheduler, scaler and history agreement',
                       'Injected infinite gradient skips exactly one optimizer/scheduler update',
                       'Two committed recovery generations'],
            'limitations': ['Engineering fixture, no official scientific scores',
                            'Not full pretrained BERT throughput or full image I/O preflight',
                            'Not cross-device bitwise reproducibility',
                            'Not durable cloud export verification'],
        }
        atomic_json(args.output, receipt)
        print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    main()
