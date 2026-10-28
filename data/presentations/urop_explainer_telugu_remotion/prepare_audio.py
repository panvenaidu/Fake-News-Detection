from pathlib import Path
import json,re,subprocess,wave,zipfile,hashlib
P=Path(__file__).resolve().parent
def main():
 source=P/'evidence/provider_sources.zip'
 with zipfile.ZipFile(source) as z:
  assert z.testzip() is None
  for x in z.infolist():assert '/' not in x.filename and '\\' not in x.filename and not x.filename.startswith('.')
  z.extractall(P/'evidence/provider')
 script=json.loads((P/'script.json').read_text());audio=P/'public/audio';audio.mkdir(exist_ok=True)
 chunks=[b'\0'*31200];cursor=.65;scenes=[];cues=[]
 for i,s in enumerate(script['scenes']):
  f=P/f'evidence/provider/scene_{i:02d}.mp3';w=audio/f'scene_{i:02d}.wav'
  if i==1:
   raw=[];alignment={'characters':[],'character_start_times_seconds':[],'character_end_times_seconds':[]};offset=0
   for part in range(3):
    partfile=P/f'evidence/provider/scene_01_part{part}.mp3';partwav=audio/f'scene_01_part{part}.wav'
    subprocess.run(['/usr/bin/afconvert','-f','WAVE','-d','LEI16@24000',str(partfile),str(partwav)],check=True,capture_output=True)
    with wave.open(str(partwav),'rb') as r:partdata=r.readframes(r.getnframes())
    if part:
     raw.append(b'\0'*8640);alignment['characters'].append(' ');alignment['character_start_times_seconds'].append(offset);offset+=.18;alignment['character_end_times_seconds'].append(offset)
    a=json.loads(partfile.with_suffix('.json').read_text())['alignment']
    alignment['characters']+=a['characters'];alignment['character_start_times_seconds'] += [t+offset for t in a['character_start_times_seconds']];alignment['character_end_times_seconds'] += [t+offset for t in a['character_end_times_seconds']]
    raw.append(partdata);offset+=len(partdata)/48000
   data=b''.join(raw)
   with wave.open(str(w),'wb') as r:r.setnchannels(1);r.setsampwidth(2);r.setframerate(24000);r.writeframes(data)
  else:
   subprocess.run(['/usr/bin/afconvert','-f','WAVE','-d','LEI16@24000',str(f),str(w)],check=True,capture_output=True)
   with wave.open(str(w),'rb') as r:
    assert r.getnchannels()==1 and r.getframerate()==24000 and r.getsampwidth()==2
    data=r.readframes(r.getnframes())
   alignment=json.loads(f.with_suffix('.json').read_text())['alignment']
  d=len(data)/48000;start=cursor
  text=s['narration'];assert ''.join(alignment['characters'])==text
  a=alignment['character_start_times_seconds'];b=alignment['character_end_times_seconds'];assert max(b)<=d+.15
  group=[]
  def flush():
   if not group:return
   lo=group[0].start();hi=group[-1].end()-1
   cues.append({'start':start+a[lo],'end':start+b[hi],'text':text[lo:hi+1],'scene':i})
   group.clear()
  for m in re.finditer(r'\S+',text):
   if group and (len(text[group[0].start():m.end()])>92 or b[m.end()-1]-a[group[0].start()]>4.6 or len(group)>=9):flush()
   group.append(m)
   if m.group().endswith(('.', ';', '?')):flush()
  flush()
  phrases=['tokenizer','BERT-base','CLS','projection','RGB','ResNet-50','pooled','fine-tune','Projections','Max fusion','position by position','classification head','GELU','Cross-entropy','Softmax','Train split','Validation','selection freeze','held-out test','Accuracy','Confusion matrix']
  beats={}
  for q in phrases:
   j=text.lower().find(q.lower())
   if j>=0:beats[q]=round((start+a[j])*30)
  chunks.extend([data,b'\0'*28800]);cursor+=d+.6
  scenes.append({**s,'audioStart':start,'start':0 if i==0 else start,'end':cursor,'audioDuration':d,'beats':beats})
 chunks.append(b'\0'*72000);cursor+=1.5
 out=audio/'narration.wav'
 with wave.open(str(out),'wb') as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(24000);w.writeframes(b''.join(chunks))
 assert 150<cursor<260, f'Inspect duration rather than silently changing narration: {cursor}'
 def tc(t):
  n=round(t*1000);return f'{n//3600000:02}:{n//60000%60:02}:{n//1000%60:02},{n%1000:03}'
 for c in cues:assert 0<=c['start']<=c['end']<=cursor
 (P/'subtitles.srt').write_text('\n\n'.join(f'{i+1}\n{tc(c["start"])} --> {tc(c["end"])}\n{c["text"]}' for i,c in enumerate(cues))+'\n')
 (P/'src/timeline.json').write_text(json.dumps({'duration':cursor,'fps':30,'scenes':scenes,'cues':cues},ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({'duration':cursor,'scenes':len(scenes),'captions':len(cues),'audio_sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'scene_durations':[s['audioDuration'] for s in scenes]}),flush=True)
if __name__=='__main__':main()
