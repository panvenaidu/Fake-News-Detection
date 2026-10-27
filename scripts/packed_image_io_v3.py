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
from collections import OrderedDict
from PIL import Image

_INDEX_CACHE = {}


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
                sizes = {packed_name(name): size for name, size in db.execute('SELECT name,bytes FROM archives')}
            _INDEX_CACHE[key] = rows, sizes
        self.rows, self.sizes = _INDEX_CACHE[key]
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
