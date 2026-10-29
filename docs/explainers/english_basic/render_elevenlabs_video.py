"""Render the verified storyboard with previously generated ElevenLabs audio.

This script makes no API calls. It requires the retained private chapter audio,
provider alignment, narration.wav and timing.json. It refuses to overwrite video.
"""
from pathlib import Path
import bisect, hashlib, html, json, math, subprocess, time
import cv2
import numpy as np
from PIL import Image, ImageDraw
import render_english_video as b

P=b.P
D=P/'docs/explainers/english_elevenlabs'
O=P/'data/presentations/urop_elevenlabs_20261028'
D.mkdir(parents=True, exist_ok=True)
F=O/'UROP_Beginner_to_Architecture_ElevenLabs.mp4'

def main():
 assert not F.exists(), 'Preserve existing video; use a new output directory.'
 tm=json.loads((O/'timing.json').read_text())
 cues=tm['cues']; chapters=tm['chapters']; duration=tm['duration']
 assert 300<duration<600 and len(chapters)==18 and len(b.SC)==18
 bases=[b.base_image(i) for i in range(18)]
 capimgs=[]; maxlines=0
 for cue in cues:
  im=Image.new('RGB',(b.W,220),b.BG);dr=ImageDraw.Draw(im)
  lines=b.wrap(dr,cue['text'],b.font(36),1740);maxlines=max(maxlines,len(lines))
  assert len(lines)<=3
  dr.line((65,10,1855,10),fill=b.LINE,width=2)
  b.text(dr,(85,38),cue['text'],36,b.INK,False,1740,11)
  capimgs.append(im)
 for i,im in enumerate(bases):im.save(O/f'chapter_{i+1:02d}.png')
 (D/'subtitles.srt').write_text('\n\n'.join(f'{i+1}\n{b.srt_time(c["start"])} --> {b.srt_time(c["end"])}\n{c["text"]}' for i,c in enumerate(cues))+'\n')
 (D/'narration.md').write_text('# UROP: beginner to architecture — ElevenLabs edition\n\nNarration: ElevenLabs Alice / Multilingual v2, via Composio. Provider character alignment is scaled with the documented pitch-preserving tempo adjustment. Scientific content matches the original verified storyboard.\n\n'+'\n\n'.join(f'## {int(c["start"])//60:02d}:{int(c["start"])%60:02d} — {s["title"]}\n\n{s["narration"]}\n\n**What if?** {s["whatif"]}' for s,c in zip(b.SC,chapters)))
 writer=cv2.VideoWriter(str(O/'visuals_silent.mp4'),cv2.VideoWriter_fourcc(*'avc1'),b.FPS,(b.W,b.H));assert writer.isOpened()
 starts=[c['start'] for c in chapters];cs=[c['start'] for c in cues]
 n=math.ceil(duration*b.FPS);tic=time.monotonic()
 for f in range(n):
  t=f/b.FPS;i=max(0,min(17,bisect.bisect_right(starts,t)-1));c=chapters[i];im=bases[i].copy();local=t-c['start']
  if i>0 and local<.45:im=Image.blend(bases[i-1],im,max(0,min(1,local/.45)))
  j=bisect.bisect_right(cs,t)-1
  if j>=0 and t<=cues[j]['end']+.1:im.paste(capimgs[j],(0,790))
  dr=ImageDraw.Draw(im);dr.rounded_rectangle((65,1060,1855,1069),4,fill=b.LINE)
  dr.rounded_rectangle((65,1060,65+1790*t/duration,1069),4,fill=b.BLUE)
  phase=max(0,min(1,local/max(.1,c['end']-c['start'])));px=110+1080*phase;dr.ellipse((px-5,768,px+5,778),fill=b.BLUE)
  writer.write(cv2.cvtColor(np.asarray(im),cv2.COLOR_RGB2BGR))
  if f%(b.FPS*30)==0:print('Rendered',round(t),'/',round(duration),'seconds; elapsed',round(time.monotonic()-tic),flush=True)
 writer.release()
 mux=P/'data/presentations/urop_explainer_20261028/mux'
 subprocess.run([str(mux),str(O/'visuals_silent.mp4'),str(O/'narration.wav'),str(F)],check=True,timeout=600)
 info=json.loads(subprocess.check_output([str(mux),'inspect',str(F)],text=True))
 assert info['audioTracks']==1 and info['videoTracks']==1 and 300<info['duration']<600
 cap=cv2.VideoCapture(str(F));expected=int(cap.get(cv2.CAP_PROP_FRAME_COUNT));decoded=0;std=[]
 while True:
  ok,frame=cap.read()
  if not ok:break
  if decoded%(b.FPS*10)==0:std.append(float(frame.std()))
  decoded+=1
 cap.release();assert decoded==expected and decoded>=n-2 and min(std)>10
 audio=json.loads(subprocess.check_output([str(P/'data/presentations/urop_explainer_20261028/verify_audio'),str(F)],text=True))
 thumb=Image.new('RGB',(1920,1350),'white');cap=cv2.VideoCapture(str(F))
 for i,c in enumerate(chapters):
  cap.set(cv2.CAP_PROP_POS_MSEC,(c['start']+min(4,(c['end']-c['start'])/2))*1000);ok,fr=cap.read();assert ok
  thumb.paste(Image.fromarray(cv2.cvtColor(fr,cv2.COLOR_BGR2RGB)).resize((480,270)),((i%4)*480,(i//4)*270))
 cap.release();thumb.save(O/'contact_sheet.jpg',quality=92)
 buttons=''.join(f'<button onclick="jump({c["start"]:.3f})"><span>{int(c["start"])//60:02d}:{int(c["start"])%60:02d}</span>{html.escape(c["title"])}</button>' for c in chapters)
 watch=(b.D/'watch_video.html').read_text()
 import re
 watch=watch.replace('urop_explainer_20261028/UROP_Beginner_to_Architecture.mp4','urop_elevenlabs_20261028/UROP_Beginner_to_Architecture_ElevenLabs.mp4')
 watch=watch.replace('9 min 49 sec · English narration',f'{int(info["duration"])//60} min {int(info["duration"])%60:02d} sec · ElevenLabs Alice narration')
 watch=watch.replace('href="faculty_questions.md"','href="../english_basic/faculty_questions.md"')
 watch=re.sub(r'<section>.*?</section>','<section>'+buttons+'</section>',watch,flags=re.S)
 (D/'watch_video.html').write_text(watch)
 receipt={'status':'decoded_complete_pending_visual_review','voice':'Alice — Clear, Engaging Educator','voice_id':'Xb7hH8MSUJpSbSDYk0k2','model_id':'eleven_multilingual_v2','provider':'ElevenLabs via Composio authorized connection','provider_settings':{'stability':.65,'similarity_boost':.75,'style':0,'use_speaker_boost':True,'speed':1.08,'seed':42},'caption_alignment':'provider original-text character timestamps, scaled by pitch-preserving audio tempo factor','audio_processing':tm['audio_processing'],'duration_seconds':info['duration'],'dimensions':[1920,1080],'fps':24,'chapters':18,'output':str(F.relative_to(P)),'bytes':F.stat().st_size,'sha256':hashlib.sha256(F.read_bytes()).hexdigest(),'video_decode':{'decoded_frames':decoded,'container_frames':expected,'sampled_frame_std_min':min(std)},'audio_decode':audio,'maximum_caption_lines':maxlines,'storyboard_sha256':hashlib.sha256((b.D/'storyboard.json').read_bytes()).hexdigest(),'original_video_preserved':True,'devmotion_render':False,'model_or_dataset_changes':False,'timing':str((O/'timing.json').relative_to(P))}
 (D/'video_verification.json').write_text(json.dumps(receipt,indent=2)+'\n')
 print(json.dumps(receipt),flush=True)

if __name__=='__main__':main()
