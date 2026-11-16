"""Lossless repack of exactly the user-approved original usable images.

Old extraction report remains FAILED for its all-row gate. No image replacement,
resampling, new download or model execution. Destination gate remains pending.
"""
import argparse
import json
import math
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from usable_cohort_v2 import load_cohort, registration, REGISTRATION, REGISTRATION_SHA, COHORT
from repack_official_images_kaggle_v1 import pack, rows_for, prep


def run(source, output, extraction_report, max_seconds=3600):
    source, output = Path(source).resolve(), Path(output).resolve()
    if output == source or not output.is_relative_to(source):
        raise ValueError('Separate derived output inside approved source root required')
    reg = registration(source / REGISTRATION)
    expected, reg = load_cohort(source, source / REGISTRATION, extraction_report,
                                source / reg['approval_file'])
    sources, rows = rows_for(source, expected)
    target = max(2 * 1024**3, math.ceil(sum(r['bytes'] + 1024 for r in rows.values())
                                     / 44 / (64 * 1024**2)) * (64 * 1024**2))
    output.mkdir(parents=True, exist_ok=True)
    names = [x['filename'] for x in reg['original_files']]
    names += [REGISTRATION, reg['approval_file']]
    for name in names:
        src, dst = source / name, output / name
        if dst.exists() and prep.sha(dst) != prep.sha(src):
            raise ValueError('Preserve differing derived provenance file')
        if not dst.exists(): shutil.copyfile(src, dst)
    dst = output / reg['extraction_report_file']
    if dst.exists() and prep.sha(dst) != reg['extraction_report_sha256']:
        raise ValueError('Preserve differing original extraction report')
    if not dst.exists(): shutil.copyfile(extraction_report, dst)
    result = pack(source, output, expected, target_bytes=target, max_seconds=max_seconds)
    result.update(cohort_id=COHORT, cohort_registration_sha256=REGISTRATION_SHA,
                  approved_exclusions=491, original_all_row_image_gate_passed=False,
                  original_report_sha256=reg['extraction_report_sha256'])
    prep.record(output / ('approved_pack_result_' + prep.uuid.uuid4().hex + '.json'), result)
    print(json.dumps(result), flush=True)
    return result


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--source-root', type=Path, required=True)
    ap.add_argument('--output-root', type=Path, required=True)
    ap.add_argument('--extraction-report', type=Path, required=True)
    ap.add_argument('--max-seconds', type=int, default=3600)
    a = ap.parse_args()
    run(a.source_root, a.output_root, a.extraction_report, a.max_seconds)
