"""Prepared lossless storage recovery; execute only after token authorization.

Reuse the bounded/checksummed transport engine, but keep original image TARs
as .bin files so Kaggle does not expand them into682170 startup file copies.
No images, official manifests, labels, split membership or model settings change.
"""
from pathlib import Path
import argparse
import hashlib
import json
import transfer_verified_packs_to_kaggle_v1 as transport

transport.STATE_NAME = 'KAGGLE_PACKED_INPUT_TRANSFER_V3.json'
transport.SLUG = 'urop-faculty-usable-packed-input-v3'
transport.TITLE = 'UROP faculty usable packed input v3'
original_upload = transport.upload_file
ADAPTER_SHA = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


def upload_packed(path, entry, item, save, deadline):
    target = entry['name'][:-4] + '.bin' if entry['name'].startswith('images_pack_') else entry['name']
    if item.get('destination_name', target) != target:
        raise ValueError('Cannot mix unpacked and packed storage generations')
    item['destination_name'] = target
    item['storage_adapter_sha256'] = ADAPTER_SHA
    return original_upload(path, {**entry, 'name': target}, item, save, deadline)


transport.upload_file = upload_packed

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--scratch', default='/content/urop_kaggle_transfer_v1_packed3')
    p.add_argument('--max-seconds', type=int, default=14400)
    p.add_argument('--max-files', type=int, default=41)
    p.add_argument('--finalize', action='store_true')
    print(json.dumps({'state': 'packed_input_transport_requested', 'adapter_sha256': ADAPTER_SHA,
                      'original_index_sha256': transport.INDEX_SHA,
                      'private_dataset': transport.OWNER + '/' + transport.SLUG,
                      'same_original_bytes': True, 'training': False}), flush=True)
    try:
        transport.run(p.parse_args())
    except BaseException as error:
        print(json.dumps({'state': 'packed_transfer_stopped', 'error_type': type(error).__name__,
                          'private_recovery': True, 'training': False}), flush=True)
        raise SystemExit(1) from None
