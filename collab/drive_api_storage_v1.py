"""Bounded Google Drive transport for approved UROP private files.

Uses existing authorized sessions only. No auth flow, DriveFS, account change,
permissions change, deletion or model execution. Session URIs are PRIVATE state.
Official protocol: developers.google.com/workspace/drive/api/guides/manage-uploads
"""
import hashlib
import json
import os
import re
import time
from pathlib import Path

API = 'https://www.googleapis.com/drive/v3/files'
UPLOAD = 'https://www.googleapis.com/upload/drive/v3/files'
FIELDS = 'id,name,size,md5Checksum,version,mimeType,parents'
CHUNK = 8 * 1024**2


def hashes(path):
    sha, md5 = hashlib.sha256(), hashlib.md5()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(CHUNK), b''):
            sha.update(block); md5.update(block)
    return sha.hexdigest(), md5.hexdigest()


def atomic_json(path, value):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.tmp')
    with temporary.open('w') as stream:
        json.dump(value, stream, indent=2, allow_nan=False); stream.write('\n')
        stream.flush(); os.fsync(stream.fileno())
    os.replace(temporary, path)


def received_offset(response, total):
    if response.status_code != 308:
        raise ValueError('Expected resumable308 status')
    value = response.headers.get('Range')
    if value is None:
        return 0
    match = re.fullmatch(r'bytes=0-(\d+)', value)
    if not match or not 0 < int(match[1]) + 1 <= total:
        raise ValueError('Invalid resumable receipt range')
    return int(match[1]) + 1


def safe_error(error):
    return re.sub(r'https?://\S+', '[private URL]', str(error))[:600]


class DriveStore:
    def __init__(self, session, progress=None):
        self.session = session
        self.progress = progress or (lambda **kw: None)

    def meta(self, ident):
        with self.session.get(API + '/' + ident, params={'fields': FIELDS}, timeout=30) as response:
            response.raise_for_status(); return response.json()

    def children(self, parent):
        files, token = [], None
        while True:
            params = {'q': "'" + parent + "' in parents and trashed = false",
                      'pageSize': 1000, 'fields': 'nextPageToken,files(' + FIELDS + ')'}
            if token: params['pageToken'] = token
            with self.session.get(API, params=params, timeout=30) as response:
                response.raise_for_status(); value = response.json()
            files.extend(value['files']); token = value.get('nextPageToken')
            if not token: break
        names = [item['name'] for item in files]
        if len(names) != len(set(names)):
            raise ValueError('Duplicate private folder names require reconciliation')
        return {item['name']: item for item in files}

    def folder(self, parent, name, create=False):
        existing = self.children(parent).get(name)
        if existing:
            if existing['mimeType'] != 'application/vnd.google-apps.folder':
                raise ValueError('Expected private folder')
            return existing['id']
        if not create: raise ValueError('Required private folder missing: ' + name)
        with self.session.post(API, params={'fields': FIELDS}, json={
                'name': name, 'parents': [parent], 'mimeType': 'application/vnd.google-apps.folder'}, timeout=30) as response:
            response.raise_for_status(); return response.json()['id']

    def read_small(self, meta, expected_sha=None, cap=32 * 1024**2):
        size = int(meta['size']); data = bytearray()
        if not 0 <= size <= cap: raise ValueError('Small-file bound exceeded')
        with self.session.get(API + '/' + meta['id'], params={'alt': 'media'}, stream=True,
                headers={'Accept-Encoding': 'identity'}, timeout=(15, 40)) as response:
            response.raise_for_status()
            if response.status_code != 200 or int(response.headers.get('Content-Length', -1)) != size:
                raise ValueError('Small-file HTTP size/status mismatch')
            for block in response.iter_content(CHUNK):
                if len(data) + len(block) > size: raise ValueError('Oversized private response')
                data.extend(block)
        raw = bytes(data)
        if len(raw) != size or hashlib.md5(raw).hexdigest() != meta['md5Checksum']:
            raise ValueError('Private file bytes differ from Drive metadata')
        if expected_sha and hashlib.sha256(raw).hexdigest() != expected_sha:
            raise ValueError('Pinned private file SHA mismatch')
        return raw

    def put_json(self, parent, name, value, existing=None):
        raw = (json.dumps(value, indent=2, allow_nan=False) + '\n').encode()
        if len(raw) > 4 * 1024**2: raise ValueError('Control JSON exceeds multipart bound')
        if existing:
            with self.session.patch(UPLOAD + '/' + existing['id'], params={'uploadType': 'media', 'fields': FIELDS},
                    headers={'Content-Type': 'application/json'}, data=raw, timeout=40) as response:
                response.raise_for_status(); meta = response.json()
        else:
            boundary = 'urop_api_control_v1'
            description = json.dumps({'name': name, 'parents': [parent], 'mimeType': 'application/json'}).encode()
            body = (b'--' + boundary.encode() + b'\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n' + description +
                    b'\r\n--' + boundary.encode() + b'\r\nContent-Type: application/json\r\n\r\n' + raw + b'\r\n--' + boundary.encode() + b'--\r\n')
            with self.session.post(UPLOAD, params={'uploadType': 'multipart', 'fields': FIELDS},
                    headers={'Content-Type': 'multipart/related; boundary=' + boundary}, data=body, timeout=40) as response:
                response.raise_for_status(); meta = response.json()
        if int(meta['size']) != len(raw) or meta['md5Checksum'] != hashlib.md5(raw).hexdigest():
            raise ValueError('Private JSON durable metadata mismatch')
        if self.read_small(meta) != raw: raise ValueError('Private JSON readback mismatch')
        return meta

    def download(self, meta, destination, expected_sha):
        """Resume a cloud-scratch copy; require immutable remote metadata and full hashes."""
        path = Path(destination); path.parent.mkdir(parents=True, exist_ok=True)
        size = int(meta['size']); part = path.with_suffix(path.suffix + '.part')
        if path.exists():
            if path.stat().st_size != size or hashes(path) != (expected_sha, meta['md5Checksum']):
                raise ValueError('Preserve conflicting existing scratch artifact')
            return path
        for attempt in range(4):
            start = part.stat().st_size if part.exists() else 0
            if start > size: raise ValueError('Oversized scratch partial')
            if start == size: break
            try:
                with self.session.get(API + '/' + meta['id'], params={'alt': 'media'}, stream=True,
                        headers={'Range': f'bytes={start}-{size-1}', 'Accept-Encoding': 'identity'},
                        timeout=(15, 60)) as response:
                    response.raise_for_status()
                    valid = response.status_code == 206 and response.headers.get('Content-Range') == f'bytes {start}-{size-1}/{size}'
                    if not valid and not (start == 0 and response.status_code == 200):
                        raise ValueError('Remote download range mismatch')
                    if int(response.headers.get('Content-Length', -1)) != size-start:
                        raise ValueError('Remote download size mismatch')
                    with part.open('ab') as stream:
                        for block in response.iter_content(CHUNK):
                            if stream.tell()+len(block)>size: raise ValueError('Download exceeded pinned size')
                            stream.write(block)
                        stream.flush(); os.fsync(stream.fileno())
                if part.stat().st_size == size: break
            except ValueError: raise
            except Exception:
                if attempt == 3: raise
                time.sleep(min(2**attempt, 4))
        if not part.exists() or part.stat().st_size != size or hashes(part) != (expected_sha, meta['md5Checksum']):
            raise ValueError('Downloaded archive failed full SHA/MD5 verification')
        current = self.meta(meta['id'])
        if any(str(current[k]) != str(meta[k]) for k in ('id', 'size', 'md5Checksum')):
            raise ValueError('Remote source changed during download')
        os.replace(part, path); return path

    def verify_remote(self, meta, expected_sha):
        sha, md5, size = hashlib.sha256(), hashlib.md5(), 0
        last_report = time.monotonic()
        with self.session.get(API + '/' + meta['id'], params={'alt': 'media'}, stream=True,
                headers={'Accept-Encoding': 'identity'}, timeout=(15, 60)) as response:
            response.raise_for_status()
            if response.status_code != 200 or int(response.headers.get('Content-Length', -1)) != int(meta['size']):
                raise ValueError('Archive verification HTTP size/status mismatch')
            for block in response.iter_content(CHUNK):
                sha.update(block); md5.update(block); size += len(block)
                if size > int(meta['size']): raise ValueError('Archive stream oversized')
                if time.monotonic()-last_report>30:
                    self.progress(state='archive_hash_progress', file=meta['name'], bytes=size, total=int(meta['size']))
                    last_report=time.monotonic()
        if size!=int(meta['size']) or sha.hexdigest()!=expected_sha or md5.hexdigest()!=meta['md5Checksum']:
            raise ValueError('Committed remote archive SHA/MD5 mismatch')
        return {'id':meta['id'],'name':meta['name'],'bytes':size,'sha256':expected_sha,
                'md5Checksum':meta['md5Checksum'],'version':meta.get('version')}

    def upload_file(self, path, parent, name, state=None, save_state=None):
        """Resumable upload. The caller keeps URI state private and recoverable."""
        path=Path(path); size=path.stat().st_size; sha,md5=hashes(path)
        save_state=save_state or (lambda state:None)
        existing=self.children(parent).get(name)
        if existing:
            if int(existing.get('size',-1))!=size or existing.get('md5Checksum')!=md5:
                raise ValueError('Preserve conflicting existing uploaded file')
            return existing
        state=state or {}
        if state and any(state.get(k)!=v for k,v in {'name':name,'bytes':size,'sha256':sha,'md5Checksum':md5,'parent':parent}.items()):
            raise ValueError('Resumable upload does not match local bytes')
        for session_attempt in range(2):
            if not state.get('uri'):
                with self.session.post(UPLOAD, params={'uploadType':'resumable','fields':FIELDS},
                        headers={'X-Upload-Content-Type':'application/octet-stream','X-Upload-Content-Length':str(size)},
                        json={'name':name,'parents':[parent]},timeout=40) as response:
                    response.raise_for_status();uri=response.headers['Location']
                if not uri.startswith('https://www.googleapis.com/upload/drive/'):
                    raise ValueError('Unexpected resumable upload destination')
                state={'uri':uri,'name':name,'bytes':size,'sha256':sha,'md5Checksum':md5,'parent':parent}
                save_state(state)
            uri=state['uri'];offset=0;failures=0
            with self.session.put(uri,headers={'Content-Length':'0','Content-Range':f'bytes */{size}'},
                    data=b'',timeout=40,allow_redirects=False) as response:
                if response.status_code in (200,201):return self._uploaded(response.json(),size,md5)
                if response.status_code==404:
                    state={};save_state(state);continue
                response.raise_for_status();offset=received_offset(response,size)
            with path.open('rb') as stream:
                while offset<size:
                    stream.seek(offset);block=stream.read(min(CHUNK,size-offset))
                    try:
                        with self.session.put(uri,data=block,headers={'Content-Length':str(len(block)),
                                'Content-Range':f'bytes {offset}-{offset+len(block)-1}/{size}'},
                                timeout=(15,90),allow_redirects=False) as response:
                            if response.status_code in (200,201):return self._uploaded(response.json(),size,md5)
                            response.raise_for_status();next_offset=received_offset(response,size)
                        if not offset<next_offset<=offset+len(block):raise ValueError('Invalid acknowledged upload position')
                        offset=next_offset;failures=0
                    except ValueError:raise
                    except Exception:
                        failures+=1
                        if failures>3:raise
                        with self.session.put(uri,headers={'Content-Length':'0','Content-Range':f'bytes */{size}'},
                                data=b'',timeout=40,allow_redirects=False) as response:
                            if response.status_code in (200,201):return self._uploaded(response.json(),size,md5)
                            response.raise_for_status();offset=received_offset(response,size)
                    self.progress(state='upload_progress',file=name,bytes=offset,total=size)
            raise ValueError('Upload reached total without committed server receipt')
        raise ValueError('Upload session expired repeatedly; preserve private state')

    @staticmethod
    def _uploaded(meta,size,md5):
        if int(meta.get('size',-1))!=size or meta.get('md5Checksum')!=md5:
            raise ValueError('Uploaded archive durable size/MD5 mismatch')
        return meta
