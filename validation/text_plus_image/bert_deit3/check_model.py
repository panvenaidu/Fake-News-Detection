"""Local engineering check; synthetic inputs, never a scientific evaluation."""
import argparse
import json
import sys
import tempfile
from pathlib import Path

import torch
from PIL import Image
from torchvision.transforms import functional as TF
from transformers import AutoConfig, AutoTokenizer, BertModel

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'model/text_plus_image/bert_deit3'))
sys.path.insert(0, str(ROOT / 'training/text_plus_image/Scripts'))
from model import IMAGE_SHA256, TEXT_SHA256, MaximumFusion, better, full_frame, load_image_checkpoint, sha256
from multimodal_recovery_v1 import map_text_encoder


def run(text_path, image_path, text_dir):
    assert sha256(text_path) == TEXT_SHA256
    assert sha256(image_path) == IMAGE_SHA256
    config = AutoConfig.from_pretrained(text_dir, local_files_only=True)
    tokenizer = AutoTokenizer.from_pretrained(text_dir / 'tokenizer', local_files_only=True)
    text = BertModel(config, add_pooling_layer=False)
    mapping = map_text_encoder(torch.load(text_path, map_location='cpu', weights_only=True), text)
    image = load_image_checkpoint(image_path)
    model = MaximumFusion(text, image)
    tile = full_frame(Image.new('RGB', (400, 100), (255, 0, 0)))
    assert tile.size == (224, 224) and tile.getpixel((0, 0)) == (124, 116, 104)
    pixels = TF.normalize(TF.to_tensor(tile), [.485, .456, .406], [.229, .224, .225]).unsqueeze(0)
    tokens = tokenizer(['synthetic engineering example'], truncation=True, max_length=128, return_tensors='pt')
    batch = {'input_ids': tokens['input_ids'], 'attention_mask': tokens['attention_mask'], 'images': pixels}
    model.train()
    logits = model(**batch)
    assert logits.shape == (1, 6) and torch.isfinite(logits).all()
    torch.nn.functional.cross_entropy(logits, torch.tensor([2])).backward()
    assert model.text.embeddings.word_embeddings.weight.grad is not None
    assert model.image.patch_embed.proj.weight.grad is not None
    assert model.classifier[-1].weight.grad is not None
    model.eval()
    with torch.no_grad():
        before = model(**batch).detach()
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / 'engineering.pt'
        torch.save(model.state_dict(), path)
        model.load_state_dict(torch.load(path, map_location='cpu', weights_only=True), strict=True)
        with torch.no_grad():
            after = model(**batch)
        assert torch.equal(before, after)
    old = {'metrics': {'accuracy': .8, 'macro_f1': .7, 'loss': .3}}
    assert better({'accuracy': .81, 'macro_f1': .1, 'loss': 9}, old)
    assert not better({'accuracy': .8, 'macro_f1': .7, 'loss': .3}, old)
    return {'status': 'passed', 'kind': 'synthetic engineering, no training or test',
            'text_sha256': TEXT_SHA256, 'image_sha256': IMAGE_SHA256,
            'text_mapping': mapping, 'output_shape': list(logits.shape),
            'backward_both_encoders': True, 'strict_reload_equal': True}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--text', type=Path, required=True)
    parser.add_argument('--image', type=Path, required=True)
    parser.add_argument('--text-dir', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.text, args.image, args.text_dir), indent=2))
