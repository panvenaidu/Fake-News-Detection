"""Matched, pixel-only linear probes. See the registered JSON and Kaggle builder."""
import io
import json
import os
import platform
import shutil
import time
from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image
import torch
import torchvision as tv
from torch import nn
from torch.nn import functional as F
from torch.utils.data import Dataset, DataLoader
from packed_image_io_v3 import ArchiveStore, sha
from usable_cohort_v2 import load_input

ARMS = ('vit', 'resnet50')
LABELS = ['True', 'Satire/Parody', 'Misleading Content', 'Imposter Content',
          'False Connection', 'Manipulated Content']
FIELDS = ['id', 'split', '6_way_label', 'source_shard', 'bytes', 'image_sha256']


def require(condition, message):
    if not condition:
        raise ValueError(message)


def save_json(path, payload):
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(payload, indent=2, allow_nan=False) + '\n')
    temporary.replace(path)


def torch_save(path, value):
    temporary = path.with_suffix('.tmp')
    torch.save(value, temporary)
    temporary.replace(path)


def load_verified(mount, cfg):
    def unique(pattern):
        found = list(mount.glob(pattern))
        require(len(found) == 1, f'Expected exactly one mounted input for {pattern}, found {len(found)}')
        return found[0]
    manifest = unique('**/urop-faculty-usable-packed-input-v3/data/official_paired_v2/paired_manifest.csv')
    root = manifest.parents[2]
    coverage = unique('**/urop_mm_packed_gate_20261026/packed_runtime_coverage.json')
    index = coverage.with_name('packed_image_index.sqlite')
    for path, key in [(manifest, 'manifest_sha256'), (coverage, 'coverage_sha256'), (index, 'index_sha256')]:
        require(sha(path) == cfg[key], f'Unrecognized {path.name}')
    gate = json.loads(coverage.read_text())
    require(gate['dataset_version'] == cfg['dataset_version'] and gate['runtime_image_bytes_verified'] and gate['image_gate_passed']
            and gate['input_layout'] == 'kaggle-packed-bin'
            and gate['cohort_id'] == cfg['cohort'] and gate['split_counts'] == cfg['counts']
            and gate['packed_index_sha256'] == cfg['index_sha256']
            and gate['manifest_sha256'] == cfg['manifest_sha256'], 'Invalid packed quality-check receipt')
    expected, reg = load_input(root)
    paired = pd.read_csv(manifest, usecols=FIELDS, dtype={'id': str}, keep_default_na=False)
    require(paired.id.is_unique and set(paired.id) == set(expected), 'Wrong paired cohort')
    canonical = pd.DataFrame.from_records(list(expected.values()), columns=FIELDS[:3])
    paired = paired.set_index('id').loc[canonical.id].reset_index()
    for key in FIELDS[:3]:
        require(np.array_equal(paired[key], canonical[key]), f'Mismatch in {key}')
    frames = {split: paired.loc[paired.split.eq(split), FIELDS].reset_index(drop=True)
              for split in cfg['counts']}
    for split, frame in frames.items():
        require(len(frame) == cfg['counts'][split] and set(frame['6_way_label']) == set(range(6)),
                f'Wrong approved counts/classes for {split}')
    return root, index, frames, reg


def stage(root, index, digest):
    # The verified loader stages exact archive bytes in /tmp and caches SQLite separately.
    began = time.monotonic()
    store = ArchiveStore(root, index, digest)
    return store, time.monotonic() - began


def sampled(frame, n, seed):
    require(6 <= n <= len(frame), 'Invalid stratified sample size')
    if n == len(frame):
        return frame
    buckets = [np.flatnonzero(frame['6_way_label'].to_numpy() == label) for label in range(6)]
    counts = np.asarray([len(x) for x in buckets])
    require(np.all(counts > 0), 'Missing class in source split')
    weights = (n - 6) * (counts - 1) / (len(frame) - 6)
    quotas = np.floor(weights).astype(int) + 1
    for label in np.argsort(-(weights - np.floor(weights)), kind='stable'):
        if quotas.sum() == n:
            break
        if quotas[label] < counts[label]:
            quotas[label] += 1
    require(quotas.sum() == n and (quotas <= counts).all(), 'Stratified allocation failed')
    rng = np.random.default_rng(seed)
    positions = np.sort(np.concatenate([rng.permutation(group)[:k] for group, k in zip(buckets, quotas)]))
    return frame.iloc[positions].reset_index(drop=True)


def transform(cfg):
    t = tv.transforms
    return t.Compose([t.Resize(cfg['resize_shorter'], interpolation=t.InterpolationMode.BILINEAR,
                               antialias=cfg['antialias']), t.CenterCrop(cfg['crop']), t.ToTensor(),
                      t.Normalize(cfg['mean'], cfg['std'])])


class Pixels(Dataset):
    def __init__(self, frame, store, cfg):
        self.rows = frame.to_dict('records')
        self.store = store
        self.apply = transform(cfg)

    def __len__(self):
        return len(self.rows)

    def __getitem__(self, i):
        row = self.rows[i]
        with Image.open(io.BytesIO(self.store.read(row))) as image:
            image.load()
            pixels = self.apply(image.convert('RGB'))
        return pixels, row['id'], row['6_way_label']


def load_pixels(frame, store, cfg, device):
    return DataLoader(Pixels(frame, store, cfg), batch_size=cfg['feature_batch'], shuffle=False,
                      num_workers=cfg['workers'], pin_memory=device.type == 'cuda')


def backbone(arm, device):
    if arm == 'vit':
        enum = tv.models.ViT_B_16_Weights.IMAGENET1K_V1
        model = tv.models.vit_b_16(weights=enum)
        dim = model.hidden_dim
        model.heads = nn.Identity()
    else:
        require(arm == 'resnet50', 'Unknown encoder')
        enum = tv.models.ResNet50_Weights.IMAGENET1K_V2
        model = tv.models.resnet50(weights=enum)
        dim = model.fc.in_features
        model.fc = nn.Identity()
    digest = sha(Path(torch.hub.get_dir()) / 'checkpoints' / enum.url.rsplit('/', 1)[-1])
    require(digest.startswith(enum.url.rsplit('-', 1)[-1].split('.')[0]), 'Pretrained weight hash prefix mismatch')
    return model.requires_grad_(False).eval().to(device), dim, {'enum': str(enum), 'url': enum.url, 'sha256': digest}


def sync(device):
    if device.type == 'cuda':
        torch.cuda.synchronize(device)


@torch.inference_mode()
def features(frame, store, models, cfg, device):
    values = {arm: np.empty((len(frame), spec[1]), np.float32) for arm, spec in models.items()}
    elapsed = dict.fromkeys(models, 0.0)
    offset, read_seconds = 0, 0.0
    loader = iter(load_pixels(frame, store, cfg, device))
    while offset < len(frame):
        start = time.monotonic()
        x, ids, labels = next(loader)
        y = labels.numpy()
        x = x.to(device, non_blocking=True)
        sync(device)
        read_seconds += time.monotonic() - start
        require(tuple(x.shape) == (len(y), 3, cfg['crop'], cfg['crop']), 'Unexpected image shape')
        target = frame.iloc[offset:offset + len(y)]
        require(list(ids) == target.id.tolist() and np.array_equal(y, target['6_way_label']),
                'Feature extraction order or labels changed')
        for arm, (encoder, dim, _) in models.items():
            start = time.monotonic()
            with torch.autocast(device.type, dtype=torch.float16, enabled=device.type == 'cuda'):
                z = encoder(x)
            z = z.float().cpu().numpy()
            elapsed[arm] += time.monotonic() - start
            require(z.shape == (len(y), dim) and np.isfinite(z).all(), f'Invalid {arm} features')
            values[arm][offset:offset + len(y)] = z
        offset += len(y)
    return values, {'read_seconds': read_seconds, 'encoder_seconds': elapsed, 'rows': offset}


def head(dim, cfg, device):
    return nn.Sequential(nn.Dropout(cfg['dropout']), nn.Linear(dim, 6)).to(device)


def batch_order(epoch, size, seed):
    return np.random.default_rng(np.random.SeedSequence([seed, epoch])).permutation(size)


@torch.inference_mode()
def infer(model, matrix, labels, cfg, device):
    model.eval()
    result, loss = [], []
    for a in range(0, len(labels), cfg['head_batch']):
        b = a + cfg['head_batch']
        x = torch.as_tensor(matrix[a:b], device=device)
        y = torch.as_tensor(labels[a:b], dtype=torch.long, device=device)
        logits = model(x)
        require(tuple(logits.shape) == (len(y), 6) and torch.isfinite(logits).all(), 'Invalid logits')
        result.append(logits.softmax(1).cpu().numpy())
        loss.append(F.cross_entropy(logits, y, reduction='none').cpu().numpy())
    return np.concatenate(result), np.concatenate(loss)


def smoke(frame, store, models, cfg, device, folder):
    samples = {}
    for i, split in enumerate(('train', 'validation')):
        f = sampled(frame[split], 48, cfg['seed'] + i)
        samples[split] = f, features(f, store, models, cfg, device)[0]
    train, train_features = samples['train']
    _, val_features = samples['validation']
    proof = {}
    for arm in models:
        torch.manual_seed(cfg['seed'])
        m = head(models[arm][1], cfg, device)
        opt = torch.optim.AdamW(m.parameters(), lr=cfg['learning_rate'], weight_decay=cfg['weight_decay'])
        before = m[1].weight.detach().clone()
        logits = m(torch.as_tensor(train_features[arm], device=device))
        loss = F.cross_entropy(logits, torch.as_tensor(train['6_way_label'].to_numpy(), device=device))
        opt.zero_grad(set_to_none=True)
        loss.backward()
        opt.step()
        require(logits.shape == (48, 6) and torch.isfinite(loss) and not torch.equal(before, m[1].weight),
                'Smoke head did not update with valid six-class logits')
        path = folder / f'smoke_{arm}.pt'
        torch_save(path, m.state_dict())
        reload_check(path, m, val_features[arm], cfg, device)
        proof[arm] = {'feature_dim': models[arm][1], 'logits': [48, 6], 'head_updated': True,
                      'validation_reload': True, 'loss': float(loss.detach().cpu())}
    return proof


@torch.inference_mode()
def reload_check(path, model, data, cfg, device):
    fresh = head(data.shape[1], cfg, device).eval()
    fresh.load_state_dict(torch.load(path, weights_only=True, map_location=device))
    x = torch.as_tensor(data[:32], device=device)
    torch.testing.assert_close(fresh(x), model.eval()(x), rtol=0, atol=0)


def fit_scope(cfg, timing, staging, setup, quota_hours, session_seconds, free_bytes):
    # Decode overlaps GPU work; use the observed end-to-end time, then pad.
    rows_per_second = timing['rows'] / timing['wall_seconds']
    per_row = 1.35 / rows_per_second + 0.002  # cached head passes + CSV/metrics
    reserve = max(1200, session_seconds * .08)
    gross = min(quota_hours * 3600, session_seconds)
    remaining = gross - setup - reserve
    # Allow cache files, save/verify working space and bounded overhead.
    row_cap = min(int(remaining / per_row), max(0, (free_bytes - 2 * 1024**3) // 12500))
    total = sum(cfg['counts'].values())
    counts = cfg['counts'].copy()
    if row_cap < total:
        ev = counts['validation'] + counts['test']
        minimum_train = cfg['preferred_pilot_train']
        if row_cap >= ev + minimum_train:
            counts['train'] = min(counts['train'], row_cap - ev)
        else:
            counts['train'] = min(minimum_train, row_cap // 2)
            left = row_cap - counts['train']
            counts['validation'] = min(counts['validation'], left // 2)
            counts['test'] = min(counts['test'], left - counts['validation'])
        require(min(counts.values()) >= 60, 'Measured quota/scratch does not support a six-class pilot')
    return {'mode': 'full' if counts == cfg['counts'] else 'pilot', 'counts': counts,
            'quota_hours_observed': quota_hours, 'session_seconds': session_seconds,
            'staging_seconds': staging, 'setup_elapsed_seconds': setup, 'saving_reserve_seconds': reserve,
            'estimated_remaining_seconds': sum(counts.values()) * per_row,
            'estimated_total_seconds': setup + sum(counts.values()) * per_row + reserve,
            'observed_rows_per_second': rows_per_second, 'working_free_bytes': free_bytes}


def cached_features(split, frame, store, models, cfg, device, out, stop):
    folder = out / 'cache' / split
    folder.mkdir(parents=True, exist_ok=True)
    matrices = {arm: [] for arm in models}
    for start in range(0, len(frame), 8192):
        block = frame.iloc[start:start + 8192].reset_index(drop=True)
        path = folder / f'{start:07d}.npz'
        if not path.exists():
            if time.monotonic() >= stop:
                raise TimeoutError('Feature extraction paused at a saved shard boundary')
            vals, speed = features(block, store, models, cfg, device)
            temp = path.with_suffix('.tmp')
            with temp.open('wb') as f:
                np.savez(f, ids=block.id.to_numpy(dtype=str),
                         labels=block['6_way_label'].to_numpy(), **vals)
            temp.replace(path)
            print(split, start + len(block), '/', len(frame), speed, flush=True)
        with np.load(path, allow_pickle=False) as saved:
            require(np.array_equal(saved['ids'], block.id)
                    and np.array_equal(saved['labels'], block['6_way_label']),
                    'Saved feature IDs or labels differ from registered manifest')
            for arm in models:
                a = saved[arm]
                require(a.shape == (len(block), models[arm][1]) and np.isfinite(a).all(),
                        'Invalid saved feature shard')
                matrices[arm].append(a)
    return {arm: np.concatenate(chunks) for arm, chunks in matrices.items()}


def metrics_from_arrays(y, predicted, ce):
    # Compute from a confusion matrix. The separate saved verifier uses sklearn.
    cm = np.bincount(6 * y + predicted, minlength=36).reshape(6, 6)
    total = cm.sum()
    support, called, correct = cm.sum(1), cm.sum(0), cm.diagonal()
    def ratio(n, d):
        return np.divide(n, d, out=np.zeros_like(n, dtype=float), where=d != 0)
    precision, recall, f1 = ratio(correct, called), ratio(correct, support), ratio(2*correct, called + support)
    accuracy = float(correct.sum() / total)
    metrics = {'accuracy': accuracy, 'micro_f1': accuracy, 'macro_f1': float(f1.mean()),
               'weighted_f1': float(f1 @ support / total), 'balanced_accuracy': float(recall[support>0].mean()),
               'loss': float(np.asarray(ce, np.float64).mean()), 'samples': int(total)}
    report = {label: {'precision': float(precision[i]), 'recall': float(recall[i]),
                      'f1-score': float(f1[i]), 'support': int(support[i])}
              for i, label in enumerate(LABELS)}
    for name, w in [('macro avg', np.ones(6)/6), ('weighted avg', support/total)]:
        report[name] = {'precision': float(w @ precision), 'recall': float(w @ recall),
                        'f1-score': float(w @ f1), 'support': int(total)}
    report['accuracy'] = accuracy
    normalized = np.divide(cm, support[:, None], out=np.zeros_like(cm, dtype=float), where=support[:, None]!=0)
    return metrics, report, {'labels': LABELS, 'raw': cm.tolist(), 'row_normalized': normalized.tolist()}


def export_eval(out, prefix, frame, prob, ce):
    y = frame['6_way_label'].to_numpy(dtype=int)
    p = prob.argmax(1)
    arrays = metrics_from_arrays(y, p, ce)
    table = pd.DataFrame({'id': frame.id, 'split': frame.split, 'true_label': y,
                          'predicted_label': p, 'cross_entropy': ce,
                          **{f'p{i}': prob[:, i].astype(np.float64) for i in range(6)}})
    path = out / f'{prefix}_predictions.csv'
    temporary = path.with_suffix('.tmp')
    table.to_csv(temporary, index=False, float_format='%.17g')
    temporary.replace(path)
    for suffix, obj in zip(('metrics', 'classification_report', 'confusions'), arrays):
        save_json(out / f'{prefix}_{suffix}.json', obj)
    return arrays[0]


def fit(arm, training, validation, frames, cfg, device, folder, stop, contract):
    folder.mkdir(exist_ok=True)
    y = frames['train']['6_way_label'].to_numpy(dtype=np.int64)
    vy = frames['validation']['6_way_label'].to_numpy(dtype=np.int64)
    torch.manual_seed(cfg['seed'])
    m = head(training.shape[1], cfg, device)
    opt = torch.optim.AdamW(m.parameters(), lr=cfg['learning_rate'], weight_decay=cfg['weight_decay'])
    state_path = folder / 'resume.pt'
    history = []
    if state_path.exists():
        state = torch.load(state_path, weights_only=True, map_location='cpu')
        require(state['contract'] == contract, 'Recovery does not match frozen run')
        m.load_state_dict(state['head'])
        opt.load_state_dict(state['optimizer'])
        history = state['history']
    for epoch in range(len(history) + 1, cfg['epochs'] + 1):
        if time.monotonic() >= stop:
            raise TimeoutError('Head training paused at a saved epoch boundary')
        m.train()
        torch.manual_seed(cfg['seed'] + epoch)
        order = batch_order(epoch, len(y), cfg['seed'])
        batch = cfg['head_batch']
        summed = torch.zeros((), device=device)
        for start in range(0, len(y), batch):
            ids = order[start:start + batch]
            xb, yb = torch.as_tensor(training[ids], device=device), torch.as_tensor(y[ids], device=device)
            opt.zero_grad(set_to_none=True)
            loss = F.cross_entropy(m(xb), yb)
            loss.backward()
            opt.step()
            summed += loss.detach() * len(ids)
        require(torch.isfinite(summed), 'Non-finite head loss')
        prob, ce = infer(m, validation, vy, cfg, device)
        metrics = export_eval(folder, f'validation_epoch{epoch}', frames['validation'], prob, ce)
        epoch_path = folder / f'epoch{epoch}.pt'
        torch_save(epoch_path, m.state_dict())
        reload_check(epoch_path, m, validation, cfg, device)
        history.append({'epoch': epoch, 'train_loss': float(summed.item()/len(y)), 'validation': metrics,
                        'weight_sha256': sha(epoch_path)})
        torch_save(state_path, {'contract': contract, 'head': m.state_dict(), 'optimizer': opt.state_dict(),
                               'history': history})
        save_json(folder / 'history.json', history)
        print(arm, history[-1], flush=True)
    save_json(folder / 'history.json', history)
    best = max(history, key=lambda x: (x['validation']['macro_f1'], -x['validation']['loss'], -x['epoch']))
    source = folder / f"epoch{best['epoch']}.pt"
    require(sha(source) == best['weight_sha256'], 'Selected epoch checkpoint changed')
    selected = folder / 'selected.pt'
    if selected.exists():
        require(sha(selected) == sha(source), 'Existing selected checkpoint differs')
    else:
        shutil.copyfile(source, selected)
    m.load_state_dict(torch.load(selected, weights_only=True, map_location=device))
    reload_check(selected, m, validation, cfg, device)
    return m, best


def run(mount, out, cfg, provenance, quota_hours, session_seconds, mode):
    from verify_frozen_image_pair_v1 import verify_run
    began = time.monotonic()
    require(mode in ('preflight', 'run'), 'Choose a supported stage')
    require(torch.cuda.is_available(), 'Kaggle CUDA GPU is required')
    require(0 < quota_hours <= 30 and 0 < session_seconds <= 43200, 'Invalid observed Kaggle budget')
    out.mkdir(parents=True, exist_ok=True)
    event = 'verified_input_hashes'
    try:
        root, index, frames, registration = load_verified(mount, cfg)
        free = {p: shutil.disk_usage(p).free for p in ('/tmp', '/kaggle/working')}
        runtime = {'python': platform.python_version(), 'torch': str(torch.__version__),
                   'torchvision': tv.__version__, 'cuda': torch.version.cuda,
                   'devices': [torch.cuda.get_device_name(i) for i in range(torch.cuda.device_count())],
                   'scratch_free_before_staging': free}
        print(event, runtime, flush=True)
        event = 'stage_input'
        store, staging = stage(root, index, cfg['index_sha256'])
        device = torch.device('cuda:0')
        event = 'initialize_encoders'
        models = {arm: backbone(arm, device) for arm in ARMS}
        refs = {arm: spec[2] for arm, spec in models.items()}
        event = 'smoke'
        proof = smoke(frames, store, models, cfg, device, out)
        print('smoke_passed', proof, flush=True)
        event = 'benchmark'
        bench = sampled(frames['train'], cfg['benchmark_rows'], cfg['seed'])
        t = time.monotonic()
        _, timing = features(bench, store, models, cfg, device)
        timing['wall_seconds'] = time.monotonic() - t
        scope = fit_scope(cfg, timing, staging, time.monotonic()-began, quota_hours, session_seconds,
                          shutil.disk_usage(out).free)
        evidence = {'runtime': runtime, 'timing': timing, 'smoke': proof, 'scope': scope, 'backbones': refs,
                    'cohort_registration': registration['cohort_id']}
        save_json(out / 'preflight.json', evidence)
        print('preflight_ready', evidence, flush=True)
        if mode == 'preflight':
            return
        event = 'register_run'
        resolved = out / 'resolved.json'
        if resolved.exists():
            registered = json.loads(resolved.read_text())
            require(registered['config'] == cfg and registered['provenance'] == provenance
                    and registered['backbones'] == refs, 'Recovery inputs, source or backbones changed')
            scope_counts = registered['scope']['counts']
        else:
            scope_counts = scope['counts']
        frames = {s: sampled(f, scope_counts[s], cfg['seed'] + i) for i, (s, f) in enumerate(frames.items())}
        manifest_hashes = {}
        for split, frame in frames.items():
            path = out / f'{split}_manifest.csv'
            payload = frame[['id', 'split', '6_way_label', 'image_sha256']].to_csv(index=False).encode()
            if path.exists():
                require(path.read_bytes() == payload, 'Recovery split manifest changed')
            else:
                path.write_bytes(payload)
            manifest_hashes[split] = sha(path)
        if not resolved.exists():
            save_json(resolved, {**evidence, 'config': cfg, 'provenance': provenance, 'manifests': manifest_hashes})
        else:
            require(registered['manifests'] == manifest_hashes, 'Recovery cohort changed')
        if (out / 'independent_verification.json').exists():
            verify_run(out)
            print('Saved result already complete and reverified', flush=True)
            return
        stop = began + min(quota_hours*3600, session_seconds) - scope['saving_reserve_seconds']
        event = 'extract_train_validation'
        cached = {s: cached_features(s, frames[s], store, models, cfg, device, out, stop)
                  for s in ('train', 'validation')}
        event = 'train_validate'
        heads, selected = {}, {}
        for arm in ARMS:
            heads[arm], selected[arm] = fit(arm, cached['train'][arm], cached['validation'][arm], frames,
                                           cfg, device, out / arm, stop, sha(resolved))
        del cached
        event = 'freeze'
        freeze = out / 'selection_frozen.json'
        freeze_record = {'resolved_sha256': sha(resolved), 'selected': selected, 'backbones': refs,
                         'test_manifest_sha256': manifest_hashes['test']}
        if freeze.exists():
            require(json.loads(freeze.read_text()) == freeze_record, 'Frozen selection changed')
        else:
            save_json(freeze, freeze_record)
        print('selection_frozen', sha(freeze), flush=True)
        event = 'test'
        test = frames['test']
        distinct_mask = ~test.image_sha256.isin(set(frames['train'].image_sha256))
        require(distinct_mask.any(), 'No non-overlapping test images')
        if scope_counts == cfg['counts']:
            require(distinct_mask.sum() == 56052, 'Full cohort exact-byte overlap mismatch')
        needs_test = [arm for arm in ARMS if not (out / arm / 'test_saved.json').exists()]
        if needs_test:
            cache_test = cached_features('test', test, store, models, cfg, device, out, stop)
            for arm in needs_test:
                if time.monotonic() >= stop:
                    raise TimeoutError('Test paused before inference')
                prob, ce = infer(heads[arm], cache_test[arm], test['6_way_label'].to_numpy(), cfg, device)
                export_eval(out / arm, 'test', test, prob, ce)
                export_eval(out / arm, 'test_no_train_hash', test[distinct_mask].reset_index(drop=True),
                            prob[distinct_mask], ce[distinct_mask])
                save_json(out / arm / 'test_saved.json', {'freeze_sha256': sha(freeze),
                          'test_predictions_sha256': sha(out / arm / 'test_predictions.csv')})
        event = 'saved_output_verification'
        save_json(out / 'runtime.json', {'current_session_seconds': time.monotonic() - began})
        verification = verify_run(out)
        save_json(out / 'independent_verification.json', verification)
        save_json(out / 'status.json', {'state': 'complete_verified', 'event': event})
        from verify_frozen_image_pair_v1 import report
        (out / 'REPORT.md').write_text(report(out, verification))
        print('complete_verified', verification['differences'], flush=True)
    except TimeoutError as exc:
        save_json(out / 'status.json', {'state': 'needs_saved_recovery', 'event': event, 'reason': str(exc)})
        print('needs_saved_recovery', event, str(exc), flush=True)
    except Exception as exc:
        save_json(out / 'status.json', {'state': 'failed', 'event': event, 'reason': str(exc)})
        raise
