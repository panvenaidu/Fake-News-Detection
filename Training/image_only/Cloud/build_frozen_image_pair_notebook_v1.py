"""Embed local source without publishing it or depending on Kaggle Git credentials."""
import hashlib
import json
import subprocess
from pathlib import Path

root = Path(__file__).resolve().parents[3]
files = [
    'Model/Image Only/frozen_image_pair_v1.py',
    'Configuration/Image Only/image_only_vit_resnet_frozen_v1.json',
    'Training/Text + Image/Scripts/packed_image_io_v3.py',
    'Training/Text + Image/Scripts/usable_cohort_v2.py',
    'Testing/Image Only/verify_frozen_image_pair_v1.py',
    'Testing/Text + Image/verify_multimodal_final_v1.py',
]
sources = {Path(name).name: (root/name).read_text() for name in files}
provenance = {'checkout_head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip(),
              'embedded_source_sha256': {name: hashlib.sha256(s.encode()).hexdigest()
                                         for name, s in sources.items()}}
header = """# UROP: matched frozen ViT-B/16 and ResNet-50
Private comparison on the approved faculty image cohort. The two encoders read the same
RGB pixels, and the trainable heads share the same data order and optimizer settings.
Only validation selects a checkpoint. Both selections are frozen before test features.
"""
params = """# Record values from the Kaggle GPU quota dialog and session limit.
GPU_HOURS_OBSERVED = 30
SESSION_SECONDS = 43200
MODE = 'run'  # 'preflight' verifies/times real rows and never runs held-out inference
# A previous private notebook version can be mounted for recovery after verifying its saved files.
RECOVERY = None  # absolute path to its saved urop_frozen_pair directory
"""
setup = """import sys, json, shutil, hashlib
from pathlib import Path
source = Path('/tmp/urop_frozen_pair_source')
source.mkdir(exist_ok=True)
for name, body in SOURCES.items():
    assert hashlib.sha256(body.encode()).hexdigest() == PROVENANCE['embedded_source_sha256'][name]
    (source/name).write_text(body)
sys.path.insert(0, str(source))
from frozen_image_pair_v1 import run
out = Path('/kaggle/working/urop_frozen_pair')
if RECOVERY is not None and not out.exists():
    shutil.copytree(RECOVERY, out)
cfg = json.loads((source/'image_only_vit_resnet_frozen_v1.json').read_text())
run(Path('/kaggle/input'), out, cfg, PROVENANCE, GPU_HOURS_OBSERVED, SESSION_SECONDS, MODE)
"""
cells = [
    {'cell_type': 'markdown', 'metadata': {}, 'id': 'protocol', 'source': header.splitlines(keepends=True)}
]
for ident, code in [('settings', params), ('embedded-source', f'SOURCES = {sources!r}\nPROVENANCE = {provenance!r}\n'),
                    ('run', setup)]:
    cells.append({'cell_type': 'code', 'metadata': {}, 'id': ident, 'source': code.splitlines(keepends=True),
                  'execution_count': None, 'outputs': []})
notebook = {'cells': cells, 'metadata': {'kernelspec': {'display_name': 'Python 3', 'language': 'python',
             'name': 'python3'}, 'language_info': {'name': 'python'}}, 'nbformat': 4, 'nbformat_minor': 5}
out = root/'Training/Image Only/Notebooks/UROP_Image_Only_ViT_ResNet50.ipynb'
out.write_text(json.dumps(notebook, indent=1) + '\n')
