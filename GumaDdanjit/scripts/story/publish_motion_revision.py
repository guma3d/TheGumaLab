"""Register v5 after technical and visual checks; preserve all older Story versions."""
import hashlib,html,json,shutil,sys
from pathlib import Path
from story.store import Store
root=Path(sys.argv[1]);store=Store(root.parents[1]);review=json.loads((root/'production-review.json').read_text());script=json.loads((root/'script.json').read_text());timeline=json.loads((root/'timeline.json').read_text());voices=json.loads((root/'voice-manifest.json').read_text())
assert review['visual_review']=='encoded scenes, captions and numeric endpoints inspected'
assert review['logo']['failed_frames']==0 and review['technical_review']['audio_cuts_checked']==114
assert review['motion']['numeric_anchors_verified'] and review['music_amplitude_ratio']==.5 and script['version']==9
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
assert sha(root/'final.mp4')==review['video_sha256'] and sha(root/'script.json')==review['script_sha256']
common=dict(character_id='',version=5,status='review',script_id='promotion',script_version=9,video_version=5,tags=['promotion','longform','video-v5','script-v9','zephyr','motion'])
def asset(key,source,kind,title,**fields):
    source=Path(source);name=key+source.suffix;target=store.root/'assets'/name
    if target.exists():assert sha(target)==sha(source)
    else:shutil.copy2(source,target)
    existing=store.asset(key)
    if not existing:
        item=store.add_asset(dict(common,id=key,file=name,kind='other' if kind=='document' else kind,title=title,tool='Gemini Flash / Zephyr + speech-timed FFmpeg motion graphics',reference='promotion-film-v4; promotion script v9',prompt='',**fields))
        if kind=='document':item=store.update_asset(key,item['revision'],dict(media='document'))
    else:assert existing['sha256']==sha(source)
    return key
reviewid=asset('promotion-v5-production-review',root/'production-review.json','document','승진 v5 · 제작 검수 기록',archived=True)
full=dict(narration=script,captions=json.loads((root/'caption-review.json').read_text()),voice_settings=json.loads((root/'voice-settings.json').read_text()))
(root/'script-and-captions.json').write_text(json.dumps(full,ensure_ascii=False,indent=2))
scriptid=asset('promotion-v5-script-and-captions',root/'script-and-captions.json','document','승진 · 대본 v9와 요약 자막 v5',archived=True)
audioid=asset('promotion-narration-v5',root/'narration-master.mp3','audio','승진 v5 · Zephyr 전체 내레이션',duration_seconds=timeline['duration'],tts_provider='gemini',tts_voice='Zephyr',tts_model='gemini-3.8-flash-tts')
cutids=[]
for voice in voices:
    key=f'promotion-v5-voice-{voice["index"]:03}';cutids.append(asset(key,root/voice['file'],'audio',f'승진 v5 · CUT {voice["index"]:03} · Zephyr',archived=True,narration=voice['text'],cut_index=voice['index'],tts_job_id=voice['tts_job_id'],reuse_source=voice.get('reuse_source'),duration_seconds=voice['duration'],voice_take=voice.get('take',1),original_sha256=voice['original_sha256'],tts_provider='gemini',tts_voice='Zephyr',tts_model='gemini-3.8-flash-tts'))
posterid=asset('promotion-poster-v5',root/'poster.png','other','승진 · 모션 영상 v5 표지')
target=store.root/'exports/promotion-film-v5.vtt'
if not target.exists():shutil.copy2(root/'captions.vtt',target)
else:assert sha(target)==sha(root/'captions.vtt')
source=store.asset('promotion-film-v4');credits=source.get('credits','')
credits='\n'.join([f'대본 promotion v9 유지 · 영상 v5 · 부모 영상 v4',f'음성 Gemini 3.8 Flash TTS / Zephyr · 재사용 {review["voice_production"]["reused"]}컷 / 새 음성 {review["voice_production"]["new"]}컷 · 부분 재생성 테이크 보관',f'모션: 상황 이미지 카메라 이동 {review["motion"]["image_camera_moves"]}컷 · 애니메이션 레이어 {review["motion"]["animated_layers"]}개 · 실제 발화에 연결한 수치 카운트/막대 확장', '글꼴: 키워드 Do Hyeon / 요약 자막 Pretendard SemiBold 50.6px(+10%)', 'BGM: Carefree — Kevin MacLeod (incompetech.com) · CC BY 4.0 https://creativecommons.org/licenses/by/4.0/ · 첫 영상 대비 진폭 0.5배(-6.0206dB), 발췌·음량 조정', '검수: 모든 컷 음량·파형·음성/음악 대비, ASR와 수치 시점, 모든 프레임 로고, 완성 장면·요약 자막·수치 최종값. 실제 전편 청취·사용자 최종 승인은 별도.', '이전 영상·원본·실패 테이크·대본·출처·검수 보존. 새 YouTube 업로드 없음.', '원문 자료 출처:']+[sc.get('source','') if isinstance(sc.get('source',''),str) else json.dumps(sc.get('source',''),ensure_ascii=False) for sc in script['scenes']])
videoid=asset('promotion-film-v5',root/'final.mp4','video',script['title'],width=1920,height=1080,fps=30,duration_seconds=timeline['duration'],poster_id=posterid,audio_id=audioid,captions_file='promotion-film-v5.vtt',chapters=timeline['chapters'],parent_video_id='promotion-film-v4',cut_audio_asset_ids=cutids,scene_asset_ids=source.get('scene_asset_ids',[]),bgm_enabled=True,bgm_amplitude_ratio=.5,tts_provider='gemini',tts_voice='Zephyr',tts_model='gemini-3.8-flash-tts',credits=credits,note='대본 v9 유지 · Zephyr · 음성에 맞춘 수치/차트·키워드 모션 · 간결한 자막 +10% · 기존 BGM 절반 음량')
base='/gumaddanjit/story/media';pageid='promotion-v5-motion-review'
minutes=int(timeline['duration']//60);seconds=round(timeline['duration']%60)
page=f'''<!doctype html><html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>승진 · Zephyr 모션 영상 v5</title><style>body{{max-width:1100px;margin:36px auto;padding:0 22px;font:17px/1.8 system-ui;background:#fafaf7;color:#24343d}}video,audio{{width:100%}}a{{color:#176c80}}section{{border-top:1px solid #ccd8dc;padding-top:20px;margin-top:24px}}li{{margin:8px 0}}</style><h1>{html.escape(script['title'])}</h1><p>영상 v5 · 대본 v9 유지 · {minutes}분 {seconds}초 · 1080p / 30fps</p><video controls playsinline preload="metadata" poster="{base}/{posterid}/original" src="{base}/{videoid}/original"></video><p><a href="/gumaddanjit/story/watch/{videoid}">영상 보관함</a> · <a href="{base}/{videoid}/original">MP4 원본</a> · <a href="{base}/{scriptid}/original">대본과 요약 자막</a> · <a href="{base}/{reviewid}/original">검수 기록</a></p><section><h2>이번 변경</h2><ul><li>최신 대본 v9의 낭독 문장은 그대로 유지했습니다. 전체 Gemini Flash / Zephyr이며 Lite·로컬 음성은 섞지 않았습니다. 동일 대사의 정상 기존 Flash 음성은 재사용하고, 변경/검수 후보는 새 테이크로 저장했습니다.</li><li>상황 이미지의 확대·이동, 주요 키워드의 순차 등장·전환, 비교 카드와 밑줄, 실제 발화에 연결한 숫자 카운트·막대 확장을 넣었습니다. 다른 질문의 6%와 76%를 증가 그래프로 표현하지 않았습니다.</li><li>자막은 원문을 그대로 반복하는 대신 의미를 유지한 요약으로 편집했습니다. 수치·대상·해석 조건을 남기고 크기를 46px에서 50.6px로 정확히 10% 키웠습니다.</li><li>첫 영상과 같은 Carefree를 신호 크기 0.5배(-6.0206dB)로 넣었습니다. 일정 게인이며 음성과의 대비와 믹스 피크를 모든 구간에서 검사했습니다.</li></ul></section><section><h2>음성만 듣기</h2><audio controls preload="metadata" src="{base}/{audioid}/original"></audio><p>원본·구간별 새 테이크·ASR·동기화·편집 기록은 보관했습니다. 자동 검사와 시각 검수는 실제 전편 청취·사용자 최종 수용을 대신하지 않습니다.</p></section><section><h2>음원 출처</h2><p>Carefree — Kevin MacLeod (incompetech.com) · <a href="https://creativecommons.org/licenses/by/4.0/">CC BY 4.0</a> · 발췌·음량 조정</p><p><a href="{review['track']['track_url']}">원곡 페이지</a></p></section></html>'''
(root/'review.html').write_text(page,encoding='utf-8');asset(pageid,root/'review.html','document','승진 v5 · Zephyr 모션 영상과 검수',archived=True)
save=dict(video_id=videoid,url=f'https://home.guma3d.com{base}/{pageid}/original',video_url=f'https://home.guma3d.com/gumaddanjit/story/watch/{videoid}',video_sha256=review['video_sha256'],script_version=9,video_version=5)
(root/'publication.json').write_text(json.dumps(save,ensure_ascii=False,indent=2));print(json.dumps(save,ensure_ascii=False))
