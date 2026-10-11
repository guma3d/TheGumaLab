"""Fail closed before recommending: issued affiliate proof and usable local resources."""
import hashlib
import json
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Literal
from urllib.parse import urlparse

from PIL import Image
from pydantic import BaseModel, Field, field_validator
from app.config import STORAGE_DIR


class EvidenceFile(BaseModel):
    path: str = Field(min_length=1)  # Relative to project storage, portable to Docker.
    sha256: str = Field(pattern=r'^[a-fA-F0-9]{64}$')


class ReadyResource(EvidenceFile):
    kind: Literal['image', 'video']
    source_url: str
    usage_basis: str = Field(min_length=10)
    product_match: str = Field(min_length=10)
    purpose: str = Field(min_length=10)
    visually_reviewed: Literal[True]
    motion_reviewed: bool = False

    @field_validator('source_url')
    @classmethod
    def public_source(cls, value):
        parsed=urlparse(value)
        if parsed.scheme not in ('https','http') or not parsed.hostname or parsed.username or parsed.password:
            raise ValueError('자료 원문 URL이 필요합니다.')
        return value


class RecommendationReadiness(BaseModel):
    checked_at: datetime
    reviewer: str = Field(min_length=1)
    product_url: str
    option: str
    affiliate_url: str
    affiliate_proof: EvidenceFile
    resources: list[ReadyResource] = Field(min_length=1, max_length=20)
    coverage_review: str = Field(min_length=30)
    generation_plan: str = ''  # Plans are not downloaded/verified resources.


def verified_path(asset, root):
    base=Path(root).resolve()
    path=(base/asset.path).resolve()
    if not path.is_relative_to(base) or not path.is_file():
        raise ValueError('추천 근거 파일이 storage에 없습니다.')
    with path.open('rb') as stream:
        actual=hashlib.file_digest(stream,'sha256').hexdigest()
    if actual.lower()!=asset.sha256.lower():
        raise ValueError('추천 근거 파일 해시가 변경됐습니다. 재검수가 필요합니다.')
    return path


def validate_readiness(item, now, root=None):
    root=STORAGE_DIR if root is None else root
    ready=item.readiness
    link=item.purchase_link
    if ready is None or link is None or not link.affiliate_url or len(link.affiliate_evidence.strip())<10:
        raise ValueError('추천 전에 실제 파트너스 링크 발급·리소스 검증이 필요합니다.')
    if ready.checked_at.tzinfo is None or not timedelta(0)<=now-ready.checked_at<=timedelta(hours=24):
        raise ValueError('추천 사전 검증은 최근 24시간 이내여야 합니다.')
    if any(getattr(ready,key)!=getattr(link,key) for key in ('option','affiliate_url')) or ready.product_url!=link.url:
        raise ValueError('파트너스 발급 근거와 추천 상품·옵션·링크가 다릅니다.')
    verified_path(ready.affiliate_proof,root)
    for asset in ready.resources:
        path=verified_path(asset,root)
        if asset.kind=='image':
            with Image.open(path) as image:
                image.load()
                if min(image.size)<720:
                    raise ValueError('추천 이미지 원본 짧은 변 720px 이상이 필요합니다.')
        else:
            if not asset.motion_reviewed:
                raise ValueError('영상 자료는 실제 사용할 동작 구간의 검수가 필요합니다.')
            result=subprocess.run(['ffprobe','-v','error','-select_streams','v:0','-show_entries',
                'stream=width,height','-of','json',str(path)],capture_output=True,text=True,check=True,timeout=30)
            streams=json.loads(result.stdout).get('streams',[])
            minimum=720 if item.category=='household' else 1080
            if not streams or min(streams[0]['width'],streams[0]['height'])<minimum:
                raise ValueError('추천 영상 원본 해상도가 카테고리 기준에 미달합니다.')
            subprocess.run(['ffmpeg','-v','error','-i',str(path),'-frames:v','1','-f','null','-'],
                capture_output=True,check=True,timeout=30)
    return ready
