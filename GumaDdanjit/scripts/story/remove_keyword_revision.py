"""Immutable promotion v6: remove keyword motion, keep exact v5 audio/captions/charts."""
import argparse, array, hashlib, json, shutil, subprocess
from pathlib import Path
from PIL import Image, ImageDraw
from render_motion_revision import prepare_cut, encode_cut, editorial, ASS, ass_time

def sha(path):
    with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(path,value):Path(path).write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')
def run(args):
    result=subprocess.run(args,capture_output=True,text=True)
    if result.returncode:raise RuntimeError(result.stderr[-3000:])
    return result.stdout

def render(root, indices=None):
    parent=root.parent/'promotion-v5'
    assert not (root.parents[1]/'assets/promotion-film-v6.mp4').exists()
    root.mkdir(exist_ok=True);(root/'motion').mkdir(exist_ok=True)
    for name in ['timeline.json','script.json','caption-review.json','captions-global.ass','captions.vtt','logo-layer.png','chart-provenance.json','voice-manifest.json','voice-production.json','voice-settings.json']:
        shutil.copy2(parent/name,root/name)
    shutil.copytree(parent/'asr',root/'asr',dirs_exist_ok=True)
    timeline=json.loads((root/'timeline.json').read_text());voices=json.loads((root/'voice-manifest.json').read_text());caps=json.loads((root/'caption-review.json').read_text())
    olds=json.loads((root.parent/'promotion-v4/visual-plan.json').read_text());ed=editorial()
    selected=list(zip(timeline['paragraphs'],voices))
    if indices:selected=[pair for pair in selected if pair[0]['index'] in indices][::-1]
    for cut,voice in selected:
        n=cut['index'];asr=json.loads((root/'asr'/f'{n:03}.json').read_text())
        folder,counts=prepare_cut(root,cut,voice,asr,olds[n-1],ed[n])
        cfg=json.loads((folder/'motion.json').read_text())
        assert all(x['role']=='bar' for x in cfg['layers'])
        previous=json.loads((parent/'motion'/f'{n:03}/motion.json').read_text())
        assert cfg['numbers']==previous['numbers'],n
        events=[]
        for cue in caps['cues']:
            if cue['index']!=n:continue
            text=cue['text'].replace('\n',r'\N').replace('{','').replace('}','')
            events.append(f'Dialogue: 0,{ass_time(cue["local_start"])},{ass_time(cue["local_end"])},Caption,,0,0,0,,{text}')
        (folder/'captions.ass').write_text(ASS+'\n'.join(events)+'\n')
        encode_cut(root,cut,folder,counts)
        if not indices:save(root/'production-state.json',dict(version=6,phase='rendering',rendered_through=n,parent_version=5,audio_regenerated=False))
        print(json.dumps({'rendered':n,'keyword_layers':0}),flush=True)
    if indices:return
    (root/'segments.txt').write_text('\n'.join(f"file '{root}/segments/{n:03}.mp4'" for n in range(1,115)))
    run(['ffmpeg','-v','error','-y','-f','concat','-safe','0','-i',str(root/'segments.txt'),'-i',str(parent/'final.mp4'),'-map','0:v','-map','1:a','-map_metadata','1','-map_chapters','1','-c','copy','-t',str(timeline['duration']),'-movflags','+faststart',str(root/'final.mp4')])
    print('render complete; verifying',flush=True)
    verify(root)

def verify(root):
    parent=root.parent/'promotion-v5';movie=root/'final.mp4';timeline=json.loads((root/'timeline.json').read_text())
    probe=json.loads(run(['ffprobe','-v','error','-show_streams','-show_format','-show_chapters','-of','json',str(movie)]));v=next(x for x in probe['streams'] if x['codec_type']=='video')
    assert (v['width'],v['height'],v['r_frame_rate'])==(1920,1080,'30/1') and len(probe['chapters'])==12
    assert abs(float(probe['format']['duration'])-timeline['duration'])<.1
    # Hash audio packets: no synthesis, re-encoding, gain, tempo or music change.
    hashes=[]
    for source in [parent/'final.mp4',movie]:
        hashes.append(run(['ffmpeg','-v','error','-i',str(source),'-map','0:a','-c:a','copy','-f','hash','-hash','sha256','-']).strip())
    assert hashes[0]==hashes[1]
    logo=Image.open(root/'logo-layer.png').convert('RGBA');box=logo.getbbox();crop=logo.crop(box);w,h=crop.size;pixels=list(crop.getdata());opaque=[i for i,p in enumerate(pixels) if p[3]==255];count=min(800,len(opaque));chosen=[opaque[k*(len(opaque)-1)//(count-1)] for k in range(count)];test=[(i*3+c,pixels[i][c]) for i in chosen for c in range(3)]
    frames=0;bad=[];worst=0
    with (root/'logo-decode.log').open('wb') as log:
        process=subprocess.Popen(['ffmpeg','-v','error','-threads','2','-i',str(movie),'-vf',f'crop={w}:{h}:{box[0]}:{box[1]}:exact=1','-filter_threads','1','-pix_fmt','rgb24','-f','rawvideo','-'],stdout=subprocess.PIPE,stderr=log)
        while True:
            raw=process.stdout.read(w*h*3)
            if not raw:break
            assert len(raw)==w*h*3
            error=sum(abs(raw[ix]-val) for ix,val in test)/len(test);worst=max(worst,error)
            if error>25:bad.append(frames)
            frames+=1
        assert process.wait()==0
    assert frames==int(v['nb_frames']) and not bad
    out=root/'encoded-review';out.mkdir(exist_ok=True)
    for cut in timeline['paragraphs']:
        run(['ffmpeg','-v','error','-threads','2','-y','-ss',str(cut['start']+cut['duration']/2),'-i',str(movie),'-frames:v','1','-q:v','2','-update','1',str(out/f'cut-{cut["index"]:03}.jpg')])
    for page in range(6):
        sheet=Image.new('RGB',(1920,960),'white');d=ImageDraw.Draw(sheet)
        for k,cut in enumerate(timeline['paragraphs'][page*20:(page+1)*20]):
            n=cut['index'];im=Image.open(out/f'cut-{n:03}.jpg');x=k%5*384;y=k//5*240;sheet.paste(im.resize((384,216)),(x,y));d.text((x+4,y+219),str(n),fill='black')
        sheet.save(out/f'sheet-{page+1:02}.jpg',quality=94)
    motions=[json.loads((root/'motion'/f'{n:03}/motion.json').read_text()) for n in range(1,115)]
    numeric=[]
    for cfg,cut in zip(motions,timeline['paragraphs']):
        if not cfg['numbers']:continue
        endpoint=min(cut['duration']-.15,max(q['end'] for q in cfg['numbers'])+.2)
        target=out/f'numeric-{cut["index"]:03}.jpg'
        run(['ffmpeg','-v','error','-threads','2','-y','-ss',str(cut['start']+endpoint),'-i',str(movie),'-frames:v','1','-q:v','2','-update','1',str(target)])
        numeric.append(target)
    for page in range((len(numeric)+4)//5):
        sheet=Image.new('RGB',(1920,216),'white')
        for k,p in enumerate(numeric[page*5:(page+1)*5]):sheet.paste(Image.open(p).resize((384,216)),(k*384,0))
        sheet.save(out/f'numeric-sheet-{page+1}.jpg',quality=95)
    run(['ffmpeg','-v','error','-y','-ss','2','-i',str(movie),'-frames:v','1','-update','1',str(root/'poster.png')])
    review=json.loads((parent/'production-review.json').read_text())
    review.update(version=6,parent_version=5,video_sha256=sha(movie),audio_packet_hash=hashes[1],audio_packet_hash_identical_to_v5=True,audio_regenerated=False,visual_review='pending v6 encoded review',user_accepted=False)
    review['parent_voice_production']=review['voice_production']
    review['voice_production']=dict(complete=114,reused=114,new=0,reused_from_version=5,model='gemini-3.8-flash-tts',voice='Zephyr',human_listening_completed=False)
    review['logo']=dict(all_frames_checked=frames,failed_frames=len(bad),worst_mae=worst)
    review['motion'].update(animated_layers=sum(len(x['layers']) for x in motions),keyword_animation_enabled=False,keyword_animated_layers=0,chart_context_static=True,concept_diagrams_static=True,numeric_values_and_timings_identical_to_v5=True,numeric_endpoint_cuts_checked=len(numeric),rendered_counter_endpoints_pending_visual_inspection=True)
    save(root/'production-review.json',review)
    save(root/'production-state.json',dict(version=6,phase='pending_visual_review',rendered_cuts=114,script_version=9,parent_version=5,audio_regenerated=False))
    print(json.dumps({'verified':True,'frames':frames,'audio_unchanged':True,'numeric_cuts':len(numeric)}),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('root',type=Path);p.add_argument('--verify-only',action='store_true');p.add_argument('--cuts',type=int,nargs='+');args=p.parse_args()
    if args.verify_only:verify(args.root)
    else:render(args.root,args.cuts)
