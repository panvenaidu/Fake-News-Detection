"""CPU storage parity check for the actual production Pairs preprocessing."""
import hashlib
import io
import json
import tarfile
import tempfile
from pathlib import Path

import pandas as pd
import torch
from PIL import Image

from packed_image_io_v3 import create_index, sha, cache_raw_archives
from train_usable_multimodal_v2 import Pairs


class TokenizerStub:
    def __call__(self, titles, **_):
        return {'input_ids': [[101, 2023, 102] for _ in titles],
                'attention_mask': [[1, 1, 1] for _ in titles]}


with tempfile.TemporaryDirectory(dir='data/official_paired_v2', prefix='packed-pair-parity-') as tmp:
    root = Path(tmp)
    archive = 'images_pack_' + 'c' * 32 + '.tar'
    name = 'images/fixture.png'
    image = Image.new('RGB', (336, 273))
    pixels = image.load()
    for y in range(image.height):
        for x in range(image.width):
            pixels[x, y] = ((x * 7 + y) % 256, (x + y * 3) % 256, (x * 5 + y * 11) % 256)
    buffer = io.BytesIO()
    image.save(buffer, format='PNG')
    raw = buffer.getvalue()
    relative = Path(archive).stem + '/' + name
    flat = root / relative
    flat.parent.mkdir(parents=True)
    flat.write_bytes(raw)
    packed = root / (archive[:-4] + '.bin')
    with tarfile.open(packed, 'w') as tar:
        member = tarfile.TarInfo(name)
        member.size = len(raw)
        tar.addfile(member, io.BytesIO(raw))
    row = {'id': 'fixture', 'split': 'train', 'clean_title': 'example headline',
           '6_way_label': '2', 'image_path': relative, 'image_sha256': hashlib.sha256(raw).hexdigest(),
           'bytes': str(len(raw)), 'source_shard': archive, 'source_member': 'public_image_set/fixture.png'}
    proof = {'file': archive, 'bytes': packed.stat().st_size, 'sha256': sha(packed)}
    result = create_index(root, [proof], [row], root / 'index.sqlite')
    cache = cache_raw_archives(root, {packed.name: (packed.stat().st_size, sha(packed))}, root/'scratch', minimum_free=0)
    assert (cache/packed.name).read_bytes() == packed.read_bytes()
    cache_raw_archives(root, {packed.name: (packed.stat().st_size, sha(packed))}, cache, minimum_free=0)
    frame = pd.DataFrame([row])
    cfg = {'seed': 42, 'max_length': 128}
    checks = []
    for training in [True, False]:
        flat_dataset = Pairs(frame, root, TokenizerStub(), cfg, training)
        packed_dataset = Pairs(frame, cache, TokenizerStub(), cfg, training,
                               root / 'index.sqlite', result['index_sha256'])
        for epoch in [1, 2] if training else [1]:
            flat_dataset.epoch = packed_dataset.epoch = epoch
            a, b = flat_dataset[0], packed_dataset[0]
            assert a['id'] == b['id'] and a['labels'] == b['labels']
            assert torch.equal(a['images'], b['images'])
            assert a['input_ids'] == b['input_ids']
        checks.append('production train crop tensors identical' if training else
                      'production validation tensors identical')
    (cache/packed.name).write_bytes(b'corrupt')
    try:
        cache_raw_archives(root, {packed.name: (packed.stat().st_size, sha(packed))}, cache, minimum_free=0)
    except ValueError:
        checks.append('corrupt cached archive rejected without overwriting')
    else:
        raise AssertionError('Corrupt cached archive accepted')
    receipt = {'status': 'passed_raw_archive_cache_and_production_tensor_parity', 'checks': checks,
               'official_rows_tested': 0, 'scientific_training': False,
               'trainer_sha256': sha('scripts/train_usable_multimodal_v2.py'),
               'adapter_sha256': sha('scripts/packed_image_io_v3.py')}
    Path('results/MM_PART1_RAW_CACHE_FIXTURE_20261027.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(receipt))
