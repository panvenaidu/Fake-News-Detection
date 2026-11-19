"""BERT + fine-tuned DeiT III maximum fusion, separate from the baseline."""
from pathlib import Path
import hashlib

from PIL import Image
import torch
from torch import nn

TEXT_SHA256 = '870bea50fa608dddd20421c21fd1786e244b1323e22734093214b87023666753'
IMAGE_SHA256 = '97cb89e986c2481d65dd61ff4f2570a907898c885c34ea2e9460385ce01ae300'
IMAGE_MODEL = 'deit3_base_patch16_224.fb_in22k_ft_in1k'


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def full_frame(image):
    """Match the 83% image-only experiment, including rounding and padding."""
    image = image.convert('RGB')
    scale = 224 / max(image.size)
    dims = tuple(max(1, min(224, round(d * scale))) for d in image.size)
    resized = image.resize(dims, Image.Resampling.BILINEAR)
    tile = Image.new('RGB', (224, 224), (124, 116, 104))
    tile.paste(resized, ((224 - dims[0]) // 2, (224 - dims[1]) // 2))
    return tile


class MaximumFusion(nn.Module):
    def __init__(self, text, image):
        super().__init__()
        self.text, self.image = text, image
        self.text_projection = nn.Sequential(nn.Linear(text.config.hidden_size, 512), nn.LayerNorm(512))
        self.image_projection = nn.Sequential(nn.Linear(image.num_features, 512), nn.LayerNorm(512))
        self.classifier = nn.Sequential(nn.Linear(512, 256), nn.GELU(), nn.Dropout(.2), nn.Linear(256, 6))

    def forward(self, input_ids, attention_mask, images):
        text = self.text(input_ids=input_ids, attention_mask=attention_mask).last_hidden_state[:, 0]
        image = self.image(images)
        return self.classifier(torch.maximum(self.text_projection(text), self.image_projection(image)))


def load_image_checkpoint(path):
    """Strictly load the six-class image checkpoint before removing its head."""
    import timm
    if sha256(path) != IMAGE_SHA256:
        raise ValueError('Incorrect full-frame DeiT checkpoint SHA-256')
    image = timm.create_model(IMAGE_MODEL, pretrained=False)
    image.head = nn.Sequential(nn.Dropout(.2), nn.Linear(image.num_features, 6))
    state = torch.load(path, map_location='cpu', weights_only=True)
    image.load_state_dict(state, strict=True)
    image.reset_classifier(0)
    return image


def better(values, best):
    """Unrounded accuracy, macro-F1, loss, and earlier epoch on ties."""
    if best is None:
        return True
    old = best['metrics']
    return (values['accuracy'], values['macro_f1'], -values['loss']) > (
        old['accuracy'], old['macro_f1'], -old['loss'])
