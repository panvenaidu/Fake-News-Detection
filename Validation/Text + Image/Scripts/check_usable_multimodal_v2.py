"""Actual trainer loop regression using synthetic CPU data; no research result."""
import copy,json,tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import numpy as np
from PIL import Image
import torch
from torch import nn
from torch.utils.data import Dataset,DataLoader,Subset
from transformers import BertConfig,BertModel,get_linear_schedule_with_warmup
from train_usable_multimodal_v2 import Engine,MaximumFusion,evaluate,measure,better,verified_frames
from multimodal_recovery_v1 import *

class Toy(Dataset):
 def __len__(self):return 13
 def __getitem__(self,i):
  g=torch.Generator().manual_seed(i+123)
  return {'input_ids':torch.randint(0,32,(4,),generator=g),'attention_mask':torch.ones(4,dtype=torch.long),'images':torch.randn(3,16,16,generator=g),'labels':torch.tensor(i%6),'id':'id'+str(i)}
def collate(rows):
 return {**{k:torch.stack([r[k] for r in rows]) for k in ['input_ids','attention_mask','images','labels']},'ids':[r['id'] for r in rows]}
class SkipScaler:
 """Deterministic AMP-skip test double, not a claim of GPU AMP execution."""
 def __init__(self,skip_at=2):self.scale_value=16.;self.calls=0;self.skip_at=skip_at
 def scale(self,x):return x
 def unscale_(self,opt):pass
 def get_scale(self):return self.scale_value
 def step(self,opt):
  self.calls+=1
  if self.calls!=self.skip_at:opt.step()
 def update(self):
  if self.calls==self.skip_at:self.scale_value/=2
 def state_dict(self):return self.__dict__.copy()
 def load_state_dict(self,d):self.__dict__.update(d)

def make(path,cfg):
 torch.manual_seed(42);np.random.seed(42)
 text=BertModel(BertConfig(vocab_size=32,hidden_size=16,num_hidden_layers=1,num_attention_heads=2,intermediate_size=24),add_pooling_layer=False)
 image=nn.Sequential(nn.Conv2d(3,4,3),nn.BatchNorm2d(4),nn.ReLU(),nn.AdaptiveAvgPool2d(1),nn.Flatten(),nn.Linear(4,2048))
 model=MaximumFusion(text,image);opt=torch.optim.AdamW(model.parameters(),lr=.001)
 sch=get_linear_schedule_with_warmup(opt,1,12)
 return Engine(model,opt,sch,SkipScaler(),cfg,path,torch.device('cpu'),{'test':'synthetic_actual_engine'})

def loader(epoch,cursor=0):
 indices=order(42,epoch,13)[cursor:].tolist()
 return DataLoader(Subset(Toy(),indices),batch_size=2,collate_fn=collate,generator=torch.Generator().manual_seed(999))

def same(a,b):
 if torch.is_tensor(a):return torch.equal(a,b)
 if isinstance(a,dict):return set(a)==set(b) and all(same(a[k],b[k]) for k in a)
 if isinstance(a,(list,tuple)):return len(a)==len(b) and all(same(x,y) for x,y in zip(a,b))
 return a==b

def simulate(engine,interrupt=False):
 first=True;ids=[]
 def hook(e,batchids,boundary):
  nonlocal first
  ids.extend(batchids)
  if interrupt and first and boundary==1:first=False;return True
  return False
 while engine.state['epoch']<=2:
  epoch=engine.state['epoch']
  if engine.state['phase']=='train':
   done=engine.train_epoch(loader(epoch,engine.state['cursor']),13,on_boundary=hook)
   if not done:
    state=copy.deepcopy(engine.state);engine.resume();assert same(state,engine.state)
    # Second interruption in same epoch proves suffix resumes repeatedly.
    def again(e,b,n):return n==1
    if engine.state['cursor']<12:
     engine.train_epoch(loader(epoch,engine.state['cursor']),13,on_boundary=again);engine.resume()
    engine.train_epoch(loader(epoch,engine.state['cursor']),13)
  value,pred=evaluate(engine.model,DataLoader(Toy(),batch_size=4,collate_fn=collate,generator=torch.Generator().manual_seed(777)),torch.device('cpu'))
  assert len(pred)==13 and pred.id.nunique()==13
  # Save epoch-end/validation-pending state, then restore before evaluating again.
  if interrupt:
   engine.save();engine.resume();value2,pred2=evaluate(engine.model,DataLoader(Toy(),batch_size=4,collate_fn=collate,generator=torch.Generator().manual_seed(777)),torch.device('cpu'));assert value==value2
  engine.finish_validation(value,{'epoch':epoch,'metrics':value})
 return engine

def main():
 torch.set_num_threads(2)
 cfg=json.loads(Path('configs/multimodal_usable_6way_v2.json').read_text());cfg.update(micro_batch=2,accumulation=3,workers=0,checkpoint_updates=100,checkpoint_seconds=99999)
 with tempfile.TemporaryDirectory(dir='data/official_paired_v2',prefix='actual-engine-') as tmp:
  a=simulate(make(Path(tmp)/'a',cfg));b=simulate(make(Path(tmp)/'b',cfg),True)
  assert same(a.model.state_dict(),b.model.state_dict()),'Model/BN resume mismatch'
  assert same(a.optimizer.state_dict(),b.optimizer.state_dict()),'Optimizer resume mismatch'
  assert same(a.scheduler.state_dict(),b.scheduler.state_dict()),'Schedule resume mismatch'
  assert same(a.scaler.state_dict(),b.scaler.state_dict()),'Scaler resume mismatch'
  assert a.state['history']==b.state['history'],'History mismatch'
  assert a.state['updates']==5 and a.state['skips']==1 and a.scheduler.last_epoch==5
  assert a.state['epoch']==3 and len(a.state['history'])==2
  # Validate exact per-sample weighting of the 1-sample tail and the 6-sample groups.
  assert a.state['history'][0]['updates']==2 and a.state['history'][0]['skips']==1
  assert len(list((Path(tmp)/'b/recovery').glob('*.pt')))==2,'Unbounded checkpoint storage'
  with patch('torch.cuda.manual_seed_all') as seed_cuda:
   crop(Image.new('RGB',(100,100)),42,1,'x');seed_cuda.assert_not_called()
  assert not better({'macro_f1':.7,'loss':.5},{'metrics':{'macro_f1':.7,'loss':.5}})
  assert better({'macro_f1':.7,'loss':.4},{'metrics':{'macro_f1':.7,'loss':.5}})
  # Independent full-batch reference for accumulation with a 1-example tail.
  class LinearOnly(nn.Module):
   def __init__(self):super().__init__();self.fc=nn.Linear(3,6)
   def forward(self,input_ids,attention_mask,images):return self.fc(images)
  torch.manual_seed(27);linear=LinearOnly();reference=copy.deepcopy(linear)
  sx=torch.randn(5,3);sy=torch.arange(5)%6
  samples=[{'input_ids':torch.zeros(1,dtype=torch.long),'attention_mask':torch.ones(1,dtype=torch.long),'images':sx[i],'labels':sy[i],'id':str(i)} for i in range(5)]
  opt=torch.optim.SGD(linear.parameters(),lr=.01);refopt=torch.optim.SGD(reference.parameters(),lr=.01)
  tailcfg={**cfg,'micro_batch':2,'accumulation':2,'gradient_clip':1e9}
  tail=Engine(linear,opt,torch.optim.lr_scheduler.LambdaLR(opt,lambda _:1),torch.amp.GradScaler('cpu',enabled=False),tailcfg,Path(tmp)/'tail',torch.device('cpu'),{'test':'tail'})
  tail.train_epoch(DataLoader(samples,batch_size=2,collate_fn=collate,generator=torch.Generator().manual_seed(5)),5)
  for begin,end in [(0,4),(4,5)]:
   refopt.zero_grad();nn.functional.cross_entropy(reference.fc(sx[begin:end]),sy[begin:end]).backward();refopt.step()
  for k,v in reference.state_dict().items():assert torch.allclose(v,linear.state_dict()[k],atol=1e-7,rtol=0),'Tail gradient weighting'
  try:verified_frames(Path('.'),Path('results/official_image_coverage_v1.json'))
  except ValueError as e:assert 'runtime gate' in str(e)
  else:raise AssertionError('Incomplete cohort accepted')
 result={'status':'passed','kind':'Synthetic CPU regression against actual full trainer Engine and MaximumFusion; no scientific training or task scores','checks':['Both-encoder actual architecture loop with13 train examples','Two mid-epoch interruptions and validation-pending restore','Repeated resume across next epoch including BatchNorm and dropout','Exact final model/optimizer/scheduler/scaler state and validation-history equality','One simulated AMP skip;5 successful updates; scheduler advanced5 times','Partial accumulation tail handled','Only two committed recovery generations retained','Crop never seeds CUDA','Selection ties preserve earlier epoch','Incomplete official image cohort rejected'],'limitations':['CUDA AMP/numerical agreement still needs cloud regression','Full data/cloud throughput/durable export not verified','CPU test uses tiny random BERT and synthetic vision branch, not a scientific pretrained run']}
 atomic_json('results/usable_multimodal_engine_checks_20261024.json',result);print(json.dumps(result,indent=2))
if __name__=='__main__':main()
