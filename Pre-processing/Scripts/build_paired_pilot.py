"""Join existing images to official rows; create an explicitly named small pilot.

Never edits official TSVs, historical manifests or images. Split membership is
inherited from the official files, never assigned randomly across splits.
"""
import csv
import hashlib
import json
import math
from collections import Counter
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'data' / 'paired_pilot_20261009'


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1048576), b''):
            h.update(block)
    return h.hexdigest()


def main():
    from PIL import Image
    cfg = json.loads((ROOT / 'configs/text_official_6way_v2.json').read_text())
    with (ROOT / 'data/verified_paired_manifest.csv').open(newline='') as f:
        available = {r['id']: r for r in csv.DictReader(f)}
    assert len(available) == 75995
    OUT.mkdir(parents=True, exist_ok=True)
    sizes = {'train': 2000, 'validation': 300, 'test': 300}
    evidence = {'purpose': 'Engineering pilot, not an official full-cohort benchmark',
                'seed': 42, 'sampling': 'proportional six-class selection by SHA256(seed,id), within each official split',
                'official_cohort': 682661, 'historical_image_manifest_sha256': digest(ROOT / 'data/verified_paired_manifest.csv'),
                'splits': {}}
    fields = ['id', 'split', 'clean_title', '6_way_label', 'image_path']
    paired, pilot, used = [], [], set()
    for split, info in cfg['splits'].items():
        file = ROOT / 'data/official_multimodal_v2' / info['filename']
        assert digest(file) == info['sha256']
        rows = []
        with file.open(newline='') as f:
            official = csv.DictReader(f, delimiter='\t')
            count = 0
            for r in official:
                count += 1
                if r['id'] not in available:
                    continue
                old = available[r['id']]
                old_split = {'val': 'validation', 'validate': 'validation'}.get(old['split'], old['split'])
                assert old_split == split, (r['id'], old_split, split)
                assert old['clean_title'] == r['clean_title']
                assert int(old['6_way_label']) == int(r['6_way_label'])
                image = ROOT / old['image_path']
                assert image.is_file() and image.stat().st_size > 0
                assert r['id'] not in used
                used.add(r['id'])
                rows.append(dict(zip(fields, [r['id'], split, r['clean_title'], r['6_way_label'], old['image_path']])))
        assert count == info['rows']
        groups = {k: [r for r in rows if int(r['6_way_label']) == k] for k in range(6)}
        quotas = {k: math.floor(sizes[split] * len(g) / len(rows)) for k, g in groups.items()}
        remaining = sizes[split] - sum(quotas.values())
        priority = sorted(groups, key=lambda k: (-(sizes[split]*len(groups[k])/len(rows)-quotas[k]), k))
        for k in priority[:remaining]:
            quotas[k] += 1
        assert min(quotas.values()) >= 1
        chosen = []
        for k, g in groups.items():
            g.sort(key=lambda r: hashlib.sha256(('42:' + r['id']).encode()).hexdigest())
            chosen.extend(g[:quotas[k]])
        chosen.sort(key=lambda r: r['id'])
        paired.extend(rows); pilot.extend(chosen)
        evidence['splits'][split] = {'official_rows': count, 'available_images': len(rows),
            'pilot_rows': len(chosen), 'pilot_class_counts': dict(sorted(Counter(r['6_way_label'] for r in chosen).items())),
            'pilot_ids_sha256': hashlib.sha256('\n'.join(r['id'] for r in chosen).encode()).hexdigest()}
    assert len(paired) == len(available) == 75995 and len(pilot) == 2600
    for name, rows in [('available_official_pairs.csv', paired), ('pilot_manifest.csv', pilot)]:
        with (OUT / name).open('w', newline='') as f:
            w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(rows)
        evidence[name + '_sha256'] = digest(OUT / name)
    with zipfile.ZipFile(OUT / 'pilot_inputs.zip', 'w', zipfile.ZIP_STORED) as z:
        for row in pilot:
            path = ROOT / row['image_path']
            with Image.open(path) as im:
                im.verify()
            z.write(path, row['image_path'])
        z.write(OUT / 'pilot_manifest.csv', 'pilot_manifest.csv')
    evidence['archive_bytes'] = (OUT / 'pilot_inputs.zip').stat().st_size
    evidence['archive_sha256'] = digest(OUT / 'pilot_inputs.zip')
    (OUT / 'dataset_evidence.json').write_text(json.dumps(evidence, indent=2) + '\n')
    print(json.dumps(evidence, indent=2))


if __name__ == '__main__':
    main()
