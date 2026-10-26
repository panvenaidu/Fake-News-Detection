"""Synthetic storage-equivalence and corruption checks, no real research data."""
from pathlib import Path
import hashlib
import io
import json
import tarfile
import tempfile
from PIL import Image
from packed_image_io_v3 import create_index, ArchiveStore, sha


def rejected(fn):
    try:
        fn()
    except ValueError:
        return
    raise AssertionError('Invalid storage input accepted')


checks = []
with tempfile.TemporaryDirectory(dir='data/official_paired_v2', prefix='packed-io-fixture-') as tmp:
    root = Path(tmp)
    archive = 'images_pack_' + 'a' * 32 + '.tar'
    target = root / (archive[:-4] + '.bin')
    rows, originals = [], {}
    with tarfile.open(target, 'w', format=tarfile.PAX_FORMAT) as tar:
        for i, mode in enumerate(['RGB', 'L', 'P', 'RGBA']):
            ident = 'fixture' + str(i)
            image = Image.new(mode, (31 + i, 27))
            buf = io.BytesIO()
            image.save(buf, format='PNG')
            raw, name = buf.getvalue(), 'images/' + ident + '.png'
            member = tarfile.TarInfo(name)
            member.size = len(raw)
            tar.addfile(member, io.BytesIO(raw))
            originals[ident] = raw
            rows.append({'id': ident, 'source_shard': archive,
                         'image_path': Path(archive).stem + '/' + name,
                         'bytes': str(len(raw)), 'image_sha256': hashlib.sha256(raw).hexdigest()})
    proof = {'file': archive, 'bytes': target.stat().st_size, 'sha256': sha(target)}
    receipt = create_index(root, [proof], rows, root / 'index.sqlite')
    store = ArchiveStore(root, root / 'index.sqlite', receipt['index_sha256'])
    for row in rows:
        raw = store.read(row)
        assert raw == originals[row['id']]
        with Image.open(io.BytesIO(raw)) as a, Image.open(io.BytesIO(originals[row['id']])) as b:
            assert a.convert('RGB').tobytes() == b.convert('RGB').tobytes()
    checks.append('RGB grayscale palette RGBA bytes and RGB pixels identical')
    for wrong in [dict(rows[0], image_sha256='0' * 64), dict(rows[0], source_shard='other.tar'),
                  dict(rows[0], bytes='1'), dict(rows[0], id='missing')]:
        rejected(lambda: store.read(wrong))
    checks.append('Changed SHA archive size and unknown ID rejected')
    rejected(lambda: ArchiveStore(root, root / 'index.sqlite', '0' * 64))
    checks.append('Index checksum mismatch rejected')
    with target.open('r+b') as stream:
        stream.seek(512)
        stream.write(b'X')
    rejected(lambda: store.read(rows[0]))
    checks.append('Changed archive image payload rejected')
result = {'state': 'passed_lossless_archive_reader_engineering_fixture', 'checks': checks,
          'official_images_tested': 0, 'scientific_training': False, 'production_integration': False,
          'source_sha256': sha(Path('scripts/packed_image_io_v3.py'))}
Path('results/MM_PART1_PACKED_READER_FIXTURE_20261026.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result))
