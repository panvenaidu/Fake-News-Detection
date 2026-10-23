"""Synthetic CPU recovery checks; no real-data training or task metrics."""
import copy,json,random,tempfile
from pathlib import Path
import numpy as np
import torch
from PIL import Image
from multimodal_recovery_v1 import *

def main():
 torch.set_num_threads(2);torch.manual_seed(42);np.random.seed(42);random.seed(42)
 image=Image.new('RGB',(350,290));before=torch.get_rng_state().clone()
 c=crop(image,42,1,'example');assert c==crop(image,42,1,'example') and torch.equal(before,torch.get_rng_state())
 assert torch.equal(order(42,1,17)[5:],order(42,1,17)[5:]);assert not torch.equal(order(42,1,17),order(42,2,17))
 model=torch.nn.Sequential(torch.nn.Linear(4,8),torch.nn.BatchNorm1d(8),torch.nn.Dropout(.2),torch.nn.Linear(8,6))
 opt=torch.optim.AdamW(model.parameters(),lr=.001);schedule=torch.optim.lr_scheduler.LambdaLR(opt,lambda n:1-n/20)
 x=torch.randn(10,4);y=torch.arange(10)%6
 def step(start):
  opt.zero_grad(set_to_none=True);loss=torch.nn.functional.cross_entropy(model(x[start:start+2]),y[start:start+2]);loss.backward();opt.step();schedule.step();opt.zero_grad(set_to_none=True)
 step(0)
 payload={'schema':SCHEMA,'gradients_cleared':True,'cursor':2,'model':copy.deepcopy(model.state_dict()),'optimizer':copy.deepcopy(opt.state_dict()),'scheduler':copy.deepcopy(schedule.state_dict()),'rng':capture_rng()}
 with tempfile.TemporaryDirectory(dir='data/official_paired_v1',prefix='recovery-check-') as tmp:
  save_generation(tmp,payload);step(2);expected=copy.deepcopy(model.state_dict());lr=schedule.get_last_lr()
  recovered,receipt=load_generation(tmp);model.load_state_dict(recovered['model'],strict=True);opt.load_state_dict(recovered['optimizer']);schedule.load_state_dict(recovered['scheduler']);restore_rng(recovered['rng']);step(2)
  assert all(torch.equal(v,model.state_dict()[k]) for k,v in expected.items()) and schedule.get_last_lr()==lr
  next_payload=copy.deepcopy(payload);next_payload['cursor']=4;generation=save_generation(tmp,next_payload)
  (Path(tmp)/generation['file']).write_bytes(b'corrupt')
  fallback,receipt=load_generation(tmp);assert fallback['cursor']==2 and receipt['fallback_errors']
  try:save_generation(tmp,{'schema':SCHEMA,'gradients_cleared':False})
  except ValueError:pass
  else:raise AssertionError('Unsafe save accepted')
 result={'status':'passed','checks':['Stable per-ID crop preserves model RNG','Deterministic epoch permutations','CPU synthetic model/optimizer/scheduler/RNG resume including BatchNorm/dropout','Corrupted generation falls back','Unsafe gradient boundary rejected'],'limitations':['Not full trainer verification','No GPU/AMP skip or real BERT strict mapping executed','No scientific training, validation or test metrics','No cloud durability proved']}
 atomic_json('results/multimodal_recovery_primitives_checks_20261023.json',result);print(json.dumps(result,indent=2))
if __name__=='__main__':main()
