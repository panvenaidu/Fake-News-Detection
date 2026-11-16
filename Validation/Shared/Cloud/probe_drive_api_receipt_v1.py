"""Bounded specimen probe using already-authorized credentials; never signs in.

Reads ONLY one known original UROP receipt via Drive API, without DriveFS.
No packing, upload, extraction, model execution or credential persistence.
"""
import hashlib
import json

FILE_ID = '1i5d6pQvshJuQlwr1sQBskXClI0VtYXdX'
NAME = 'images_0784678d477441dd9378373cf7830aad.receipt.json'
SIZE = 1778013
SHA256 = '92008e69c84c7485965def2c5a7c2d29663d9c18feb587d1bcf9fef5d69108c4'
ARCHIVE_SHA256 = 'eff931cf4bcb6294c2be3ece8c5795780b860dc99cad5b95d5c9895e472879d9'
CHUNK_BYTES = 256 * 1024


def probe(session):
    url = 'https://www.googleapis.com/drive/v3/files/' + FILE_ID
    with session.get(url, params={'fields': 'id,name,size,md5Checksum'}, timeout=20) as response:
        response.raise_for_status()
        meta = response.json()
    if meta.get('id') != FILE_ID or meta.get('name') != NAME or int(meta.get('size', -1)) != SIZE:
        raise ValueError('Pinned source identity/size mismatch')
    data = bytearray()
    with session.get(url, params={'alt': 'media'}, headers={'Range': f'bytes=0-{SIZE-1}',
                     'Accept-Encoding': 'identity'}, stream=True, timeout=(15, 25)) as response:
        response.raise_for_status()
        if response.status_code not in (200, 206):
            raise ValueError('Unexpected response status')
        if response.headers.get('Content-Encoding', 'identity') not in ('', 'identity'):
            raise ValueError('Encoded response refused')
        if response.status_code == 206 and response.headers.get('Content-Range') != f'bytes 0-{SIZE-1}/{SIZE}':
            raise ValueError('Wrong response range')
        if int(response.headers.get('Content-Length', -1)) != SIZE:
            raise ValueError('Wrong response length')
        for chunk in response.iter_content(chunk_size=CHUNK_BYTES):
            if len(data) + len(chunk) > SIZE:
                raise ValueError('Oversized response refused')
            data.extend(chunk)
    if len(data) != SIZE or hashlib.sha256(data).hexdigest() != SHA256:
        raise ValueError('Pinned receipt bytes/hash mismatch')
    receipt = json.loads(data)
    if receipt['archive'] != NAME.replace('.receipt.json', '.tar') or receipt['sha256'] != ARCHIVE_SHA256:
        raise ValueError('Pinned archive metadata mismatch')
    rows = receipt['images']
    if len(rows) != 5022 or len({row['id'] for row in rows}) != 5022:
        raise ValueError('Receipt membership mismatch')
    return {'state': 'bounded_drive_api_receipt_passed', 'file': NAME, 'bytes': SIZE,
            'sha256': SHA256, 'images': len(rows), 'archive_sha256': ARCHIVE_SHA256,
            'chunk_bytes': CHUNK_BYTES, 'new_auth_invoked': False,
            'source_modified': False, 'training': False, 'test_inference': False}


if __name__ == '__main__':
    import google.auth
    from google.auth.transport.requests import AuthorizedSession
    credentials, _ = google.auth.default()
    with AuthorizedSession(credentials) as session:
        print(json.dumps(probe(session)), flush=True)
