"""Use downloaded provider audio/alignment; never generates or retries API calls."""
from pathlib import Path
import hashlib,json,math,re,subprocess,wave,zipfile
P=Path('/Users/panveenaidu/Downloads/SEM7/UROP')
O=P/'data/presentations/urop_elevenlabs_20261028'
def main():
 assert not (O/'narration.wav').exists(), 'Preserve prepared narration.'
 with zipfile.ZipFile(O/'urop_elevenlabs_sources.zip') as z:
  assert z.testzip() is None
  for f in z.infolist():
   assert '/' not in f.filename and '\\' not in f.filename and not f.filename.startswith('.')
  z.extractall(O)
 sc=json.loads((O/'storyboard.json').read_text());manifest=json.loads((O/'PROVIDER_MANIFEST.json').read_text())
 cursor=.65;parts=[b'\0'*int(cursor*48000)];chapters=[];cues=[]
 for i,s in enumerate(sc):
  source=O/f'chapter_{i+1:02d}.mp3';wav=source.with_suffix('.wav');r=json.loads(source.with_suffix('.json').read_text())
  assert hashlib.sha256(source.read_bytes()).hexdigest()==manifest['chapters'][i]['audio_sha256']
  spoken=s['narration'].replace('UROP','U R O P');a=r['alignment']
  assert ''.join(a['characters'])==spoken
  assert len(a['characters'])==len(a['character_start_times_seconds'])==len(a['character_end_times_seconds'])
  if not wav.exists():subprocess.run(['/usr/bin/afconvert','-f','WAVE','-d','LEI16@24000',str(source),str(wav)],check=True,capture_output=True)
  with wave.open(str(wav),'rb') as w:
   assert w.getframerate()==24000 and w.getnchannels()==1 and w.getsampwidth()==2
   data=w.readframes(w.getnframes())
  duration=len(data)/48000;start=cursor;parts.append(data)
  assert max(a['character_end_times_seconds'])<=duration+.12
  for match in re.finditer(r'\S.*?(?:[.!?](?=\s|$)|$)',spoken):
   t0=start+a['character_start_times_seconds'][match.start()]
   t1=start+a['character_end_times_seconds'][match.end()-1]
   assert t1>t0
   cues.append({'start':t0,'end':t1,'text':match.group(),'chapter':i})
  cursor+=duration;parts.append(b'\0'*24000);cursor+=.5
  chapters.append({'index':i,'title':s['title'],'start':start,'end':cursor})
 parts.append(b'\0'*144000);cursor+=3
 raw=O/'narration_original_tempo.wav'
 with wave.open(str(raw),'wb') as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(24000);w.writeframes(b''.join(parts))
 rate=max(1,math.ceil(cursor/580*10000)/10000)
 subprocess.run([str(P/'data/presentations/urop_explainer_20261028/tempo'),str(raw),str(O/'narration.wav'),str(rate)],check=True)
 with wave.open(str(O/'narration.wav'),'rb') as w:duration=w.getnframes()/w.getframerate()
 assert 300<duration<590
 for row in cues+chapters:row['start']/=rate;row['end']/=rate
 assert all(0<=c['start']<c['end']<=duration for c in cues)
 tm={'voice':'ElevenLabs Alice','duration':duration,'chapters':chapters,'cues':cues,'audio_processing':{'provider_speed_setting':1.08,'raw_duration_seconds':cursor,'postproduction_tempo_factor':rate,'pitch_shift_semitones':0,'backend':'native macOS AVAudioEngine AVAudioUnitTimePitch offline','target_maximum_duration_seconds':580,'timing_basis':'original provider character alignment scaled by tempo factor'}}
 (O/'timing.json').write_text(json.dumps(tm,indent=2)+'\n')
 print(json.dumps({'duration':duration,'raw_duration':cursor,'tempo_factor':rate,'chapters':len(chapters),'cues':len(cues)}),flush=True)
if __name__=='__main__':main()
