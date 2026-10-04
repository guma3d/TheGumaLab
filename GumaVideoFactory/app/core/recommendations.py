"""새 제품 3개와 공식 기술 영상을 검증·저장. 추천 이력으로 중복 방지."""
import hashlib
import json
import os
import uuid
import re
import unicodedata
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse
from typing import Literal
from pydantic import BaseModel, Field, field_validator, model_validator
from app.config import RECOMMENDATIONS_DIR
from app.core.categories import PRESETS
from app.core.source_media import MediaSource

KST = timezone(timedelta(hours=9))


def now_kst():
    return datetime.now(KST)


class Source(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    url: str
    published_date: str

    @field_validator("url")
    @classmethod
    def safe_url(cls, value):
        parsed = urlparse(value)
        if parsed.scheme not in ("http", "https") or not parsed.netloc or parsed.username or parsed.password:
            raise ValueError("출처는 HTTP(S) URL이어야 합니다.")
        return value

    @field_validator("published_date")
    @classmethod
    def dated_source(cls, value):
        day = datetime.strptime(value, "%Y-%m-%d").date()
        if day > now_kst().date():
            raise ValueError("미래 날짜 출처는 사용할 수 없습니다.")
        return value


class TechnicalVideo(Source):
    creator: str = Field(min_length=1, max_length=200)
    official_page: str
    technical_content: str = Field(min_length=20, max_length=2000)
    channel_id: str = Field(min_length=1, max_length=100)

    @field_validator('url')
    @classmethod
    def video_url(cls, value):
        if not re.fullmatch(r'https://www\.youtube\.com/watch\?v=[A-Za-z0-9_-]{11}', value):
            raise ValueError('공식 YouTube 단일 영상 링크가 필요합니다.')
        return value

    @field_validator('official_page')
    @classmethod
    def official_url(cls, value):
        return Source.safe_url(value)


def product_key(value):
    return re.sub(r'[^a-z0-9가-힣]', '', unicodedata.normalize('NFKD', value).casefold())


class PurchaseLink(BaseModel):
    url: str
    seller: str = Field(min_length=1)
    official_evidence: str = Field(min_length=10)
    rocket_evidence: str = Field(min_length=10)
    option: str = Field(min_length=1)
    checked_at: datetime
    affiliate_url: str = ""
    affiliate_evidence: str = ""

    @field_validator("affiliate_url")
    @classmethod
    def affiliate(cls, value):
        if not value:return value
        p=urlparse(value)
        if p.scheme!="https" or p.hostname!="link.coupang.com" or p.username or p.password or not p.path.startswith("/a/"):
            raise ValueError("실제 발급한 쿠팡 파트너스 링크가 필요합니다.")
        return value

    @field_validator('url')
    @classmethod
    def product_url(cls, value):
        parsed = urlparse(value)
        if parsed.scheme != 'https' or parsed.hostname != 'www.coupang.com' or parsed.username or parsed.password or not re.fullmatch(r'/vp/products/[0-9]+', parsed.path):
            raise ValueError('정확한 쿠팡 상품 상세 URL이 필요합니다.')
        return value

    @field_validator('checked_at')
    @classmethod
    def recent_check(cls, value):
        if value.tzinfo is None or not timedelta(0) <= now_kst() - value <= timedelta(hours=24):
            raise ValueError('공식 판매처·로켓배송을 최근 24시간 내 확인해야 합니다.')
        return value


class Recommendation(BaseModel):
    category: str
    title: str = Field(min_length=1, max_length=200)
    subject: str = Field(min_length=1, max_length=200)
    hook: str = Field(min_length=1, max_length=500)
    why_now: str = Field(min_length=1, max_length=1000)
    key_feature: str = Field(min_length=1, max_length=1000)
    visual_concept: str = Field(min_length=1, max_length=1000)
    product_keyword: str = Field(min_length=1, max_length=200)
    facts: list[str] = Field(min_length=1, max_length=8)
    cautions: str = Field(default="", max_length=1000)
    sources: list[Source] = Field(min_length=1, max_length=5)
    supporting_features: list[str] = Field(default_factory=list, max_length=4)
    media_sources: list[MediaSource] = Field(default_factory=list, max_length=8)
    product_identity: str = Field(default='', max_length=200)
    technical_video: TechnicalVideo | None = None
    purchase_link: PurchaseLink | None = None
    official_images: list[Source] = Field(default_factory=list,max_length=8)

    @model_validator(mode='after')
    def technical_source(self):
        if self.category == 'tech' and (not (self.technical_video or self.official_images) or not self.product_identity.strip()):
            raise ValueError('테크는 정식 제품명과 공식 영상 또는 이미지 출처가 필요합니다.')
        return self

    @field_validator("category")
    @classmethod
    def registered_category(cls, value):
        if value not in PRESETS:
            raise ValueError("등록되지 않은 카테고리입니다.")
        return value

    def stable_id(self):
        identity = f"{self.category}:{self.subject.strip().casefold()}"
        return hashlib.sha256(identity.encode()).hexdigest()[:16]


class DailyBatch(BaseModel):
    date: str
    researched_at: datetime
    items: list[Recommendation] = Field(min_length=1)
    slot: Literal["09:00","15:00","21:00"]

    @model_validator(mode="after")
    def complete_daily_list(self):
        if self.date != now_kst().strftime("%Y-%m-%d"):
            raise ValueError("오늘 한국시간 날짜의 목록만 갱신할 수 있습니다.")
        if self.researched_at.tzinfo is None or self.researched_at.astimezone(KST).strftime("%Y-%m-%d") != self.date:
            raise ValueError("조사 시간은 한국시간 기준 오늘이어야 합니다.")
        if self.researched_at > now_kst() + timedelta(minutes=5):
            raise ValueError("미래 조사 시간은 사용할 수 없습니다.")
        if len(self.items)!=1:
            raise ValueError("각 시간대에는 아이템 1개만 등록합니다.")
        if len({i.stable_id() for i in self.items}) != len(self.items):
            raise ValueError("중복 아이템은 사용할 수 없습니다.")
        for item in self.items:
            if not item.purchase_link or not item.purchase_link.affiliate_url or len(item.purchase_link.affiliate_evidence)<10:
                raise ValueError("공식 판매처·로켓배송이 검증된 쿠팡 상품 링크가 필요합니다.")
            if item.category == "tech" and len(item.supporting_features) < 2:
                raise ValueError("테크 추천에는 검증된 추가 주요 기능이 2개 이상 필요합니다.")
            if not any((now_kst().date() - datetime.strptime(s.published_date, "%Y-%m-%d").date()).days <= 30 for s in item.sources):
                raise ValueError("아이템마다 최근 30일 이내 출처가 하나 이상 필요합니다.")
        return self


def load_daily(date=None):
    date = date or now_kst().strftime("%Y-%m-%d")
    datetime.strptime(date, "%Y-%m-%d")
    path = RECOMMENDATIONS_DIR / f"{date}.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {"date": date, "researched_at": None, "items": [], "research_count": 0}


def save_batch(batch: DailyBatch):
    old = load_daily(batch.date)
    if old.get("researched_at") and datetime.fromisoformat(old["researched_at"]) >= batch.researched_at:
        raise ValueError("이전 조사 결과로 최신 목록을 덮어쓸 수 없습니다.")
    if batch.slot in old.get("completed_slots",[]):
        raise ValueError("이 시간대 아이템은 이미 등록됐습니다.")
    if old.get("research_count",0)>=3:
        raise ValueError("하루 3개 등록이 완료됐습니다.")
    seen = recommended_products()
    current = set()
    for item in batch.items:
        key = product_key(item.product_identity or item.subject)
        tagged = item.category + ':' + key
        if tagged in seen or tagged in current:
            raise ValueError('이미 추천한 제품입니다: ' + item.subject)
        current.add(tagged)
    data = batch.model_dump(mode="json")
    data["completed_slots"] = [*old.get("completed_slots",[]),batch.slot]
    data["research_count"] = old.get("research_count", 0) + 1
    for item, record in zip(batch.items, data["items"]):
        record["id"] = item.stable_id()
        record["slot"] = batch.slot
    data["items"] = [*old.get("items",[]),*data["items"]]
    RECOMMENDATIONS_DIR.mkdir(parents=True, exist_ok=True)
    archive = RECOMMENDATIONS_DIR / "history"
    archive.mkdir(exist_ok=True)
    stamp = batch.researched_at.strftime("%H%M%S") + "_" + uuid.uuid4().hex[:8]
    (archive / f"{batch.date}_{stamp}.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    target = RECOMMENDATIONS_DIR / f"{batch.date}.json"
    temp = target.with_suffix(f".{uuid.uuid4().hex}.tmp")
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(temp, target)
    return data


def recommended_products():
    """History survives production resets; normalized identities forbid reworded repeats."""
    seen = set()
    for path in list(RECOMMENDATIONS_DIR.glob('????-??-??.json')) + list((RECOMMENDATIONS_DIR/'history').glob('*.json')):
        for item in json.loads(path.read_text(encoding='utf-8')).get('items', []):
            seen.add(item['category'] + ':' + product_key(item.get('product_identity') or item['subject']))
    return seen
