"""Independent media decoding and storyboard readback; no generation/inference."""
from pathlib import Path
import cv2,json,subprocess,hashlib,datetime,time
from PIL import Image
P=Path(__file__).resolve().parent
ROOT=P.parents[2]
def main():
 video=P/'UROP_Telugu_English_Bella.mp4';timeline=json.loads((P/'src/timeline.json').read_text())
 cap=cv2.VideoCapture(str(video));assert cap.isOpened();n=int(cap.get(cv2.CAP_PROP_FRAME_COUNT));fps=cap.get(cv2.CAP_PROP_FPS);w=int(cap.get(cv2.CAP_PROP_FRAME_WIDTH));h=int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT));assert (w,h)==(1920,1080) and fps==30
 count=0;std=[];tic=time.monotonic()
 while True:
  ok,frame=cap.read()
  if not ok:break
  if count%90==0:std.append(float(frame.std()))
  count+=1
 cap.release();assert count==n and min(std)>10 and abs(n/fps-timeline['duration'])<.05
 native=ROOT/'data/presentations/urop_explainer_20261028/verify_audio'
 audio=json.loads(subprocess.check_output([str(native),str(video)],text=True));assert audio['status']=='passed_full_encoded_audio_decode'
 cap=cv2.VideoCapture(str(video));sheet=Image.new('RGB',(1920,1080),'white')
 for i,s in enumerate(timeline['scenes']):
  t=s['start']+s['audioDuration']*.72
  cap.set(cv2.CAP_PROP_POS_MSEC,t*1000);ok,frame=cap.read();assert ok
  tile=Image.fromarray(cv2.cvtColor(frame,cv2.COLOR_BGR2RGB));tile.save(P/f'rendered/final_scene_{i}.png');sheet.paste(tile.resize((640,360)),((i%3)*640,(i//3)*360))
 cap.release();sheet.save(P/'rendered/final_contact_sheet.png')
 receipt=json.loads((P/'evidence/PRODUCTION_RECEIPT.json').read_text());receipt.update({'status':'decoded_complete_pending_final_visual_review','verified_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'output':'UROP_Telugu_English_Bella.mp4','bytes':video.stat().st_size,'sha256':hashlib.sha256(video.read_bytes()).hexdigest(),'duration_seconds':n/fps,'video_decode':{'all_frames':count,'container_frames':n,'sampled_frame_std_min':min(std),'elapsed_seconds':time.monotonic()-tic},'audio_decode':audio})
 (P/'evidence/PRODUCTION_RECEIPT.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:receipt[k] for k in ['status','sha256','duration_seconds','bytes','video_decode','audio_decode']}),flush=True)
if __name__=='__main__':main()
