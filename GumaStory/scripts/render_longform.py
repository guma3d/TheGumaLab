"""Render exact paragraph audio, readable captions, chapters and licensed music."""
import json, sys, subprocess, re, wave, math, hashlib, array
from pathlib import Path
from app.core import bgm
from longform_audio import mix

root=Path(sys.argv[1]);fonts=Path('/app/app/assets/fonts')
script=json.loads((root/'script.json').read_text(encoding='utf-8'))
voices=json.loads((root/'voice-manifest.json').read_text(encoding='utf-8'))
visual=json.loads((root/'visual-plan.json').read_text(encoding='utf-8'))
assert len(voices)==len(visual)==114
def run(args):
    p=subprocess.run(args,capture_output=True,text=True)
    if p.returncode:raise RuntimeError(p.stderr[-2500:])
    return p
def dur(file):return float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','default=noprint_wrappers=1:nokey=1',str(file)]))
def digest(file):
    with open(file,'rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def ass_time(t):
    cs=round(t*100);return f'{cs//360000}:{cs//6000%60:02}:{cs//100%60:02}.{cs%100:02}'
def vtt_time(t):
    ms=round(t*1000);return f'{ms//3600000:02}:{ms//60000%60:02}:{ms//1000%60:02}.{ms%1000:03}'
def caption_groups(text):
    words=text.split();lines=[];line=''
    for w in words:
        trial=(line+' '+w).strip()
        if len(trial)>31 and line:lines.append(line);line=w
        else:line=trial
    if line:lines.append(line)
    return ['\n'.join(lines[i:i+2]) for i in range(0,len(lines),2)]

(root/'processed').mkdir(exist_ok=True)
segments=[]
for v in voices:
    file=root/v['file'];raw=file.with_suffix('.wav')
    with wave.open(str(raw),'rb') as w:
        assert w.getnchannels()==1 and w.getsampwidth()==2
        rate=w.getframerate();samples=array.array('h',w.readframes(w.getnframes()))
    step=rate//100
    active=[i for i in range(0,len(samples),step) if math.sqrt(sum(s*s for s in samples[i:i+step])/max(1,len(samples[i:i+step])))>75]
    assert active
    first=max(0,active[0]-int(rate*.1));last=min(len(samples),active[-1]+step+int(rate*.18))
    trimmed=root/'processed'/f'{v["index"]:03}-trim.wav'
    with wave.open(str(trimmed),'wb') as w:
        w.setnchannels(1);w.setsampwidth(2);w.setframerate(rate);w.writeframes(samples[first:last].tobytes())
    segments.append(dict(v,trimmed=str(trimmed),trim_start=first/rate,trim_end=(len(samples)-last)/rate,raw_seconds=(last-first)/rate))
raw_total=sum(x['raw_seconds'] for x in segments)
# A modest global tempo adjustment, never long filler silence to hit a target.
tempo=max(1.0,min(1.08,raw_total/(1200-len(segments)*.28-2)))
timeline=[];cursor=0;chapters=[];all_pcm=[]
for s in segments:
    file=root/'processed'/f'{s["index"]:03}.wav'
    run(['ffmpeg','-v','error','-y','-i',s['trimmed'],'-af',f'atempo={tempo:.6f}','-ar','48000','-ac','1',str(file)])
    with wave.open(str(file),'rb') as w: pcm=w.readframes(w.getnframes());sr=w.getframerate()
    speech=len(pcm)/2/sr;seconds=math.ceil((speech+.28)*30)/30
    padding=round(seconds*sr)-len(pcm)//2;all_pcm.append(pcm+b'\0\0'*padding)
    if not chapters or chapters[-1]['scene']!=s['scene']:chapters.append(dict(scene=s['scene'],title=script['scenes'][s['scene']-1]['title'],start=cursor))
    timeline.append(dict(s,start=cursor,end=cursor+seconds,speech_seconds=speech,duration=seconds))
    cursor+=seconds
# Short end hold, no duplicate narration.
timeline[-1]['end']+=2;timeline[-1]['duration']+=2;cursor+=2;all_pcm.append(b'\0\0'*96000)
voice_wav=root/'narration.wav'
with wave.open(str(voice_wav),'wb') as w:
    w.setnchannels(1);w.setsampwidth(2);w.setframerate(48000)
    for p in all_pcm:w.writeframes(p)
run(['ffmpeg','-v','error','-y','-i',str(voice_wav),'-c:a','libmp3lame','-b:a','192k',str(root/'narration.mp3')])
events=[];vtt=['WEBVTT',''];metadata=[';FFMETADATA1','title='+script['title']]
for c,nextc in zip(chapters,chapters[1:]+[dict(start=cursor)]):
    c['end']=nextc['start'];metadata.extend(['[CHAPTER]','TIMEBASE=1/1000',f'START={round(c["start"]*1000)}',f'END={round(c["end"]*1000)}','title='+c['title']])
for s in timeline:
    groups=caption_groups(s['text']);weights=[len(re.sub(r'\s','',g)) for g in groups];total=sum(weights);t=s['start']+.03
    for g,weight in zip(groups,weights):
        end=min(s['start']+s['speech_seconds'],t+s['speech_seconds']*weight/total)
        safe=g.replace('{','').replace('}','').replace('\n',r'\N')
        # Shared two-outline style. Brief entry pop, then fixed placement.
        for layer,style in [(0,'Outer'),(1,'Caption')]:
            events.append(f'Dialogue: {layer},{ass_time(t)},{ass_time(end)},{style},,0,0,0,,{{\\fscx104\\fscy104\\t(0,120,\\fscx100\\fscy100)}}{safe}')
        vtt.extend([f'{vtt_time(t)} --> {vtt_time(end)}',g,'']);t=end
ass='''[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 2
ScaledBorderAndShadow: yes
[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Outer,Maplestory,52,&H00FFFFFF,&H00FFFFFF,&H00FFFFFF,&H00000000,-1,0,0,0,100,100,0,0,1,7,0,2,70,70,38,1
Style: Caption,Maplestory,52,&H00FFFFFF,&H00FFFFFF,&H00151515,&H00000000,-1,0,0,0,100,100,0,0,1,4,0,2,70,70,38,1
[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
'''+ '\n'.join(events)+'\n'
(root/'captions.ass').write_text(ass,encoding='utf-8');(root/'captions.vtt').write_text('\n'.join(vtt),encoding='utf-8')
(root/'chapters.txt').write_text('\n'.join(metadata),encoding='utf-8')
concat=['ffconcat version 1.0']
for s in timeline:
    concat.extend([f"file '{root}/frames/{s['index']:03}.png'",f'duration {s["duration"]:.9f}'])
concat.append(f"file '{root}/frames/{timeline[-1]['index']:03}.png'")
(root/'frames.txt').write_text('\n'.join(concat),encoding='utf-8')
(root/'timeline.json').write_text(json.dumps(dict(duration=cursor,tempo=tempo,chapters=chapters,paragraphs=timeline,caption_alignment='paragraph audio boundaries; within-paragraph reading-weight estimates'),ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'stage':'render','duration':cursor,'tempo':tempo,'paragraphs':len(timeline)}),flush=True)
silent=root/'narrated.mp4'
with (root/'render.log').open('w') as log:
    subprocess.run(['ffmpeg','-hide_banner','-y','-f','concat','-safe','0','-i',str(root/'frames.txt'),'-i',str(voice_wav),'-i',str(root/'chapters.txt'),'-map','0:v','-map','1:a','-map_metadata','2','-map_chapters','2','-vf',f'fps=30,ass={root}/captions.ass:fontsdir={fonts},format=yuv420p','-t',str(cursor),'-c:v','libx264','-preset','veryfast','-tune','stillimage','-crf','20','-threads','6','-c:a','aac','-b:a','192k','-ar','48000','-movflags','+faststart',str(silent)],stdout=log,stderr=log,check=True)
boardfile=root/'music-selection.json'
if boardfile.exists():board=json.loads(boardfile.read_text())
else:
    board={};bgm.assign_random(board);boardfile.write_text(json.dumps(board,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'stage':'mix','music':board['bgm_track']}),flush=True)
review=mix(silent,root/'final.mp4',board)
review.update(duration=cursor,tempo=tempo,script_version=script['version'],script_sha256=digest(root/'script.json'),video_sha256=digest(root/'final.mp4'),caption_timing='paragraph-synchronous; intra-paragraph estimated',visual_review='all composition contact sheets and encoded samples',listened_to_audio=False)
review['tts_models']=sorted({v['model'] for v in voices})
(root/'production-review.json').write_text(json.dumps(review,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'complete':True,'duration':cursor,'video_sha256':review['video_sha256']}),flush=True)
