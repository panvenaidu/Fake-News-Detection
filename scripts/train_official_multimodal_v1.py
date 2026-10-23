"""Full-cohort six-way multimodal train/validate executable; NEVER runs test.

Launch requires exact official paired data and coverage. --stage part1 hard-stops
at epoch2. Part2 resumes the same four-epoch schedule, with final test implemented
separately against a frozen validation-selected checkpoint. No local real training.
"""
import argparse
import copy
import csv
import hashlib
import json
import math
import os
import random
import signal
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
os.environ.setdefault('TOKENIZERS_PARALLELISM','false')
os.environ.setdefault('CUBLAS_WORKSPACE_CONFIG',':4096:8')
import numpy as np
import pandas as pd
import torchvision
import transformers
import PIL
from PIL import Image
import torch
from torch import nn
from torch.utils.data import DataLoader,Dataset,Subset
from torchvision import transforms as T
from torchvision.transforms import functional as F
from torchvision.models import resnet50,ResNet50_Weights
from transformers import AutoTokenizer,AutoConfig,BertModel,get_linear_schedule_with_warmup
from sklearn.metrics import accuracy_score,balanced_accuracy_score,classification_report,confusion_matrix,f1_score
from multimodal_recovery_v1 import SCHEMA,atomic_json,sha,stable_seed,order,crop,capture_rng,restore_rng,map_text_encoder,save_generation,load_generation

LABELS=['True','Satire/Parody','Misleading Content','Imposter Content','False Connection','Manipulated Content']
STOP=False

def utc():return datetime.now(timezone.utc).isoformat()

def request_stop(*_):
 global STOP
 STOP=True

class MaximumFusion(nn.Module):
 def __init__(self,text,image):
  super().__init__();self.text=text;self.image=image
  self.text_projection=nn.Sequential(nn.Linear(text.config.hidden_size,512),nn.LayerNorm(512))
  self.image_projection=nn.Sequential(nn.Linear(2048,512),nn.LayerNorm(512))
  self.classifier=nn.Sequential(nn.Linear(512,256),nn.GELU(),nn.Dropout(.2),nn.Linear(256,6))
 def forward(self,input_ids,attention_mask,images):
  t=self.text(input_ids=input_ids,attention_mask=attention_mask).last_hidden_state[:,0]
  v=self.image(images)
  return self.classifier(torch.maximum(self.text_projection(t),self.image_projection(v)))

class Pairs(Dataset):
 def __init__(self,frame,root,tokenizer,cfg,training):
  self.frame=frame.reset_index(drop=True);self.root=Path(root).resolve();self.cfg=cfg;self.training=training;self.epoch=1
  self.tokens={'input_ids':[],'attention_mask':[]}
  for start in range(0,len(frame),8192):
   chunk=tokenizer(frame.clean_title.iloc[start:start+8192].tolist(),truncation=True,max_length=cfg['max_length'],padding=False)
   for k in self.tokens:self.tokens[k].extend(chunk[k])
 def __len__(self):return len(self.frame)
 def __getitem__(self,index):
  row=self.frame.iloc[index];p=(self.root/row.image_path).resolve()
  if not p.is_relative_to(self.root):raise ValueError('Image path escapes root: '+row.id)
  try:
   with Image.open(p) as im:
    im=im.convert('RGB')
    if self.training:
     i,j,h,w=crop(im,self.cfg['seed'],self.epoch,row.id)
     im=F.resized_crop(im,i,j,h,w,[224,224],T.InterpolationMode.BILINEAR,antialias=True)
    else:im=F.center_crop(F.resize(im,232,T.InterpolationMode.BILINEAR,antialias=True),[224,224])
    tensor=F.normalize(F.to_tensor(im),[.485,.456,.406],[.229,.224,.225])
  except Exception as e:raise RuntimeError('Image failure for '+row.id) from e
  return {**{k:v[index] for k,v in self.tokens.items()},'images':tensor,'labels':int(row['6_way_label']),'id':row.id}

class Collate:
 def __init__(self,tokenizer):self.tokenizer=tokenizer
 def __call__(self,rows):
  tokens=self.tokenizer.pad([{k:r[k] for k in ['input_ids','attention_mask']} for r in rows],padding=True,pad_to_multiple_of=8,return_tensors='pt')
  return {**tokens,'images':torch.stack([r['images'] for r in rows]),'labels':torch.tensor([r['labels'] for r in rows]),'ids':[r['id'] for r in rows]}

def verified_frames(root,coverage_path):
 root=Path(root);coverage=json.loads(Path(coverage_path).read_text())
 if coverage.get('image_gate_passed') is not True:raise ValueError('Full image coverage gate has not passed')
 manifest=root/'data/official_paired_v1/paired_manifest.csv'
 if sha(manifest)!=coverage['manifest_sha256']:raise ValueError('Manifest hash mismatch')
 frame=pd.read_csv(manifest,dtype=str,keep_default_na=False)
 if frame.id.duplicated().any():raise ValueError('Duplicate paired IDs')
 expected=json.loads((root/'results/official_dataset_provenance.json').read_text())
 hashes={x['filename']:x['sha256'] for x in expected['files']}
 frames={};all_ids=set()
 for split,name,count in [('train','multimodal_train.tsv',564000),('validation','multimodal_validate.tsv',59342),('test','multimodal_test_public.tsv',59319)]:
  p=root/'data/official_multimodal_v2'/name
  if sha(p)!=hashes[name]:raise ValueError('Official TSV hash mismatch')
  official=pd.read_csv(p,sep='\t',dtype=str,keep_default_na=False);paired=frame[frame.split.eq(split)]
  if len(official)!=count or len(paired)!=count or official.id.duplicated().any():raise ValueError('Wrong split row count')
  if all_ids.intersection(set(official.id)):raise ValueError('Cross-split ID overlap')
  all_ids.update(official.id)
  paired=paired.set_index('id').loc[official.id].reset_index()
  for key in ['clean_title','6_way_label']:
   if not np.array_equal(paired[key].to_numpy(),official[key].to_numpy()):raise ValueError('Official '+key+' differs')
  if not set(paired['6_way_label'])==set(map(str,range(6))) or paired.clean_title.str.strip().eq('').any():raise ValueError('Invalid text/labels')
  for row in paired[['id','image_path','image_sha256']].itertuples(index=False):
   q=(root/row.image_path).resolve()
   if not q.is_relative_to(root.resolve()) or not q.is_file():raise ValueError('Missing/escaping image '+row.id)
   if sha(q)!=row.image_sha256:raise ValueError('Runtime image hash mismatch '+row.id)
  # Test is checked for integrity only; no test dataset, loader or metrics created.
  if split!='test':frames[split]=paired
 if len(frame)!=len(all_ids):raise ValueError('Unexpected extra manifest rows')
 return frames,{'manifest_sha256':sha(manifest),'coverage_sha256':sha(coverage_path),'tsv_sha256':hashes}

def measure(y,pred,ce):
 return {'accuracy':float(accuracy_score(y,pred)),'micro_f1':float(f1_score(y,pred,average='micro')),
  'macro_f1':float(f1_score(y,pred,average='macro',labels=range(6),zero_division=0)),
  'weighted_f1':float(f1_score(y,pred,average='weighted',labels=range(6),zero_division=0)),
  'balanced_accuracy':float(balanced_accuracy_score(y,pred)),'loss':float(np.mean(ce)),'samples':len(y)}

@torch.inference_mode()
def evaluate(model,loader,device):
 model.eval();ids=[];ys=[];probabilities=[];losses=[]
 for batch in loader:
  ids.extend(batch.pop('ids'));labels=batch.pop('labels').to(device)
  with torch.autocast(device.type,dtype=torch.float16,enabled=device.type=='cuda'):
   logits=model(**{k:v.to(device,non_blocking=True) for k,v in batch.items()})
  # Export full float32 CE rather than infer loss from rounded confidence.
  loss=nn.functional.cross_entropy(logits.float(),labels,reduction='none')
  ys.extend(labels.cpu().tolist());losses.extend(loss.cpu().tolist());probabilities.extend(logits.float().softmax(-1).cpu().tolist())
 if len(ids)!=len(set(ids)) or not losses:raise ValueError('Duplicate/empty evaluation')
 probs=np.array(probabilities);pred=probs.argmax(1)
 return measure(ys,pred,losses),pd.DataFrame({'id':ids,'true_label':ys,'predicted_label':pred,'cross_entropy':losses,**{'p'+str(i):probs[:,i] for i in range(6)}})

def export_eval(folder,epoch,values,frame):
 prefix='validation_epoch'+str(epoch);path=folder/(prefix+'_predictions.csv');frame.to_csv(path,index=False,float_format='%.17g')
 y=frame.true_label.to_numpy();pred=frame.predicted_label.to_numpy();cm=confusion_matrix(y,pred,labels=range(6))
 atomic_json(folder/(prefix+'_metrics.json'),values)
 atomic_json(folder/(prefix+'_classification_report.json'),classification_report(y,pred,labels=range(6),target_names=LABELS,zero_division=0,output_dict=True))
 atomic_json(folder/(prefix+'_confusions.json'),{'labels':LABELS,'raw':cm.tolist(),'row_normalized':np.divide(cm,cm.sum(1,keepdims=True),out=np.zeros_like(cm,dtype=float),where=cm.sum(1,keepdims=True)!=0).tolist()})
 return {'predictions_file':path.name,'predictions_sha256':sha(path),'metrics':values,'epoch':epoch}

def better(values,best):
 return best is None or (values['macro_f1'],-values['loss'])>(best['metrics']['macro_f1'],-best['metrics']['loss'])

class Engine:
 """The actual loop is injectable for synthetic interrupted-resume regression."""
 def __init__(self,model,optimizer,scheduler,scaler,cfg,output,device,contract):
  self.model=model;self.optimizer=optimizer;self.scheduler=scheduler;self.scaler=scaler;self.cfg=cfg;self.out=Path(output);self.out.mkdir(parents=True,exist_ok=True);self.device=device;self.contract=contract
  self.state={'epoch':1,'cursor':0,'phase':'train','updates':0,'skips':0,'loss_sum':0.,'seen':0,'history':[],'best':None,'patience_reference':-1.,'stale':0,'early_stopped':False}
  self.last_save=time.monotonic()
 def save(self):
  if any(p.grad is not None for p in self.model.parameters()):raise ValueError('Gradients not cleared')
  payload={'schema':SCHEMA,'gradients_cleared':True,'cursor':self.state['cursor'],'state':self.state,'model':self.model.state_dict(),'optimizer':self.optimizer.state_dict(),'scheduler':self.scheduler.state_dict(),'scaler':self.scaler.state_dict(),'rng':capture_rng(),'contract':self.contract}
  receipt=save_generation(self.out/'recovery',payload);self.last_save=time.monotonic()
  atomic_json(self.out/'runtime_recovery.json',{'utc':utc(),'state':self.state,'generation':receipt,'durability':'session-local only until independently exported and verified'})
  return receipt
 def resume(self):
  p,receipt=load_generation(self.out/'recovery')
  if p['contract']!=self.contract:raise ValueError('Immutable config/source/input contract changed')
  for obj,key in [(self.model,'model'),(self.optimizer,'optimizer'),(self.scheduler,'scheduler'),(self.scaler,'scaler')]:obj.load_state_dict(p[key])
  self.state=p['state'];restore_rng(p['rng']);self.optimizer.zero_grad(set_to_none=True)
  if self.state['best']:
   path=self.out/self.state['best']['weights_file']
   if sha(path)!=self.state['best']['weights_sha256']:raise ValueError('Selected weights missing/corrupt')
  return receipt
 def train_epoch(self,loader,total_rows,on_boundary=None):
  self.model.train();self.optimizer.zero_grad(set_to_none=True);s=self.state;cfg=self.cfg
  if s['cursor']!=s['seen']:raise ValueError('Consumed cursor mismatch')
  original_cursor=s['cursor'];micro=cfg['micro_batch'];acc=cfg['accumulation'];boundaries=0
  for batch in loader:
   ids=batch.pop('ids');labels=batch.pop('labels').to(self.device);n=len(labels)
   group_start=(s['cursor']//(micro*acc))*(micro*acc);group_n=min(micro*acc,total_rows-group_start)
   with torch.autocast(self.device.type,dtype=torch.float16,enabled=self.device.type=='cuda'):
    logits=self.model(**{k:v.to(self.device,non_blocking=True) for k,v in batch.items()});loss=nn.functional.cross_entropy(logits,labels)
   if not torch.isfinite(loss):raise RuntimeError('Nonfinite loss; no silent sample exclusion')
   self.scaler.scale(loss*n/group_n).backward();s['loss_sum']+=float(loss.detach())*n;s['seen']+=n;s['cursor']+=n
   boundary=s['cursor']%(micro*acc)==0 or s['cursor']==total_rows
   if boundary:
    self.scaler.unscale_(self.optimizer);nn.utils.clip_grad_norm_(self.model.parameters(),cfg['gradient_clip'])
    scale=self.scaler.get_scale();self.scaler.step(self.optimizer);self.scaler.update()
    if self.scaler.get_scale()>=scale:self.scheduler.step();s['updates']+=1
    else:s['skips']+=1
    self.optimizer.zero_grad(set_to_none=True);boundaries+=1
    if s['cursor']==total_rows:s['phase']='validation'
    if on_boundary and on_boundary(self,ids,boundaries):self.save();return False
    stop=STOP or (self.out/'STOP_REQUESTED').exists()
    due=(s['updates']>0 and s['updates']%cfg['checkpoint_updates']==0) or time.monotonic()-self.last_save>=cfg['checkpoint_seconds']
    if due or stop or s['phase']=='validation':self.save()
    if stop:return False
   if boundary and (boundaries%50==0 or s['cursor']==total_rows):
    atomic_json(self.out/'status.json',{'utc':utc(),'state':'training','epoch':s['epoch'],'samples_seen':s['cursor'],'batches_seen':math.ceil(s['cursor']/micro),'optimizer_updates':s['updates'],'amp_skips':s['skips'],'loss':s['loss_sum']/s['seen']})
  if s['cursor']!=total_rows:raise ValueError('Loader ended before full epoch')
  return True
 def finish_validation(self,values,proof):
  s=self.state;epoch=s['epoch']
  if s['phase']!='validation':raise ValueError('Validation before training completion')
  if better(values,s['best']):
   name='selected_epoch%d_%s.pt'%(epoch,uuid.uuid4().hex);path=self.out/name
   with path.open('wb') as f:torch.save(self.model.state_dict(),f);f.flush();os.fsync(f.fileno())
   s['best']={**proof,'weights_file':name,'weights_sha256':sha(path)}
  s['history'].append({'epoch':epoch,'train_loss':s['loss_sum']/s['seen'],'validation':values,'updates':s['updates'],'skips':s['skips']})
  if values['macro_f1']>=s['patience_reference']+self.cfg['early_stop_delta']:s['patience_reference']=values['macro_f1'];s['stale']=0
  else:s['stale']+=1
  s['early_stopped']=epoch>=self.cfg['early_stop_min_epoch'] and s['stale']>=self.cfg['early_stop_patience']
  s.update(epoch=epoch+1,cursor=0,phase='train',loss_sum=0.,seen=0);self.save();atomic_json(self.out/'history.json',s['history'])

def build_loader(dataset,tokenizer,cfg,training,cursor=0):
 if training:
  permutation=order(cfg['seed'],dataset.epoch,len(dataset));data=Subset(dataset,permutation[cursor:].tolist())
 else:data=dataset
 generator=torch.Generator().manual_seed(stable_seed(cfg['seed'],dataset.epoch,'workers-'+str(cursor)))
 return DataLoader(data,batch_size=cfg['micro_batch'] if training else cfg['eval_batch'],shuffle=False,num_workers=cfg['workers'],generator=generator,collate_fn=Collate(tokenizer),pin_memory=True,persistent_workers=False)

def run(args):
 cfg=json.loads(Path(args.config).read_text())
 if cfg['planned_epochs']!=4 or cfg['seed']!=42:raise ValueError('Unexpected registered budget/seed')
 stop=args.stop_after_epoch
 if args.stage=='part1' and stop not in [1,2]:raise ValueError('Part1 hard limit is epoch2; no test in this executable')
 if args.stage=='part2' and (not args.resume or stop not in [3,4]):raise ValueError('Part2 must resume same run')
 frames,inputs=verified_frames(args.root,args.coverage)
 if not torch.cuda.is_available():raise RuntimeError('Cloud CUDA required; local scientific training refused')
 out=Path(args.output);out.mkdir(parents=True,exist_ok=args.resume)
 lock=out/'trainer.lock'
 try:fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
 except FileExistsError:raise RuntimeError('Attempt lock exists; verify original process/job before removing it')
 os.write(fd,str(os.getpid()).encode());os.close(fd)
 try:
  source_files=[Path(__file__),Path(__file__).with_name('multimodal_recovery_v1.py')]
  versions={'python':sys.version,'torch':torch.__version__,'torchvision':torchvision.__version__,'transformers':transformers.__version__,'numpy':np.__version__,'pillow':PIL.__version__}
  contract={'config':cfg,'config_sha256':sha(args.config),'inputs':inputs,'versions':versions,'sources':{p.name:sha(p) for p in source_files}}
  protocol=out/'protocol.json'
  if args.resume and json.loads(protocol.read_text())!=contract:raise ValueError('Run protocol mismatch')
  atomic_json(protocol,contract)
  random.seed(cfg['seed']);np.random.seed(cfg['seed']);torch.manual_seed(cfg['seed']);torch.cuda.manual_seed_all(cfg['seed']);torch.backends.cudnn.benchmark=False;torch.backends.cuda.matmul.allow_tf32=False;torch.use_deterministic_algorithms(True,warn_only=True)
  tokenizer=AutoTokenizer.from_pretrained(cfg['bert_checkpoint'],revision=cfg['bert_revision']);bcfg=AutoConfig.from_pretrained(cfg['bert_checkpoint'],revision=cfg['bert_revision'])
  text=BertModel(bcfg,add_pooling_layer=False)
  if not args.resume:
   if sha(args.warmstart)!=cfg['warmstart_sha256']:raise ValueError('Warmstart hash mismatch')
   atomic_json(out/'warmstart_mapping.json',map_text_encoder(torch.load(args.warmstart,map_location='cpu',weights_only=True),text))
  image=resnet50(weights=None if args.resume else ResNet50_Weights.IMAGENET1K_V2);image.fc=nn.Identity();model=MaximumFusion(text,image).cuda()
  groups={}
  for name,p in model.named_parameters():
   family='bert' if name.startswith('text.') else 'image' if name.startswith('image.') else 'head';lr=cfg[family+'_lr'];decay=0. if p.ndim<=1 else cfg['image_decay' if family=='image' else 'bert_head_decay'];groups.setdefault((lr,decay),[]).append(p)
  opt=torch.optim.AdamW([{'params':p,'lr':lr,'weight_decay':wd} for (lr,wd),p in groups.items()],betas=(.9,.999),eps=1e-8)
  budget=math.ceil(math.ceil(len(frames['train'])/cfg['micro_batch'])/cfg['accumulation'])*cfg['planned_epochs'];scheduler=get_linear_schedule_with_warmup(opt,math.ceil(budget*cfg['warmup_fraction']),budget);scaler=torch.amp.GradScaler('cuda')
  data={k:Pairs(f,args.root,tokenizer,cfg,k=='train') for k,f in frames.items()}
  engine=Engine(model,opt,scheduler,scaler,cfg,out,torch.device('cuda'),contract)
  if args.resume:atomic_json(out/'last_resume_verification.json',engine.resume())
  else:tokenizer.save_pretrained(out/'tokenizer');engine.save()
  if args.stage=='part2' and len(engine.state['history'])<2:raise ValueError('Part2 requires completed Part1 train/validation history')
  if args.stage=='part1' and len(engine.state['history'])>2:raise ValueError('This attempt has progressed past Part1; preserve its later state')
  atomic_json(out/'environment.json',{'utc':utc(),'python':sys.version,'torch':torch.__version__,'gpu':torch.cuda.get_device_name(0),'used_devices':1,'cuda_visible_devices':os.environ.get('CUDA_VISIBLE_DEVICES'),'planned_update_boundaries':budget})
  for sig in [signal.SIGTERM,signal.SIGINT]:signal.signal(sig,request_stop)
  while engine.state['epoch']<=stop and not engine.state['early_stopped']:
   if STOP or (out/'STOP_REQUESTED').exists():engine.save();return
   epoch=engine.state['epoch'];data['train'].epoch=epoch
   if engine.state['phase']=='train':
    if not engine.train_epoch(build_loader(data['train'],tokenizer,cfg,True,engine.state['cursor']),len(data['train'])):return
   values,pred=evaluate(model,build_loader(data['validation'],tokenizer,cfg,False),torch.device('cuda'))
   if pred.id.tolist()!=frames['validation'].id.tolist():raise ValueError('Validation ID/order mismatch')
   proof=export_eval(out,epoch,values,pred);engine.finish_validation(values,proof)
  atomic_json(out/('part1_runtime_complete.json' if args.stage=='part1' else 'training_runtime_complete.json'),{'utc':utc(),'epochs_completed':len(engine.state['history']),'best':engine.state['best'],'no_test_performed':True,'durability':'Runtime complete only; not accepted until independent verification/export/Git receipt'})
 finally:lock.unlink(missing_ok=True)

if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--root',required=True,type=Path);ap.add_argument('--coverage',required=True,type=Path);ap.add_argument('--config',required=True,type=Path);ap.add_argument('--output',required=True,type=Path);ap.add_argument('--warmstart',required=True,type=Path);ap.add_argument('--stage',choices=['part1','part2'],default='part1');ap.add_argument('--stop-after-epoch',type=int,default=2);ap.add_argument('--resume',action='store_true');run(ap.parse_args())
