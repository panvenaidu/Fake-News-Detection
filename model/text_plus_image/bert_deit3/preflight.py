"""Real-pair CUDA engineering gate. Does not train a scientific model or touch test."""
import argparse
import json
import math
import tempfile
import time
from pathlib import Path

import torch
from transformers import AutoConfig, AutoTokenizer, BertModel

import train
from model import IMAGE_SHA256, TEXT_SHA256, MaximumFusion, load_image_checkpoint, sha256


def run(a):
    if not torch.cuda.is_available():
        raise RuntimeError('CUDA GPU is required for this preflight')
    cfg = json.loads(a.config.read_text())
    if sha256(a.text) != TEXT_SHA256 or sha256(a.image) != IMAGE_SHA256:
        raise ValueError('Wrong encoder checkpoint')
    frames, inputs = train.verified_frames(a.root, a.coverage, a.packed_index)
    tokenizer = AutoTokenizer.from_pretrained(cfg['bert_checkpoint'], revision=cfg['bert_revision'])
    text = BertModel(AutoConfig.from_pretrained(cfg['bert_checkpoint'], revision=cfg['bert_revision']), add_pooling_layer=False)
    mapping = train.map_text_encoder(torch.load(a.text, map_location='cpu', weights_only=True), text)
    model = MaximumFusion(text, load_image_checkpoint(a.image)).cuda()
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-5)
    scaler = torch.amp.GradScaler('cuda')
    data = {}
    for split in ('train', 'validation'):
        sample = frames[split].iloc[:512].copy()
        data[split] = train.Pairs(sample, a.root, tokenizer, cfg, False, a.packed_index, inputs['packed_index_sha256'])
    started = time.monotonic()
    batch = next(iter(train.build_loader(data['train'], tokenizer, cfg, True)))
    ids = batch.pop('ids')
    labels = batch.pop('labels').cuda()
    assert len(ids) == cfg['micro_batch'] and len(set(ids)) == len(ids)
    batch = {key: value.cuda() for key, value in batch.items()}
    model.train()
    with torch.autocast('cuda', dtype=torch.float16):
        logits = model(**batch)
    assert logits.shape == (len(ids), 6) and torch.isfinite(logits).all()
    scaler.scale(torch.nn.functional.cross_entropy(logits.float(), labels)).backward()
    assert model.text.embeddings.word_embeddings.weight.grad is not None
    assert model.image.patch_embed.proj.weight.grad is not None
    scaler.step(optimizer)
    scaler.update()
    optimizer.zero_grad(set_to_none=True)
    model.eval()
    val = next(iter(train.build_loader(data['validation'], tokenizer, cfg, False)))
    val_ids = val.pop('ids'); val.pop('labels')
    assert val_ids == frames['validation'].id.iloc[:len(val_ids)].tolist()
    val = {key: value.cuda() for key, value in val.items()}
    with torch.inference_mode():
        with torch.autocast('cuda', dtype=torch.float16):
            before = model(**val)
    with tempfile.TemporaryDirectory(dir=a.scratch) as folder:
        path = Path(folder) / 'engineering.pt'
        torch.save({'model': model.state_dict(), 'optimizer': optimizer.state_dict(), 'scaler': scaler.state_dict()}, path)
        saved = torch.load(path, map_location='cpu', weights_only=True)
        model.load_state_dict(saved['model'], strict=True)
        optimizer.load_state_dict(saved['optimizer'])
        scaler.load_state_dict(saved['scaler'])
        with torch.inference_mode():
            with torch.autocast('cuda', dtype=torch.float16):
                after = model(**val)
        assert torch.equal(before, after)
    # Time the actual microbatch/accumulation path on training rows only. This
    # small benchmark is an estimate, not an epoch or a scientific update.
    model.train(); optimizer.zero_grad(set_to_none=True)
    train_start = time.monotonic(); seen = 0; updates = 0
    loader = train.build_loader(data['train'], tokenizer, cfg, True)
    while time.monotonic() - train_start < a.benchmark_seconds:
        for i, item in enumerate(loader):
            item.pop('ids'); target = item.pop('labels').cuda(non_blocking=True)
            with torch.autocast('cuda', dtype=torch.float16):
                output = model(**{k: v.cuda(non_blocking=True) for k, v in item.items()})
                loss = torch.nn.functional.cross_entropy(output.float(), target) / cfg['accumulation']
            scaler.scale(loss).backward(); seen += len(target)
            if (i + 1) % cfg['accumulation'] == 0:
                scaler.unscale_(optimizer)
                torch.nn.utils.clip_grad_norm_(model.parameters(), cfg['gradient_clip'])
                scaler.step(optimizer); scaler.update(); optimizer.zero_grad(set_to_none=True); updates += 1
            if time.monotonic() - train_start >= a.benchmark_seconds and (i + 1) % cfg['accumulation'] == 0:
                break
    torch.cuda.synchronize(); training_seconds = time.monotonic() - train_start
    eval_start = time.monotonic()
    metrics, predictions = train.evaluate(model, train.build_loader(data['validation'], tokenizer, cfg, False), torch.device('cuda'))
    torch.cuda.synchronize(); evaluation_seconds = time.monotonic() - eval_start
    assert predictions.id.tolist() == frames['validation'].id.iloc[:len(data['validation'])].tolist()
    assert math.isfinite(metrics['loss']) and updates > 0
    receipt = {'status': 'passed', 'device': 'cuda', 'gpu': torch.cuda.get_device_name(0),
               'real_paired_images': True, 'cohort_id': train.COHORT, 'inputs': inputs,
               'source_sha256': sha256(Path(train.__file__)), 'model_sha256': sha256(Path(train.__file__).with_name('model.py')),
               'config_sha256': sha256(a.config), 'text_sha256': TEXT_SHA256, 'image_sha256': IMAGE_SHA256,
               'train_sample_count': len(ids), 'validation_sample_count': len(val_ids),
               'text_mapping': mapping, 'strict_reload_equal': True, 'seconds': time.monotonic()-started,
               'training_samples': seen, 'training_updates': updates, 'training_seconds': training_seconds,
               'training_samples_per_second': seen / training_seconds,
               'validation_samples': len(predictions), 'validation_seconds': evaluation_seconds,
               'validation_samples_per_second': len(predictions) / evaluation_seconds,
               'estimated_epoch_seconds_excluding_checkpoint': 563601 / (seen / training_seconds) + 59299 / (len(predictions) / evaluation_seconds),
               'peak_cuda_bytes': torch.cuda.max_memory_allocated(),
               'note': 'Engineering sample only; quota estimate needs staging, checkpoint and safety margin.'}
    train.atomic_json(a.output, receipt)
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    for name in ('root', 'coverage', 'packed-index', 'config', 'text', 'image', 'output', 'scratch'):
        p.add_argument('--' + name, type=Path, required=True)
    p.add_argument('--benchmark-seconds', type=int, default=180)
    run(p.parse_args())
