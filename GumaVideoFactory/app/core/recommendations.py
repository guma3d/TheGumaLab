"""검증된 조사 결과를 일별 5+5 추천 목록으로 저장. AI 생성/영상 호출 없음."""
import hashlib
import json
import os
import uuid
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse
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

    @model_validator(mode="after")
    def complete_daily_list(self):
        if self.date != now_kst().strftime("%Y-%m-%d"):
            raise ValueError("오늘 한국시간 날짜의 목록만 갱신할 수 있습니다.")
        if self.researched_at.tzinfo is None or self.researched_at.astimezone(KST).strftime("%Y-%m-%d") != self.date:
            raise ValueError("조사 시간은 한국시간 기준 오늘이어야 합니다.")
        if self.researched_at > now_kst() + timedelta(minutes=5):
            raise ValueError("미래 조사 시간은 사용할 수 없습니다.")
        for category in {item.category for item in self.items}:
            if sum(i.category == category for i in self.items) != 5:
                raise ValueError("카테고리별 정확히 5개가 필요합니다.")
        if len({i.stable_id() for i in self.items}) != len(self.items):
            raise ValueError("중복 아이템은 사용할 수 없습니다.")
        for item in self.items:
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
    data = batch.model_dump(mode="json")
    updated_categories = {item.category for item in batch.items}
    data["items"].extend(item for item in old.get("items", []) if item["category"] not in updated_categories)
    data["research_count"] = old.get("research_count", 0) + 1
    for item, record in zip(batch.items, data["items"]):
        record["id"] = item.stable_id()
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
