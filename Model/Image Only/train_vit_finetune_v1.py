"""Accuracy-first, end-to-end, pixel-only ViT. One optimizer boundary is resumable."""
import argparse
import datetime as dt
import hashlib
import io
import json
import math
import os
import random
import signal
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image, ImageFile
import torch
import torch.distributed as dist
from torch import nn
from torch.nn import functional as F
from torch.nn.parallel import DistributedDataParallel
from torch.utils.data import DataLoader, Dataset, Subset
from torchvision import models, transforms as T
from torchvision.transforms import functional as TF

from frozen_image_pair_v1 import FIELDS, export_eval, require, sampled, save_json, torch_save
from packed_image_io_v3 import ArchiveStore, sha

STOP = False


def on_stop(*_):
    global STOP
    STOP = True


def read(p):
    return json.loads(Path(p).read_text())


def stamp():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def rank():
    return dist.get_rank() if dist.is_initialized() else 0


def size():
    return dist.get_world_size() if dist.is_initialized() else 1


def barrier():
    if dist.is_initialized():
        dist.barrier()


def reduce_(t):
    if dist.is_initialized():
        dist.all_reduce(t)
    return t


def seed_all(seed):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


def rng_state():
    name, keys, pos, flag, value = np.random.get_state()
    return [random.getstate(), [name, keys.tolist(), pos, flag, value],
            torch.random.get_rng_state(), torch.cuda.get_rng_state()]


def restore_rng(state):
    py, (name, keys, pos, flag, value), cpu, cuda = state
    random.setstate(py)
    np.random.set_state((name, np.array(keys, dtype=np.uint32), pos, flag, value))
    torch.random.set_rng_state(cpu)
    torch.cuda.set_rng_state(cuda)


class Images(Dataset):
    def __init__(self, frame, reader, cfg, epoch=None):
        self.rows = frame[FIELDS].to_dict('records')
        self.reader, self.cfg, self.epoch = reader, cfg, epoch

    def __len__(self):
        return len(self.rows)

    def __getitem__(self, i):
        row = self.rows[i]
        require(not ImageFile.LOAD_TRUNCATED_IMAGES, 'Strict decoding is required')
        with Image.open(io.BytesIO(self.reader.read(row))) as im:
            im.load()
            image = im.convert('RGB')
        if self.epoch is None:
            image = TF.center_crop(TF.resize(image, 256, T.InterpolationMode.BILINEAR,
                                             antialias=True), [224, 224])
        else:
            # Crop depends only on the registered seed, epoch and post ID, not workers/prefetch.
            h = hashlib.blake2b(f"{self.cfg['seed']}:{self.epoch}:{row['id']}".encode(),
                                digest_size=8).digest()
            g = torch.Generator().manual_seed(int.from_bytes(h, 'little'))
            width, height = image.size
            area = width * height
            for _ in range(10):
                scale, aspect = torch.rand(2, generator=g).tolist()
                scale = self.cfg['crop_scale'][0] + scale * (self.cfg['crop_scale'][1]-self.cfg['crop_scale'][0])
                ratio = math.exp(math.log(.75) + aspect * math.log((4/3)/.75))
                w, h = round(math.sqrt(area*scale*ratio)), round(math.sqrt(area*scale/ratio))
                if 0 < w <= width and 0 < h <= height:
                    top = int(torch.randint(height-h+1, (1,), generator=g).item())
                    left = int(torch.randint(width-w+1, (1,), generator=g).item())
                    break
            else:
                w = min(width, round(height*4/3))
                h = min(height, round(width/.75))
                top, left = (height-h)//2, (width-w)//2
            image = TF.resized_crop(image, top, left, h, w, [224, 224],
                                    T.InterpolationMode.BILINEAR, antialias=True)
        return TF.pil_to_tensor(image), row['id'], int(row['6_way_label'])


def loader(frame, reader, cfg, positions=None, epoch=None, batch=None, workers=None):
    data = Images(frame, reader, cfg, epoch)
    if positions is not None:
        data = Subset(data, positions)
    if batch is None:
        batch = cfg['microbatch_per_device'] if epoch is not None else cfg['eval_batch']
    if workers is None:
        workers = cfg['workers_total'] // (size() if epoch is not None else 1)
    # The dedicated generator prevents iterator construction from changing the model RNG.
    return DataLoader(data, batch_size=batch, num_workers=workers, pin_memory=True,
                      generator=torch.Generator().manual_seed(cfg['seed'] + (epoch or 0)))


def network(device, cfg, pretrained=False, variant=None):
    if variant is None:
        enum = models.ViT_B_16_Weights.IMAGENET1K_V1
        m = models.vit_b_16(weights=None)
        if pretrained:
            path = Path(torch.hub.get_dir()) / 'checkpoints' / enum.url.rsplit('/', 1)[-1]
            require(sha(path) == cfg['weight_sha256'], 'Pretrained weights failed full SHA-256')
            m.load_state_dict(torch.load(path, map_location='cpu', weights_only=True))
        m.heads = nn.Sequential(nn.Dropout(cfg['dropout']), nn.Linear(m.hidden_dim, 6))
    else:
        from safetensors.torch import load_file
        import timm
        m = timm.create_model(variant['implementation'].split('.',1)[1], pretrained=False)
        if pretrained:
            path = Path(torch.hub.get_dir())/'checkpoints'/f"{variant['sha256']}.safetensors"
            require(sha(path)==variant['sha256'], 'DeiT III checkpoint SHA differs')
            m.load_state_dict(load_file(str(path)), strict=True)
        m.head = nn.Sequential(nn.Dropout(cfg['dropout']), nn.Linear(m.num_features,6))
    return m.requires_grad_(True).to(device)


def pixels(x, device):
    require(tuple(x.shape[1:]) == (3, 224, 224) and x.dtype == torch.uint8, 'Wrong RGB pixel tensor')
    x = x.to(device, non_blocking=True, dtype=torch.float32).mul_(1/255)
    # Constants are created once on each device per process.
    if not hasattr(pixels, 'constants'):
        pixels.constants = (x.new_tensor([.485, .456, .406])[None, :, None, None],
                            x.new_tensor([.229, .224, .225])[None, :, None, None])
    mean, std = pixels.constants
    return x.sub_(mean).div_(std)


class Engine:
    def __init__(self, device, cfg, plan, initial):
        self.device, self.cfg, self.plan = device, cfg, plan
        seed_all(cfg['seed'])
        self.raw = network(device, cfg, initial, plan.get("variant"))
        self.model = (DistributedDataParallel(self.raw, device_ids=[device.index],
                                             gradient_as_bucket_view=True, broadcast_buffers=False)
                      if size() > 1 else self.raw)
        groups = {}
        for name, p in self.raw.named_parameters():
            lr = plan['lr'] * (cfg['head_lr_ratio'] if name.startswith(('heads.','head.')) else 1)
            decay = cfg['weight_decay'] if p.ndim > 1 else 0.0
            groups.setdefault((lr, decay), []).append(p)
        self.optim = torch.optim.AdamW([{'params': params, 'lr': lr, 'weight_decay': decay}
                                       for (lr, decay), params in groups.items()], fused=True)
        total = plan['epochs'] * math.ceil(plan['rows']/cfg['effective_batch'])
        warm = max(1, math.ceil(total*cfg['warmup_fraction']))

        def schedule(success):
            if success < warm:
                return (success + 1) / warm
            return .5 * (1 + math.cos(math.pi * min(1, (success-warm)/max(1, total-warm-1))))

        self.sched = torch.optim.lr_scheduler.LambdaLR(self.optim, schedule)
        self.scaler = torch.amp.GradScaler('cuda', init_scale=512)
        micro = cfg['microbatch_per_device']
        require(cfg['effective_batch'] % (micro*size()) == 0, 'Effective batch must divide evenly')
        require(micro >= 2, 'Final shard requires at least one real sample or dummy per rank')
        self.progress = dict(epoch=1, cursor=0, updates=0, skips=0, train_loss_sum=0., history=[],
                             best=None, last_accuracy_gain=0, max_accuracy=-1., paused=False,
                             stopped_early=False, segments_seconds=0.)
        self.probes = (
            {'encoder':self.raw.encoder.layers[0].mlp[0].weight,'head':self.raw.heads[1].weight}
            if plan.get('variant') is None else
            {'encoder':self.raw.blocks[0].mlp.fc1.weight,'head':self.raw.head[1].weight})

    def order(self, n, epoch):
        return np.random.default_rng(np.random.SeedSequence([self.cfg['seed'], epoch])).permutation(n)

    def split_order(self, order):
        # Round-robin unique coverage. A paired dummy only makes a rank enter the
        # final collective when one rank has zero real rows. Its loss weight is zero.
        return order[rank()::size()].tolist()

    def epoch_batches(self, frame, store, end=None):
        p = self.progress
        order = self.order(len(frame), p['epoch'])[p['cursor']:end]
        positions = self.split_order(order)
        if (len(positions) + self.cfg['microbatch_per_device'] - 1)//self.cfg['microbatch_per_device'] < math.ceil(math.ceil(len(order)/size())/self.cfg['microbatch_per_device']):
            positions.append(-1)
        # Index -1 refers to an existing train row; the boundary masks it out.
        data = loader(frame, store, self.cfg, positions, p['epoch'])
        def checked():
            for start, batch in zip(range(0, len(positions), data.batch_size), data, strict=True):
                indices = positions[start:start+data.batch_size]
                wanted = [data.dataset.dataset.rows[j] for j in indices]
                require(list(batch[1])==[row['id'] for row in wanted]
                        and batch[2].tolist()==[row['6_way_label'] for row in wanted],
                        'Runtime sampler coverage or labels differ from registered row order')
                yield batch
        return checked(), len(order)

    def boundary(self, batches, num_rows, smoke=False):
        p = self.progress
        batch = self.cfg['microbatch_per_device']
        local_real = (num_rows + size()-1-rank())//size()
        calls = math.ceil(math.ceil(num_rows/size())/batch)
        self.model.train()
        self.optim.zero_grad(set_to_none=True)
        total = torch.zeros((), device=self.device)
        seen = 0
        for i in range(calls):
            from contextlib import nullcontext
            x, _, y = next(batches)
            real = min(len(y), local_real-seen)
            seen += real
            ctx = self.model.no_sync() if size() > 1 and i+1 < calls else nullcontext()
            with ctx:
                with torch.autocast('cuda', dtype=torch.float16):
                    logits = self.model(pixels(x, self.device))
                require(logits.shape == (len(y), 6), 'Wrong logits shape')
                loss = F.cross_entropy(logits.float()[:real], y.to(self.device, non_blocking=True)[:real],
                                       reduction='sum')
                self.scaler.scale(loss * (size()/num_rows)).backward()
                total += loss.detach()
        require(seen == local_real, 'Distributed batch coverage differs')
        self.scaler.unscale_(self.optim)
        gradients = ({k: float(torch.linalg.vector_norm(v.grad).item()) for k,v in self.probes.items()}
                     if smoke else {})
        torch.nn.utils.clip_grad_norm_(self.raw.parameters(), self.cfg['gradient_clip'], foreach=True)
        self.scaler.step(self.optim)
        before = self.scaler.get_scale()
        self.scaler.update()
        if self.scaler.get_scale() >= before:
            self.sched.step()
            p['updates'] += 1
        else:
            p['skips'] += 1
        loss_sum = float(reduce_(total).item())
        require(math.isfinite(loss_sum), 'Nonfinite training loss')
        p['cursor'] += num_rows
        p['train_loss_sum'] += loss_sum
        return gradients, loss_sum/num_rows

    def save(self, path, contract):
        local = rng_state()
        gathered = [None]*size() if rank() == 0 else None
        if size() > 1:
            dist.gather_object(local, gathered, dst=0)
        else:
            gathered = [local]
        if rank() == 0:
            # Retain the prior complete pair through the two-file atomic promotion.
            receipt_path = path.with_suffix('.json')
            prior = path.with_stem(path.stem+'.prev')
            if path.exists() and receipt_path.exists() and path.stat().st_size == read(receipt_path)['bytes']:
                prior_link = prior.with_suffix('.link')
                prior_link.unlink(missing_ok=True)
                os.link(path, prior_link)
                prior_link.replace(prior)
                save_json(prior.with_suffix('.json'), read(receipt_path))
            torch_save(path, dict(contract=contract, model=self.raw.state_dict(),
                                  optimizer=self.optim.state_dict(), scheduler=self.sched.state_dict(),
                                  scaler=self.scaler.state_dict(), rng=gathered, progress=self.progress))
            receipt = dict(sha256=sha(path), bytes=path.stat().st_size, progress=self.progress, utc=stamp())
            save_json(path.with_suffix('.json'), receipt)
        barrier()

    def resume(self, path, contract):
        receipt = read(path.with_suffix('.json'))
        if sha(path) != receipt['sha256']:
            path = path.with_stem(path.stem+'.prev')
            receipt = read(path.with_suffix('.json'))
            require(sha(path) == receipt['sha256'], 'Both saved recovery generations failed their SHA')
        state = torch.load(path, map_location='cpu', weights_only=True)
        require(state['contract'] == contract and state['progress'] == receipt['progress'],
                'Recovery contract or saved cursor changed')
        self.raw.load_state_dict(state['model'], strict=True)
        self.optim.load_state_dict(state['optimizer'])
        self.sched.load_state_dict(state['scheduler'])
        self.scaler.load_state_dict(state['scaler'])
        self.progress = state['progress']
        require(len(state['rng']) == size(), 'Recovery world size differs')
        restore_rng(state['rng'][rank()])
        require(self.sched.last_epoch == self.progress['updates'], 'Successful-update schedule mismatch')


@torch.inference_mode()
def predict(model, frame, store, cfg, device, deadline=None, amp=True):
    model.eval()
    probabilities, losses, offset = [], [], 0
    for x, ids, labels in loader(frame, store, cfg):
        if deadline is not None and time.time() > deadline:
            raise TimeoutError('Evaluation exceeded the registered session work window')
        target = frame.iloc[offset:offset+len(ids)]
        require(list(ids) == target.id.tolist() and np.array_equal(labels, target['6_way_label']),
                'Evaluation IDs or labels changed')
        with torch.autocast('cuda', dtype=torch.float16, enabled=amp):
            z = model(pixels(x, device)).float()
        require(z.shape == (len(ids), 6) and bool(torch.isfinite(z).all()), 'Invalid evaluation logits')
        probabilities.append(z.softmax(1).cpu().numpy())
        losses.append(F.cross_entropy(z, labels.to(device), reduction='none').cpu().numpy())
        offset += len(ids)
    require(offset == len(frame), 'Evaluation coverage differs')
    return np.concatenate(probabilities), np.concatenate(losses)


def selection(row):
    m = row['validation']
    return m['accuracy'], m['macro_f1'], -m['loss'], -row['epoch']


def frames_from_buffer(buffer, subsets=('train', 'validation')):
    return {s: pd.read_csv(buffer/f'{s}.csv', dtype={'id': str}) for s in subsets}


def preflight(buffer, out, cfg, store, frames, device):
    folder = out/'preflight'
    if rank() == 0:
        folder.mkdir(exist_ok=True)
    barrier()
    plan = dict(lr=cfg['encoder_lr'], epochs=1,
                rows=(cfg['benchmark_updates']+cfg['benchmark_warmup'])*cfg['effective_batch'])
    train = sampled(frames['train'], plan['rows'], cfg['seed']+13)
    valid = sampled(frames['validation'], cfg['benchmark_validation_rows'], cfg['seed']+17)
    contract = {'plan': plan, 'world_size': size(), 'scope': 'engineering_only'}
    e = Engine(device, cfg, plan, initial=True)
    torch.cuda.reset_peak_memory_stats()
    before = {k:v.detach().clone() for k,v in e.probes.items()}
    batches, _ = e.epoch_batches(train, store)
    first, loss = e.boundary(batches, cfg['effective_batch'], smoke=True)
    require(e.progress['updates'] == 1 and all(math.isfinite(v) and v > 0 for v in first.values())
            and all(not torch.equal(before[k], v) for k,v in e.probes.items()),
            'Smoke did not update both encoder and head with finite nonzero gradients')
    # Save after bucket rebucketing/initialization has settled.
    for _ in range(3):
        e.boundary(batches, cfg['effective_batch'])
    before_resume_update = e.progress['updates']
    path = folder/'smoke_resume.pt'
    start = time.monotonic()
    e.save(path, contract)
    save_seconds = time.monotonic()-start
    val_smoke = sampled(valid, 48, cfg['seed'])
    if rank() == 0:
        eval_before = predict(e.raw, val_smoke, store, cfg, device)
    original_grad, original_loss = e.boundary(batches, cfg['effective_batch'], smoke=True)
    original_probes = {k:v.detach().clone() for k,v in e.probes.items()}
    if rank() == 0:
        expected = predict(e.raw, val_smoke, store, cfg, device, amp=False)
    e.resume(path, contract)
    if rank() == 0:
        for a,b in zip(eval_before, predict(e.raw, val_smoke, store, cfg, device)):
            np.testing.assert_allclose(a, b, rtol=0, atol=0)
    del batches
    batches, _ = e.epoch_batches(train, store)
    resumed_grad, resumed_loss = e.boundary(batches, cfg['effective_batch'], smoke=True)
    require(abs(resumed_loss - original_loss) <= 5e-5 and e.progress['updates'] == before_resume_update+1,
            'Resumed update diverged')
    for k,v in e.probes.items():
        torch.testing.assert_close(v, original_probes[k], atol=2e-6, rtol=1e-4)
        require(abs(resumed_grad[k]-original_grad[k]) < .002, 'Resumed gradient diverged')
    if rank() == 0:
        continued = predict(e.raw, val_smoke, store, cfg, device, amp=False)
        continuation_errors = [float(np.max(np.abs(a-b))) for a,b in zip(expected, continued)]
        for a,b,tol in zip(expected,continued,(5e-4, 2e-3)):
            np.testing.assert_allclose(a,b,rtol=0,atol=tol)
        print('smoke_passed_gradients_weights_reload_continuation', first, continuation_errors, flush=True)
    for _ in range(cfg['benchmark_warmup']-5):
        e.boundary(batches, cfg['effective_batch'])
    barrier()
    torch.cuda.synchronize()
    start = time.monotonic()
    for i in range(cfg['benchmark_updates']):
        e.boundary(batches, cfg['effective_batch'])
        if rank() == 0 and (i+1) % 40 == 0:
            print('benchmark_updates', i+1, 'seconds', round(time.monotonic()-start, 3), flush=True)
    torch.cuda.synchronize()
    barrier()
    seconds = time.monotonic()-start
    peak = torch.tensor(torch.cuda.max_memory_allocated(), device=device, dtype=torch.int64)
    if size() > 1:
        dist.all_reduce(peak, op=dist.ReduceOp.MAX)
    if rank() == 0:
        start = time.monotonic()
        predict(e.raw, valid, store, cfg, device)
        val_seconds = time.monotonic()-start
        save_json(folder/'timing.json', {
            'utc': stamp(), 'first_update_loss': loss, 'nonzero_gradients': first,
            'input_shape': [cfg['microbatch_per_device'], 3, 224, 224],
            'logit_shape': [cfg['microbatch_per_device'], 6], 'encoder_and_head_changed': True,
            'continuation_probe_tolerances': {'weight_atol': 2e-6, 'weight_rtol': 1e-4,
                                               'fp32_eval_probability_atol': 5e-4, 'fp32_eval_ce_atol': 2e-3,
                                               'train_loss_atol': 5e-5},
            'continuation_max_errors': {'fp32_eval_probability':continuation_errors[0],
                                        'fp32_eval_ce':continuation_errors[1],
                                        'train_loss':abs(resumed_loss-original_loss)},
            'validation_reload_exact': True, 'continuation_passed': True,
            'train_rows_per_second': cfg['benchmark_updates']*cfg['effective_batch']/seconds,
            'validation_rows_per_second': len(valid)/val_seconds,
            'benchmark_train_seconds': seconds, 'benchmark_validation_seconds': val_seconds,
            'benchmark_successful_updates_including_warmup': e.progress['updates'],
            'benchmark_skips': e.progress['skips'], 'peak_device_bytes': int(peak.item()),
            'checkpoint_seconds': save_seconds, 'checkpoint_bytes': path.stat().st_size,
            'trainable_parameters': sum(p.numel() for p in e.raw.parameters() if p.requires_grad),
            'device_count_used': size(), 'effective_batch': cfg['effective_batch'],
        })
        print('preflight_complete', (folder/'timing.json').read_text(), flush=True)
    barrier()


def train_trial(frames, store, cfg, device, trial, folder, registration, deadline):
    if rank() == 0:
        folder.mkdir(parents=True, exist_ok=True)
    barrier()
    if (folder/'complete.json').is_file():
        return read(folder/'complete.json')
    train, val = frames['train'], frames['validation']
    if trial['kind'] == 'pilot':
        train = sampled(train, cfg['pilot_rows'], cfg['seed'])
    require(len(train) == trial['rows'], 'Wrong registered training count')
    contract = {'trial': trial, 'config': cfg, 'registration_sha256': registration,
                'world_size': size()}
    path = folder/'resume.pt'
    e = Engine(device, cfg, trial, initial=not path.exists())
    if path.exists():
        e.resume(path, contract)
    p = e.progress
    torch.cuda.reset_peak_memory_stats()
    rolled = p['segments_seconds']
    started, last_save = time.monotonic(), time.monotonic()

    def persist():
        nonlocal last_save
        p['segments_seconds'] = rolled + time.monotonic()-started
        e.save(path, contract)
        if rank() == 0:
            save_json(folder/'history.json', p['history'])
            print('checkpoint', trial['id'], p['epoch'], p['cursor'], p['updates'], p['skips'], flush=True)
        last_save = time.monotonic()

    while p['epoch'] <= trial['epochs'] and not p['stopped_early']:
        p['paused'] = False
        if p['cursor'] < len(train):
            batches, _ = e.epoch_batches(train, store)
            while p['cursor'] < len(train):
                if rank() == 0:
                    stop = STOP or (time.time() >= deadline)
                    action = 2 if stop else int(time.monotonic()-last_save >= cfg['checkpoint_seconds']
                                or ((p['updates']+p['skips']) % cfg['checkpoint_attempts'] == 0
                                    and p['cursor'] > 0))
                else:
                    action = 0
                if size() > 1:
                    flag = torch.tensor(action, device=device)
                    dist.broadcast(flag, src=0)
                    action = int(flag.item())
                if action:
                    p['paused'] = action == 2
                    persist()
                    if action == 2:
                        return None
                check_variant = trial.get('variant') is not None and p['updates']==0 and p['skips']==0
                before = {k:v.detach().clone() for k,v in e.probes.items()} if check_variant else {}
                gradients, first_loss = e.boundary(
                    batches, min(cfg['effective_batch'], len(train)-p['cursor']), smoke=check_variant)
                if check_variant:
                    require(p['updates']==1 and all(math.isfinite(g) and g>0 for g in gradients.values())
                            and all(not torch.equal(before[k], e.probes[k]) for k in gradients),
                            'Optional DeiT candidate failed its initial update gate')
                    if rank()==0:
                        save_json(folder/'initial_update_receipt.json', {'first_loss':first_loss,
                            'nonzero_probe_gradients':gradients, 'encoder_and_head_changed':True})
            del batches
        result = None
        if rank() == 0:
            prefix = f"validation_epoch{p['epoch']}"
            print('validation_started', trial['id'], p['epoch'], flush=True)
            try:
                prob, ce = predict(e.raw, val, store, cfg, device, deadline)
            except TimeoutError:
                pass
            else:
                metrics = export_eval(folder, prefix, val, prob, ce)
                result = {'epoch':p['epoch'], 'validation':metrics,
                          'validation_predictions_sha256':sha(folder/f'{prefix}_predictions.csv'),
                          'train_loss':p['train_loss_sum']/len(train), 'updates':p['updates'],
                          'skips':p['skips'],
                          'class_recall':{k:v['recall'] for k,v in read(folder/f'{prefix}_classification_report.json').items()
                                          if isinstance(v, dict) and not k.endswith(' avg')}}
                if p['best'] is None or selection(result) > selection(p['best']):
                    weights = folder/f"best_epoch{p['epoch']}.pt"
                    torch_save(weights, e.raw.state_dict())
                    result.update(selected_weight=weights.name, weight_sha256=sha(weights))
                print('validation_complete', trial['id'], result, flush=True)
        if size() > 1:
            msg = [result]
            dist.broadcast_object_list(msg, src=0, device=device)
            result = msg[0]
        if result is None:
            p['paused'] = True
            persist()
            return None
        prior = p['best']
        if 'selected_weight' in result:
            p['best'] = result
        if result['validation']['accuracy'] > p['max_accuracy']:
            p['max_accuracy'] = result['validation']['accuracy']
            p['last_accuracy_gain'] = p['epoch']
        p['history'].append(result)
        p['stopped_early'] = (trial['kind']=='full' and p['epoch'] >= cfg['early_stop_min_epochs']
                              and p['epoch']-p['last_accuracy_gain'] >= cfg['early_stop_patience'])
        p['cursor'], p['epoch'], p['train_loss_sum'] = 0, p['epoch']+1, 0.
        persist()
        if rank() == 0 and prior and p['best'] != prior:
            (folder/prior['selected_weight']).unlink(missing_ok=True)
    require(p['updates']+p['skips'] == len(p['history'])*math.ceil(len(train)/cfg['effective_batch']),
            'Completed epoch boundaries do not reconcile')
    complete = {**p, 'trial':trial, 'trainable_parameters':sum(v.numel() for v in e.raw.parameters()),
                'device_peak_allocated_bytes_rank0':torch.cuda.max_memory_allocated(),
                'resume_sha256':sha(path) if rank()==0 else None}
    if rank() == 0:
        save_json(folder/'complete.json', complete)
        backup = path.with_stem(path.stem+'.prev')
        backup.unlink(missing_ok=True)
        backup.with_suffix('.json').unlink(missing_ok=True)
    barrier()
    return read(folder/'complete.json')


def run(args):
    torch.set_num_threads(1)
    device = torch.device('cuda', int(os.getenv('LOCAL_RANK', '0')))
    torch.cuda.set_device(device)
    if int(os.getenv('WORLD_SIZE', '1')) > 1:
        dist.init_process_group('nccl', timeout=dt.timedelta(minutes=90), device_id=device)
    signal.signal(signal.SIGTERM, on_stop)
    signal.signal(signal.SIGINT, on_stop)
    cfg = read(args.buffer/'config.json')
    host = read(args.buffer/'storage.json')
    # Parent staged and hashed the bytes. Local scratch is recognized as local by ArchiveStore.
    store = ArchiveStore(host['archive_cache'], host['local_index'], host['index_sha256'])
    frames = frames_from_buffer(args.buffer)
    if args.mode == 'preflight':
        preflight(args.buffer, args.out, cfg, store, frames, device)
    elif args.mode == 'train':
        train_registered(args.buffer, args.out, cfg, store, frames, device)
    elif args.mode == 'fixed-validation':
        fixed_validation(args.buffer, args.out, cfg, store, frames['validation'], device)
    elif args.mode == 'test':
        frozen_test(args.buffer, args.out, cfg, store, frames['train'], device)
    else:
        raise ValueError(args.mode)
    if dist.is_initialized():
        dist.destroy_process_group()


if __name__ == '__main__':
    # Driver definitions follow in the separate science control module, imported after
    # the engine is defined so it can be reused for readback on a fresh process.
    sys.modules['train_vit_finetune_v1'] = sys.modules[__name__]
    from vit_finetune_control_v1 import fixed_validation, frozen_test, train_registered
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=['preflight', 'train', 'fixed-validation', 'test'])
    parser.add_argument('buffer', type=Path)
    parser.add_argument('out', type=Path)
    run(parser.parse_args())
