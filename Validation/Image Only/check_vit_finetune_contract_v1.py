"""CPU regression on registered split, DDP coverage and saved CSV readback.

No held-out examples or historical test predictions are opened by this test.
"""
import importlib.util
import json
import math
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

root=Path(__file__).resolve().parents[2]
for p in ('Model/Image Only','Training/Image Only/Cloud','Training/Text + Image/Scripts','Testing/Image Only'):
    sys.path.insert(0, str(root/p))

import train_vit_finetune_v1 as t
from frozen_image_pair_v1 import export_eval, sampled
from verify_vit_finetune_v1 import prediction_file, wilson

cfg=json.loads((root/'Configuration/Image Only/image_only_vit_finetune_v1.json').read_text())
e=t.Engine.__new__(t.Engine)
e.cfg=cfg
rank,size=t.rank,t.size
try:
    t.size=lambda:2
    for n in (1,17,32,33,63,64,563601,30000):
        order=e.order(n,1)
        t.rank=lambda:0
        a=e.split_order(order)
        t.rank=lambda:1
        b=e.split_order(order)
        restored=np.empty(n,dtype=int)
        restored[::2]=a
        restored[1::2]=b
        assert np.array_equal(restored,order)
        assert np.array_equal(np.sort(restored),np.arange(n))
        for start in range(0,n,64):
            rows=min(64,n-start)
            allocations=[(rows+1-r)//2 for r in (0,1)]
            assert sum(allocations)==rows
            assert allocations==[len(a[start//2:start//2+32]),len(b[start//2:start//2+32])]
finally:
    t.rank,t.size=rank,size

frame=pd.DataFrame({'id':[f'i{i}' for i in range(180)],'split':'validation',
                    '6_way_label':np.repeat(np.arange(6),[80,8,35,4,44,9])})
subset=sampled(frame,60,42)
assert len(subset)==60 and set(subset['6_way_label'])==set(range(6))
assert subset.equals(sampled(frame,60,42))
base={'accuracy':.7,'macro_f1':.5,'loss':.8}
candidates=[
    {'epoch':4,'validation':{**base,'accuracy':.700000001,'macro_f1':.01}},
    {'epoch':2,'validation':{**base,'macro_f1':.9}},
    {'epoch':1,'validation':base},]
assert max(candidates,key=t.selection)['epoch']==4
assert max(candidates[1:],key=t.selection)['epoch']==2
assert max([candidates[-1],{'epoch':3,'validation':base}],key=t.selection)['epoch']==1
rng=np.random.default_rng(22)
logits=rng.standard_normal((len(frame),6))
p=np.exp(logits)/np.exp(logits).sum(1,keepdims=True)
ce=-np.log(p[np.arange(len(frame)),frame['6_way_label']])
with tempfile.TemporaryDirectory() as out:
    out=Path(out)
    m=export_eval(out,'validation_epoch1',frame,p,ce)
    _,proof=prediction_file(out,'validation_epoch1',frame)
    assert abs(m['accuracy']-proof['metrics']['accuracy'])<1e-12
    wrong=frame.copy()
    wrong.loc[0,'6_way_label']=1
    try:
        prediction_file(out,'validation_epoch1',wrong)
    except ValueError:
        pass
    else:
        raise AssertionError('Independent verifier accepted an altered label')
assert wilson(82,100)[0]<.82<wilson(82,100)[1]
print('Passed partition/reconstruction, stratified sampling, checkpoint ordering, metrics readback, and label rejection')
