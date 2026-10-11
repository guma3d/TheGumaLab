"""Verify v2's exact audio reuse, all-frame logo, display numerals and decoded cuts."""
import hashlib,json,subprocess,sys
from pathlib import Path
from PIL import Image
from display_captions import display_text,assert_display_numbers

root=Path(sys.argv[1]);parent=root.parent/'promotion-v1';movie=root/'final.mp4'
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def audio_hash(p):
    return subprocess.check_output(['ffmpeg','-v','error','-i',str(p),'-map','0:a:0','-c:a','copy','-f','hash','-hash','sha256','-'],text=True).strip()
before=audio_hash(parent/'final.mp4');after=audio_hash(movie);assert before==after
timeline=json.loads((root/'timeline.json').read_text())
script=json.loads((root/'script.json').read_text())
assert ''.join(p['text'] for p in timeline['paragraphs'])==''.join(s['narration'].replace('\n\n','') for s in script['scenes'])
caps=json.loads((root/'caption-review.json').read_text());assert len(caps['cues'])>114
for p in timeline['paragraphs']:
    cues=[c for c in caps['cues'] if c['index']==p['index']]
    assert ''.join(''.join(c['text'].split()) for c in cues)==''.join(display_text(p['text']).split())
    for c in cues:
        assert_display_numbers(c['text']);assert len(c['text'].splitlines())<=2
        assert p['start']<=c['start']<c['end']<=p['start']+p['speech_seconds']+.01
ass=(root/'captions.ass').read_text();assert 'Maplestory' not in ass and '\\fscx' not in ass
probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-show_chapters','-of','json',str(movie)]))
v=next(s for s in probe['streams'] if s['codec_type']=='video')
assert (v['width'],v['height'],v['r_frame_rate'])==(1920,1080,'30/1')
assert abs(float(probe['format']['duration'])-timeline['duration'])<.15 and len(probe['chapters'])==12
logo=Image.open(root/'logo-layer.png').convert('RGBA');box=logo.getbbox();crop=logo.crop(box);w,h=crop.size
pixels=list(crop.getdata());opaque=[i for i,p in enumerate(pixels) if p[3]==255];assert len(opaque)>100
sample_count=min(800,len(opaque))
selected=[opaque[k*(len(opaque)-1)//(sample_count-1)] for k in range(sample_count)]
samples=[(i*3+c,pixels[i][c]) for i in selected for c in range(3)]
cmd=['ffmpeg','-v','error','-threads','2','-i',str(movie),'-vf',f'crop={w}:{h}:{box[0]}:{box[1]}:exact=1','-filter_threads','1','-pix_fmt','rgb24','-f','rawvideo','-']
count=0;bad=[];worst=0
with (root/'logo-decode.log').open('wb') as log:
    proc=subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=log)
    while True:
        raw=proc.stdout.read(w*h*3)
        if not raw:break
        assert len(raw)==w*h*3
        error=sum(abs(raw[offset]-expected) for offset,expected in samples)/len(samples)
        worst=max(worst,error)
        if error>25:bad.append(count)
        count+=1
    assert proc.wait()==0
assert count==int(v['nb_frames']) and not bad,(count,bad[:10],worst)
print(json.dumps({'audio_stream_unchanged':True,'logo_frames':count,'logo_worst_mae':worst}),flush=True)
midpoints=[round((p['start']+p['duration']/2)*30) for p in timeline['paragraphs']]
def select(ns):
    if len(ns)==1:return f'eq(n,{ns[0]})'
    m=len(ns)//2;return '('+select(ns[:m])+'+'+select(ns[m:])+')'
folder=root/'encoded-review';folder.mkdir(exist_ok=True)
result=subprocess.run(['ffmpeg','-v','error','-threads','2','-y','-i',str(movie),'-vf',f"select='{select(midpoints)}',scale=384:216,tile=5x4",'-filter_threads','1','-fps_mode','vfr','-threads','2',str(folder/'sheet-%02d.jpg')],capture_output=True,text=True)
assert result.returncode==0 and not result.stderr.strip(),result.stderr[-2000:]
report=dict(video_sha256=sha(movie),parent_video_sha256=sha(parent/'final.mp4'),script_sha256=sha(root/'script.json'),
 duration=timeline['duration'],audio_stream_unchanged=True,audio_stream_sha256=after,new_scene_images=65,
 captions=dict(font='Pretendard SemiBold',size=46,outline=1.3,layers=1,pop=False,numeric_display_verified=True,changed_paragraphs=len(caps['changes']),
 alignment='original paragraph audio boundaries; intra-paragraph reading-weight estimate'),
 logo=dict(all_frames_checked=count,failed_frames=len(bad),worst_mae=worst),
 technical_review=dict(width=1920,height=1080,fps=30,chapter_count=12,paragraph_count=114,approved_script_text_preserved=True,
 encoded_contact_sheets=len(list(folder.glob('sheet-*.jpg'))),decode_error_output=result.stderr),
 image_generation='built-in ImageGen, current character masters as identity references only',
 visual_review='pending final encoded contact-sheet inspection',human_listening_completed=False,
 audio_review='unchanged v1 speech and music; exact compressed audio stream hash matches parent',
 track=json.loads((parent/'production-review.json').read_text())['track'])
(root/'production-review.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report['technical_review']),flush=True)
