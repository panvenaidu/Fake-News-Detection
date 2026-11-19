"""Synthetic interrupted-resume check of the new experiment's actual engine."""
import copy
import json
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import torch
from torch import nn
from torch.utils.data import DataLoader, Dataset, Subset
from transformers import get_linear_schedule_with_warmup

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'model/text_plus_image/bert_deit3'))
from train import Engine, MaximumFusion, better, evaluate, order


class Text(nn.Module):
    def __init__(self):
        super().__init__(); self.config = SimpleNamespace(hidden_size=8); self.emb = nn.Embedding(32, 8)
    def forward(self, input_ids, attention_mask):
        return SimpleNamespace(last_hidden_state=self.emb(input_ids))


class Image(nn.Module):
    def __init__(self):
        super().__init__(); self.num_features = 8; self.linear = nn.Linear(3, 8)
    def forward(self, images):
        return self.linear(images)


class Toy(Dataset):
    def __len__(self): return 13
    def __getitem__(self, i):
        g = torch.Generator().manual_seed(i + 1)
        return {'input_ids': torch.randint(32, (4,), generator=g), 'attention_mask': torch.ones(4, dtype=torch.long),
                'images': torch.randn(3, generator=g), 'labels': torch.tensor(i % 6), 'id': str(i)}


def collate(rows):
    return {**{k: torch.stack([r[k] for r in rows]) for k in ('input_ids', 'attention_mask', 'images', 'labels')},
            'ids': [r['id'] for r in rows]}


def loader(cursor=0):
    return DataLoader(Subset(Toy(), order(42, 1, 13)[cursor:].tolist()), batch_size=2, collate_fn=collate,
                      generator=torch.Generator().manual_seed(8))


def make(folder, cfg):
    torch.manual_seed(42); np.random.seed(42)
    model = MaximumFusion(Text(), Image()); opt = torch.optim.AdamW(model.parameters(), lr=.001)
    scheduler = get_linear_schedule_with_warmup(opt, 1, 3)
    return Engine(model, opt, scheduler, torch.amp.GradScaler('cpu', enabled=False), cfg, folder,
                  torch.device('cpu'), {'fixture': 'synthetic'})


def same(a, b):
    if torch.is_tensor(a): return torch.equal(a, b)
    if isinstance(a, dict): return a.keys() == b.keys() and all(same(a[k], b[k]) for k in a)
    if isinstance(a, (list, tuple)): return len(a) == len(b) and all(same(x, y) for x, y in zip(a, b))
    return a == b


def main():
    torch.set_num_threads(2)
    cfg = json.loads((ROOT / 'configs/text_plus_image/bert_deit3/experiment.json').read_text())
    cfg.update(micro_batch=2, accumulation=3, checkpoint_updates=100, checkpoint_seconds=9999)
    with tempfile.TemporaryDirectory() as tmp:
        direct = make(Path(tmp)/'direct', cfg); direct.train_epoch(loader(), 13)
        resumed = make(Path(tmp)/'resumed', cfg)
        assert not resumed.train_epoch(loader(), 13, on_boundary=lambda e, ids, n: n == 1)
        assert resumed.state['cursor'] == 6
        resumed.resume(); assert resumed.train_epoch(loader(resumed.state['cursor']), 13)
        for a, b in ((direct.model, resumed.model), (direct.optimizer, resumed.optimizer),
                     (direct.scheduler, resumed.scheduler), (direct.scaler, resumed.scaler)):
            assert same(a.state_dict(), b.state_dict())
        assert direct.state == resumed.state
        dl = DataLoader(Toy(), batch_size=4, collate_fn=collate)
        values, predictions = evaluate(resumed.model, dl, torch.device('cpu'))
        assert len(predictions) == 13 and predictions.id.is_unique
        resumed.finish_validation(values, {'epoch': 1, 'metrics': values})
        resumed.resume(); assert resumed.state['best']['epoch'] == 1
        best = {'metrics': {'accuracy': .8, 'macro_f1': .7, 'loss': .4}}
        assert better({'accuracy': .80001, 'macro_f1': .1, 'loss': 1.}, best)
        assert better({'accuracy': .8, 'macro_f1': .71, 'loss': 1.}, best)
        assert better({'accuracy': .8, 'macro_f1': .7, 'loss': .39}, best)
        assert not better({'accuracy': .8, 'macro_f1': .7, 'loss': .4}, best)
    print(json.dumps({'status': 'passed', 'scope': 'synthetic CPU only', 'rows': 13,
                      'checks': ['interrupted continuation', 'model optimizer scheduler scaler equality',
                                 'validation and selected checkpoint reload', 'accuracy-first selection and ties']}))


if __name__ == '__main__': main()
