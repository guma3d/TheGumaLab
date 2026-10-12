"""Versioned silence edits and pitch-preserving tempo, with a caption time map."""
import argparse,array,hashlib,json,math,re,shutil,statistics,subprocess,wave
from pathlib import Path
from difflib import SequenceMatcher
from display_captions import display_text,assert_display_numbers
from sentence_pacing import canonical


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def save(path,data):path.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
def run(args):return subprocess.run(args,capture_output=True,text=True,check=True)


def silence_plan(samples,rate,sentences):
    hop=round(rate*.01)
    db=[20*math.log10(math.sqrt(sum(int(x)*int(x) for x in samples[i:i+hop])/len(samples[i:i+hop]))/32768+1e-10) for i in range(0,len(samples),hop)]
    threshold=max(-48,max(db)-35)
    active=[v>threshold for v in db]
    edits=[];start=None
    for i,value in enumerate(active+[True]):
        if not value and start is None:start=i
        if value and start is not None:
            a,b=start*.01,i*.01;duration=b-a
            boundary=any(s['end'] <= (a+b)/2 <= t['start'] for s,t in zip(sentences,sentences[1:]))
            keep=.45 if boundary else .22
            if start==0:keep=.08
            if i==len(active):keep=.14
            required=.65 if boundary else .40
            if start==0 or i==len(active):required=.20
            if duration>required and duration>keep:
                left=round((a+keep/2)*rate);right=round((b-keep/2)*rate)
                left=max(0,left);right=min(len(samples),right)
                # Only frames already measured as quiet may be deleted.
                assert not any(active[left//hop:math.ceil(right/hop)])
                edits.append(dict(start=left/rate,end=right/rate,removed_seconds=(right-left)/rate,
                    quiet_start=a,quiet_end=b,kept_seconds=keep,sentence_boundary=boundary,
                    activity_threshold_dbfs=threshold))
            start=None
    return edits


def compressed_time(value,edits):
    return value-sum(max(0,min(value,e['end'])-e['start']) for e in edits)


def mapped_time(value,edits,pieces):
    compressed=compressed_time(value,edits)
    for piece in pieces:
        if compressed<=piece['input_end']+.00001:
            fraction=max(0,min(1,(compressed-piece['input_start'])/max(.00001,piece['input_end']-piece['input_start'])))
            return piece['output_start']+fraction*(piece['output_end']-piece['output_start'])
    return pieces[-1]['output_end']


def caption_alignment(cues,words):
    target=''.join(canonical(c['text']) for c in cues)
    actual=''.join(canonical(w['text']) for w in words)
    char_times=[]
    for w in words:
        count=len(canonical(w['text']))
        for i in range(count):char_times.append((w['start']+(w['end']-w['start'])*i/count,w['start']+(w['end']-w['start'])*(i+1)/count))
    mapping={}
    for block in SequenceMatcher(None,target,actual,autojunk=False).get_matching_blocks():
        for offset in range(block.size):mapping[block.a+offset]=block.b+offset
    cursor=0;result=[]
    for cue in cues:
        length=len(canonical(cue['text']));positions=[mapping[p] for p in range(cursor,cursor+length) if p in mapping];cursor+=length
        coverage=len(positions)/max(1,length)
        result.append(dict(cue,start=char_times[positions[0]][0] if positions else None,
            end=char_times[positions[-1]][1] if positions else None,coverage=coverage))
    return result


def process(root,parent,audit):
    if (root/'publication.json').exists():raise ValueError('Published versions are immutable')
    root.mkdir(parents=True,exist_ok=True);(root/'tools').mkdir(exist_ok=True);(root/'processed').mkdir(exist_ok=True)
    from app.core import bgm
    report=json.loads((audit/'sentence-prosody-review.json').read_text())
    assert report['source']['video_sha256']==sha(parent/'final.mp4')
    for name in ('script.json','visual-plan.json','music-selection.json','logo-layer.png','voice-settings.json','voice-jobs.json'):
        shutil.copy2(parent/name,root/name)
    for folder in ('frames','voice'):shutil.copytree(parent/folder,root/folder,dirs_exist_ok=True)
    voices=json.loads((parent/'voice-manifest.json').read_text());old=json.loads((parent/'timeline.json').read_text());oldcuts={p['index']:p for p in old['paragraphs']}
    cap_source=json.loads((parent/'caption-review.json').read_text());header=(parent/'captions.ass').read_text().split('Dialogue:')[0]
    timelines=[];edits_all=[];audio_checks=[];chapters=[];cursor=0;all_pcm=[];cues=[]
    for voice in voices:
        index=voice['index'];source=parent/f'processed/{index:03}.wav'
        with wave.open(str(source),'rb') as w:
            assert w.getnchannels()==1 and w.getsampwidth()==2
            rate=w.getframerate();samples=array.array('h',w.readframes(w.getnframes()))
        measured=next(r for r in report['measurements'] if r['index']==index)
        sentences=[s for s in measured['sentences'] if s['status']=='aligned']
        edits=silence_plan(samples,rate,sentences)
        trimmed=array.array('h');last=0
        for edit in edits:
            a,b=round(edit['start']*rate),round(edit['end']*rate);trimmed.extend(samples[last:a]);last=b
        trimmed.extend(samples[last:]);duration=len(trimmed)/rate
        slow={s['sentence'] for s in report['sentences'] if s['index']==index and any(f['type']=='slow_sentence_active' for f in s['findings'])}
        bounds=[0]+[(s['end']+t['start'])/2 for s,t in zip(sentences,sentences[1:])]+[len(samples)/rate]
        groups=[]
        for n,s in enumerate(sentences):
            tempo=min(1.12,max(1,s['active_seconds_per_syllable']/.165)) if s['sentence'] in slow else 1
            a,b=compressed_time(bounds[n],edits),compressed_time(bounds[n+1],edits)
            if groups and groups[-1]['tempo']==tempo:groups[-1]['input_end']=b
            else:groups.append(dict(input_start=a,input_end=b,tempo=tempo))
        if not groups:groups=[dict(input_start=0,input_end=duration,tempo=1)]
        pieces=[];out=array.array('h');parts=root/'processed'/f'{index:03}-parts';parts.mkdir(exist_ok=True)
        for number,group in enumerate(groups):
            a,b=round(group['input_start']*rate),round(group['input_end']*rate);piece=trimmed[a:b];file=parts/f'{number:02}-input.wav'
            with wave.open(str(file),'wb') as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(rate);w.writeframes(piece.tobytes())
            if group['tempo']!=1:
                output=parts/f'{number:02}-tempo.wav';run(['ffmpeg','-v','error','-y','-i',str(file),'-af',f"atempo={group['tempo']:.8f}",'-c:a','pcm_s16le',str(output)])
                with wave.open(str(output),'rb') as w:piece=array.array('h',w.readframes(w.getnframes()))
            pieces.append(dict(group,output_start=len(out)/rate,output_end=(len(out)+len(piece))/rate))
            out.extend(piece)
        path=root/f'processed/{index:03}.wav';before=root/f'processed/{index:03}-before-gain.wav'
        with wave.open(str(before),'wb') as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(rate);w.writeframes(out.tobytes())
        speech=len(out)/rate;level_before=bgm.measure_audio(before,speech);gain=min(-18-level_before['integrated_lufs'],-1.8-level_before['true_peak_dbfs'])
        run(['ffmpeg','-v','error','-y','-i',str(before),'-af',f'volume={gain:.8f}dB:precision=double','-c:a','pcm_s16le',str(path)])
        with wave.open(str(path),'rb') as w:pcm=w.readframes(w.getnframes())
        level=bgm.measure_audio(path,speech);assert level['true_peak_dbfs']<=-1 and level['integrated_lufs']>=-22
        seconds=math.ceil((speech+.28)*30)/30;all_pcm.append(pcm+b'\0\0'*(round(seconds*rate)-len(pcm)//2))
        if not chapters or chapters[-1]['scene']!=voice['scene']:
            chapters.append(dict(scene=voice['scene'],title=old['chapters'][len(chapters)]['title'],start=cursor))
        timelines.append(dict(voice,start=cursor,end=cursor+seconds,speech_seconds=speech,duration=seconds,trim_start=0,trim_end=0,processed_file=f'processed/{index:03}.wav'))
        old_cues=[c for c in cap_source['cues'] if c['index']==index]
        aligned=caption_alignment(old_cues,measured['words'])
        for c,original in zip(aligned,old_cues):
            if c['coverage']<.80:
                a,b=original['start']-oldcuts[index]['start'],original['end']-oldcuts[index]['start'];method='parent timing mapped; alignment below .80'
            else:a,b=c['start'],c['end'];method='source final ASR character alignment + edit time map'
            a=max(.03,min(speech-.08,mapped_time(a,edits,pieces)));b=min(speech,max(a+.06,mapped_time(b,edits,pieces)))
            cues.append(dict(original,start=cursor+a,end=cursor+b,alignment=method,alignment_coverage=c['coverage']))
        meta=json.loads((root/voice['file']).with_suffix('.tts.json').read_text())
        audio_checks.append(dict(index=index,trimmed_before_gain=level_before,processed_static_gain_db=gain,source=meta['normalization']['input'],normalized=meta['normalization']['output'],processed=level,trim_start=0,trim_end=0,silent=False,listened=False))
        edit_record=dict(index=index,source_processed_sha256=sha(source),output_processed_sha256=sha(path),source_seconds=len(samples)/rate,edited_seconds=speech,
            quiet_edits=edits,time_pieces=pieces,tempo_max=max(g['tempo'] for g in groups),pitch_shift_applied=False,static_gain_db=gain)
        edits_all.append(edit_record);voice['audio_edit']=dict(processed_sha256=sha(path),parent_processed_sha256=sha(source))
        cursor+=seconds
    timelines[-1]['end']+=2;timelines[-1]['duration']+=2;cursor+=2;all_pcm.append(b'\0\0'*96000)
    for c,t in zip(chapters,chapters[1:]+[dict(start=cursor)]):c['end']=t['start']
    save(root/'voice-manifest.json',voices);save(root/'timeline.json',dict(duration=cursor,tempo=1,chapters=chapters,paragraphs=timelines,caption_alignment='ASR alignment and non-linear edit time map'))
    save(root/'audio-edits.json',dict(parent_video_sha256=sha(parent/'final.mp4'),cuts=edits_all,total_silence_removed=sum(e['removed_seconds'] for c in edits_all for e in c['quiet_edits']),changed_cuts=[c['index'] for c in edits_all if c['quiet_edits'] or c['tempo_max']>1],speed_corrected_cuts=[c['index'] for c in edits_all if c['tempo_max']>1],human_listening_completed=False))
    save(root/'cut-audio-review.json',audio_checks)
    with wave.open(str(root/'narration.wav'),'wb') as w:
        w.setnchannels(1);w.setsampwidth(2);w.setframerate(48000)
        for pcm in all_pcm:w.writeframes(pcm)
    def at(value):
        n=round(value*100);return f'{n//360000}:{n//6000%60:02}:{n//100%60:02}.{n%100:02}'
    def vt(value):
        n=round(value*1000);return f'{n//3600000:02}:{n//60000%60:02}:{n//1000%60:02}.{n%1000:03}'
    events=[];vtt=['WEBVTT','']
    for cue in cues:
        assert_display_numbers(cue['text']);safe=cue['text'].replace('\n',r'\N');events.append(f"Dialogue: 0,{at(cue['start'])},{at(cue['end'])},Caption,,0,0,0,,{safe}");vtt.extend([f"{vt(cue['start'])} --> {vt(cue['end'])}",cue['text'],''])
    (root/'captions.ass').write_text(header+'\n'.join(events)+'\n');(root/'captions.vtt').write_text('\n'.join(vtt));save(root/'caption-review.json',dict(cap_source,cues=cues))
    metadata=[';FFMETADATA1','title='+json.loads((root/'script.json').read_text())['title']]
    for c in chapters:metadata.extend(['[CHAPTER]','TIMEBASE=1/1000',f"START={round(c['start']*1000)}",f"END={round(c['end']*1000)}",'title='+c['title']])
    (root/'chapters.txt').write_text('\n'.join(metadata));concat=['ffconcat version 1.0']
    for p in timelines:concat.extend([f"file '{root}/frames/{p['index']:03}.png'",f"duration {p['duration']:.9f}"])
    concat.append(f"file '{root}/frames/{timelines[-1]['index']:03}.png'");(root/'frames.txt').write_text('\n'.join(concat))
    names=['script.json','voice-manifest.json','timeline.json','captions.ass','narration.wav','logo-layer.png','chapters.txt','frames.txt']+[f'frames/{n:03}.png' for n in range(1,29)];save(root/'prepared-inputs.json',{name:sha(root/name) for name in names})
    review=json.loads((parent/'production-review-final.json').read_text());review['speaker_review']['conditioning']='preserved Sohee source; silence editing and pitch-preserving tempo, no synthesis';review['asr_review']['status']='pending edited final audio transcription';save(root/'production-review.json',review)
    save(root/'audio-release.json',dict(voice_manifest_sha256=sha(root/'voice-manifest.json'),asr_review=review['asr_review'],human_listening_completed=False))
    print(json.dumps(dict(prepared=True,duration=cursor,removed_silence=sum(e['removed_seconds'] for c in edits_all for e in c['quiet_edits']),speed_cuts=[c['index'] for c in edits_all if c['tempo_max']>1])),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('root',type=Path);p.add_argument('parent',type=Path);p.add_argument('audit',type=Path);a=p.parse_args();process(a.root,a.parent,a.audit)
