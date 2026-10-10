"""Technical and visual review evidence; does not claim human listening."""
import json, subprocess, hashlib, sys, re
from pathlib import Path
root=Path(sys.argv[1]);movie=root/'final.mp4';report=json.loads((root/'production-review.json').read_text(encoding='utf-8'))
timeline=json.loads((root/'timeline.json').read_text(encoding='utf-8'));script=json.loads((root/'script.json').read_text(encoding='utf-8'))
probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_format','-show_streams','-show_chapters','-of','json',str(movie)]))
v=next(s for s in probe['streams'] if s['codec_type']=='video');a=next(s for s in probe['streams'] if s['codec_type']=='audio')
assert (v['width'],v['height'],v['r_frame_rate'],v['codec_name'])==(1920,1080,'30/1','h264')
assert a['codec_name']=='aac' and int(a['sample_rate'])==48000
assert abs(float(probe['format']['duration'])-timeline['duration'])<.15
assert len(probe['chapters'])==12
spoken=''.join(x['text'] for x in timeline['paragraphs'])
approved=''.join(s['narration'].replace('\n\n','') for s in script['scenes'])
assert spoken==approved
frames=[round((p['start']+p['duration']/2)*30) for p in timeline['paragraphs']]
selection='+'.join(f'eq(n,{n})' for n in frames)
folder=root/'encoded-review';folder.mkdir(exist_ok=True)
command=['ffmpeg','-v','error','-y','-i',str(movie),'-vf',f"select='{selection}',scale=384:216,tile=5x4",'-fps_mode','vfr',str(folder/'sheet-%02d.jpg')]
result=subprocess.run(command,capture_output=True,text=True,check=True)
report['technical_review']=dict(width=v['width'],height=v['height'],fps=30,video_codec=v['codec_name'],audio_codec=a['codec_name'],duration=float(probe['format']['duration']),chapter_count=len(probe['chapters']),paragraph_count=len(frames),approved_script_text_preserved=True,decode_error_output=result.stderr,encoded_contact_sheets=len(list(folder.glob('sheet-*.jpg'))),human_listening_completed=False)
assert not result.stderr.strip()
(root/'production-review.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report['technical_review']))
