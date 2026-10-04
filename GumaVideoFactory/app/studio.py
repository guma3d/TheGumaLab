import copy
import json
import uuid
import hashlib
from io import BytesIO
from pathlib import Path
from urllib.parse import urlparse
from typing import Literal
from fastapi import APIRouter, Request, HTTPException, BackgroundTasks, UploadFile, File, Form
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from PIL import Image, ImageOps
from app.core import versions as store
from app.core.studio_jobs import execute
from app.core.recommendations import load_daily, now_kst
from app.core.categories import PRESETS
from app.core.source_media import MediaSource, store_media

router=APIRouter()
templates=Jinja2Templates(directory=str(Path(__file__).parent/'templates'))


class IdeaRequest(BaseModel):
    recommendation_id: str
    date: str


class StageRequest(BaseModel):
    regenerate: bool=False
    model_version: int | None=Field(default=None,ge=1)
    preview_version: int | None=Field(default=None,ge=1)
    approved: bool=False
    product_url: str=Field(default='',max_length=2000)
    narrations: list[str]=Field(default_factory=list,max_length=8)


class Approval(BaseModel):
    appearance_confirmed: bool=False
    usage_confirmed: bool=False


class ModelRevision(BaseModel):
    operation: Literal['single_product','restore_materials']='single_product'


def find(idea_id):
    try: return store.read(idea_id)
    except (ValueError,FileNotFoundError): raise HTTPException(404,'아이디어를 찾을 수 없습니다.')


def version(idea_id,stage,number):
    try: return store.get(idea_id,stage,number)
    except (ValueError,FileNotFoundError,TypeError): raise HTTPException(404,'버전을 선택해주세요.')


class CutFeedback(BaseModel):
    narration: str = Field(min_length=1,max_length=1000)
    feedback: str = Field(default='',max_length=3000)


@router.post('/api/ideas/{idea_id}/Video/{number}/cuts/{cut}/feedback')
async def cut_feedback(idea_id:str,number:int,cut:int,req:CutFeedback):
    find(idea_id)
    v=version(idea_id,'Video',number)
    cuts=v.get('cuts',[])
    if v['status']!='ready' or not 1<=cut<=len(cuts):
        raise HTTPException(409,'완성된 영상의 컷 번호를 선택해주세요.')
    request_id=uuid.uuid4().hex
    data=dict(id=request_id,idea_id=idea_id,video_version=number,cut_number=cut,
        original_narration=cuts[cut-1]['narration_ko'],narration=req.narration.strip(),
        feedback=req.feedback.strip(),state='pending',created_at=now_kst().isoformat())
    if not data['narration']:raise HTTPException(400,'대사를 입력해주세요.')
    with store.LOCK:
        folder=store.directory(idea_id)/'edit_requests'
        for path in folder.glob('*.json'):
            old=json.loads(path.read_text(encoding='utf-8'))
            if old.get('state')=='pending' and all(old.get(k)==data[k] for k in ('video_version','cut_number','narration','feedback')):
                return old
        store.write_json(folder/(request_id+'.json'),data)
    return data


@router.get('/ideas/{idea_id}')
async def idea_page(request:Request,idea_id:str):
    find(idea_id)
    return templates.TemplateResponse(request=request,name='idea.html',context={'idea':dict(store.snapshot(idea_id),workflow=store.workflow(store.read(idea_id)))})


@router.post('/api/ideas')
async def approve_idea(req:IdeaRequest):
    try: daily=load_daily(req.date)
    except ValueError: raise HTTPException(400,'추천 날짜를 확인해주세요.')
    rec=next((r for r in daily['items'] if r['id']==req.recommendation_id),None)
    if not rec: raise HTTPException(404,'추천 아이디어를 찾을 수 없습니다.')
    return store.create(rec,req.date)


@router.get('/api/ideas/{idea_id}')
async def get_idea(idea_id:str):
    idea=find(idea_id);return dict(store.snapshot(idea_id),workflow=store.workflow(idea))


@router.post('/api/ideas/{idea_id}/{stage}')
async def start(idea_id:str,stage:Literal['3DModel','Preview','Video'],req:StageRequest,tasks:BackgroundTasks):
    idea=find(idea_id)
    if stage!='Video':raise HTTPException(410,'3D 기능은 제거됐습니다. 컷씬은 매일 09시 Astra가 준비합니다.')
    from app.core.shopping import enqueue
    try:return enqueue(idea_id,req.preview_version,req.regenerate)
    except (ValueError,FileNotFoundError,TypeError) as error:raise HTTPException(409,str(error))


@router.post('/api/ideas/{idea_id}/Video/{number}/publish')
async def request_publish(idea_id:str,number:int,req:StageRequest):
    find(idea_id)
    if not req.approved:raise HTTPException(400,'완성 영상을 확인하고 공개를 승인해주세요.')
    path=store.version_dir(idea_id,'Video',number)/'upload.json'
    with store.LOCK:
        if not path.exists():raise HTTPException(409,'비공개 업로드가 먼저 필요합니다.')
        data=json.loads(path.read_text(encoding='utf-8'))
        from app.core.prepared_packages import digest
        if digest(path.parent/'final.mp4')!=data['file_sha256']:raise HTTPException(409,'영상이 변경됐습니다.')
        if data['state']=='publish_requested':return data
        if data['state']!='private':raise HTTPException(409,'비공개 업로드된 영상만 공개 승인할 수 있습니다.')
        data.update(state='publish_requested',approved_at=now_kst().isoformat())
        store.write_json(path,data)
        store.update(idea_id,'Video',number,publication_state='publish_requested',message='공개 승인 완료 · 브라우저 작업 대기')
        return data


@router.post('/api/ideas/{idea_id}/3DModel/{number}/approve')
@router.post('/api/ideas/{idea_id}/3DModel/{number}/revise')
async def removed_model(idea_id:str,number:int):
    raise HTTPException(410,'3D 모델 기능은 제거되었습니다.')


@router.post('/api/ideas/{idea_id}/references')
async def upload_reference(idea_id:str,file:UploadFile=File(...)):
    idea=find(idea_id)
    if idea['category']!='tech':raise HTTPException(400,'음식 자료는 출처와 함께 등록해주세요.')
    data=await file.read(12*1024*1024+1)
    if len(data)>12*1024*1024:raise HTTPException(413,'사진은 12MB 이하로 등록해주세요.')
    try:
        with Image.open(BytesIO(data)) as im:
            if im.format not in ('PNG','JPEG','WEBP') or im.width*im.height>25000000:raise ValueError()
            im=ImageOps.exif_transpose(im).convert('RGB');im.thumbnail((1600,1600))
            folder=store.directory(idea_id)/'inputs';folder.mkdir(exist_ok=True)
            path=folder/f'reference_{now_kst().strftime("%Y%m%d%H%M%S")}_{uuid.uuid4().hex[:8]}.jpg';im.save(path,quality=92)
    except Exception:raise HTTPException(400,'정상 PNG/JPEG/WebP 사진을 등록해주세요.')
    return {'message':'사진을 등록했습니다. 다음 컷씬 검토에 참고합니다.','url':store.url(path)}


@router.post('/api/ideas/{idea_id}/media')
async def upload_food(idea_id:str,file:UploadFile=File(...),metadata:str=Form(...)):
    idea=find(idea_id)
    if idea['category']!='food':raise HTTPException(400,'음식 카테고리용 자료입니다.')
    try:
        source=MediaSource.model_validate_json(metadata)
        source.local_file=store_media(await file.read(40*1024*1024+1),source.kind)
        with store.LOCK:
            path=store.directory(idea_id)/'inputs'/'food.json'
            values=json.loads(path.read_text(encoding='utf-8')) if path.exists() else []
            if len(values)>=8:raise ValueError('자료는 최대 8개까지 등록할 수 있습니다.')
            values.append(source.model_dump());store.write_json(path,values)
    except ValueError as e:raise HTTPException(400,str(e))
    return {'message':'자료를 등록했습니다. 실사 자료 재생성에 반영됩니다.'}
