"""Build a CPU cell for verifying a mounted, completed, private Kaggle run.

In a separate private notebook, attach the exact saved science version, run
this cell, and reopen the resulting verification and report.
"""
from pathlib import Path

root = Path(__file__).resolve().parents[3]
sources = {
    'verify_multimodal_final_v1': (root / 'Testing/Text + Image/verify_multimodal_final_v1.py').read_text(),
    'verify_frozen_image_pair_v1': (root / 'Testing/Image Only/verify_frozen_image_pair_v1.py').read_text(),
}
cell = '''# Independent CPU readback of the private frozen image comparison.
import json, sys
from pathlib import Path
from types import ModuleType

science_version = "https://www.kaggle.com/code/rocky62/urop-image-only-vit-vs-resnet-50?scriptVersionId=369302248"
candidates = list(Path('/kaggle/input').glob('**/urop_frozen_pair/independent_verification.json'))
assert len(candidates) == 1, f"Expected one completed attached science version; found {len(candidates)}"
saved = candidates[0].parent
out = Path('/kaggle/working')
'''
cell += f'\nsources = {sources!r}\n'
cell += '''
def install(name, body):
    m = ModuleType(name)
    sys.modules[name] = m
    exec(compile(body, name + '.py', 'exec'), m.__dict__)
    return m

existing = install('verify_multimodal_final_v1', sources['verify_multimodal_final_v1'])
sys.modules['packed_image_io_v3'] = ModuleType('packed_image_io_v3')
sys.modules['packed_image_io_v3'].sha = existing.sha
verifier = install('verify_frozen_image_pair_v1', sources['verify_frozen_image_pair_v1'])
assert verifier.read(saved / 'status.json')['state'] == 'complete_verified'
proof = verifier.verify_run(saved)
assert proof == verifier.read(saved / 'independent_verification.json')
computed_report = verifier.report(saved, proof)
assert computed_report == (saved / 'REPORT.md').read_text()
(out / 'REOPENED_VERIFICATION.json').write_text(json.dumps({
    'science_version': science_version, 'source_receipt_sha256': existing.sha(candidates[0]),
    'verified_on_reopened_saved_output': True, **proof
}, indent=2) + '\\n')
(out / 'REOPENED_REPORT.md').write_text(computed_report.replace(
    '\\n\\nScope:', '\\n\\n[Saved science version](' + science_version + ')\\n\\nScope:', 1))
print("Reopened saved outputs independently verified.", proof['differences'])
'''
compile(cell, '<private readback cell>', 'exec')
path = root / '.tmp/UROP_ViT_Kaggle_Readback.txt'
path.parent.mkdir(exist_ok=True)
path.write_text(cell)
print(path)
