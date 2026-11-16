"""Six-way BERT + ResNet-50 maximum-fusion engineering pilot.

CUDA training only. --smoke performs synthetic CPU implementation checks, never
research evaluation. Official split membership is audited by build_paired_pilot.
"""
import argparse
import hashlib
import json
import math
import os
import random
import shutil
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

os.environ.setdefault('TOKENIZERS_PARALLELISM', 'false')
os.environ.setdefault('CUBLAS_WORKSPACE_CONFIG', ':4096:8')
import numpy as np
import pandas as pd
from PIL import Image
import torch
from torch import nn
from torch.utils.data import Dataset, DataLoader
import torchvision
from torchvision import transforms as T
from torchvision.models import resnet50, ResNet50_Weights
from transformers import AutoModel, AutoTokenizer, BertConfig, BertModel
from transformers import get_linear_schedule_with_warmup
from train_official_text import metrics, export_eval, sha, Tee


def now():
    return datetime.now(timezone.utc).isoformat()


def save_json(path, value):
    # Session-local filesystem, not Drive FUSE; unique temporary names.
    path = Path(path)
    tmp = path.with_name(path.name + '.tmp.' + str(os.getpid()))
    with tmp.open('w') as f:
        json.dump(value, f, indent=2, allow_nan=False); f.write('\n')
        f.flush(); os.fsync(f.fileno())
    os.replace(tmp, path)


def image_transform(training):
    prefix = [T.RandomResizedCrop(224, scale=(.8, 1.), ratio=(.75, 4/3),
                    interpolation=T.InterpolationMode.BILINEAR, antialias=True)] if training else [
                    T.Resize(232, interpolation=T.InterpolationMode.BILINEAR, antialias=True), T.CenterCrop(224)]
    return T.Compose(prefix + [T.ToTensor(), T.Normalize([.485, .456, .406], [.229, .224, .225])])


class MaximumFusion(nn.Module):
    def __init__(self, text, image):
        super().__init__()
        self.text = text; self.image = image
        self.text_projection = nn.Sequential(nn.Linear(text.config.hidden_size, 512), nn.LayerNorm(512))
        self.image_projection = nn.Sequential(nn.Linear(2048, 512), nn.LayerNorm(512))
        self.classifier = nn.Sequential(nn.Linear(512, 256), nn.GELU(), nn.Dropout(.2), nn.Linear(256, 6))

    def forward(self, input_ids, attention_mask, images):
        text = self.text(input_ids=input_ids, attention_mask=attention_mask).last_hidden_state[:, 0]
        image = self.image(images)
        return self.classifier(torch.maximum(self.text_projection(text), self.image_projection(image)))


class Pairs(Dataset):
    def __init__(self, frame, root, tokenizer, cfg, training):
        self.frame = frame.reset_index(drop=True); self.root = root
        self.tokens = tokenizer(frame.clean_title.tolist(), truncation=True, max_length=cfg['max_length'], padding=False)
        self.transform = image_transform(training)

    def __len__(self):
        return len(self.frame)

    def __getitem__(self, i):
        row = self.frame.iloc[i]
        path = self.root / row.image_path
        if not path.resolve().is_relative_to(self.root.resolve()):
            raise ValueError('Image path escapes input root')
        with Image.open(path) as image:
            tensor = self.transform(image.convert('RGB'))
        return {**{k: self.tokens[k][i] for k in ['input_ids', 'attention_mask']},
                'images': tensor, 'labels': int(row['6_way_label'])}


class Collate:
    def __init__(self, tokenizer):
        self.tokenizer = tokenizer

    def __call__(self, rows):
        tokens = self.tokenizer.pad([{k: r[k] for k in ['input_ids', 'attention_mask']} for r in rows],
                                    padding=True, pad_to_multiple_of=8, return_tensors='pt')
        return {**tokens, 'images': torch.stack([r['images'] for r in rows]),
                'labels': torch.tensor([r['labels'] for r in rows])}


@torch.inference_mode()
def evaluate(model, loader):
    model.eval(); ys, ps, cs = [], [], []; loss = 0.
    for batch in loader:
        labels = batch.pop('labels').cuda()
        with torch.autocast('cuda', dtype=torch.float16):
            logits = model(**{k: v.cuda(non_blocking=True) for k, v in batch.items()})
            batch_loss = nn.functional.cross_entropy(logits, labels)
        probs = logits.float().softmax(-1)
        loss += float(batch_loss) * len(labels)
        ys.extend(labels.cpu().tolist()); ps.extend(probs.argmax(-1).cpu().tolist()); cs.extend(probs.max(-1).values.cpu().tolist())
    return metrics(ys, ps, loss/len(ys)), ys, ps, cs


def smoke(output):
    torch.set_num_threads(2); torch.manual_seed(42)
    image = resnet50(weights=None); image.fc = nn.Identity()
    text = BertModel(BertConfig(vocab_size=128, hidden_size=32, num_hidden_layers=1,
                               num_attention_heads=4, intermediate_size=64), add_pooling_layer=False)
    model = MaximumFusion(text, image)
    batch = {'input_ids': torch.randint(0, 128, (2, 8)), 'attention_mask': torch.ones(2, 8, dtype=torch.long),
             'images': torch.randn(2, 3, 224, 224)}
    logits = model(**batch); assert logits.shape == (2, 6)
    loss = nn.functional.cross_entropy(logits, torch.tensor([0, 5])); assert torch.isfinite(loss)
    loss.backward()
    gradients = {name: sum(float(p.grad.abs().sum()) for p in module.parameters() if p.grad is not None)
                 for name, module in [('text', model.text), ('image', model.image), ('classifier', model.classifier)]}
    assert all(v > 0 and math.isfinite(v) for v in gradients.values())
    model.eval()
    with torch.no_grad(): before = model(**batch)
    output.mkdir(parents=True, exist_ok=True)
    path = output / 'synthetic_checkpoint.pt'
    torch.save(model.state_dict(), path)
    model.load_state_dict(torch.load(path, weights_only=True))
    with torch.no_grad(): after = model(**batch)
    assert torch.equal(before, after); path.unlink()
    for mode in ['RGB', 'RGBA', 'P', 'L']:
        x = image_transform(False)(Image.new(mode, (260, 250)).convert('RGB'))
        assert x.shape == (3, 224, 224) and torch.isfinite(x).all()
    result = {'status': 'passed', 'kind': 'synthetic CPU implementation check; no pretrained model or research metrics',
              'checks': ['six logits', 'finite loss', 'nonzero gradients through BOTH encoders and head',
                         'checkpoint roundtrip identical', 'RGB/RGBA/palette/grayscale preprocessing'],
              'gradient_sums': gradients, 'torch': torch.__version__, 'torchvision': torchvision.__version__, 'utc': now()}
    save_json(output / 'smoke_result.json', result); print(json.dumps(result, indent=2))


def train(args):
    if not torch.cuda.is_available():
        raise RuntimeError('Cloud CUDA required; refusing local CPU training')
    cfg = json.loads(Path(args.config).read_text()); root = Path(args.input).resolve()
    manifest = root / 'pilot_manifest.csv'
    evidence = json.loads((root / 'dataset_evidence.json').read_text())
    assert sha(manifest) == evidence['pilot_manifest.csv_sha256']
    frame = pd.read_csv(manifest, dtype=str, keep_default_na=False)
    assert not frame.id.duplicated().any() and frame['6_way_label'].isin([str(i) for i in range(6)]).all()
    frames = {k: frame[frame.split.eq(k)].reset_index(drop=True) for k in ['train', 'validation', 'test']}
    for split, f in frames.items():
        assert len(f) == evidence['splits'][split]['pilot_rows']
        assert set(f['6_way_label']) == set(map(str, range(6)))
    out = Path(args.output); out.mkdir(parents=True, exist_ok=args.resume)
    if args.resume:
        assert json.loads((out/'protocol.json').read_text()) == cfg
        assert json.loads((out/'dataset_evidence.json').read_text()) == evidence
        if (out/'result.json').exists():
            print('Completed pilot preserved:', (out/'result.json').read_text()); return
    save_json(out/'protocol.json', cfg); save_json(out/'dataset_evidence.json', evidence)
    shutil.copy2(__file__, out/('source_resume.py' if args.resume else 'source.py'))
    sys.stdout = Tee(sys.stdout, out/'training.log'); sys.stderr = Tee(sys.stderr, out/'stderr.log')
    save_json(out/'environment.json', {'utc': now(), 'python': sys.version, 'torch': torch.__version__,
        'torchvision': torchvision.__version__, 'gpu': torch.cuda.get_device_name(0), 'source_sha256': sha(__file__),
        'config_sha256': sha(args.config), 'manifest_sha256': sha(manifest)})
    random.seed(cfg['seed']); np.random.seed(cfg['seed']); torch.manual_seed(cfg['seed']); torch.cuda.manual_seed_all(cfg['seed'])
    torch.backends.cudnn.benchmark = False; torch.backends.cuda.matmul.allow_tf32 = False
    torch.use_deterministic_algorithms(True, warn_only=True)
    tokenizer = AutoTokenizer.from_pretrained(cfg['bert_checkpoint'], revision=cfg['bert_revision'])
    text = AutoModel.from_pretrained(cfg['bert_checkpoint'], revision=cfg['bert_revision'], add_pooling_layer=False,
                                     attn_implementation='sdpa')
    image = resnet50(weights=ResNet50_Weights.IMAGENET1K_V2); image.fc = nn.Identity()
    model = MaximumFusion(text, image).cuda(); tokenizer.save_pretrained(out/'tokenizer')
    groups = {}
    for name, p in model.named_parameters():
        family = 'text' if name.startswith('text.') else 'image' if name.startswith('image.') else 'head'
        lr = cfg[{'text': 'bert_lr', 'image': 'image_lr', 'head': 'head_lr'}[family]]
        decay = 0. if p.ndim <= 1 else cfg['image_decay' if family == 'image' else 'bert_head_decay']
        groups.setdefault((lr, decay), []).append(p)
    optimizer = torch.optim.AdamW([{'params': p, 'lr': lr, 'weight_decay': wd} for (lr, wd), p in groups.items()])
    generator = torch.Generator().manual_seed(cfg['seed'])
    loaders = {k: DataLoader(Pairs(f, root, tokenizer, cfg, k == 'train'),
             batch_size=cfg['micro_batch'] if k == 'train' else cfg['eval_batch'], shuffle=k == 'train',
             generator=generator if k == 'train' else None, collate_fn=Collate(tokenizer), num_workers=0, pin_memory=True)
             for k, f in frames.items()}
    updates_per_epoch = math.ceil(len(loaders['train']) / cfg['accumulation'])
    budget = updates_per_epoch * cfg['epochs']
    scheduler = get_linear_schedule_with_warmup(optimizer, math.ceil(budget * cfg['warmup_fraction']), budget)
    scaler = torch.amp.GradScaler('cuda'); start_epoch = 1; history = []; best = None; updates = 0; skips = 0
    if args.resume:
        recovery = torch.load(out/'resume_checkpoint.pt', map_location='cuda', weights_only=False)
        for obj, key in [(model,'model'), (optimizer,'optimizer'), (scheduler,'scheduler'), (scaler,'scaler')]: obj.load_state_dict(recovery[key])
        start_epoch = recovery['epoch'] + 1; history = recovery['history']; best = recovery['best']
        updates = recovery['updates']; skips = recovery['skips']
        generator.set_state(recovery['generator'].cpu()); random.setstate(recovery['python_rng']); np.random.set_state(recovery['numpy_rng'])
        torch.set_rng_state(recovery['torch_rng'].cpu()); torch.cuda.set_rng_state_all([s.cpu() for s in recovery['cuda_rng']])
    started = time.monotonic()
    for epoch in range(start_epoch, cfg['epochs'] + 1):
        model.train(); total = 0.; seen = 0; optimizer.zero_grad(set_to_none=True)
        for step, batch in enumerate(loaders['train'], 1):
            labels = batch.pop('labels').cuda()
            group_start = ((step-1)//cfg['accumulation']) * cfg['accumulation']
            # Exact sample weighting also for an incomplete final accumulated batch.
            group_n = min(cfg['micro_batch']*cfg['accumulation'], len(frames['train'])-group_start*cfg['micro_batch'])
            with torch.autocast('cuda', dtype=torch.float16):
                logits = model(**{k: v.cuda(non_blocking=True) for k,v in batch.items()})
                loss = nn.functional.cross_entropy(logits, labels)
            if not torch.isfinite(loss): raise RuntimeError('Nonfinite loss; no sample exclusion')
            scaler.scale(loss * len(labels) / group_n).backward()
            total += float(loss.detach()) * len(labels); seen += len(labels)
            if step % cfg['accumulation'] == 0 or step == len(loaders['train']):
                scaler.unscale_(optimizer); nn.utils.clip_grad_norm_(model.parameters(), 1.)
                scale = scaler.get_scale(); scaler.step(optimizer); scaler.update()
                if scaler.get_scale() >= scale: scheduler.step(); updates += 1
                else: skips += 1
                optimizer.zero_grad(set_to_none=True)
            if step % 25 == 0 or step == len(loaders['train']):
                save_json(out/'status.json', {'state':'training', 'epoch':epoch, 'batch':step,
                    'batches_per_epoch':len(loaders['train']), 'samples_seen':seen, 'optimizer_updates':updates, 'utc':now()})
                print('TRAIN',epoch,step,len(loaders['train']),'loss',total/seen,flush=True)
        val = evaluate(model, loaders['validation'])
        history.append({'epoch':epoch,'train_loss':total/seen,'validation':val[0],'updates':updates,'skips':skips})
        if best is None or (val[0]['macro_f1'], -val[0]['loss']) > (best['metrics']['macro_f1'], -best['metrics']['loss']):
            best = {'epoch':epoch,'metrics':val[0]}
            torch.save(model.state_dict(), out/'best_weights.pt.tmp'); os.replace(out/'best_weights.pt.tmp', out/'best_weights.pt')
            save_json(out/'best_checkpoint.json', best); export_eval(out,'validation',frames['validation'],val)
        save_json(out/'history.json',history)
        state = {'epoch':epoch,'model':model.state_dict(),'optimizer':optimizer.state_dict(),'scheduler':scheduler.state_dict(),
                 'scaler':scaler.state_dict(),'history':history,'best':best,'updates':updates,'skips':skips,
                 'generator':generator.get_state(),'python_rng':random.getstate(),'numpy_rng':np.random.get_state(),
                 'torch_rng':torch.get_rng_state(),'cuda_rng':torch.cuda.get_rng_state_all()}
        torch.save(state,out/'resume_checkpoint.pt.tmp'); os.replace(out/'resume_checkpoint.pt.tmp',out/'resume_checkpoint.pt')
        save_json(out/'recovery_checkpoint.json',{'epoch':epoch,'epoch_finished':True,'utc':now(),'checkpoint_bytes':(out/'resume_checkpoint.pt').stat().st_size})
        print('VALIDATION',epoch,json.dumps(val[0]),flush=True)
    model.load_state_dict(torch.load(out/'best_weights.pt',map_location='cuda',weights_only=True))
    test = evaluate(model,loaders['test']); export_eval(out,'test',frames['test'],test)
    result = {'model':'BERT-base + ResNet-50 maximum fusion','protocol_id':cfg['protocol_id'],'pilot':True,
        'seed':cfg['seed'],'selected_epoch':best['epoch'],'validation':best['metrics'],'test':test[0],
        'epochs_completed':len(history),'optimizer_updates':updates,'skipped_updates':skips,'elapsed_seconds_this_session':time.monotonic()-started,
        'peak_gpu_allocated_bytes':torch.cuda.max_memory_allocated(),'completed_utc':now(),
        'limitation':'2600-row engineering pilot; not comparable to the official full-cohort paper benchmark'}
    save_json(out/'result.json',result); save_json(out/'status.json',{'state':'complete','utc':now(),'result':result})
    print('FINAL PILOT RESULT',json.dumps(result),flush=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('--config'); p.add_argument('--input'); p.add_argument('--output',required=True)
    p.add_argument('--resume',action='store_true'); p.add_argument('--smoke',action='store_true'); args = p.parse_args()
    if args.smoke: smoke(Path(args.output))
    else:
        try: train(args)
        except Exception:
            import traceback
            out=Path(args.output); out.mkdir(parents=True,exist_ok=True)
            save_json(out/'status.json',{'state':'failed','utc':now(),'reason':traceback.format_exc()}); raise
