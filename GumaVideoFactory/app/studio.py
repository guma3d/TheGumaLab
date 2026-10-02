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


@router.get('/ideas/{idea_id}')
async def idea_page(request:Request,idea_id:str):
    find(idea_id)
    return templates.TemplateResponse(request=request,name='idea.html',context={'idea':store.snapshot(idea_id)})


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
    if idea['category']=='tech' and stage!='Video':
        raise HTTPException(409,'프리뷰·3D는 09·21시 Codex 예약 작업에서 준비합니다. 유료 사전 생성은 중단되었습니다.')
    with store.LOCK:
        parents={}
        # A normal click opens the existing result without additional API calls.
        existing=store.history(idea_id,stage)
        if existing and not req.regenerate: return existing[0]
        if idea['category']=='tech':
            if stage=='3DModel':
                preview=version(idea_id,'Preview',req.preview_version)
                if preview['status']!='ready' or not preview.get('needs_3d'):
                    raise HTTPException(409,'3D 보완이 필요한 완성 프리뷰를 먼저 선택해주세요.')
                if not req.approved:raise HTTPException(400,'프리뷰·클립을 확인하고 3D 보완을 승인해주세요.')
                parents=dict(preview_version=preview['number'],preview_approved_at=now_kst().isoformat())
            elif stage=='Video':
                preview=version(idea_id,'Preview',req.preview_version)
                from app.core.prepared_packages import verify_package
                try: package=verify_package(idea_id,preview['number'])
                except ValueError as e: raise HTTPException(409,str(e))
                if preview['status']!='ready':raise HTTPException(409,'완성된 프리뷰가 필요합니다.')
                if not req.approved:raise HTTPException(400,'대본과 클립을 확인하고 최종 승인해주세요.')
                scenes=copy.deepcopy(preview['storyboard']['scenes'])
                if len(req.narrations)!=len(scenes) or any(not s.strip() or len(s)>1000 for s in req.narrations):
                    raise HTTPException(400,'각 컷의 대본을 1~1000자로 입력해주세요.')
                folder=store.version_dir(idea_id,'Preview',preview['number'])
                if not 6<=len(scenes)<=8 or any(not (folder/f'scene_{i:02d}.{ext}').is_file() for i in range(1,len(scenes)+1) for ext in ('png','mp4')):
                    raise HTTPException(409,'모든 공식 클립·프리뷰가 준비되어야 합니다.')
                p=urlparse(req.product_url.strip())
                if p.scheme!='https' or not p.hostname or p.username or p.password:raise HTTPException(400,'HTTPS 상품 링크를 입력해주세요.')
                model=None
                if preview.get('needs_3d'):
                    models=[v for v in store.history(idea_id,'3DModel') if v.get('preview_version')==preview['number']]
                    model=version(idea_id,'3DModel',req.model_version) if req.model_version else (models[0] if models else None)
                    if not model or model['number']!=package.get('model_version'):
                        raise HTTPException(409,'검수된 준비 묶음의 3D 모델을 사용해주세요.')
                    if not model or model.get('preview_version')!=preview['number'] or model['status']!='ready' or not (model.get('approved_at') or model.get('quality_reviewed_at')):
                        raise HTTPException(409,'이 프리뷰의 3D 모델을 생성하고 승인해야 합니다.')
                    path=store.version_dir(idea_id,'3DModel',model['number'])/'model.blend'
                    if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=model.get('model_sha256'):
                        raise HTTPException(409,'승인한 모델이 변경됐습니다. 외형을 다시 확인해주세요.')
                for scene,text in zip(scenes,req.narrations):scene['narration_ko']=text.strip()
                parents=dict(preview_version=preview['number'],model_version=model['number'] if model else None,
                    approved_at=now_kst().isoformat(),veo_transition=package['veo_transition'],product_url=req.product_url.strip(),storyboard=dict(preview['storyboard'],scenes=scenes))
        elif stage in ('Preview','Video'):
            if stage=='Preview':
                if not req.model_version: raise HTTPException(409,'3D 모델·자료 버전을 선택해주세요.')
                model=version(idea_id,'3DModel',req.model_version)
                parents['model_version']=req.model_version
            else:
                if not req.preview_version: raise HTTPException(409,'프리뷰 버전을 선택해주세요.')
                preview=version(idea_id,'Preview',req.preview_version)
                if preview['status']!='ready': raise HTTPException(409,'완성된 프리뷰가 필요합니다.')
                model=version(idea_id,'3DModel',preview['model_version'])
                if not req.approved: raise HTTPException(400,'대본과 컷을 확인하고 최종 승인해주세요.')
                scenes=copy.deepcopy(preview['storyboard']['scenes'])
                if len(req.narrations)!=len(scenes) or any(not s.strip() or len(s)>1000 for s in req.narrations):
                    raise HTTPException(400,'각 컷의 대본을 1~1000자로 입력해주세요.')
                if not 6<=len(scenes)<=8 or any(not (store.version_dir(idea_id,'Preview',req.preview_version)/f'scene_{i:02d}.png').is_file() for i in range(1,len(scenes)+1)):
                    raise HTTPException(409,'모든 컷 이미지가 준비되어야 합니다.')
                p=urlparse(req.product_url.strip())
                if p.scheme!='https' or not p.hostname or p.username or p.password:
                    raise HTTPException(400,'HTTPS 상품 링크를 입력해주세요.')
                for scene,text in zip(scenes,req.narrations):scene['narration_ko']=text.strip()
                parents=dict(preview_version=req.preview_version,model_version=preview['model_version'],
                    approved_at=now_kst().isoformat(),product_url=req.product_url.strip(),
                    storyboard=dict(preview['storyboard'],scenes=scenes))
            if model['status']!='ready' or not model.get('approved_at'):
                raise HTTPException(409,'선택한 모델·자료의 승인이 먼저 필요합니다.')
            if idea['category']=='tech' and not (store.version_dir(idea_id,'3DModel',model['number'])/'model.blend').is_file():
                raise HTTPException(409,'승인한 Blender 파일이 없습니다.')
            if idea['category']=='tech':
                model_path=store.version_dir(idea_id,'3DModel',model['number'])/'model.blend'
                if hashlib.sha256(model_path.read_bytes()).hexdigest()!=model.get('model_sha256'):
                    raise HTTPException(409,'승인 후 모델 파일이 변경됐습니다. 외형을 다시 확인하고 승인해주세요.')
        try: result,created=store.reserve(idea_id,stage,req.regenerate,queued=True,**parents)
        except ValueError as e: raise HTTPException(409,str(e))
        return result


@router.post('/api/ideas/{idea_id}/3DModel/{number}/approve')
async def approve_model(idea_id:str,number:int,req:Approval):
    idea=find(idea_id)
    with store.LOCK:
        value=version(idea_id,'3DModel',number)
        if value['status']!='ready': raise HTTPException(409,'완성된 모델·자료만 승인할 수 있습니다.')
        if not req.appearance_confirmed or not req.usage_confirmed:
            raise HTTPException(400,'제품 외형과 자료 사용 조건을 모두 확인해주세요.')
        proof={}
        if idea['category']=='tech':
            path=store.version_dir(idea_id,'3DModel',number)/'model.blend'
            if not path.is_file():raise HTTPException(409,'모델 파일이 없습니다.')
            proof['model_sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
        return store.update(idea_id,'3DModel',number,approved_at=now_kst().isoformat(),message='외형·자료 승인 완료. 최종 영상을 제작할 수 있습니다.' if idea['category']=='tech' else '자료 승인 완료. 프리뷰를 생성할 수 있습니다.',**proof)


@router.post('/api/ideas/{idea_id}/3DModel/{number}/revise')
async def revise_model(idea_id:str,number:int,req:ModelRevision,tasks:BackgroundTasks):
    idea=find(idea_id)
    with store.LOCK:
        parent=version(idea_id,'3DModel',number)
        if idea['category']!='tech' or parent['status']!='ready' or parent.get('kind')!='downloaded':
            raise HTTPException(409,'완료된 다운로드 모델에서 수정해주세요.')
        from app.core.product_selection import selection_policy
        if req.operation=='single_product' and not selection_policy(idea['recommendation']['subject']):
            raise HTTPException(409,'이 제품은 기종을 구분할 치수 근거가 아직 없습니다. 임의로 모델을 분리하지 않습니다.')
        original=store.version_dir(idea_id,'3DModel',number)
        if not any(p.suffix in ('.blend','.glb','.usdz','.obj','.fbx') for p in original.glob('downloaded.*')):
            raise HTTPException(409,'수정할 원본 3D 자료가 없습니다.')
        try:
            result,_=store.reserve(idea_id,'3DModel',True,queued=True,parent_model_version=number,
                preview_version=parent.get('preview_version'),
                revision_operation=req.operation,revision_note=('공식 치수로 기종 한 대를 분리하고 화면 중심 재정렬' if req.operation=='single_product' else '원본 UV 좌표·표면 재질 복원: 잘못된 가로 띠 제거'))
        except ValueError as error:raise HTTPException(409,str(error))
        return result


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
    return {'message':'사진을 등록했습니다. 3D 모델 재생성에 반영됩니다.','url':store.url(path)}


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
