"""Recovery primitives for OFFICIAL-6W-MM-v1; not a full trainer/launch gate.

No network or GPU allocation. State serialization trusts only owned local files.
"""
import hashlib
import json
import os
import random
import uuid
from pathlib import Path
import numpy as np
import torch
from torchvision import transforms as T

SCHEMA='MM-RECOVERY-v1'

def sha(path):
 h=hashlib.sha256()
 with open(path,'rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()

def stable_seed(seed,epoch,ident):
 return int.from_bytes(hashlib.sha256(json.dumps([SCHEMA,seed,epoch,str(ident)],separators=(',',':')).encode()).digest()[:8],'big')%(2**63-1)

def order(seed,epoch,count):
 return torch.randperm(count,generator=torch.Generator().manual_seed(stable_seed(seed,epoch,'sampler')))

def crop(image,seed,epoch,ident):
 # Local CPU RNG fork makes augmentation independent of worker/model RNG.
 with torch.random.fork_rng(devices=[]):
  # torch.manual_seed also seeds CUDA; crop must never change model CUDA RNG.
  torch.random.default_generator.manual_seed(stable_seed(seed,epoch,ident))
  return T.RandomResizedCrop.get_params(image,(.8,1.),(.75,4/3))

def capture_rng():
 return {'python':random.getstate(),'numpy':np.random.get_state(),'torch':torch.get_rng_state(),
         'cuda':torch.cuda.get_rng_state_all() if torch.cuda.is_available() else []}

def restore_rng(state):
 random.setstate(state['python']);np.random.set_state(state['numpy']);torch.set_rng_state(state['torch'].cpu())
 if state['cuda']:torch.cuda.set_rng_state_all([x.cpu() for x in state['cuda']])

def map_text_encoder(source,target):
 excluded={'bert.pooler.dense.weight','bert.pooler.dense.bias','classifier.weight','classifier.bias'}
 if set(source)-excluded != {'bert.'+k for k in target.state_dict()}:raise ValueError('Unexpected warm-start keys')
 mapped={k.removeprefix('bert.'):v for k,v in source.items() if k not in excluded}
 for k,v in target.state_dict().items():
  if v.shape!=mapped[k].shape or v.dtype!=mapped[k].dtype:raise ValueError('Warm-start shape/dtype '+k)
 target.load_state_dict(mapped,strict=True)
 return {'mapped_keys':len(mapped),'excluded_keys':sorted(excluded),'strict':True}

def atomic_json(path,value):
 path=Path(path);tmp=path.with_name(path.name+'.tmp-'+uuid.uuid4().hex)
 with tmp.open('w') as f:json.dump(value,f,indent=2,allow_nan=False);f.write('\n');f.flush();os.fsync(f.fileno())
 os.replace(tmp,path)

def save_generation(folder,payload):
 folder=Path(folder);folder.mkdir(parents=True,exist_ok=True)
 if payload.get('schema')!=SCHEMA or not payload.get('gradients_cleared'):raise ValueError('Not a safe recovery boundary')
 generation=uuid.uuid4().hex;path=folder/(generation+'.pt');tmp=path.with_suffix('.tmp')
 with tmp.open('wb') as f:torch.save(payload,f);f.flush();os.fsync(f.fileno())
 os.replace(tmp,path)
 # Reload before committing pointer. This alone is scratch persistence, not cloud durability.
 check=torch.load(path,map_location='cpu',weights_only=False)
 if check['schema']!=SCHEMA or check['cursor']!=payload['cursor']:raise ValueError('Reload failed')
 item={'file':path.name,'sha256':sha(path),'bytes':path.stat().st_size,'cursor':payload['cursor']}
 pointer=folder/'generations.json';old=json.loads(pointer.read_text()) if pointer.exists() else {'generations':[]}
 generations=[item]+old['generations'][:1];atomic_json(pointer,{'schema':SCHEMA,'generations':generations})
 # Bound scratch space only after the new pointer is committed. Never sweep
 # unrelated files or uncommitted/corrupt artifacts retained for diagnosis.
 for retired in old['generations'][1:]:
  candidate=folder/retired['file']
  if candidate.parent.resolve()==folder.resolve() and len(candidate.stem)==32 and all(c in '0123456789abcdef' for c in candidate.stem):
   candidate.unlink(missing_ok=True)
 return item

def load_generation(folder):
 folder=Path(folder);pointer=json.loads((folder/'generations.json').read_text());errors=[]
 for generation in pointer['generations']:
  try:
   path=folder/generation['file']
   if path.parent.resolve()!=folder.resolve() or sha(path)!=generation['sha256']:raise ValueError('Hash/path mismatch')
   payload=torch.load(path,map_location='cpu',weights_only=False)
   if payload['schema']!=SCHEMA or payload['cursor']!=generation['cursor']:raise ValueError('Schema/cursor mismatch')
   return payload,{'loaded':generation,'fallback_errors':errors}
  except (OSError,ValueError,RuntimeError,KeyError) as e:errors.append(str(e))
 raise ValueError('No usable recovery generation: '+repr(errors))
