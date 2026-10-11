"""Render clean scenes with per-cut local narration, numeric captions, and no BGM."""
import array,hashlib,json,math,subprocess,sys,wave
from pathlib import Path
from app.core import bgm
from longform_audio import mix

root=Path(sys.argv[1]).resolve();fonts=Path('/app/app/assets/fonts')
if (root.parents[1]/'imports/promotion-film-v3.json').exists():raise SystemExit('Published version is immutable.')
script=json.loads((root/'script.json').read_text());voices=json.loads((root/'voice-manifest.json').read_text())
assert len(voices)==114
assert json.loads((root/'music-selection.json').read_text())['bgm_enabled'] is False
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf-8')
def run(args):
    p=subprocess.run(args,capture_output=True,text=True)
    if p.returncode:raise RuntimeError(p.stderr[-3000:])
    return p
prepared_files=['script.json','voice-manifest.json','timeline.json','captions.ass','narration.wav','logo-layer.png','chapters.txt','frames.txt']+[f'frames/{n:03}.png' for n in range(1,115)]
if '--encode-only' not in sys.argv[2:]:
    processed=root/'processed';processed.mkdir(exist_ok=True)
    timeline=[];chapters=[];cursor=0;pcm_all=[];cut_checks=[]
    for voice in voices:
        source=root/voice['file'];meta=json.loads(source.with_suffix('.tts.json').read_text())
        assert voice['model']=='qwen-design-1.7b' and voice['voice']=='M5' and meta['provider']=='local'
        assert sha(source)==voice['audio_sha256'] and sha(source.with_suffix('.wav'))==meta['original_sha256']
        decoded=processed/f'{voice["index"]:03}-decoded.wav'
        run(['ffmpeg','-v','error','-y','-i',str(source),'-ar','48000','-ac','1','-c:a','pcm_s16le',str(decoded)])
        with wave.open(str(decoded),'rb') as w:samples=array.array('h',w.readframes(w.getnframes()));rate=w.getframerate()
        step=480;active=[i for i in range(0,len(samples),step) if math.sqrt(sum(s*s for s in samples[i:i+step])/len(samples[i:i+step]))>75]
        assert active, f'Silent cut {voice["index"]}'
        first=max(0,active[0]-4800);last=min(len(samples),active[-1]+step+8640)
        pcm=samples[first:last].tobytes();speech=len(pcm)/2/rate
        path=processed/f'{voice["index"]:03}.wav'
        with wave.open(str(path),'wb') as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(rate);w.writeframes(pcm)
        seconds=math.ceil((speech+.28)*30)/30
        pcm_all.append(pcm+b'\0\0'*(round(seconds*rate)-len(pcm)//2))
        if not chapters or chapters[-1]['scene']!=voice['scene']:chapters.append(dict(scene=voice['scene'],title=script['scenes'][voice['scene']-1]['title'],start=cursor))
        timeline.append(dict(voice,start=cursor,end=cursor+seconds,speech_seconds=speech,duration=seconds,trim_start=first/rate,trim_end=(len(samples)-last)/rate,processed_file=f'processed/{voice["index"]:03}.wav'))
        level=bgm.measure_audio(path,speech)
        assert level['true_peak_dbfs']<=-1 and level['integrated_lufs']>=-22,level
        cut_checks.append(dict(index=voice['index'],source=meta['normalization']['input'],normalized=meta['normalization']['output'],processed=level,trim_start=first/rate,trim_end=(len(samples)-last)/rate,peak_sample=max(abs(s) for s in samples[first:last]),silent=False,listened=False))
        cursor+=seconds
    timeline[-1]['end']+=2;timeline[-1]['duration']+=2;cursor+=2;pcm_all.append(b'\0\0'*96000)
    for c,nextc in zip(chapters,chapters[1:]+[dict(start=cursor)]):c['end']=nextc['start']
    save(root/'timeline.json',dict(duration=cursor,tempo=1,chapters=chapters,paragraphs=timeline,caption_alignment='per-cut audio boundaries; intra-cut reading-weight estimates'))
    save(root/'cut-audio-review.json',cut_checks)
    wav=root/'narration.wav'
    with wave.open(str(wav),'wb') as w:
        w.setnchannels(1);w.setsampwidth(2);w.setframerate(48000)
        for pcm in pcm_all:w.writeframes(pcm)
    metadata=[';FFMETADATA1','title='+script['title']]
    for c in chapters:metadata.extend(['[CHAPTER]','TIMEBASE=1/1000',f'START={round(c["start"]*1000)}',f'END={round(c["end"]*1000)}','title='+c['title']])
    (root/'chapters.txt').write_text('\n'.join(metadata),encoding='utf-8')
    run([sys.executable,str(root/'tools/compose_promotion_v3.py'),str(root)])
    concat=['ffconcat version 1.0']
    for cut in timeline:concat.extend([f"file '{root}/frames/{cut['index']:03}.png'",f'duration {cut["duration"]:.9f}'])
    concat.append(f"file '{root}/frames/{timeline[-1]['index']:03}.png'")
    (root/'frames.txt').write_text('\n'.join(concat),encoding='utf-8')
    save(root/'prepared-inputs.json',{name:sha(root/name) for name in prepared_files})
else:
    prepared=json.loads((root/'prepared-inputs.json').read_text())
    assert all(sha(root/name)==prepared[name] for name in prepared_files),'Prepared inputs changed; rebuild before encoding.'
    timeline=json.loads((root/'timeline.json').read_text());cursor=timeline['duration'];timeline=timeline['paragraphs'];wav=root/'narration.wav'
print(json.dumps({'stage':'render','duration':cursor,'cuts':len(timeline),'bgm_enabled':False,'static_logo':'single frame repeatlast'}),flush=True)
source=root/'narrated.mkv'
graph=f'[0:v]fps=30,ass={root}/captions.ass:fontsdir={fonts}[captioned];[captioned][2:v]overlay=0:0:format=auto:eof_action=repeat:repeatlast=1:shortest=0,format=yuv420p[v]'
with (root/'render.log').open('w') as log:
    subprocess.run(['ffmpeg','-hide_banner','-y','-threads','1','-f','concat','-safe','0','-i',str(root/'frames.txt'),'-i',str(wav),'-threads','1','-i',str(root/'logo-layer.png'),'-i',str(root/'chapters.txt'),'-filter_complex_threads','2','-filter_complex',graph,'-map','[v]','-map','1:a','-map_metadata','3','-map_chapters','3','-t',str(cursor),'-c:v','libx264','-preset','veryfast','-tune','stillimage','-crf','20','-threads','4','-c:a','pcm_s16le',str(source)],stdout=log,stderr=log,check=True)
review=mix(source,root/'final.mp4',{'bgm_enabled':False})
review.update(duration=cursor,tempo=1,script_version=script['version'],script_sha256=sha(root/'script.json'),video_sha256=sha(root/'final.mp4'),tts_models=['qwen-design-1.7b'],tts_voice='M5',human_listening_completed=False,visual_review='pending encoded-frame inspection',caption_timing='per-cut boundaries; intra-cut reading-weight estimate')
save(root/'production-review.json',review)
print(json.dumps({'complete':True,'duration':cursor,'video_sha256':review['video_sha256']}),flush=True)
