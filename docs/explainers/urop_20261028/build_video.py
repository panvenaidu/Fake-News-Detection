"""Offline narrated educational video; no ML inference or changes to experiments.
Native macOS speech + OpenCV/AVFoundation H264; source and verified facts retained.
"""
from pathlib import Path
import json,re,subprocess,wave,hashlib,math,bisect,time
import numpy as np
import cv2
from PIL import Image,ImageDraw,ImageFont
P=Path('/Users/panveenaidu/Downloads/SEM7/UROP');D=P/'docs/explainers/urop_20261028';O=P/'data/presentations/urop_explainer_20261028';O.mkdir(parents=True,exist_ok=True)
SC=json.loads((D/'storyboard.json').read_text());R=json.loads((P/'results/MM_FINAL_COMPLETION_RECEIPT_20261028.json').read_text());assert R['status']=='multimodal_part1_part2_complete_verified' and R['selected_epoch']==4
W,H,FPS=1920,1080,24
BG='#F5F5F1';INK='#182D3A';MUT='#536879';BLUE='#246FE5';CORAL='#DB6355';GREEN='#138677';LINE='#D9E1E7';WHITE='#FFFFFF'
FONT='/System/Library/Fonts/Supplemental/Arial.ttf';BOLD='/System/Library/Fonts/Supplemental/Arial Bold.ttf'
def font(n,b=False):return ImageFont.truetype(BOLD if b else FONT,n)
def wrap(draw,s,f,width):
 words=s.split();lines=[];line=''
 for word in words:
  test=(line+' '+word).strip()
  if draw.textlength(test,font=f)>width and line:lines.append(line);line=word
  else:line=test
 if line:lines.append(line)
 return lines

def text(draw,xy,s,size=30,color=INK,b=False,width=None,spacing=9):
 f=font(size,b);lines=wrap(draw,s,f,width) if width else str(s).split('\n')
 for i,l in enumerate(lines):draw.text((xy[0],xy[1]+i*(size+spacing)),l,font=f,fill=color)
 return len(lines)*(size+spacing)
def box(draw,rect,title,sub='',color=BLUE,fs=31):
 draw.rounded_rectangle(rect,18,fill=WHITE,outline=color,width=3);x,y,x2,y2=rect
 lines=wrap(draw,title,font(fs,True),x2-x-30);hh=len(lines)*(fs+6)+(30 if sub else 0);top=y+(y2-y-hh)/2
 for l in lines:
  ww=draw.textlength(l,font=font(fs,True));draw.text((x+(x2-x-ww)/2,top),l,font=font(fs,True),fill=color);top+=fs+6
 if sub:
  ww=draw.textlength(sub,font=font(23));draw.text((x+(x2-x-ww)/2,top+5),sub,font=font(23),fill=MUT)
def arrow(draw,a,b,color=MUT,width=4):
 draw.line([a,b],fill=color,width=width);ang=math.atan2(b[1]-a[1],b[0]-a[0]);L=15
 draw.polygon([b,(b[0]-L*math.cos(ang-.45),b[1]-L*math.sin(ang-.45)),(b[0]-L*math.cos(ang+.45),b[1]-L*math.sin(ang+.45))],fill=color)
def architecture(draw,focus=''):
 c1=BLUE if focus!='head' else MUT;c2=CORAL if focus!='head' else MUT
 box(draw,(110,290,295,390),'Title','tokens',c1);box(draw,(340,290,610,390),'BERT-base','CLS: 768',c1);box(draw,(655,290,890,390),'Projection','512 + LayerNorm',c1,28)
 box(draw,(110,485,295,585),'Image','RGB 224 × 224',c2);box(draw,(340,485,610,585),'ResNet-50','pooled: 2,048',c2);box(draw,(655,485,890,585),'Projection','512 + LayerNorm',c2,28)
 for y in [340,535]:arrow(draw,(297,y),(337,y));arrow(draw,(612,y),(652,y))
 draw.line([(892,340),(920,340),(920,438),(944,438)],fill=MUT,width=4);draw.line([(892,535),(920,535),(920,438)],fill=MUT,width=4)
 box(draw,(948,385,1190,490),'MAX','512 features',GREEN,35);box(draw,(948,550,1190,655),'Classifier','256 → 6 logits',GREEN,29);arrow(draw,(1070,492),(1070,547))
 text(draw,(125,665),'Both encoders are fine-tuned; no ResNet-55 in this run.',24,MUT)
def diagram(draw,kind):
 if kind in ['encoders','projection','overview']:
  architecture(draw,kind);return
 if kind=='classes':
  labs=['True','Satire / Parody','Misleading Content','Imposter Content','False Connection','Manipulated Content'];subs=['benchmark true label','satirical framing','deceptive framing','machine-generated sources','text–image mismatch','edited-image sources']
  for i,(lab,sub) in enumerate(zip(labs,subs)):
   x=110+(i%3)*365;y=290+(i//3)*190;box(draw,(x,y,x+335,y+135),lab,sub,[BLUE,GREEN,CORAL][i%3],27)
  text(draw,(125,690),'Weak supervision: source-based labels can contain noise.',26,MUT);return
 if kind=='data':
  for i,(a,n,c) in enumerate([('TRAIN','563,601',BLUE),('VALIDATION','59,299',GREEN),('PUBLIC TEST','59,270',CORAL)]):
   x=110+i*365;box(draw,(x,305,x+335,485),n,a,c,51)
  text(draw,(135,545),'682,661 original rows  −  491 strict decode failures',31,INK,True)
  text(draw,(135,600),'= 682,170 approved usable faculty pairs',34,GREEN,True)
  text(draw,(135,665),'489 False Connection + 2 Satire/Parody exclusions',26,MUT);return
 if kind=='split':
  for i,(a,b,c) in enumerate([('TRAIN','learn weights',BLUE),('VALIDATE','select epoch',GREEN),('FREEZE','lock selection',INK),('TEST','evaluate once',CORAL)]):
   x=110+i*275;box(draw,(x,350,x+235,490),a,b,c,30)
   if i<3:arrow(draw,(x+237,420),(x+272,420))
  text(draw,(135,560),'No test-guided tuning or checkpoint selection.',35,INK,True)
  text(draw,(135,635),'Distinct post IDs do not guarantee distinct image bytes.',28,MUT);return
 if kind=='text':
  box(draw,(120,285,1160,390),'[CLS]   title   tokens   [SEP]','Illustrative token sequence',BLUE,39)
  box(draw,(160,460,560,590),'Token IDs + mask','max 128 · padded batches',BLUE,31);box(draw,(680,460,1130,590),'BERT attention','context → CLS vector 768',GREEN,31);arrow(draw,(563,525),(675,525))
  text(draw,(170,650),'The attention mask separates real tokens from padding.',28,MUT);return
 if kind=='image':
  for row in range(8):
   for col in range(8):
    v=120+((row*13+col*19)%110);draw.rectangle((130+col*35,315+row*35,163+col*35,348+row*35),fill=(v,195,210))
  draw.rectangle((165,350,375,560),outline=CORAL,width=7);arrow(draw,(440,455),(525,455))
  box(draw,(535,335,850,575),'224 × 224','RGB tensor',CORAL,49);arrow(draw,(853,455),(906,455));box(draw,(918,335,1195,575),'Normalize','ImageNet statistics',GREEN,30)
  text(draw,(135,640),'Train: stable random crop   |   Evaluate: resize 232 → center crop 224',27,MUT);return
 if kind=='fusion':
  rows=[([.2,.7,-.1],BLUE,310),([.5,.1,-.2],CORAL,455),([.5,.7,-.1],GREEN,620)]
  for vals,c,y in rows:
   for j,v in enumerate(vals):box(draw,(250+j*260,y,470+j*260,y+85),str(v),'',c,43)
  text(draw,(115,333),'Text',30,BLUE,True);text(draw,(115,478),'Image',30,CORAL,True);text(draw,(115,643),'MAX',30,GREEN,True)
  text(draw,(280,255),'Toy example — real vectors contain 512 positions',27,MUT)
  for j in range(3):arrow(draw,(360+j*260,542),(360+j*260,612),GREEN)
  return
 if kind=='head':
  for i,(a,b) in enumerate([('Linear','512 → 256'),('GELU','nonlinearity'),('Dropout','p = 0.2'),('Linear','256 → 6')]):
   x=110+i*278;box(draw,(x,320,x+240,455),a,b,GREEN,30)
   if i<3:arrow(draw,(x+242,390),(x+275,390))
  text(draw,(135,510),'Softmax: six probabilities summing to one',35,INK,True)
  for i,v in enumerate([.58,.06,.12,.04,.14,.06]):
   x=135+i*175;draw.rounded_rectangle((x,610-v*110,x+130,640),6,fill=BLUE);text(draw,(x+20,655),str(v),25,MUT)
  text(draw,(145,705),'Illustrative probabilities, not a measured example.',23,MUT);return
 if kind=='learning':
  for i,(a,b) in enumerate([('Predict','forward pass'),('Loss','cross-entropy'),('Gradients','backpropagation'),('Update','AdamW')]):
   x=110+i*278;box(draw,(x,340,x+240,490),a,b,BLUE if i<2 else GREEN,30)
   if i<3:arrow(draw,(x+242,415),(x+275,415))
  text(draw,(135,560),'BERT 1e−5   ·   ResNet 1e−4   ·   Head 1e−3',35,INK,True)
  text(draw,(135,635),'Warmup → decay · weight decay · stable recovery',29,MUT);return
 if kind=='batch':
  for i in range(4):box(draw,(120+i*210,320,295+i*210,450),'8','microbatch',BLUE,49)
  arrow(draw,(960,385),(1010,385));box(draw,(1020,310,1200,465),'32','effective batch',GREEN,49)
  for i,(a,b) in enumerate([('FP16','autocast'),('Scaler','numerical range'),('Clip 1','limit gradients')]):
   x=135+i*355;box(draw,(x,540,x+315,655),a,b,CORAL,31)
  text(draw,(145,695),'Tesla T4 device 0 only; two devices allocated, one used.',25,MUT);return
 if kind in ['epochs','history']:
  hist=json.loads((P/'results/experiments/multimodal/OFFICIAL-6W-MM-USABLE-v2_seed42_20261027/final_362955511/history.json').read_text())
  heads=['Epoch','Accuracy','Macro-F1','Weighted-F1','Val loss'];xs=[130,300,520,750,1010]
  for x,t in zip(xs,heads):text(draw,(x,290),t,25,MUT,True)
  for i,h in enumerate(hist):
   y=350+i*75
   if i==3:draw.rounded_rectangle((110,y-8,1200,y+53),9,fill='#E8F3ED')
   m=h['validation'];vals=[str(h['epoch']),f'{100*m["accuracy"]:.4f}%',f'{m["macro_f1"]:.6f}',f'{m["weighted_f1"]:.6f}',f'{m["loss"]:.6f}']
   for x,t in zip(xs,vals):text(draw,(x,y),t,28,GREEN if i==3 else INK,i==3)
  text(draw,(135,685),'One seed-42 experiment; epoch 4 selected before testing.',27,MUT);return
 if kind=='metrics':
  fields=[('Accuracy','accuracy',True),('Micro-F1','micro_f1',False),('Macro-F1','macro_f1',False),('Weighted-F1','weighted_f1',False),('Balanced acc.','balanced_accuracy',True),('Loss','loss',False)]
  text(draw,(125,270),'Metric',26,MUT,True);text(draw,(410,270),'Validation',26,MUT,True);text(draw,(635,270),'Test',26,MUT,True)
  for i,(label,k,pct) in enumerate(fields):
   y=320+i*55;text(draw,(125,y),label,27,INK,True)
   for x,m in [(410,R['validation_metrics']),(635,R['test_metrics'])]:text(draw,(x,y),f'{m[k]*100:.4f}%' if pct else f'{m[k]:.6f}',27,BLUE)
  labs=['True','Satire','Misleading','Imposter','False conn.','Manipulated'];fs=[.886982,.785757,.814194,.662188,.955496,.853874]
  text(draw,(915,270),'Test class F1',26,MUT,True)
  for i,(lab,v) in enumerate(zip(labs,fs)):
   y=320+i*55;text(draw,(915,y),lab,21,MUT);draw.rounded_rectangle((915,y+29,915+v*220,y+40),4,fill=CORAL if i==3 else GREEN)
  return
 if kind=='comparison':
  for row,(lab,paper,ours) in enumerate([('VALIDATION',86.,88.5073947),('TEST',85.88,88.1457736)]):
   y=290+row*190;text(draw,(135,y),lab,29,MUT,True)
   for j,(name,v,c) in enumerate([('Paper',paper,'#8D9BA5'),('Ours',ours,BLUE)]):
    yy=y+55+j*60;text(draw,(135,yy),name,26,INK);draw.rounded_rectangle((250,yy,250+v*8,yy+35),7,fill=c);text(draw,(990,yy-2),f'{v:.4f}%',29,c,True)
  text(draw,(135,700),'+2.2658 test percentage points — numerical comparison only',29,GREEN,True);return
 if kind=='recovery':
  names=['Model + BN','Optimizer','Scheduler','AMP scaler','RNG states','Row cursor','Crop + order','Selection history']
  for i,name in enumerate(names):
   x=125+(i%4)*270;y=300+(i//4)*145;box(draw,(x,y,x+240,y+105),name,'',BLUE if i<4 else GREEN,27)
  text(draw,(135,625),'Fresh counters + durable files + SHA-256 + independent metrics',29,INK,True)
  text(draw,(135,688),'A spinner or old output alone proves neither progress nor failure.',25,MUT);return
 if kind=='choices':
  for i,(a,b,c) in enumerate([('Text-only','VERIFIED COMPLETE',GREEN),('Text + image','VERIFIED COMPLETE',GREEN),('Image-only','PENDING',CORAL)]):
   x=115+i*365;box(draw,(x,310,x+335,480),a,b,c,34)
  text(draw,(135,550),'Future studies: CLIP · vision transformers · newer text encoders',30,INK,True)
  text(draw,(135,620),'New models require controlled training, validation and testing.',29,MUT)
  text(draw,(135,690),'No universal best-model or real-world truth guarantee.',28,MUT);return
 architecture(draw)

def base_image(i):
 s=SC[i];im=Image.new('RGB',(W,H),BG);d=ImageDraw.Draw(im)
 text(d,(65,35),'UROP  /  FAKEDDIT  /  SIX CLASSES',24,MUT,True);text(d,(65,86),s['title'],55,INK,True)
 text(d,(1450,38),s['level'],22,BLUE,True)
 d.rounded_rectangle((64,205,1230,755),22,fill='#EDF1F2',outline=LINE,width=2);d.rounded_rectangle((1260,205,1855,755),22,fill=WHITE,outline=LINE,width=2)
 diagram(d,s['kind']);text(d,(1290,240),'TAKEAWAYS',24,BLUE,True)
 y=292
 for p in s['points']:y+=text(d,(1290,y),'• '+p,31,INK,False,530)+18
 y=max(y+15,475);text(d,(1290,y),'IF WE SKIP OR CHANGE IT',23,CORAL,True);text(d,(1290,y+43),s['whatif'],29,INK,False,530)
 text(d,(65,1020),f'{i+1:02d} / {len(SC):02d}   •   Beginner → architecture',23,MUT);text(d,(1370,1020),'VERIFIED PROJECT SNAPSHOT · 28 OCT 2026',18,MUT)
 return im

def build_audio(rate):
 cues=[];chapters=[];parts=[];cursor=.65;parts.append(b'\0'*int(cursor*24000)*2)
 for i,s in enumerate(SC):
  start=cursor;sentences=re.split(r'(?<=[.!?])\s+',s['narration'])
  for sentence in sentences:
   spoken=sentence.replace('UROP','U R O P').replace('Adam W','Adam double-u')
   key=hashlib.sha256((str(rate)+spoken).encode()).hexdigest()[:16];a=O/(key+'.aiff');w=O/(key+'.wav')
   if not w.exists():
    subprocess.run(['/usr/bin/say','-v','Samantha','-r',str(rate),'-o',str(a),spoken],check=True,timeout=60)
    subprocess.run(['/usr/bin/afconvert','-f','WAVE','-d','LEI16@24000',str(a),str(w)],check=True,timeout=30,capture_output=True)
   with wave.open(str(w),'rb') as f:
    assert f.getframerate()==24000 and f.getsampwidth()==2 and f.getnchannels()==1;data=f.readframes(f.getnframes())
   duration=len(data)/48000;parts.append(data);cues.append({'start':cursor,'end':cursor+duration,'text':sentence,'chapter':i});cursor+=duration
   parts.append(b'\0'*int(.12*24000)*2);cursor+=.12
  parts.append(b'\0'*int(.38*24000)*2);cursor+=.38;chapters.append({'index':i,'start':start,'end':cursor,'title':s['title']});print('Narration',i+1,'/',len(SC),'at',round(cursor,1),'seconds',flush=True)
 parts.append(b'\0'*int(3*24000)*2);cursor+=3
 out=O/'narration.wav'
 with wave.open(str(out),'wb') as f:f.setnchannels(1);f.setsampwidth(2);f.setframerate(24000);f.writeframes(b''.join(parts))
 return cues,chapters,cursor

def srt_time(v):
 ms=round(v*1000);return f'{ms//3600000:02d}:{ms//60000%60:02d}:{ms//1000%60:02d},{ms%1000:03d}'
def main():
 rate=175;cues,chapters,duration=build_audio(rate)
 if duration>=590:rate=190;cues,chapters,duration=build_audio(rate)
 assert 300<duration<600,f'Unexpected duration {duration}'
 (D/'captions.srt').write_text('\n\n'.join(f'{i+1}\n{srt_time(c["start"])} --> {srt_time(c["end"])}\n{c["text"]}' for i,c in enumerate(cues))+'\n')
 (O/'timing.json').write_text(json.dumps({'duration':duration,'voice':'Samantha','words_per_minute_setting':rate,'chapters':chapters,'cues':cues},indent=2)+'\n')
 (D/'TRANSCRIPT.md').write_text('# UROP: beginner to architecture\n\nLocal narrated-video fallback: DevMotion returned Unknown tool for design guide and create_project. No DevMotion project or hosted video was created.\n\n'+ '\n\n'.join(f'## {int(c["start"])//60:02d}:{int(c["start"])%60:02d} — {s["title"]}\n\n{s["narration"]}\n\n**What if?** {s["whatif"]}' for s,c in zip(SC,chapters)))
 bases=[base_image(i) for i in range(len(SC))]
 for i,b in enumerate(bases):b.save(O/f'chapter_{i+1:02d}.png')
 caption_images=[]
 for c in cues:
  im=Image.new('RGB',(W,220),BG);dr=ImageDraw.Draw(im);dr.line((65,10,1855,10),fill=LINE,width=2);text(dr,(85,38),c['text'],36,INK,False,1740,11);caption_images.append(im)
 out=O/'visuals_silent.mp4';writer=cv2.VideoWriter(str(out),cv2.VideoWriter_fourcc(*'avc1'),FPS,(W,H));assert writer.isOpened();starts=[c['start'] for c in chapters];cue_starts=[c['start'] for c in cues];n=math.ceil(duration*FPS);tic=time.monotonic()
 for f in range(n):
  t=f/FPS;i=max(0,min(len(SC)-1,bisect.bisect_right(starts,t)-1));c=chapters[i];im=bases[i].copy()
  local=t-c['start']
  if i>0 and local<.45:im=Image.blend(bases[i-1],im,max(0,min(1,local/.45)))
  j=bisect.bisect_right(cue_starts,t)-1
  if j>=0 and t<=cues[j]['end']+.1:im.paste(caption_images[j],(0,790))
  d=ImageDraw.Draw(im);d.rounded_rectangle((65,1060,1855,1069),4,fill=LINE);d.rounded_rectangle((65,1060,65+1790*t/duration,1069),4,fill=BLUE)
  phase=max(0,min(1,local/max(.1,c['end']-c['start'])));px=110+1080*phase;d.ellipse((px-5,768,px+5,778),fill=BLUE)
  writer.write(cv2.cvtColor(np.asarray(im),cv2.COLOR_RGB2BGR))
  if f%(FPS*30)==0:print('Video',round(t), '/',round(duration),'seconds; render elapsed',round(time.monotonic()-tic),flush=True)
 writer.release();print('Silent visual render complete',flush=True)
 final=O/'UROP_Beginner_to_Architecture.mp4';assert not final.exists()
 subprocess.run([str(O/'mux'),str(out),str(O/'narration.wav'),str(final)],check=True,timeout=600)
 info=json.loads(subprocess.check_output([str(O/'mux'),'inspect',str(final)],text=True));assert info['audioTracks']==1 and info['videoTracks']==1 and 300<info['duration']<600
 cap=cv2.VideoCapture(str(final));total=int(cap.get(cv2.CAP_PROP_FRAME_COUNT));assert total>=n-2
 thumb=Image.new('RGB',(4*480,5*270),'#FFFFFF')
 for i,c in enumerate(chapters):
  cap.set(cv2.CAP_PROP_POS_MSEC,(c['start']+min(4,(c['end']-c['start'])/2))*1000);ok,frame=cap.read();assert ok
  tile=Image.fromarray(cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)).resize((480,270));thumb.paste(tile,((i%4)*480,(i//4)*270))
 cap.release();thumb.save(O/'contact_sheet.jpg',quality=92)
 manifest={'status':'rendered_pending_visual_and_full_decode_review','plugin':'DevMotion attempted: backend Unknown tool; local fallback used','duration_seconds':info['duration'],'dimensions':[info['width'],info['height']],'fps':info['fps'],'audio_tracks':info['audioTracks'],'chapters':len(chapters),'output':str(final.relative_to(P)),'bytes':final.stat().st_size,'sha256':hashlib.sha256(final.read_bytes()).hexdigest(),'timing':str((O/'timing.json').relative_to(P)),'transcript':str((D/'TRANSCRIPT.md').relative_to(P)),'evidence':['results/MM_FINAL_COMPLETION_RECEIPT_20261028.json','configs/multimodal_usable_6way_v2.json','scripts/train_usable_multimodal_v2.py','scripts/multimodal_recovery_v1.py'],'model_or_dataset_changes':False}
 (D/'VIDEO_RECEIPT.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps(manifest),flush=True)
if __name__=='__main__':main()
