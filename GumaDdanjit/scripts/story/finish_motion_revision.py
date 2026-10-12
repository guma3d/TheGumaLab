"""Mix half-amplitude legacy BGM, verify every cut/frame, and preserve review evidence."""
import array,hashlib,json,math,subprocess,sys,wave
from pathlib import Path
from PIL import Image,ImageDraw
from concurrent.futures import ThreadPoolExecutor
from app.core import bgm
root=Path(sys.argv[1]);movie=root/'final.mp4';timeline=json.loads((root/'timeline.json').read_text());voices=json.loads((root/'voice-manifest.json').read_text());caps=json.loads((root/'caption-review.json').read_text())
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2))
def run(args):
    p=subprocess.run(args,capture_output=True,text=True)
    if p.returncode:raise RuntimeError(p.stderr[-3000:])
    return p
seconds=timeline['duration'];music,track=bgm.select({'bgm_track':'Carefree'})
old_mix=json.loads((root.parent/'promotion-v1/production-review.json').read_text())
music_gain=old_mix['music_gain_db']+20*math.log10(.5)
voice_level=bgm.measure_audio(root/'narration.wav',seconds)
music_level=bgm.measure_audio(music,seconds,loop=True,gain_db=music_gain)
remaining=10**(-1.5/20)-10**(music_level['true_peak_dbfs']/20)
voice_gain=min(-16-voice_level['integrated_lufs'],20*math.log10(remaining)-voice_level['true_peak_dbfs'])
assert voice_level['integrated_lufs']+voice_gain-music_level['integrated_lufs']>=8
graph=f'[0:a]aresample=48000,aformat=channel_layouts=stereo,volume={voice_gain}dB[v];[1:a]aresample=48000,aformat=channel_layouts=stereo,atrim=duration={seconds},asetpts=PTS-STARTPTS,volume={music_gain}dB[m];[v][m]amix=inputs=2:duration=first:normalize=0[a]'
run(['ffmpeg','-v','error','-y','-i',str(root/'narrated.mkv'),'-stream_loop','-1','-i',str(music),'-filter_complex',graph,'-map','0:v','-map','[a]','-map_metadata','0','-map_chapters','0','-c:v','copy','-c:a','aac','-b:a','192k','-ar','48000','-ac','2','-t',str(seconds),'-movflags','+faststart',str(movie)])
run(['ffmpeg','-v','error','-y','-i',str(root/'narration.wav'),'-af',f'volume={voice_gain}dB','-ac','2','-b:a','192k',str(root/'narration-master.mp3')])
run(['ffmpeg','-v','error','-y','-i',str(root/'narration.wav'),'-af',f'volume={voice_gain}dB','-ac','2','-c:a','pcm_s16le',str(root/'voice-stem.wav')])
run(['ffmpeg','-v','error','-y','-stream_loop','-1','-i',str(music),'-t',str(seconds),'-af',f'volume={music_gain}dB','-ar','48000','-ac','2','-c:a','pcm_s16le',str(root/'music-stem.wav')])
final_level=bgm.measure_audio(movie,seconds);assert final_level['true_peak_dbfs']<=-1
probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-show_chapters','-of','json',str(movie)]));v=next(x for x in probe['streams'] if x['codec_type']=='video')
assert (v['width'],v['height'],v['r_frame_rate'])==(1920,1080,'30/1') and len(probe['chapters'])==12
assert abs(float(probe['format']['duration'])-seconds)<.1
final=root/'final-audio.wav';run(['ffmpeg','-v','error','-y','-i',str(movie),'-vn','-ar','48000','-ac','2','-c:a','pcm_s16le',str(final)])
def samples(p):
    with wave.open(str(p),'rb') as f:return array.array('h',f.readframes(f.getnframes()))
a=samples(final);voice=samples(root/'voice-stem.wav');music_pcm=samples(root/'music-stem.wav');reviews=[]
folder=root/'final-cuts';folder.mkdir(exist_ok=True)
for cut,selected in zip(timeline['paragraphs'],voices):
    n=cut['index'];alignment=json.loads((root/'asr'/f'{n:03}.json').read_text());assert alignment['source_sha256']==selected['original_sha256'] and sha(root/selected['file'])==selected['audio_sha256']
    first=round(cut['start']*48000)*2;last=round((cut['start']+cut['speech_seconds'])*48000)*2
    aa=a[first:last:16];expected=[x+y for x,y in zip(voice[first:last:16],music_pcm[first:last:16])]
    corr=sum(x*y for x,y in zip(aa,expected))/math.sqrt(sum(x*x for x in aa)*sum(y*y for y in expected));assert corr>.97,(n,corr)
    out=folder/f'{n:03}.wav'
    with wave.open(str(out),'wb') as f:f.setnchannels(2);f.setsampwidth(2);f.setframerate(48000);f.writeframes(a[first:last].tobytes())
    level=bgm.measure_audio(out,cut['speech_seconds']);assert level['true_peak_dbfs']<=-1 and level['integrated_lufs']>=-25
    processed=alignment['processed_measurement'];separation=processed['lufs']+voice_gain-music_level['integrated_lufs'];assert separation>=6,(n,separation)
    reviews.append(dict(index=n,source_sha256=alignment['source_sha256'],processed_sha256=alignment['audio_sha256'],tts_job_id=selected['tts_job_id'],reuse_source=selected.get('reuse_source'),source=alignment['source_measurement'],processed=processed,final=level,voice_to_music_lu_difference=separation,final_mix_cosine=corr,trim_start=alignment['trim_start'],trim_end=alignment['trim_end'],human_listening_completed=False))
save(root/'cut-audio-review.json',reviews);print(json.dumps({'audio_checked':len(reviews)}),flush=True)
logo=Image.open(root/'logo-layer.png').convert('RGBA');box=logo.getbbox();crop=logo.crop(box);width,height=crop.size;pixels=list(crop.getdata());opaque=[i for i,p in enumerate(pixels) if p[3]==255]
count=min(800,len(opaque));chosen=[opaque[k*(len(opaque)-1)//(count-1)] for k in range(count)];test=[(i*3+c,pixels[i][c]) for i in chosen for c in range(3)]
cmd=['ffmpeg','-v','error','-threads','2','-i',str(movie),'-vf',f'crop={width}:{height}:{box[0]}:{box[1]}:exact=1','-filter_threads','1','-pix_fmt','rgb24','-f','rawvideo','-'];frames=0;bad=[];worst=0
with (root/'logo-decode.log').open('wb') as log:
    process=subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=log)
    while True:
        raw=process.stdout.read(width*height*3)
        if not raw:break
        assert len(raw)==width*height*3
        error=sum(abs(raw[ix]-val) for ix,val in test)/len(test);worst=max(worst,error)
        if error>25:bad.append(frames)
        frames+=1
    assert process.wait()==0
assert frames==int(v['nb_frames']) and not bad
review=root/'encoded-review';review.mkdir(exist_ok=True)
def snapshot(cut):
    run(['ffmpeg','-v','error','-threads','2','-y','-ss',str(cut['start']+cut['duration']/2),'-i',str(movie),'-frames:v','1','-q:v','2','-update','1',str(review/f'cut-{cut["index"]:03}.jpg')])
with ThreadPoolExecutor(max_workers=2) as pool:list(pool.map(snapshot,timeline['paragraphs']))
strips=Image.new('RGB',(1920,24*36),'white')
for page in range(6):
    sheet=Image.new('RGB',(1920,960),'white');d=ImageDraw.Draw(sheet)
    for k,cut in enumerate(timeline['paragraphs'][page*20:(page+1)*20]):
        n=cut['index'];im=Image.open(review/f'cut-{n:03}.jpg');x=k%5*384;y=k//5*240;sheet.paste(im.resize((384,216)),(x,y));d.text((x+4,y+219),str(n),fill='black')
        j=n-1;strips.paste(im.crop((0,900,1920,1080)).resize((384,36)),(j%5*384,j//5*36))
    sheet.save(review/f'sheet-{page+1:02}.jpg',quality=94)
strips.save(review/'caption-strips.jpg',quality=96)
motions=[json.loads((root/'motion'/f'{n:03}/motion.json').read_text()) for n in range(1,115)]
motion_review=dict(cuts=len(motions),image_camera_moves=sum(x['motion']['zoom_end']>1 for x in motions),animated_layers=sum(len(x['layers']) for x in motions),animated_numeric_values=sum(not q['static'] for x in motions for q in x['numbers']),numeric_anchors_verified=all(q['anchor_aligned'] for x in motions for q in x['numbers'] if not q['static']),keyword_font='Do Hyeon',rendered_counter_endpoints_pending_visual_inspection=True)
report=dict(version=5,script_version=9,script_sha256=sha(root/'script.json'),video_sha256=sha(movie),duration=seconds,tts_provider='gemini',tts_model='gemini-3.8-flash-tts',tts_voice='Zephyr',voice_production=json.loads((root/'voice-production.json').read_text()),bgm_enabled=True,track=track,music_gain_db=music_gain,reference_music_gain_db=old_mix['music_gain_db'],music_amplitude_ratio=.5,music_reduction_db=20*math.log10(.5),music_measurement=music_level,voice_gain_db=voice_gain,voice_measurement=voice_level,final_measurement=final_level,ducking=False,speech_tempo=1,pitch_shift=False,motion=motion_review,captions=dict(font='Pretendard SemiBold',size=50.6,parent_size=46,increase_percent=10,cue_count=len(caps['cues']),compact=True),logo=dict(all_frames_checked=frames,failed_frames=len(bad),worst_mae=worst),technical_review=dict(audio_cuts_checked=114,final_mix_matches_stems=True,chapters=12,width=1920,height=1080,fps=30),visual_review='pending encoded contact sheets and counter endpoints',human_listening_completed=False,user_accepted=False)
save(root/'production-review.json',report);print(json.dumps({'final':str(movie),'duration':seconds,'logo_frames':frames,'voice_to_bgm_lu':voice_level['integrated_lufs']+voice_gain-music_level['integrated_lufs']}),flush=True)
