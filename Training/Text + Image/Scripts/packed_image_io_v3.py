"""Lossless TAR image storage adapter. Does not change pixels or research rows.

Build a bounded index while strictly hashing/decoding every member. Read only
the pinned byte range during training. No image extraction or model execution.
"""
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import sqlite3
import tarfile
import shutil
import time
from concurrent.futures import ThreadPoolExecutor
from collections import OrderedDict
from PIL import Image

_INDEX_CACHE = {}
_ARCHIVE_CACHE = {}


def cache_raw_archives(root, proofs, cache, minimum_free=120 * 1024**3):
    """Copy exact source archives into bounded cloud scratch; never re-encode.

    A complete SHA proof, not a filename or prior receipt, authorizes reuse.
    Originals remain read-only. Temporary writes are owned by this cache only.
    """
    root, cache = Path(root).resolve(), Path(cache).resolve()
    total = sum(size for size, digest in proofs.values())
    if not proofs or total > 100 * 1024**3:
        raise ValueError('Raw archive cache exceeds registered storage bound')
    cache.mkdir(parents=True, exist_ok=True)
    if shutil.disk_usage(cache).free < minimum_free:
        raise ValueError('Insufficient cloud scratch for verified raw archive cache')
    started = time.monotonic()

    def copy_one(item):
        name, (size, digest) = item
        source, target = root / name, cache / name
        if source.parent != root or target.parent != cache or not name.endswith('.bin'):
            raise ValueError('Unsafe raw archive cache name')
        if source.stat().st_size != size:
            raise ValueError('Source raw archive size changed')
        if target.exists():
            if target.stat().st_size != size or sha(target) != digest:
                raise ValueError('Preserve conflicting cloud raw archive cache')
            return {'file': name, 'bytes': size, 'sha256': digest, 'reused': True}
        temporary = target.with_suffix('.copy-' + str(os.getpid()))
        if temporary.exists():
            raise ValueError('Preserve interrupted raw archive copy for inspection')
        h, count = hashlib.sha256(), 0
        with source.open('rb') as src, temporary.open('xb') as dst:
            while block := src.read(16 * 1024**2):
                if time.monotonic() - started > 3600:
                    raise TimeoutError('Raw archive staging exceeded one-hour bound')
                dst.write(block); h.update(block); count += len(block)
            dst.flush(); os.fsync(dst.fileno())
        if count != size or h.hexdigest() != digest:
            raise ValueError('Raw archive cache copy SHA mismatch')
        os.replace(temporary, target)
        print(json.dumps({'state': 'raw_archive_cached', 'file': name,
                          'bytes': count, 'seconds': time.monotonic()-started}), flush=True)
        return {'file': name, 'bytes': count, 'sha256': digest, 'reused': False}

    with ThreadPoolExecutor(max_workers=4) as pool:
        copied = list(pool.map(copy_one, sorted(proofs.items())))
    receipt = {'state': 'exact_raw_archive_cache_verified', 'source': str(root),
               'cache': str(cache), 'bytes': total, 'archives': copied,
               'seconds': time.monotonic()-started, 'pixels_changed': False}
    (cache / 'raw_archive_cache_receipt.json').write_text(json.dumps(receipt, indent=2)+'\n')
    return cache


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(4 * 1024**2), b''):
            h.update(block)
    return h.hexdigest()


def packed_name(archive):
    p = PurePosixPath(archive)
    if len(p.parts) != 1 or not archive.endswith('.tar'):
        raise ValueError('Expected a simple original TAR filename')
    return archive[:-4] + '.bin'


class HashReader:
    def __init__(self, stream):
        self.stream, self.digest, self.count = stream, hashlib.sha256(), 0

    def read(self, size=-1):
        block = self.stream.read(size)
        self.digest.update(block)
        self.count += len(block)
        return block


def index_archive(root, archive, proof, rows, connection):
    """One transaction per archive; caller commits a final index only after all."""
    path = Path(root) / packed_name(archive)
    if path.stat().st_size != proof['bytes']:
        raise ValueError('Packed archive size mismatch')
    expected = {r['id']: r for r in rows}
    if len(expected) != len(rows):
        raise ValueError('Duplicate expected image IDs')
    seen = set()
    with path.open('rb') as source:
        reader = HashReader(source)
        with tarfile.open(fileobj=reader, mode='r|') as container:
            for member in container:
                p = PurePosixPath(member.name)
                if not member.isfile() or p.is_absolute() or '..' in p.parts:
                    raise ValueError('Unexpected non-image or unsafe TAR member')
                ident = p.stem
                row = expected.get(ident)
                if row is None or ident in seen or row['source_shard'] != archive:
                    raise ValueError('Unexpected/duplicate image membership')
                if str(PurePosixPath(Path(archive).stem) / p) != row['image_path']:
                    raise ValueError('TAR member differs from original paired manifest')
                if member.size != int(row['bytes']):
                    raise ValueError('TAR image size differs from original paired manifest')
                raw = container.extractfile(member).read()
                if len(raw) != member.size or hashlib.sha256(raw).hexdigest() != row['image_sha256']:
                    raise ValueError('Packed image SHA mismatch: ' + ident)
                with Image.open(io.BytesIO(raw)) as image:
                    image.load()
                    image.convert('RGB').load()
                connection.execute('INSERT INTO images VALUES (?,?,?,?,?)',
                                   (ident, packed_name(archive), member.offset_data,
                                    member.size, row['image_sha256']))
                seen.add(ident)
        # Hash remaining TAR padding too, not merely the last image payload.
        while reader.read(4 * 1024**2):
            pass
        if reader.count != proof['bytes'] or reader.digest.hexdigest() != proof['sha256']:
            raise ValueError('Full original TAR SHA mismatch')
    if seen != set(expected):
        raise ValueError('Incomplete archive image membership')
    return len(seen)


def create_index(root, shards, rows, output):
    output = Path(output)
    if output.exists():
        raise ValueError('Preserve an existing index; explicit recovery required')
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix('.building.sqlite')
    groups = {}
    for row in rows:
        groups.setdefault(row['source_shard'], []).append(row)
    if set(groups) != {s['file'] for s in shards}:
        raise ValueError('Archive set differs from manifest')
    count = 0
    with sqlite3.connect(temporary) as db:
        db.execute('PRAGMA synchronous=FULL')
        if not db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='images'").fetchone():
            db.execute('CREATE TABLE images (id TEXT PRIMARY KEY, archive TEXT NOT NULL, offset INTEGER NOT NULL, size INTEGER NOT NULL, sha256 TEXT NOT NULL)')
            db.execute('CREATE TABLE archives (name TEXT PRIMARY KEY, bytes INTEGER NOT NULL, sha256 TEXT NOT NULL, images INTEGER NOT NULL)')
            db.commit()
        if {x[0] for x in db.execute("SELECT name FROM sqlite_master WHERE type='table'")} != {'images', 'archives'}:
            raise ValueError('Unrecognized incomplete index schema; preserve for inspection')
        if db.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
            raise ValueError('Incomplete SQLite index failed integrity check')
        completed = {name: (size, digest, n) for name, size, digest, n in
                     db.execute('SELECT name,bytes,sha256,images FROM archives')}
        if set(completed) - set(groups):
            raise ValueError('Incomplete index contains an unexpected archive')
        for shard in shards:
            name = shard['file']
            if name in completed:
                size, digest, n = completed[name]
                actual = list(db.execute('SELECT id,offset,size,sha256 FROM images WHERE archive=?', (packed_name(name),)))
                expected = {r['id']: (int(r['bytes']), r['image_sha256']) for r in groups[name]}
                if (size, digest, n) != (shard['bytes'], shard['sha256'], len(expected)) or len(actual) != n:
                    raise ValueError('Incomplete index archive proof differs from pinned source')
                if any(ident not in expected or offset < 0 or (length, image_sha) != expected[ident]
                       for ident, offset, length, image_sha in actual):
                    raise ValueError('Incomplete index image rows differ from pinned manifest')
                path = Path(root) / packed_name(name)
                if path.stat().st_size != size or sha(path) != digest:
                    raise ValueError('Previously indexed archive bytes changed')
                count += n
                print(json.dumps({'state': 'previous_packed_archive_reverified', 'archive': name,
                                  'verified_images': count}), flush=True)
                continue
            try:
                db.execute('BEGIN')
                n = index_archive(root, name, shard, groups[name], db)
                db.execute('INSERT INTO archives VALUES (?,?,?,?)', (name, shard['bytes'], shard['sha256'], n))
                db.commit()
            except BaseException:
                db.rollback()
                raise
            count += n
            print(json.dumps({'state': 'packed_archive_fully_verified', 'archive': shard['file'],
                              'verified_images': count}), flush=True)
        assert db.execute('SELECT count(*) FROM images').fetchone()[0] == count == len(rows)
    with temporary.open('rb') as stream:
        os.fsync(stream.fileno())
    os.replace(temporary, output)
    return {'images': count, 'index_sha256': sha(output), 'index': str(output)}


class ArchiveStore:
    def __init__(self, root, index, index_sha256):
        self.root, self.source_index = Path(root).resolve(), Path(index).resolve()
        if sha(self.source_index) != index_sha256:
            raise ValueError('Archive index SHA mismatch')
        self.index = self.source_index
        # Kaggle inputs use a remote filesystem. SQLite's tiny random page reads
        # were the measured bottleneck; cache only this exact 108 MB index.
        if self.source_index.is_relative_to(Path('/kaggle/input')):
            cache = Path('/kaggle/working/urop_verified_index_cache')
            cache.mkdir(parents=True, exist_ok=True)
            local = cache / (index_sha256 + '.sqlite')
            if not local.exists():
                temporary = local.with_suffix('.tmp-' + str(os.getpid()))
                shutil.copyfile(self.source_index, temporary)
                if sha(temporary) != index_sha256:
                    raise ValueError('Copied index SHA mismatch')
                os.replace(temporary, local)
            if sha(local) != index_sha256:
                raise ValueError('Preserve conflicting cached index')
            self.index = local
        key = (str(self.index), index_sha256)
        if key not in _INDEX_CACHE:
            with sqlite3.connect('file:' + str(self.index) + '?mode=ro&immutable=1', uri=True) as db:
                rows = {ident: (name, offset, size, digest) for ident, name, offset, size, digest in
                        db.execute('SELECT id,archive,offset,size,sha256 FROM images')}
                proofs = {packed_name(name): (size, digest) for name, size, digest in db.execute('SELECT name,bytes,sha256 FROM archives')}
            _INDEX_CACHE[key] = rows, proofs
        self.rows, proofs = _INDEX_CACHE[key]
        self.sizes = {name: item[0] for name, item in proofs.items()}
        if self.root.is_relative_to(Path('/kaggle/input')):
            cache_key = (str(self.root), index_sha256)
            if cache_key not in _ARCHIVE_CACHE:
                _ARCHIVE_CACHE[cache_key] = cache_raw_archives(
                    self.root, proofs, '/tmp/urop_verified_raw_archives/' + index_sha256)
            self.root = _ARCHIVE_CACHE[cache_key]
        self.pid, self.db, self.handles = None, None, OrderedDict()

    def __getstate__(self):
        return {**self.__dict__, 'pid': None, 'db': None, 'handles': OrderedDict()}

    def read(self, row):
        if self.pid != os.getpid():
            for handle in self.handles.values():
                handle.close()
            self.handles, self.pid = OrderedDict(), os.getpid()
        item = self.rows.get(row['id'])
        if item is None:
            raise ValueError('Image missing from verified archive index')
        name, offset, size, digest = item
        if name != packed_name(row['source_shard']) or size != int(row['bytes']) or digest != row['image_sha256']:
            raise ValueError('Archive index differs from pinned original manifest')
        if name not in self.sizes or offset < 0 or offset + size > self.sizes[name]:
            raise ValueError('Invalid indexed archive byte range')
        if name not in self.handles:
            path = (self.root / name).resolve()
            if path.parent != self.root or path.stat().st_size != self.sizes[name]:
                raise ValueError('Packed archive path/size changed')
            self.handles[name] = path.open('rb', buffering=0)
            if len(self.handles) > 64:
                _, old = self.handles.popitem(last=False)
                old.close()
        stream = self.handles.pop(name)
        self.handles[name] = stream
        stream.seek(offset)
        raw = stream.read(size)
        if len(raw) != size or hashlib.sha256(raw).hexdigest() != digest:
            raise ValueError('Indexed image bytes changed')
        return raw
