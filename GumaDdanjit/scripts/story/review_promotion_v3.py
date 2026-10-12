"""Verify every local audio cut, numeric caption, encoded scene and logo frame."""
import array,hashlib,json,math,subprocess,sys,wave
from prosody_review import production_summary
from pathlib import Path
from PIL import Image
from app.core import bgm
from display_captions import display_text,assert_display_numbers

root=Path(sys.argv[1]);movie=root/'final.mp4'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
timeline=json.loads((root/'timeline.json').read_text());script=json.loads((root/'script.json').read_text())
review=json.loads((root/'production-review.json').read_text());voices=json.loads((root/'voice-manifest.json').read_text())
def audio_hash(path):return subprocess.check_output(['ffmpeg','-v','error','-i',str(path),'-map','0:a:0','-c:a','copy','-f','hash','-hash','sha256','-'],text=True).strip()
parent=root/'superseded-renders/attempt-2/final.mp4'
assert audio_hash(movie)==audio_hash(parent),'Caption revision changed the checked narration stream'
review['audio_stream_unchanged_from_checked_render']=True
assert review['bgm_enabled'] is False and review['track'] is None
assert ''.join(p['text'] for p in timeline['paragraphs'])==''.join(s['narration'].replace('\n\n','') for s in script['scenes'])
assert '가상' not in ''.join(s['narration'] for s in script['scenes'])
caps=json.loads((root/'caption-review.json').read_text())
for p in timeline['paragraphs']:
    cues=[c for c in caps['cues'] if c['index']==p['index']]
    assert ''.join(''.join(c['text'].split()) for c in cues)==''.join(display_text(p['text']).split())
    for c in cues:
        assert_display_numbers(c['text']);assert len(c['text'].splitlines())<=2
        assert p['start']<=c['start']<c['end']<=p['start']+p['speech_seconds']+.01
ass=(root/'captions.ass').read_text();assert 'Maplestory' not in ass and '\\fscx' not in ass
plan=json.loads((root/'visual-plan.json').read_text())
assert len(plan)==114
for cut in plan:
    assert not any(word in label for label in cut['visible_text'] for word in ('가상','설명용','편집자','/ 12','V4'))
    assert sha(root/cut['file'])==cut['frame_sha256']
probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-show_chapters','-of','json',str(movie)]))
v=next(s for s in probe['streams'] if s['codec_type']=='video')
assert (v['width'],v['height'],v['r_frame_rate'])==(1920,1080,'30/1')
assert abs(float(probe['format']['duration'])-timeline['duration'])<.15 and len(probe['chapters'])==12

# Decode the final voice once. Comparison with the narration stem confirms no
# additional music stream/content was introduced and every cut stayed aligned.
decoded=root/'final-voice.wav'
subprocess.run(['ffmpeg','-v','error','-y','-i',str(movie),'-vn','-ar','48000','-ac','2','-c:a','pcm_s16le',str(decoded)],check=True,capture_output=True)
with wave.open(str(decoded),'rb') as w:final=array.array('h',w.readframes(w.getnframes()))
with wave.open(str(root/'narration.wav'),'rb') as w:expected=array.array('h',w.readframes(w.getnframes()))
audio_checks=json.loads((root/'cut-audio-review.json').read_text());final_folder=root/'final-cuts';final_folder.mkdir(exist_ok=True)
for cut,check,voice in zip(timeline['paragraphs'],audio_checks,voices):
    assert cut['index']==voice['index']==check['index']
    meta=json.loads((root/voice['file']).with_suffix('.tts.json').read_text())
    assert meta['provider']=='local' and meta['voice']=='M5' and meta['model']=='qwen-design-1.7b'
    start=round(cut['start']*48000);end=round((cut['start']+cut['speech_seconds'])*48000)
    stereo=final[start*2:end*2];a=stereo[::2];b=expected[start:end];length=min(len(a),len(b));a=a[:length];b=b[:length]
    aa=a[::8];bb=b[::8]
    cosine=sum(x*y for x,y in zip(aa,bb))/math.sqrt(sum(x*x for x in aa)*sum(y*y for y in bb))
    assert cosine>.97, (cut['index'],cosine)
    file=final_folder/f'{cut["index"]:03}.wav'
    with wave.open(str(file),'wb') as w:w.setnchannels(2);w.setsampwidth(2);w.setframerate(48000);w.writeframes(stereo.tobytes())
    level=bgm.measure_audio(file,cut['speech_seconds'])
    assert level['true_peak_dbfs']<=-1 and level['integrated_lufs']>=-22.5,(cut['index'],level)
    assert abs(level['integrated_lufs']-(check['processed']['integrated_lufs']+review['voice_gain_db']))<.6
    check.update(final=level,final_voice_cosine=cosine,clipping_passed=True,bgm_present=False,cut_boundary_preserved=True)
(root/'cut-audio-review.json').write_text(json.dumps(audio_checks,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'audio_cuts_checked':len(audio_checks),'no_bgm_verified':True}),flush=True)

logo=Image.open(root/'logo-layer.png').convert('RGBA');box=logo.getbbox();crop=logo.crop(box);w,h=crop.size
pixels=list(crop.getdata());opaque=[i for i,p in enumerate(pixels) if p[3]==255];assert len(opaque)>100
sample_count=min(800,len(opaque));selected=[opaque[k*(len(opaque)-1)//(sample_count-1)] for k in range(sample_count)]
samples=[(i*3+c,pixels[i][c]) for i in selected for c in range(3)]
cmd=['ffmpeg','-v','error','-threads','2','-i',str(movie),'-vf',f'crop={w}:{h}:{box[0]}:{box[1]}:exact=1','-filter_threads','1','-pix_fmt','rgb24','-f','rawvideo','-']
count=0;bad=[];worst=0
with (root/'logo-decode.log').open('wb') as log:
    proc=subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=log)
    while True:
        raw=proc.stdout.read(w*h*3)
        if not raw:break
        assert len(raw)==w*h*3
        error=sum(abs(raw[offset]-value) for offset,value in samples)/len(samples);worst=max(worst,error)
        if error>25:bad.append(count)
        count+=1
    assert proc.wait()==0
assert count==int(v['nb_frames']) and not bad,(count,bad[:10],worst)
midpoints=[round((p['start']+p['duration']/2)*30) for p in timeline['paragraphs']]
def select(ns):
    if len(ns)==1:return f'eq(n,{ns[0]})'
    m=len(ns)//2;return '('+select(ns[:m])+'+'+select(ns[m:])+')'
folder=root/'encoded-review';folder.mkdir(exist_ok=True)
graph=f"[0:v]select='{select(midpoints)}',split=2[scene][caption];[scene]scale=384:216,tile=5x4[full];[caption]crop=1920:180:0:900,scale=384:36,tile=5x24[strips]"
result=subprocess.run(['ffmpeg','-v','error','-threads','2','-y','-i',str(movie),'-filter_complex_threads','1','-filter_complex',graph,'-map','[full]','-fps_mode','vfr','-threads','2',str(folder/'sheet-%02d.jpg'),'-map','[strips]','-frames:v','1','-fps_mode','vfr','-threads','2',str(folder/'caption-strips.jpg')],capture_output=True,text=True)
assert result.returncode==0 and not result.stderr.strip(),result.stderr[-2000:]
review.update(video_sha256=sha(movie),script_sha256=sha(root/'script.json'),
    captions=dict(font='Pretendard SemiBold',size=46,outline=1.3,layers=1,pop=False,numeric_display_verified=True,changed_paragraphs=len(caps['changes'])),
    logo=dict(all_frames_checked=count,failed_frames=len(bad),worst_mae=worst),
    technical_review=dict(width=1920,height=1080,fps=30,chapter_count=12,paragraph_count=114,script_text_verified=True,encoded_contact_sheets=len(list(folder.glob('sheet-*.jpg'))),audio_cuts_checked=len(audio_checks),no_bgm_verified=True,production_overlays_removed=True,caption_strip_count=len(midpoints)),
    visual_review='pending encoded contact-sheet inspection',human_listening_completed=False)
review['prosody_review'] = production_summary(root)
(root/'production-review.json').write_text(json.dumps(review,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(review['technical_review']),flush=True)
