"""Align editorial cue meanings to source words, then replace the subtitle plate once."""
import json,re,shutil,subprocess,sys
from pathlib import Path
from difflib import SequenceMatcher
from render_motion_revision import char_times,fraction_time,font,lines,ASS,ass_time,vtt_time,norm
from promotion_motion_editorial import editorial
from display_captions import assert_display_numbers,display_text
r=Path(sys.argv[1]);timeline=json.loads((r/'timeline.json').read_text());ed=editorial();cues=[];events=[];fallbacks=[]
PHRASES={(22,3):'마감을 늦출 수 있을까요',(59,1):'첫 번째는',(96,1):'모든 회사에서',(96,2):'그래도 막연한 불안이',(109,1):'다만 우리가',(109,2):'임원이 되고 싶은가'}
for cut in timeline['paragraphs']:
    n=cut['index'];asr=json.loads((r/'asr'/f'{n:03}.json').read_text());target,times,_=char_times(cut['text'],asr['words'],asr['duration']);previous=0;starts=[.03];records=[]
    for i,cue in enumerate(ed[n]['captions'][1:],1):
        text=norm(cue);blocks=SequenceMatcher(None,target,text,autojunk=False).get_matching_blocks()
        candidates=[b for b in blocks if b.size>=2 and b.a>previous+4 and b.b<=len(text)*.5]
        if (n,i) in PHRASES:
            position=target.find(norm(display_text(PHRASES[(n,i)])));assert position>=0;method='reviewed explicit source phrase / ASR'
        elif candidates and sum(b.size for b in blocks)>=min(6,len(text)*.45):
            chosen=min(candidates,key=lambda b:(b.b,b.a));position=chosen.a;method='editorial source phrase / ASR character timing'
        else:
            position=round(i*len(target)/len(ed[n]['captions']));method='source character fraction fallback';fallbacks.append(dict(index=n,cue=i))
        nearby=min(times,key=lambda k:abs(k-position));start=times[nearby][0]
        if start<=starts[-1]+.25:
            position=round(i*len(target)/len(ed[n]['captions']));start=fraction_time(i/len(ed[n]['captions']),target,times,asr['duration']);method='monotonic source fraction fallback';fallbacks.append(dict(index=n,cue=i))
        assert start>starts[-1]+.1 and start<asr['duration'];starts.append(start);previous=position;records.append(dict(cue=i,source_position=position,source_context=target[max(0,position-5):position+30],method=method,start=start))
    starts.append(asr['duration'])
    for i,text in enumerate(ed[n]['captions']):
        assert_display_numbers(text);rows=lines(text,font(50.6),1620);assert len(rows)<=2
        value='\n'.join(rows);start=cut['start']+starts[i];end=cut['start']+starts[i+1];assert end>start
        cues.append(dict(index=n,start=start,end=end,text=value,local_start=starts[i],local_end=starts[i+1],source_anchors=records))
        safe=value.replace('\n',r'\N').replace('{','').replace('}','');events.append(f'Dialogue: 0,{ass_time(start)},{ass_time(end)},Caption,,0,0,0,,{safe}')
if not (r/'caption-review-initial.json').exists():shutil.copy2(r/'caption-review.json',r/'caption-review-initial.json')
(r/'editorial.json').write_text(json.dumps(ed,ensure_ascii=False,indent=2))
(r/'caption-review.json').write_text(json.dumps(dict(font='Pretendard SemiBold',font_size=50.6,parent_font_size=46,increase_percent=10,cues=cues,full_narration_unchanged=True,alignment='compact cue meaning anchored in immutable source words / ASR',fallbacks=fallbacks),ensure_ascii=False,indent=2))
(r/'captions-global.ass').write_text(ASS+'\n'.join(events)+'\n')
vtt=['WEBVTT','']
for cue in cues:vtt.extend([f'{vtt_time(cue["start"])} --> {vtt_time(cue["end"])}',cue['text'],''])
(r/'captions.vtt').write_text('\n'.join(vtt))
print(json.dumps({'cues':len(cues),'fallbacks':len(fallbacks),'anchors':{n:[{'start':c['local_start'],'text':c['text']} for c in cues if c['index']==n] for n in [33,41]}},ensure_ascii=False),flush=True)
if '--check-only' in sys.argv:raise SystemExit()
source=r/'narrated-initial-captions.mkv'
if not source.exists():(r/'narrated.mkv').rename(source)
graph=f'drawbox=x=0:y=920:w=1920:h=160:color=0x163544:t=fill,ass={r}/captions-global.ass:fontsdir=/app/app/assets/fonts'
result=subprocess.run(['ffmpeg','-v','error','-y','-i',str(source),'-vf',graph,'-map','0:v','-map','0:a','-map_metadata','0','-map_chapters','0','-c:v','libx264','-preset','veryfast','-crf','20','-threads','6','-pix_fmt','yuv420p','-c:a','copy',str(r/'narrated.mkv')],capture_output=True,text=True)
if result.returncode:raise RuntimeError(result.stderr[-3000:])
print(json.dumps({'semantic_captions_complete':True}),flush=True)
