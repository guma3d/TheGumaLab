from __future__ import annotations

import html
import json
import os
import queue
import re
import threading
import time
import uuid
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import quote, urlencode
import urllib.error
import urllib.request

import tenacity
from dotenv import load_dotenv
from flask import Flask, jsonify, request, send_file, send_from_directory

try:
    from google import genai
    from google.genai import errors, types
except Exception:  # pragma: no cover - optional runtime dependency
    genai = None
    errors = None
    types = None


ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT.parent / ".env")
load_dotenv(ROOT / ".env")

DATA_DIR = Path(os.getenv("DATA_DIR", ROOT / "data"))
OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", ROOT / "outputs" / "html"))
DATA_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

TASK_STATUS_FILE = DATA_DIR / "task_status.json"
APP_TITLE = "GumaTutorDoc"

app = Flask(__name__, static_folder=".", static_url_path="")

task_queue: queue.Queue[tuple[str, dict[str, Any]]] = queue.Queue()
task_lock = threading.RLock()
task_status: dict[str, dict[str, Any]] = {}

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GUMATUBE_GEMINI_MODEL = "gemini-3.5-flash"


def normalize_gemini_model(model_name: str | None) -> str:
    model_name = (model_name or "").strip()
    if not model_name or model_name.startswith("gpt-") or "2.5-flash" in model_name:
        return GUMATUBE_GEMINI_MODEL
    return model_name


PRIMARY_MODEL = normalize_gemini_model(os.getenv("GUMATUTORDOC_MODEL", os.getenv("GEMINI_MODEL", GUMATUBE_GEMINI_MODEL)))
MODEL_CHAIN = [PRIMARY_MODEL]
gemini_client = genai.Client(api_key=GEMINI_API_KEY) if genai and GEMINI_API_KEY else None

if gemini_client and types:
    original_generate_content = gemini_client.models.generate_content
    _gemini_last_req_time = 0.0
    _gemini_req_lock = threading.Lock()

    def _is_retryable_gemini_exception(exc: Exception) -> bool:
        error_msg = str(exc)
        return (
            "429" in error_msg
            or "RESOURCE_EXHAUSTED" in error_msg
            or "503" in error_msg
            or "UNAVAILABLE" in error_msg
        )

    def _gemini_before_sleep(retry_state: tenacity.RetryCallState) -> None:
        exc = retry_state.outcome.exception() if retry_state.outcome else None
        error_msg = str(exc)
        error_type = (
            "Quota/Rate Limit (429)"
            if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg
            else "Server Overloaded (503)"
        )
        wait_time = retry_state.next_action.sleep if retry_state.next_action else 0
        print(f"[Gemini API] {error_type}. retry in {wait_time:.1f}s ({retry_state.attempt_number}/5)")

    class GeminiWait(tenacity.wait.wait_base):
        def __init__(self, minimum: float = 30, maximum: float = 120):
            self.minimum = minimum
            self.maximum = maximum

        def __call__(self, retry_state: tenacity.RetryCallState) -> float:
            wait_time = min(self.minimum * (2 ** (retry_state.attempt_number - 1)), self.maximum)
            exc = retry_state.outcome.exception() if retry_state.outcome else None
            match = re.search(r"retry in ([\d.]+)s", str(exc), re.IGNORECASE)
            if match:
                try:
                    wait_time = max(wait_time, float(match.group(1)) + 2.0)
                except ValueError:
                    pass
            return wait_time

    def _with_gumatube_safety_settings(config: Any | None) -> Any:
        safety_settings = [
            types.SafetySetting(
                category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                threshold=types.HarmBlockThreshold.BLOCK_NONE,
            ),
            types.SafetySetting(
                category=types.HarmCategory.HARM_CATEGORY_HARASSMENT,
                threshold=types.HarmBlockThreshold.BLOCK_NONE,
            ),
            types.SafetySetting(
                category=types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                threshold=types.HarmBlockThreshold.BLOCK_NONE,
            ),
            types.SafetySetting(
                category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                threshold=types.HarmBlockThreshold.BLOCK_NONE,
            ),
        ]
        if config is None:
            return types.GenerateContentConfig(safety_settings=safety_settings)
        if hasattr(config, "safety_settings") and not getattr(config, "safety_settings", None):
            config.safety_settings = safety_settings
        elif isinstance(config, dict) and "safety_settings" not in config:
            config["safety_settings"] = safety_settings
        return config

    @tenacity.retry(
        retry=tenacity.retry_if_exception(_is_retryable_gemini_exception),
        wait=GeminiWait(minimum=30, maximum=120),
        stop=tenacity.stop_after_attempt(5),
        before_sleep=_gemini_before_sleep,
        reraise=True,
    )
    def generate_content_with_retry(*args: Any, **kwargs: Any) -> Any:
        global _gemini_last_req_time
        with _gemini_req_lock:
            elapsed = time.time() - _gemini_last_req_time
            if elapsed < 4.1:
                time.sleep(4.1 - elapsed)
            _gemini_last_req_time = time.time()

        kwargs["config"] = _with_gumatube_safety_settings(kwargs.get("config"))
        return original_generate_content(*args, **kwargs)

    gemini_client.models.generate_content = generate_content_with_retry


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def load_task_status() -> None:
    global task_status
    if not TASK_STATUS_FILE.exists():
        task_status = {}
        return

    try:
        data = json.loads(TASK_STATUS_FILE.read_text(encoding="utf-8-sig"))
        if isinstance(data, dict):
            task_status = data
    except Exception as exc:
        print(f"[status] load failed: {exc}")
        task_status = {}

    changed = False
    for task in task_status.values():
        if task.get("status") in {"queued", "processing"}:
            task["status"] = "failed"
            task["progress"] = "서버 재시작으로 작업이 중단되었습니다."
            task["error"] = task["progress"]
            task["updated_at"] = now_iso()
            changed = True
    if changed:
        save_task_status()


def save_task_status() -> None:
    tmp = TASK_STATUS_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(task_status, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(TASK_STATUS_FILE)


def update_task(task_id: str, **changes: Any) -> None:
    with task_lock:
        task = task_status.setdefault(task_id, {})
        task.update(changes)
        task["updated_at"] = now_iso()
        save_task_status()


def safe_slug(text: str) -> str:
    slug = re.sub(r'[<>:"/\\|?*\x00-\x1f]+', "", text.strip())
    slug = re.sub(r"\s+", "_", slug)
    slug = slug.strip("._-")
    return (slug or "learning_topic")[:80]


def extract_json(text: str) -> dict[str, Any]:
    raw_text = text.strip()
    candidates = [raw_text]
    fenced = re.search(r"```(?:json)?\s*(.*?)```", raw_text, re.DOTALL | re.IGNORECASE)
    if fenced:
        candidates.insert(0, fenced.group(1).strip())

    decoder = json.JSONDecoder()
    last_error: Exception | None = None
    for candidate in candidates:
        start = candidate.find("{")
        while start >= 0:
            try:
                parsed, _ = decoder.raw_decode(candidate[start:])
                if isinstance(parsed, dict):
                    return parsed
                last_error = ValueError("Gemini response JSON was not an object")
            except json.JSONDecodeError as exc:
                last_error = exc
            start = candidate.find("{", start + 1)

    preview = raw_text[:500].replace("\n", " ")
    raise ValueError(f"Gemini response did not contain a valid JSON object: {last_error}; preview={preview}")


def fetch_json_url(url: str, *, timeout: int = 8) -> dict[str, Any] | None:
    request_obj = urllib.request.Request(
        url,
        headers={"User-Agent": "GumaTutorDoc/1.0 (https://gumatutordoc.guma3d.com)"},
    )
    try:
        with urllib.request.urlopen(request_obj, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError) as exc:
        print(f"[wiki] fetch failed: {exc}")
        return None


def wiki_api_url(lang: str, params: dict[str, Any]) -> str:
    base_params = {"format": "json", "origin": "*"}
    base_params.update(params)
    return f"https://{lang}.wikipedia.org/w/api.php?" + urlencode(base_params)


def commons_file_url(filename: str) -> dict[str, str] | None:
    filename = str(filename or "").replace("File:", "").strip()
    if not filename:
        return None
    params = {
        "action": "query",
        "titles": f"File:{filename}",
        "prop": "imageinfo",
        "iiprop": "url|mime|size|extmetadata",
        "iiurlwidth": "1200",
        "format": "json",
        "origin": "*",
    }
    payload = fetch_json_url("https://commons.wikimedia.org/w/api.php?" + urlencode(params))
    pages = ((payload or {}).get("query", {}).get("pages", {}) or {}).values()
    for page in pages:
        info_items = page.get("imageinfo") or []
        if not info_items:
            continue
        info = info_items[0]
        image_url = str(info.get("thumburl") or info.get("url") or "")
        if image_url:
            metadata = info.get("extmetadata") or {}
            artist = clean_metadata_text((metadata.get("Artist") or {}).get("value"))
            license_short = clean_metadata_text((metadata.get("LicenseShortName") or {}).get("value"))
            return {
                "image_url": image_url,
                "source_url": str(info.get("descriptionurl") or ""),
                "source_title": str(page.get("title") or f"File:{filename}").replace("File:", ""),
                "credit": ", ".join(part for part in [artist, license_short] if part),
            }
    return None


def fetch_wikipedia_page(topic: str, lang: str) -> dict[str, Any] | None:
    search_payload = fetch_json_url(
        wiki_api_url(
            lang,
            {
                "action": "query",
                "list": "search",
                "srsearch": topic,
                "srlimit": "1",
            },
        )
    )
    matches = (search_payload or {}).get("query", {}).get("search") or []
    if not matches:
        return None

    title = str(matches[0].get("title") or "").strip()
    if not title:
        return None
    payload = fetch_json_url(
        wiki_api_url(
            lang,
            {
                "action": "query",
                "titles": title,
                "prop": "extracts|pageimages|pageprops|langlinks",
                "explaintext": "1",
                "exsectionformat": "plain",
                "piprop": "original|thumbnail",
                "pithumbsize": "1200",
                "lllang": "en",
                "redirects": "1",
            },
        )
    )
    pages = list(((payload or {}).get("query", {}).get("pages", {}) or {}).values())
    if not pages:
        return None
    page = pages[0]
    if str(page.get("missing") or ""):
        return None
    page_id = str(page.get("pageid") or "")
    return {
        "lang": lang,
        "title": str(page.get("title") or title).strip(),
        "page_id": page_id,
        "source_url": f"https://{lang}.wikipedia.org/wiki/{quote(str(page.get('title') or title).replace(' ', '_'))}",
        "extract": str(page.get("extract") or "").strip(),
        "wikidata_id": str((page.get("pageprops") or {}).get("wikibase_item") or "").strip(),
        "en_title": str(((page.get("langlinks") or [{}])[0] or {}).get("*") or "").strip(),
        "page_image": (page.get("original") or page.get("thumbnail") or {}).get("source"),
    }


def fetch_wikidata_reference(qid: str) -> dict[str, Any]:
    if not qid:
        return {}
    payload = fetch_json_url(
        "https://www.wikidata.org/w/api.php?"
        + urlencode(
            {
                "action": "wbgetentities",
                "ids": qid,
                "props": "labels|aliases|claims",
                "languages": "ko|en",
                "format": "json",
                "origin": "*",
            }
        )
    )
    entity = ((payload or {}).get("entities") or {}).get(qid) or {}
    labels = entity.get("labels") or {}
    aliases = entity.get("aliases") or {}
    claims = entity.get("claims") or {}

    image_files: list[str] = []
    for claim in claims.get("P18") or []:
        value = (((claim.get("mainsnak") or {}).get("datavalue") or {}).get("value") or "")
        if value:
            image_files.append(str(value))
    commons_category = ""
    for claim in claims.get("P373") or []:
        value = (((claim.get("mainsnak") or {}).get("datavalue") or {}).get("value") or "")
        if value:
            commons_category = str(value)
            break

    alias_values: list[str] = []
    for lang_aliases in aliases.values():
        for item in lang_aliases or []:
            value = str(item.get("value") or "").strip()
            if value and value not in alias_values:
                alias_values.append(value)

    return {
        "labels": {
            "ko": str((labels.get("ko") or {}).get("value") or "").strip(),
            "en": str((labels.get("en") or {}).get("value") or "").strip(),
        },
        "aliases": alias_values[:10],
        "image_files": image_files[:4],
        "commons_category": commons_category,
    }


def fetch_wikidata_search_reference(topic: str) -> dict[str, Any] | None:
    for language in ("ko", "en"):
        payload = fetch_json_url(
            "https://www.wikidata.org/w/api.php?"
            + urlencode(
                {
                    "action": "wbsearchentities",
                    "search": topic,
                    "language": language,
                    "uselang": language,
                    "limit": "1",
                    "format": "json",
                    "origin": "*",
                }
            )
        )
        results = (payload or {}).get("search") or []
        if not results:
            continue
        qid = str(results[0].get("id") or "").strip()
        if not qid:
            continue
        wikidata = fetch_wikidata_reference(qid)
        labels = wikidata.get("labels") or {}
        image_candidates: list[dict[str, str]] = []
        for filename in wikidata.get("image_files") or []:
            image_data = commons_file_url(str(filename))
            if image_data:
                image_candidates.append(image_data)
        title = str(labels.get("ko") or labels.get("en") or results[0].get("label") or topic).strip()
        description = str(results[0].get("description") or "").strip()
        return {
            "title": title,
            "lang": "wikidata",
            "source_url": f"https://www.wikidata.org/wiki/{qid}",
            "extract": description,
            "wikidata_id": qid,
            "english_title": str(labels.get("en") or "").strip(),
            "korean_title": str(labels.get("ko") or title).strip(),
            "aliases": wikidata.get("aliases") or [],
            "commons_category": wikidata.get("commons_category") or "",
            "image_candidates": image_candidates[:5],
        }
    return None


def fetch_wiki_reference(topic: str) -> dict[str, Any] | None:
    cache_key = f"wiki:{topic.lower().strip()}"
    if cache_key in wiki_cache:
        cached = wiki_cache[cache_key]
        return dict(cached) if isinstance(cached, dict) else None

    langs = ("ko", "en") if re.search(r"[가-힣]", topic) else ("en", "ko")
    page = None
    for lang in langs:
        page = fetch_wikipedia_page(topic, lang)
        if page:
            break
    if not page:
        reference = fetch_wikidata_search_reference(topic)
        wiki_cache[cache_key] = reference
        return dict(reference) if isinstance(reference, dict) else None

    wikidata = fetch_wikidata_reference(page.get("wikidata_id", ""))
    image_candidates: list[dict[str, str]] = []
    if page.get("page_image"):
        image_candidates.append(
            {
                "image_url": str(page.get("page_image")),
                "source_url": str(page.get("source_url") or ""),
                "source_title": str(page.get("title") or topic),
                "credit": "Wikipedia",
            }
        )
    for filename in wikidata.get("image_files") or []:
        image_data = commons_file_url(str(filename))
        if image_data and image_data.get("image_url") not in {item.get("image_url") for item in image_candidates}:
            image_candidates.append(image_data)

    reference = {
        "title": page.get("title") or topic,
        "lang": page.get("lang") or "",
        "source_url": page.get("source_url") or "",
        "extract": str(page.get("extract") or "")[:7000],
        "wikidata_id": page.get("wikidata_id") or "",
        "english_title": page.get("en_title") or (wikidata.get("labels") or {}).get("en") or "",
        "korean_title": (wikidata.get("labels") or {}).get("ko") or page.get("title") or topic,
        "aliases": wikidata.get("aliases") or [],
        "commons_category": wikidata.get("commons_category") or "",
        "image_candidates": image_candidates[:5],
    }
    wiki_cache[cache_key] = reference
    return dict(reference)


def wiki_context_for_prompt(reference: dict[str, Any] | None) -> str:
    if not reference:
        return ""
    facts = str(reference.get("extract") or "").strip()
    facts = re.sub(r"\n{3,}", "\n\n", facts)[:5500]
    names = [
        str(reference.get("korean_title") or "").strip(),
        str(reference.get("english_title") or "").strip(),
        *[str(alias).strip() for alias in reference.get("aliases") or []],
    ]
    names = [name for name in dict.fromkeys(names) if name][:12]
    lines = [
        "REFERENCE_CONTEXT_FROM_WIKIPEDIA_WIKIDATA",
        f"title: {reference.get('title') or ''}",
        f"source_url: {reference.get('source_url') or ''}",
        f"wikidata_id: {reference.get('wikidata_id') or ''}",
        f"canonical_names: {', '.join(names)}",
        f"commons_category: {reference.get('commons_category') or ''}",
        "facts:",
        facts,
    ]
    return "\n".join(lines)


def apply_wiki_reference(pack: dict[str, Any], reference: dict[str, Any] | None) -> dict[str, Any]:
    if not reference:
        return pack

    sources = pack.get("sources")
    if not isinstance(sources, list):
        sources = []
    wikidata_id = str(reference.get("wikidata_id") or "").strip()
    source_candidates = [reference.get("source_url")]
    if wikidata_id:
        source_candidates.append(f"https://www.wikidata.org/wiki/{wikidata_id}")
    for source in source_candidates:
        source_text = str(source or "").strip()
        if source_text and source_text not in sources:
            sources.insert(0, source_text)
    pack["sources"] = sources

    sections = pack.get("content_sections")
    if not isinstance(sections, list) or not sections:
        return pack

    image_candidates = [
        candidate
        for candidate in reference.get("image_candidates") or []
        if isinstance(candidate, dict) and str(candidate.get("image_url") or "").strip()
    ]
    if image_candidates:
        first_section = sections[0]
        if isinstance(first_section, dict):
            images = first_section.get("images")
            if not isinstance(images, list):
                images = []
            topic_title = str(reference.get("title") or pack.get("topic") or "").strip()
            primary = dict(image_candidates[0])
            primary.update(
                {
                    "title": primary.get("source_title") or f"{topic_title} Wikipedia image",
                    "caption": f"{topic_title}를 실제 자료 이미지로 먼저 확인합니다.",
                    "query": f"{reference.get('english_title') or topic_title} photograph",
                    "notes": ["실제 자료 사진을 먼저 보며 전체 모습을 확인합니다."],
                }
            )
            first_section["images"] = [primary, *images][:2]

    english_title = str(reference.get("english_title") or "").strip()
    commons_category = str(reference.get("commons_category") or "").strip()
    category_images: list[dict[str, str]] = []
    if commons_category and english_title:
        category_images = fetch_commons_category_candidates(commons_category, english_title, limit=12)
    if english_title:
        category_index = 0
        for section in sections:
            if not isinstance(section, dict):
                continue
            images = section.get("images")
            if not isinstance(images, list):
                images = []
            section_title = str(section.get("title") or "").strip()
            wiki_query = f"{english_title} {section_title} photograph"
            if commons_category:
                wiki_query = f"{english_title} {commons_category} {section_title} photograph"
            images.append(
                {
                    "title": f"{section_title or english_title} reference photo",
                    "caption": "위키/위키미디어 자료와 맞는 사진을 우선 찾습니다.",
                    "query": wiki_query,
                    "notes": [],
                }
            )
            if category_index < len(category_images):
                category_image = dict(category_images[category_index])
                category_index += 1
                category_image.update(
                    {
                        "title": category_image.get("source_title") or f"{section_title or english_title} Wikimedia image",
                        "caption": f"{section_title or english_title}와 직접 관련된 위키미디어 카테고리 이미지입니다.",
                        "query": wiki_query,
                        "notes": [],
                    }
                )
                images.insert(0, category_image)
            section["images"] = images[:3]
    return pack


def generate_with_gemini(topic: str, grade: str, quiz_count: int, reference: dict[str, Any] | None = None) -> dict[str, Any]:
    if not gemini_client or not types:
        raise RuntimeError("GEMINI_API_KEY가 없어 AI 생성기를 사용할 수 없습니다.")

    schema = {
        "topic": topic,
        "grade": grade,
        "title": "학습자료 제목",
        "subtitle": "짧은 소개 문장",
        "summary": [
            "전체 내용을 이해하는 데 중요한 문장 1",
            "전체 내용을 이해하는 데 중요한 문장 2",
            "전체 내용을 이해하는 데 중요한 문장 3",
            "전체 내용을 이해하는 데 중요한 문장 4",
            "전체 내용을 이해하는 데 중요한 문장 5",
        ],
        "content_sections": [
            {
                "title": "자세히 배울 내용",
                "paragraphs": ["아이 눈높이에 맞춘 자세한 설명 문단 1", "자세한 설명 문단 2"],
                "examples": ["생활 속 예시", "관찰하거나 떠올려볼 장면"],
                "images": [
                    {
                        "title": "내용을 이해하는 데 필요한 사진 제목",
                        "caption": "사진을 보며 확인할 핵심 내용",
                        "query": "specific English Wikimedia Commons photo search query",
                        "notes": ["사진에서 바로 확인할 짧은 문장 1", "사진을 보며 떠올릴 짧은 문장 2"],
                    }
                ],
            }
        ],
        "key_points": [
            {"title": "핵심 개념", "body": "쉬운 설명", "example": "생활 속 예시나 비유"}
        ],
        "vocabulary": [{"term": "용어", "meaning": "쉬운 뜻"}],
        "quiz": [
            {
                "question": "객관식 문제",
                "choices": ["보기 1", "보기 2", "보기 3"],
                "answer": "정답 보기",
                "explanation": "왜 정답인지 쉬운 해설",
            }
        ],
        "sources": ["검증에 참고할 만한 공개 자료명 또는 기관명"],
    }
    system_prompt = (
        "당신은 어린이와 청소년을 위한 한국어 학습자료 편집자입니다. "
        "사용자가 준 주제에 대해 나이에 맞는 학습자료와 간단한 퀴즈를 만듭니다. "
        "사실로 단정하기 어려운 내용은 참고자료에 검증 가능한 자료명을 적고, "
        "위험한 실험이나 따라 하면 안 되는 행동은 안전한 관찰 활동으로 바꿉니다. "
        "반드시 JSON 객체만 반환합니다."
    )
    reference_context = wiki_context_for_prompt(reference)
    reference_instruction = ""
    if reference_context:
        reference_instruction = (
            "Use the REFERENCE_CONTEXT_FROM_WIKIPEDIA_WIKIDATA block as the primary factual source. "
            "Rewrite it for the requested Korean grade level instead of copying encyclopedia text. "
            "Do not invent facts that conflict with the reference. "
            "For image queries, prefer the canonical English/Wikidata name, Wikimedia Commons category, and exact subject terms from the reference.\n\n"
            f"{reference_context}\n\n"
        )

    user_prompt = (
        f"주제: {topic}\n"
        f"대상 수준: {grade}\n"
        f"퀴즈 수: {quiz_count}\n\n"
        f"{reference_instruction}"
        "아래 스키마와 같은 키를 가진 JSON만 반환하세요. "
        "key_points는 4~6개, vocabulary는 4~8개, quiz는 요청한 수만큼 작성하세요. "
        "summary는 전체 내용을 대표하는 중요한 한국어 문장 정확히 5개로 작성하세요. "
        "content_sections는 4~10개로 만들고, 내용이 많은 주제는 한 페이지에 문장을 많이 넣지 말고 소주제를 더 잘게 나누어 페이지와 사진을 늘리세요. 각 항목의 paragraphs에는 디테일한 설명을 2~4문단 넣으세요. "
        "paragraphs에서 핵심 용어, 관찰 포인트, 꼭 기억할 단어는 **이런 형식**으로 표시하세요. "
        "각 content_sections 항목의 images에는 그 소주제를 이해하는 데 직접 필요한 실제 사진 검색어를 1~2개 넣으세요. "
        "그림, 일러스트, 도해, 지도, 아이콘, 로고, 차트 검색어는 넣지 마세요. "
        "images.query는 Wikimedia Commons에서 실제 자료 사진을 찾기 좋은 구체적인 영어 검색어로 작성하고, photo 또는 photograph 같은 단어를 포함하세요. "
        "사진 검색어는 반드시 주제 자체가 주 피사체가 되도록 작성하세요. 예를 들어 주제가 개미라면 개미 종, 개미 몸, 개미집, 여왕개미, 일개미 사진처럼 개미 자체가 중심인 검색어만 사용하세요. "
        "소주제가 주둥이, 알, 산란, 서식지, 몸 구조처럼 특정 부분을 설명하더라도 검색어에는 반드시 전체 주제 생물/사물의 정확한 영어 이름을 먼저 포함하세요. 예: elephant weevil rostrum photograph, elephant weevil eggs photograph, honeypot ant replete worker photograph. "
        "정확한 소주제 사진을 찾기 어렵다면 다른 동물이나 도구 사진을 쓰지 말고, 같은 주제 생물/사물의 선명한 실제 사진 검색어를 사용하세요. "
        "단, 공룡, 멸종생물, 신화 속 괴물처럼 현실에서 실제 사진이 존재할 수 없는 주제는 예외입니다. 이런 경우에만 realistic reconstruction, paleoart, scientific illustration, lifelike illustration 같은 실사에 가까운 복원도/일러스트 검색어를 사용할 수 있습니다. "
        "모든 content_sections에는 반드시 이미지가 있어야 합니다. 실제 주제 사진을 찾기 어려운 경우에도 빈 이미지로 두지 말고, 주제와 직접 맞는 실사풍 복원도나 디테일한 과학 일러스트 검색어를 넣으세요. "
        "아이, 사람, 손으로 잡는 장면, 돋보기, 관찰 도구, 교실 활동, 장난감, 모형처럼 주제 외 대상이 중심인 사진 검색어는 절대 사용하지 마세요. "
        "각 소주제의 이미지 검색어는 서로 다르게 작성해서 같은 사진이 반복되지 않게 하세요. 가능하면 Wikipedia, Wikimedia Commons, 박물관, 대학, 정부기관, 학술 참고자료의 사진으로 이어질 만한 정확한 영어 명칭을 사용하세요. "
        "images.notes에는 사진 옆에 보여줄 짧은 한국어 관찰 문장 2~3개를 넣으세요. "
        "예를 들어 서식지 설명에는 지역명 사진과 환경 사진 검색어를 함께 넣고, 구조/과정 설명에는 관련 부위·과정·비교 사진 검색어를 넣으세요. "
        "모든 설명은 한국어로, 문장은 짧고 읽기 쉽게 작성하세요.\n\n"
        f"{json.dumps(schema, ensure_ascii=False, indent=2)}"
    )

    last_exc: Exception | None = None
    for model_name in MODEL_CHAIN:
        try:
            config = types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0.55,
                response_mime_type="application/json",
            )
            response = gemini_client.models.generate_content(
                model=model_name,
                contents=user_prompt,
                config=config,
            )
            return normalize_pack(extract_json(response.text or ""), topic, grade, quiz_count)
        except Exception as exc:
            if errors and isinstance(exc, getattr(errors, "ClientError", ())):
                if getattr(exc, "code", None) != 429:
                    raise
            last_exc = exc
            print(f"[gemini] {model_name} failed: {exc}")
    raise RuntimeError(f"AI 생성 실패: {last_exc}")


def generate_fallback_pack(topic: str, grade: str, quiz_count: int) -> dict[str, Any]:
    quiz_count = max(1, min(quiz_count, 7))
    quiz = []
    for idx in range(quiz_count):
        quiz.append(
            {
                "question": f"{topic}을 배울 때 먼저 확인하면 좋은 것은 무엇일까요? ({idx + 1})",
                "choices": ["뜻과 기본 개념", "상관없는 이야기", "아무 자료 없이 외우기"],
                "answer": "뜻과 기본 개념",
                "explanation": "처음에는 주제의 뜻과 기본 개념을 정확히 잡는 것이 좋아요.",
            }
        )
    return {
        "topic": topic,
        "grade": grade,
        "title": f"{topic} 학습자료",
        "subtitle": "AI 연결 전에도 저장 흐름을 확인할 수 있는 기본 템플릿입니다.",
        "summary": [
            f"{topic}을 이해하려면 먼저 무엇을 뜻하는지 살펴보는 것이 중요합니다.",
            f"{topic}은 여러 작은 개념과 예시가 서로 연결되어 있습니다.",
            "그림이나 사진을 함께 보면 글로만 볼 때보다 더 쉽게 이해할 수 있습니다.",
            "중요한 단어를 정리하면 뒤의 자세한 설명을 따라가기 쉬워집니다.",
            "마지막에는 간단한 퀴즈로 배운 내용을 스스로 확인할 수 있습니다.",
        ],
        "content_sections": [
            {
                "title": f"{topic}의 기본 뜻",
                "paragraphs": [
                    f"{topic}이 무엇을 말하는지 먼저 쉬운 말로 정리합니다.",
                    "관련 자료를 다시 생성하면 이 부분에 실제 사실을 바탕으로 한 자세한 설명이 들어갑니다.",
                ],
                "examples": ["백과사전이나 교과서에서 같은 주제를 찾아 비교해보기"],
                "images": [
                    {
                        "title": f"{topic} 관련 사진",
                        "caption": "주제를 실제 자료 사진으로 확인합니다.",
                        "query": f"{topic} photo",
                    }
                ],
            },
            {
                "title": "더 깊게 생각해보기",
                "paragraphs": [
                    "이 주제가 우리 생활, 자연, 역사, 기술 중 어디와 연결되는지 생각해봅니다.",
                    "궁금한 점을 질문으로 바꾸면 다음에 찾아볼 내용이 더 분명해집니다.",
                ],
                "examples": ["왜 그럴까?", "언제 생길까?", "어디에서 볼 수 있을까?"],
                "images": [
                    {
                        "title": f"{topic} 주변 환경",
                        "caption": "주제와 연결된 장소나 환경을 사진으로 살펴봅니다.",
                        "query": f"{topic} habitat environment photo",
                    }
                ],
            },
        ],
        "key_points": [
            {
                "title": "무엇인지 알아보기",
                "body": f"{topic}이 무엇을 뜻하는지 먼저 짧게 정리합니다.",
                "example": "교과서, 백과사전, 신뢰할 수 있는 기관 자료를 비교합니다.",
            },
            {
                "title": "왜 중요한지 생각하기",
                "body": f"{topic}이 생활, 자연, 역사, 기술 중 어디와 연결되는지 살펴봅니다.",
                "example": "내 주변에서 볼 수 있는 사례를 하나 찾습니다.",
            },
            {
                "title": "질문으로 정리하기",
                "body": "모르는 점을 질문으로 바꾸면 다음 학습 단계가 분명해집니다.",
                "example": "왜 그럴까, 언제 생길까, 어디에 쓰일까처럼 질문합니다.",
            },
        ],
        "vocabulary": [
            {"term": "핵심 개념", "meaning": "주제를 이해하는 데 가장 중요한 생각"},
            {"term": "예시", "meaning": "개념을 쉽게 이해하도록 보여주는 실제 사례"},
            {"term": "근거", "meaning": "설명이 맞는지 확인할 수 있는 자료"},
        ],
        "quiz": quiz,
        "sources": ["AI 생성 비활성 상태: 직접 검증 자료를 추가하세요."],
    }


def normalize_image_items(value: Any, topic: str, section_title: str) -> list[dict[str, str]]:
    if isinstance(value, dict):
        value = [value]
    if not isinstance(value, list):
        value = []

    normalized: list[dict[str, str]] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        title = str(item.get("title") or item.get("name") or "").strip()
        caption = str(item.get("caption") or item.get("description") or "").strip()
        query = str(item.get("query") or item.get("search_query") or item.get("prompt") or "").strip()
        image_url = str(item.get("image_url") or item.get("url") or "").strip()
        source_url = str(item.get("source_url") or "").strip()
        source_title = str(item.get("source_title") or "").strip()
        credit = str(item.get("credit") or "").strip()
        notes = item.get("notes") or item.get("observations") or item.get("photo_notes")
        if isinstance(notes, str):
            notes = [notes]
        if not isinstance(notes, list):
            notes = []
        if query or image_url:
            normalized.append(
                {
                    "title": title or section_title or "이미지 자료",
                    "caption": caption,
                    "query": query or title or section_title or topic,
                    "image_url": image_url,
                    "source_url": source_url,
                    "source_title": source_title,
                    "credit": credit,
                    "notes": [str(note).strip() for note in notes if str(note).strip()][:3],
                }
            )

    if not normalized:
        normalized.append(
            {
                "title": f"{section_title or topic} 사진",
                "caption": f"{section_title or topic}을 실제 이미지로 살펴봅니다.",
                "query": f"{topic} {section_title} photo",
                "image_url": "",
                "notes": [],
            }
        )

    return normalized[:2]


def normalize_pack(pack: dict[str, Any], topic: str, grade: str, quiz_count: int) -> dict[str, Any]:
    pack["topic"] = str(pack.get("topic") or topic).strip()
    pack["grade"] = str(pack.get("grade") or grade).strip()
    pack["title"] = str(pack.get("title") or f"{topic} 학습자료").strip()
    pack["subtitle"] = str(pack.get("subtitle") or "").strip()

    summary = pack.get("summary")
    if isinstance(summary, str):
        summary = [line.strip() for line in re.split(r"[\n\r]+", summary) if line.strip()]
    if not isinstance(summary, list):
        summary = []
    normalized_summary = [str(item).strip() for item in summary if str(item).strip()]
    if not normalized_summary and pack.get("overview"):
        normalized_summary = [str(pack.get("overview")).strip()]
    while len(normalized_summary) < 5:
        normalized_summary.append(f"{topic}을 이해하는 데 필요한 중요한 내용을 차근차근 살펴봅니다.")
    pack["summary"] = normalized_summary[:5]

    content_sections = pack.get("content_sections")
    if not isinstance(content_sections, list):
        content_sections = []
    normalized_sections = []
    for item in content_sections:
        if not isinstance(item, dict):
            continue
        paragraphs = item.get("paragraphs")
        if isinstance(paragraphs, str):
            paragraphs = [paragraphs]
        if not isinstance(paragraphs, list):
            paragraphs = []
        examples = item.get("examples")
        if isinstance(examples, str):
            examples = [examples]
        if not isinstance(examples, list):
            examples = []
        section_title = str(item.get("title") or "자세한 설명").strip()
        normalized_sections.append(
            {
                "title": section_title,
                "paragraphs": [str(paragraph).strip() for paragraph in paragraphs if str(paragraph).strip()],
                "examples": [str(example).strip() for example in examples if str(example).strip()],
                "images": normalize_image_items(item.get("images") or item.get("visuals"), topic, section_title),
            }
        )

    if not normalized_sections:
        for point in pack.get("key_points", []):
            if not isinstance(point, dict):
                continue
            paragraphs = [str(point.get("body") or "").strip()]
            examples = [str(point.get("example") or "").strip()]
            normalized_sections.append(
                {
                    "title": str(point.get("title") or "자세한 설명").strip(),
                    "paragraphs": [paragraph for paragraph in paragraphs if paragraph],
                    "examples": [example for example in examples if example],
                    "images": normalize_image_items([], topic, str(point.get("title") or "자세한 설명").strip()),
                }
            )
    if not normalized_sections:
        normalized_sections = [
            {
                "title": f"{topic} 자세히 알아보기",
                "paragraphs": [pack["summary"][0]],
                "examples": [],
                "images": normalize_image_items([], topic, f"{topic} 자세히 알아보기"),
            }
        ]

    legacy_visuals = pack.get("visuals")
    if isinstance(legacy_visuals, list):
        target_index = 0
        for visual in legacy_visuals:
            if not normalized_sections:
                break
            image_items = normalize_image_items([visual], topic, normalized_sections[target_index]["title"])
            normalized_sections[target_index].setdefault("images", []).extend(image_items)
            normalized_sections[target_index]["images"] = normalized_sections[target_index]["images"][:2]
            target_index = (target_index + 1) % len(normalized_sections)

    pack["content_sections"] = normalized_sections[:10]
    pack["visuals"] = []

    pack["overview"] = str(pack.get("overview") or "").strip()

    for key in ("learning_goals", "activities", "sources"):
        value = pack.get(key)
        if not isinstance(value, list):
            pack[key] = []
        else:
            pack[key] = [str(item).strip() for item in value if str(item).strip()]

    key_points = pack.get("key_points")
    if not isinstance(key_points, list):
        key_points = []
    pack["key_points"] = [
        {
            "title": str(item.get("title", "")).strip(),
            "body": str(item.get("body", "")).strip(),
            "example": str(item.get("example", "")).strip(),
        }
        for item in key_points
        if isinstance(item, dict)
    ]

    vocabulary = pack.get("vocabulary")
    if not isinstance(vocabulary, list):
        vocabulary = []
    pack["vocabulary"] = [
        {"term": str(item.get("term", "")).strip(), "meaning": str(item.get("meaning", "")).strip()}
        for item in vocabulary
        if isinstance(item, dict)
    ]

    quiz = pack.get("quiz")
    if not isinstance(quiz, list):
        quiz = []
    normalized_quiz = []
    for item in quiz[: max(1, min(quiz_count, 7))]:
        if not isinstance(item, dict):
            continue
        choices = item.get("choices")
        if not isinstance(choices, list):
            choices = []
        normalized_quiz.append(
            {
                "question": str(item.get("question", "")).strip(),
                "choices": [str(choice).strip() for choice in choices if str(choice).strip()][:4],
                "answer": str(item.get("answer", "")).strip(),
                "explanation": str(item.get("explanation", "")).strip(),
            }
        )
    pack["quiz"] = normalized_quiz
    pack["verification_note"] = str(pack.get("verification_note") or "").strip()
    return pack


def e(value: Any) -> str:
    return html.escape(str(value or ""), quote=True)


def list_html(items: list[Any], class_name: str = "") -> str:
    if not items:
        return ""
    return "<ul{}>{}</ul>".format(
        f' class="{class_name}"' if class_name else "",
        "".join(f"<li>{e(item)}</li>" for item in items),
    )


def render_material_html_legacy(pack: dict[str, Any], task_id: str) -> str:
    goals = list_html(pack.get("learning_goals", []), "goals")
    activities = list_html(pack.get("activities", []))
    sources = list_html(pack.get("sources", []))

    key_points = "\n".join(
        f"""
        <section class="point">
          <h3>{e(point.get("title"))}</h3>
          <p>{e(point.get("body"))}</p>
          {f'<p class="example"><strong>예시</strong> {e(point.get("example"))}</p>' if point.get("example") else ''}
        </section>
        """
        for point in pack.get("key_points", [])
    )

    vocabulary = "\n".join(
        f"""
        <tr>
          <th>{e(item.get("term"))}</th>
          <td>{e(item.get("meaning"))}</td>
        </tr>
        """
        for item in pack.get("vocabulary", [])
    )

    quiz = "\n".join(
        f"""
        <section class="quiz-item">
          <h3>문제 {idx}</h3>
          <p>{e(item.get("question"))}</p>
          {list_html(item.get("choices", []), "choices")}
          <details>
            <summary>정답 보기</summary>
            <p><strong>{e(item.get("answer"))}</strong></p>
            <p>{e(item.get("explanation"))}</p>
          </details>
        </section>
        """
        for idx, item in enumerate(pack.get("quiz", []), start=1)
    )

    return f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="apple-mobile-web-app-capable" content="yes">
  <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
  <title>{e(pack.get("title"))}</title>
  <style>
    :root {{
      color-scheme: light;
      --ink: #172033;
      --muted: #596579;
      --line: #d9e1ec;
      --paper: #ffffff;
      --bg: #f4f7fb;
      --accent: #0f766e;
      --accent-soft: #dff5f1;
      --warm: #f59e0b;
      --warm-soft: #fff3d6;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: "Malgun Gothic", "Apple SD Gothic Neo", system-ui, sans-serif;
      color: var(--ink);
      background: var(--bg);
      line-height: 1.65;
    }}
    .page {{
      max-width: 980px;
      margin: 0 auto;
      padding: 40px 20px 72px;
    }}
    header {{
      padding: 28px 0 24px;
      border-bottom: 3px solid var(--accent);
    }}
    .meta {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-bottom: 18px;
      color: var(--muted);
      font-size: 14px;
    }}
    .pill {{
      border: 1px solid var(--line);
      border-radius: 999px;
      padding: 3px 10px;
      background: var(--paper);
    }}
    h1 {{
      margin: 0;
      font-size: 40px;
      line-height: 1.18;
      letter-spacing: 0;
    }}
    .subtitle {{
      margin: 14px 0 0;
      color: var(--muted);
      font-size: 18px;
    }}
    main {{
      display: grid;
      gap: 18px;
      margin-top: 22px;
    }}
    section.block {{
      background: var(--paper);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 22px;
    }}
    h2 {{
      margin: 0 0 14px;
      font-size: 22px;
      line-height: 1.3;
      letter-spacing: 0;
    }}
    h3 {{
      margin: 0 0 8px;
      font-size: 18px;
      line-height: 1.35;
      letter-spacing: 0;
    }}
    p {{ margin: 0 0 10px; }}
    ul {{ margin: 0; padding-left: 22px; }}
    .goals {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 10px;
      padding: 0;
      list-style: none;
    }}
    .goals li {{
      border-left: 4px solid var(--accent);
      background: var(--accent-soft);
      padding: 10px 12px;
      border-radius: 6px;
    }}
    .point {{
      border-top: 1px solid var(--line);
      padding-top: 16px;
      margin-top: 16px;
    }}
    .point:first-child {{
      border-top: 0;
      padding-top: 0;
      margin-top: 0;
    }}
    .example {{
      background: var(--warm-soft);
      border-left: 4px solid var(--warm);
      border-radius: 6px;
      padding: 10px 12px;
      color: #533b05;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
    }}
    th, td {{
      border-bottom: 1px solid var(--line);
      padding: 11px 10px;
      text-align: left;
      vertical-align: top;
    }}
    th {{
      width: 160px;
      color: var(--accent);
    }}
    .quiz-item {{
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 16px;
      margin-top: 12px;
    }}
    .choices {{
      margin: 8px 0 12px;
    }}
    details {{
      border-top: 1px solid var(--line);
      padding-top: 10px;
    }}
    summary {{
      cursor: pointer;
      color: var(--accent);
      font-weight: 700;
    }}
    footer {{
      margin-top: 22px;
      color: var(--muted);
      font-size: 13px;
    }}
    @media (max-width: 640px) {{
      .page {{ padding: 24px 14px 48px; }}
      h1 {{ font-size: 30px; }}
      section.block {{ padding: 18px; }}
      th {{ width: 110px; }}
    }}
  </style>
</head>
<body class="doc-view">
  <div class="page">
    <header>
      <div class="meta">
        <span class="pill">{e(APP_TITLE)}</span>
        <span class="pill">{e(pack.get("grade"))}</span>
        <span class="pill">문서 ID {e(task_id[:8])}</span>
      </div>
      <h1>{e(pack.get("title"))}</h1>
      <p class="subtitle">{e(pack.get("subtitle"))}</p>
    </header>
    <main>
      <section class="block">
        <h2>요약</h2>
        <p>{e(pack.get("overview"))}</p>
      </section>
      <section class="block">
        <h2>요약</h2>
        {goals}
      </section>
      <section class="block">
        <h2>핵심 내용</h2>
        {key_points}
      </section>
      <section class="block">
        <h2>용어 정리</h2>
        <table>
          <tbody>{vocabulary}</tbody>
        </table>
      </section>
      <section class="block">
        <h2>간단한 퀴즈</h2>
        {quiz}
      </section>
      <section class="block">
        <h2>내용</h2>
        {activities}
      </section>
      <section class="block">
        <h2>참고자료</h2>
        <p>{e(pack.get("verification_note") or "생성된 내용을 수업이나 발표에 쓰기 전 한 번 더 확인하세요.")}</p>
        {sources}
      </section>
    </main>
    <footer>생성일: {e(now_iso())}</footer>
  </div>
</body>
</html>
"""


def svg_placeholder_url(title: str, seed: int) -> str:
    palettes = [
        ("#e0f2fe", "#0284c7", "#fef3c7"),
        ("#dcfce7", "#15803d", "#fee2e2"),
        ("#fef3c7", "#b45309", "#dbeafe"),
        ("#fce7f3", "#be185d", "#e0f2fe"),
    ]
    bg, ink, accent = palettes[seed % len(palettes)]
    safe_title = str(title or "이미지 자료")[:28]
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="900" height="520" viewBox="0 0 900 520">
<rect width="900" height="520" fill="{bg}"/>
<circle cx="730" cy="130" r="92" fill="{accent}"/>
<circle cx="185" cy="405" r="118" fill="{accent}" opacity="0.72"/>
<rect x="92" y="92" width="716" height="336" rx="34" fill="#ffffff" opacity="0.9"/>
<path d="M170 330 C260 210 330 250 410 170 C500 82 620 140 720 235" fill="none" stroke="{ink}" stroke-width="18" stroke-linecap="round"/>
<circle cx="258" cy="225" r="34" fill="{ink}" opacity="0.88"/>
<circle cx="505" cy="160" r="46" fill="{ink}" opacity="0.78"/>
<circle cx="680" cy="260" r="38" fill="{ink}" opacity="0.84"/>
<text x="450" y="410" text-anchor="middle" font-family="Malgun Gothic, Arial, sans-serif" font-size="44" font-weight="700" fill="#172033">{html.escape(safe_title)}</text>
</svg>"""
    return "data:image/svg+xml;charset=utf-8," + quote(svg, safe="")


commons_cache: dict[str, Any] = {}
wiki_cache: dict[str, Any] = {}

NON_PHOTO_TERMS = (
    "illustration",
    "drawing",
    "diagram",
    "chart",
    "graph",
    "map",
    "icon",
    "logo",
    "symbol",
    "clipart",
    "cartoon",
    "painting",
    "watercolor",
    "engraving",
    "lithograph",
    "plate",
    "poster",
    "schema",
    "schematic",
    "silhouette",
    "render",
    "animation",
    "vector",
    "svg",
)

REALISTIC_ILLUSTRATION_TERMS = (
    "realistic",
    "lifelike",
    "scientific illustration",
    "paleoart",
    "reconstruction",
    "restoration",
    "life restoration",
    "artist's impression",
    "artists impression",
)

NO_PHOTO_SUBJECT_TERMS = (
    "dinosaur",
    "dinosaurs",
    "fossil",
    "fossils",
    "extinct",
    "prehistoric",
    "pterosaur",
    "triceratops",
    "tyrannosaurus",
    "velociraptor",
    "monster",
    "dragon",
    "kraken",
    "unicorn",
    "griffin",
    "goblin",
    "ghost",
    "myth",
    "mythical",
    "cryptid",
)

PHOTO_TERMS = (
    "photo",
    "photograph",
    "photographs",
    "jpg",
    "jpeg",
    "camera",
    "macro",
    "close-up",
    "closeup",
    "microscope",
    "micrograph",
)

AUTHORITATIVE_SOURCE_TERMS = (
    "wikipedia",
    "wikimedia commons",
    "commons",
    "museum",
    "university",
    "institute",
    "academy",
    "government",
    "national",
    "official",
    "usda",
    "nasa",
    "noaa",
    "usgs",
    "nih",
    "cdc",
    "nhm",
    "smithsonian",
    "encyclopedia",
    "encyclopaedia",
    "biodiversity heritage library",
    "library",
    "archive",
)

OFF_SUBJECT_PHOTO_TERMS = (
    "boy",
    "girl",
    "child",
    "children",
    "kid",
    "kids",
    "student",
    "students",
    "person",
    "people",
    "man",
    "woman",
    "hand",
    "hands",
    "holding",
    "catching",
    "classroom",
    "teacher",
    "magnifier",
    "magnifying glass",
    "lens",
    "observation",
    "observing",
    "experiment",
    "activity",
    "lesson",
    "toy",
    "model",
    "animatronic",
    "bench",
    "carving",
    "sculpture",
    "sign",
    "statue",
)

SECTION_DETAIL_TERMS = {
    "abdomen",
    "adult",
    "body",
    "colony",
    "egg",
    "eggs",
    "environment",
    "female",
    "habitat",
    "head",
    "larva",
    "larvae",
    "leg",
    "legs",
    "male",
    "mandible",
    "mandibles",
    "mouthpart",
    "nest",
    "nymph",
    "oviposition",
    "pupa",
    "pupae",
    "queen",
    "replete",
    "rostrum",
    "snout",
    "thorax",
    "trunk",
    "wing",
    "wings",
    "worker",
    "workers",
}

IMAGE_QUERY_STOPWORDS = {
    "and",
    "commons",
    "close",
    "closeup",
    "image",
    "macro",
    "photo",
    "photograph",
    "photographs",
    "picture",
    "pictures",
    "up",
    "wikimedia",
}


def clean_metadata_text(value: Any) -> str:
    text = re.sub(r"<[^>]+>", "", str(value or ""))
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def metadata_blob(page: dict[str, Any], info: dict[str, Any]) -> str:
    metadata = info.get("extmetadata") or {}
    parts = [
        str(page.get("title") or ""),
        clean_metadata_text((metadata.get("ObjectName") or {}).get("value")),
        clean_metadata_text((metadata.get("ImageDescription") or {}).get("value")),
        clean_metadata_text((metadata.get("Categories") or {}).get("value")),
    ]
    parts.extend(str(category.get("title") or "") for category in page.get("categories") or [])
    return " ".join(parts).lower()


def subject_blob(page: dict[str, Any], info: dict[str, Any]) -> str:
    metadata = info.get("extmetadata") or {}
    parts = [
        str(page.get("title") or ""),
        clean_metadata_text((metadata.get("ObjectName") or {}).get("value")),
    ]
    parts.extend(str(category.get("title") or "") for category in page.get("categories") or [])
    return " ".join(parts).lower()


def source_blob(page: dict[str, Any], info: dict[str, Any]) -> str:
    metadata = info.get("extmetadata") or {}
    parts = [
        str(page.get("title") or ""),
        str(info.get("descriptionurl") or ""),
        clean_metadata_text((metadata.get("Artist") or {}).get("value")),
        clean_metadata_text((metadata.get("Credit") or {}).get("value")),
        clean_metadata_text((metadata.get("Attribution") or {}).get("value")),
        clean_metadata_text((metadata.get("ImageDescription") or {}).get("value")),
        clean_metadata_text((metadata.get("Categories") or {}).get("value")),
    ]
    parts.extend(str(category.get("title") or "") for category in page.get("categories") or [])
    return " ".join(parts).lower()


def text_has_term(text: str, term: str) -> bool:
    term = term.lower().strip()
    if not term:
        return False
    if " " in term:
        return term in text
    return re.search(rf"(?<![a-z0-9]){re.escape(term)}(?![a-z0-9])", text) is not None


def text_has_any_term(text: str, terms: Any) -> bool:
    return any(text_has_term(text, str(term)) for term in terms)


def text_term_count(text: str, terms: Any) -> int:
    return sum(1 for term in terms if text_has_term(text, str(term)))


def allows_realistic_illustration(query: str) -> bool:
    lowered = query.lower()
    return text_has_any_term(lowered, NO_PHOTO_SUBJECT_TERMS) or text_has_any_term(lowered, REALISTIC_ILLUSTRATION_TERMS)


def subject_search_query(query: str) -> str:
    tokens = []
    seen = set()
    for token in re.findall(r"[a-z0-9]+", query.lower()):
        if len(token) < 3 or token in IMAGE_QUERY_STOPWORDS:
            continue
        if token not in seen:
            tokens.append(token)
            seen.add(token)
    return " ".join(tokens)


def ordered_query_tokens(query: str) -> list[str]:
    tokens: list[str] = []
    seen: set[str] = set()
    for token in re.findall(r"[a-z0-9]+", query.lower()):
        if len(token) < 3 or token in IMAGE_QUERY_STOPWORDS:
            continue
        variants = [token]
        if token.endswith("ies") and len(token) > 4:
            variants.append(token[:-3] + "y")
        elif token.endswith("es") and len(token) > 4:
            variants.append(token[:-2])
        elif token.endswith("s") and len(token) > 4:
            variants.append(token[:-1])
        for variant in variants:
            if variant not in seen:
                tokens.append(variant)
                seen.add(variant)
    return tokens


def query_keywords(query: str) -> set[str]:
    return set(ordered_query_tokens(query))


def query_core_keywords(query: str) -> list[str]:
    return [token for token in ordered_query_tokens(query) if token not in SECTION_DETAIL_TERMS]


def required_core_match_count(core_keywords: list[str]) -> int:
    if not core_keywords:
        return 0
    return min(2, len(core_keywords))


def is_subject_first_photo(page: dict[str, Any], info: dict[str, Any], query: str) -> bool:
    blob = metadata_blob(page, info)
    core_keywords = query_core_keywords(query)
    keywords = query_keywords(query)
    if core_keywords:
        subject = subject_blob(page, info)
        required_matches = required_core_match_count(core_keywords)
        subject_matches = sum(1 for keyword in core_keywords if keyword in subject)
        blob_matches = sum(1 for keyword in core_keywords if keyword in blob)
        if subject_matches < required_matches and blob_matches < required_matches:
            return False
    elif keywords:
        subject = subject_blob(page, info)
        if not any(keyword in subject for keyword in keywords):
            return False
    if text_has_any_term(blob, OFF_SUBJECT_PHOTO_TERMS):
        authority_blob = source_blob(page, info)
        allowed_terms = core_keywords or list(keywords)
        if not any(keyword in authority_blob for keyword in allowed_terms):
            return False
    return True


def commons_photo_score(page: dict[str, Any], info: dict[str, Any], query: str) -> int | None:
    mime = str(info.get("mime") or "")
    image_url = str(info.get("thumburl") or info.get("url") or "")
    if not image_url or not mime.startswith("image/") or mime == "image/svg+xml":
        return None

    width = int(info.get("thumbwidth") or info.get("width") or 0)
    height = int(info.get("thumbheight") or info.get("height") or 0)
    if width < 500 or height < 300:
        return None

    aspect_ratio = width / max(height, 1)
    if aspect_ratio < 0.42 or aspect_ratio > 2.9:
        return None

    blob = metadata_blob(page, info)
    allow_illustration = allows_realistic_illustration(query)
    if text_has_any_term(blob, NON_PHOTO_TERMS) and not (
        allow_illustration and text_has_any_term(blob, REALISTIC_ILLUSTRATION_TERMS)
    ):
        return None
    if not is_subject_first_photo(page, info, query):
        return None

    keywords = query_keywords(query)
    core_keywords = query_core_keywords(query)
    detail_keywords = keywords.difference(core_keywords)
    if core_keywords:
        required_matches = required_core_match_count(core_keywords)
        core_blob_matches = sum(1 for keyword in core_keywords if keyword in blob)
        if core_blob_matches < required_matches:
            return None
    elif keywords:
        keyword_matches = sum(1 for keyword in keywords if keyword in blob)
        if keyword_matches < min(2, len(keywords)):
            return None

    score = 0
    if mime in {"image/jpeg", "image/jpg"}:
        score += 5
    elif mime == "image/webp":
        score += 3
    elif mime == "image/png":
        score += 1

    subject = subject_blob(page, info)
    score += text_term_count(blob, PHOTO_TERMS)
    if allow_illustration and text_has_any_term(blob, REALISTIC_ILLUSTRATION_TERMS):
        score += 4
    score += 8 * sum(1 for keyword in core_keywords if keyword in subject)
    score += 2 * sum(1 for keyword in core_keywords if keyword in blob)
    score += 3 * sum(1 for keyword in detail_keywords if keyword in blob)
    if detail_keywords and not any(keyword in blob for keyword in detail_keywords):
        score -= 2
    if "category:photographs" in blob or "photographs of" in blob:
        score += 3
    authority_blob = source_blob(page, info)
    authority_matches = text_term_count(authority_blob, AUTHORITATIVE_SOURCE_TERMS)
    score += min(authority_matches, 4) * 3
    if "own work" in authority_blob and authority_matches == 0:
        score -= 2

    return score if score >= 4 else None


def commons_relaxed_photo_score(page: dict[str, Any], info: dict[str, Any], query: str = "") -> int | None:
    mime = str(info.get("mime") or "")
    image_url = str(info.get("thumburl") or info.get("url") or "")
    if not image_url or mime not in {"image/jpeg", "image/jpg", "image/webp"}:
        return None

    width = int(info.get("thumbwidth") or info.get("width") or 0)
    height = int(info.get("thumbheight") or info.get("height") or 0)
    if width < 420 or height < 260:
        return None

    aspect_ratio = width / max(height, 1)
    if aspect_ratio < 0.34 or aspect_ratio > 3.4:
        return None

    blob = metadata_blob(page, info)
    allow_illustration = allows_realistic_illustration(query)
    if text_has_any_term(blob, NON_PHOTO_TERMS) and not (
        allow_illustration and text_has_any_term(blob, REALISTIC_ILLUSTRATION_TERMS)
    ):
        return None
    if not is_subject_first_photo(page, info, query):
        return None

    score = 2
    if mime in {"image/jpeg", "image/jpg"}:
        score += 4
    if text_has_any_term(blob, PHOTO_TERMS):
        score += 2
    core_keywords = query_core_keywords(query)
    subject = subject_blob(page, info)
    score += 6 * sum(1 for keyword in core_keywords if keyword in subject)
    score += 2 * sum(1 for keyword in core_keywords if keyword in blob)
    authority_blob = source_blob(page, info)
    authority_matches = text_term_count(authority_blob, AUTHORITATIVE_SOURCE_TERMS)
    score += min(authority_matches, 3) * 2
    if "own work" in authority_blob and authority_matches == 0:
        score -= 1
    return score


def commons_illustration_score(page: dict[str, Any], info: dict[str, Any], query: str) -> int | None:
    mime = str(info.get("mime") or "")
    image_url = str(info.get("thumburl") or info.get("url") or "")
    if not image_url or not mime.startswith("image/") or mime == "image/svg+xml":
        return None

    width = int(info.get("thumbwidth") or info.get("width") or 0)
    height = int(info.get("thumbheight") or info.get("height") or 0)
    if width < 500 or height < 300:
        return None

    aspect_ratio = width / max(height, 1)
    if aspect_ratio < 0.42 or aspect_ratio > 2.9:
        return None

    blob = metadata_blob(page, info)
    if text_has_any_term(blob, OFF_SUBJECT_PHOTO_TERMS):
        return None
    if not is_subject_first_photo(page, info, query):
        return None
    if not text_has_any_term(blob, REALISTIC_ILLUSTRATION_TERMS + ("illustration", "restoration", "reconstruction")):
        return None

    core_keywords = query_core_keywords(query)
    if core_keywords:
        required_matches = required_core_match_count(core_keywords)
        if sum(1 for keyword in core_keywords if keyword in blob) < required_matches:
            return None

    subject = subject_blob(page, info)
    authority_blob = source_blob(page, info)
    score = 4
    if mime in {"image/jpeg", "image/jpg"}:
        score += 4
    elif mime == "image/webp":
        score += 3
    elif mime == "image/png":
        score += 2
    score += 7 * sum(1 for keyword in core_keywords if keyword in subject)
    score += 2 * sum(1 for keyword in core_keywords if keyword in blob)
    score += min(text_term_count(authority_blob, AUTHORITATIVE_SOURCE_TERMS), 4) * 3
    score += text_term_count(blob, REALISTIC_ILLUSTRATION_TERMS) * 3
    return score if score >= 6 else None


def fetch_commons_pages(search_query: str, limit: int = 20) -> list[dict[str, Any]]:
    params = {
        "action": "query",
        "generator": "search",
        "gsrsearch": search_query,
        "gsrnamespace": "6",
        "gsrlimit": str(limit),
        "prop": "imageinfo|categories",
        "iiprop": "url|mime|size|extmetadata",
        "iiurlwidth": "1200",
        "clshow": "!hidden",
        "cllimit": "20",
        "format": "json",
        "origin": "*",
    }
    url = "https://commons.wikimedia.org/w/api.php?" + urlencode(params)
    request_obj = urllib.request.Request(
        url,
        headers={"User-Agent": "GumaTutorDoc/1.0 (https://gumatutordoc.guma3d.com)"},
    )
    try:
        with urllib.request.urlopen(request_obj, timeout=8) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError) as exc:
        print(f"[commons] search failed for {search_query}: {exc}")
        return []

    return list((payload.get("query", {}).get("pages", {}) or {}).values())


def resolve_commons_candidates(query: str, *, relaxed: bool = False, limit: int = 8) -> list[dict[str, str]]:
    query = re.sub(r"\s+", " ", str(query or "").strip())
    if not query:
        return []
    cache_key = f"{'relaxed' if relaxed else 'strict'}:candidates:{query.lower()}"
    if cache_key in commons_cache:
        cached = commons_cache[cache_key]
        return list(cached) if isinstance(cached, list) else []

    subject_query = subject_search_query(query)
    reduced_subject_queries = []
    subject_terms = subject_query.split()
    if len(subject_terms) > 2:
        reduced_subject_queries.append(" ".join(subject_terms[:2]))
        reduced_subject_queries.append(" ".join(subject_terms[:3]))
    core_subject_query = " ".join(query_core_keywords(query)[:3])
    illustration_queries = []
    if core_subject_query:
        illustration_queries = [
            f"{core_subject_query} realistic reconstruction",
            f"{core_subject_query} lifelike scientific illustration",
        ]
    search_queries = [
        f"{core_subject_query} photograph -diagram -illustration -drawing -map -icon -logo -chart" if core_subject_query else "",
        f"{subject_query} photograph -diagram -illustration -drawing -map -icon -logo -chart",
        f"{subject_query} photo",
        *[f"{reduced_query} photograph -diagram -illustration -drawing -map -icon -logo -chart" for reduced_query in reduced_subject_queries],
        *[f"{reduced_query} photo" for reduced_query in reduced_subject_queries],
        f"{query} photograph -diagram -illustration -drawing -map -icon -logo -chart",
        f"{query} photo",
        *illustration_queries,
        query,
    ] if subject_query else [
        f"{query} photograph -diagram -illustration -drawing -map -icon -logo -chart",
        f"{query} photo",
        query,
    ]
    search_queries = [search_query for search_query in search_queries if search_query.strip()]
    candidates: list[tuple[int, dict[str, str]]] = []
    seen_urls: set[str] = set()

    for search_query in search_queries:
        for page in fetch_commons_pages(search_query, limit=30):
            info_items = page.get("imageinfo") or []
            if not info_items:
                continue
            info = info_items[0]
            score_query = f"{query} {search_query}"
            score = commons_photo_score(page, info, score_query)
            if score is None and relaxed:
                score = commons_relaxed_photo_score(page, info, score_query)
            if score is None:
                continue
            image_url = str(info.get("thumburl") or info.get("url") or "")
            if image_url in seen_urls:
                continue
            seen_urls.add(image_url)
            metadata = info.get("extmetadata") or {}
            artist = clean_metadata_text((metadata.get("Artist") or {}).get("value"))
            license_short = clean_metadata_text((metadata.get("LicenseShortName") or {}).get("value"))
            candidates.append(
                (
                    score,
                    {
                        "image_url": image_url,
                        "source_url": str(info.get("descriptionurl") or ""),
                        "source_title": str(page.get("title") or "").replace("File:", ""),
                        "credit": ", ".join(part for part in [artist, license_short] if part),
                    },
                )
            )

    if candidates:
        candidates.sort(key=lambda item: item[0], reverse=True)
        results = [candidate for _, candidate in candidates[:limit]]
        commons_cache[cache_key] = results
        return results

    commons_cache[cache_key] = []
    return []


def resolve_commons_image(query: str, *, relaxed: bool = False, excluded_urls: set[str] | None = None) -> dict[str, str] | None:
    excluded_urls = excluded_urls or set()
    for candidate in resolve_commons_candidates(query, relaxed=relaxed):
        image_url = candidate.get("image_url", "")
        if image_url and image_url not in excluded_urls:
            return candidate
    return None


def resolve_commons_illustration(query: str, *, excluded_urls: set[str] | None = None) -> dict[str, str] | None:
    query = re.sub(r"\s+", " ", str(query or "").strip())
    excluded_urls = excluded_urls or set()
    if not query:
        return None
    cache_key = f"illustration:{query.lower()}"
    if cache_key in commons_cache:
        cached = commons_cache[cache_key]
        candidates = list(cached) if isinstance(cached, list) else []
    else:
        subject_query = subject_search_query(query)
        core_subject_query = " ".join(query_core_keywords(query)[:3])
        base_query = core_subject_query or subject_query or query
        search_queries = [
            f"{query} realistic scientific illustration",
            f"{query} life restoration",
            f"{query} reconstruction",
            f"{base_query} realistic reconstruction",
            f"{base_query} lifelike scientific illustration",
            f"{base_query} artist impression",
            f"{base_query} paleoart",
        ]
        scored: list[tuple[int, dict[str, str]]] = []
        seen_urls: set[str] = set()
        for search_query in search_queries:
            for page in fetch_commons_pages(search_query, limit=40):
                info_items = page.get("imageinfo") or []
                if not info_items:
                    continue
                info = info_items[0]
                score_query = f"{query} {search_query} realistic scientific illustration"
                score = commons_illustration_score(page, info, score_query)
                if score is None:
                    continue
                image_url = str(info.get("thumburl") or info.get("url") or "")
                if not image_url or image_url in seen_urls:
                    continue
                seen_urls.add(image_url)
                metadata = info.get("extmetadata") or {}
                artist = clean_metadata_text((metadata.get("Artist") or {}).get("value"))
                license_short = clean_metadata_text((metadata.get("LicenseShortName") or {}).get("value"))
                scored.append(
                    (
                        score,
                        {
                            "image_url": image_url,
                            "source_url": str(info.get("descriptionurl") or ""),
                            "source_title": str(page.get("title") or "").replace("File:", ""),
                            "credit": ", ".join(part for part in [artist, license_short] if part),
                        },
                    )
                )
        scored.sort(key=lambda item: item[0], reverse=True)
        candidates = [candidate for _, candidate in scored[:8]]
        commons_cache[cache_key] = candidates

    for candidate in candidates:
        image_url = candidate.get("image_url", "")
        if image_url and image_url not in excluded_urls:
            return candidate
    return None


def fetch_commons_category_candidates(category: str, query: str, *, limit: int = 12) -> list[dict[str, str]]:
    category = str(category or "").replace("Category:", "").strip()
    query = re.sub(r"\s+", " ", str(query or "").strip())
    if not category or not query:
        return []
    cache_key = f"category-images:{category.lower()}:{query.lower()}:{limit}"
    if cache_key in commons_cache:
        cached = commons_cache[cache_key]
        return list(cached) if isinstance(cached, list) else []

    params = {
        "action": "query",
        "generator": "categorymembers",
        "gcmtitle": f"Category:{category}",
        "gcmtype": "file",
        "gcmlimit": "50",
        "prop": "imageinfo|categories",
        "iiprop": "url|mime|size|extmetadata",
        "iiurlwidth": "1200",
        "clshow": "!hidden",
        "cllimit": "20",
        "format": "json",
        "origin": "*",
    }
    payload = fetch_json_url("https://commons.wikimedia.org/w/api.php?" + urlencode(params))
    pages = list(((payload or {}).get("query", {}).get("pages", {}) or {}).values())
    scored: list[tuple[int, dict[str, str]]] = []
    seen_urls: set[str] = set()
    score_query = f"{query} {category} realistic scientific illustration photograph"
    for page in pages:
        info_items = page.get("imageinfo") or []
        if not info_items:
            continue
        info = info_items[0]
        blob = metadata_blob(page, info)
        if text_has_any_term(blob, OFF_SUBJECT_PHOTO_TERMS):
            continue
        if text_has_any_term(blob, NON_PHOTO_TERMS) and not text_has_any_term(blob, REALISTIC_ILLUSTRATION_TERMS):
            continue
        score = commons_photo_score(page, info, score_query)
        if score is None:
            score = commons_illustration_score(page, info, score_query)
        if score is None:
            score = commons_relaxed_photo_score(page, info, score_query)
        if score is None:
            continue
        image_url = str(info.get("thumburl") or info.get("url") or "")
        if not image_url or image_url in seen_urls:
            continue
        seen_urls.add(image_url)
        metadata = info.get("extmetadata") or {}
        artist = clean_metadata_text((metadata.get("Artist") or {}).get("value"))
        license_short = clean_metadata_text((metadata.get("LicenseShortName") or {}).get("value"))
        scored.append(
            (
                score,
                {
                    "image_url": image_url,
                    "source_url": str(info.get("descriptionurl") or ""),
                    "source_title": str(page.get("title") or "").replace("File:", ""),
                    "credit": ", ".join(part for part in [artist, license_short] if part),
                },
            )
        )
    scored.sort(key=lambda item: item[0], reverse=True)
    results = [candidate for _, candidate in scored[:limit]]
    commons_cache[cache_key] = results
    return results


def image_data_for_item(item: dict[str, str], excluded_urls: set[str] | None = None) -> dict[str, str] | None:
    excluded_urls = excluded_urls or set()
    title = str(item.get("title") or "이미지 자료").strip()
    caption = str(item.get("caption") or "").strip()
    query = str(item.get("query") or title).strip()
    data = {
        "title": title,
        "caption": caption,
        "query": query,
        "image_url": str(item.get("image_url") or "").strip(),
        "source_url": str(item.get("source_url") or "").strip(),
        "source_title": str(item.get("source_title") or "").strip(),
        "credit": str(item.get("credit") or "").strip(),
    }
    if data["image_url"] and data["image_url"] in excluded_urls:
        data["image_url"] = ""
    if not data["image_url"]:
        resolved = resolve_commons_image(query, excluded_urls=excluded_urls)
        if not resolved:
            resolved = resolve_commons_image(query, relaxed=True, excluded_urls=excluded_urls)
        if resolved:
            data.update(resolved)
            item.update(resolved)
    if not data["image_url"]:
        return None
    return data


def fallback_visual_url(title: str, seed: int) -> str:
    svg = f"""
    <svg xmlns="http://www.w3.org/2000/svg" width="1200" height="675" viewBox="0 0 1200 675">
      <defs>
        <linearGradient id="bg" x1="0" x2="1" y1="0" y2="1">
          <stop offset="0" stop-color="#06120f"/>
          <stop offset="0.52" stop-color="#0f2a22"/>
          <stop offset="1" stop-color="#1f2937"/>
        </linearGradient>
        <radialGradient id="glow" cx="50%" cy="45%" r="60%">
          <stop offset="0" stop-color="#34d399" stop-opacity="0.38"/>
          <stop offset="1" stop-color="#34d399" stop-opacity="0"/>
        </radialGradient>
      </defs>
      <rect width="1200" height="675" fill="url(#bg)"/>
      <rect width="1200" height="675" fill="url(#glow)"/>
      <ellipse cx="600" cy="385" rx="330" ry="120" fill="#020617" opacity="0.28"/>
      <path d="M310 400 C420 250, 780 250, 890 400 C790 505, 410 505, 310 400 Z" fill="#14532d" stroke="#86efac" stroke-width="10" opacity="0.86"/>
      <circle cx="485" cy="375" r="36" fill="#bbf7d0" opacity="0.92"/>
      <circle cx="715" cy="375" r="36" fill="#bbf7d0" opacity="0.92"/>
      <path d="M405 445 C475 515, 725 515, 795 445" fill="none" stroke="#bbf7d0" stroke-width="18" stroke-linecap="round" opacity="0.72"/>
      <text x="600" y="106" text-anchor="middle" fill="#f8fafc" font-family="Malgun Gothic, Arial, sans-serif" font-size="44" font-weight="800">{html.escape(title[:32])}</text>
      <text x="600" y="594" text-anchor="middle" fill="#a7f3d0" font-family="Malgun Gothic, Arial, sans-serif" font-size="24">실사풍 참고 이미지가 없을 때 사용하는 임시 시각자료</text>
    </svg>
    """
    return "data:image/svg+xml;charset=utf-8," + quote(svg, safe="")


def render_material_html(pack: dict[str, Any], task_id: str) -> str:
    summary = list_html(pack.get("summary", []), "summary-list")
    sources = list_html(pack.get("sources", []), "sources")
    topic = str(pack.get("topic") or "").strip()
    used_image_urls: set[str] = set()
    subject_core_queries: list[str] = []
    for section in pack.get("content_sections", []):
        if not isinstance(section, dict):
            continue
        for item in section.get("images") or []:
            if not isinstance(item, dict):
                continue
            core_query = " ".join(query_core_keywords(str(item.get("query") or ""))[:3]).strip()
            if core_query and core_query not in subject_core_queries:
                subject_core_queries.append(core_query)
    highlight_terms = sorted(
        {
            str(item.get("term") or "").strip()
            for item in pack.get("vocabulary", [])
            if isinstance(item, dict) and len(str(item.get("term") or "").strip()) >= 2
        },
        key=len,
        reverse=True,
    )[:12]

    def highlight_plain_text(value: str) -> str:
        rendered = e(value)
        for term in highlight_terms:
            escaped_term = e(term)
            rendered = re.sub(
                re.escape(escaped_term),
                f'<strong class="keyword-highlight">{escaped_term}</strong>',
                rendered,
                count=1,
            )
        return rendered

    def rich_text_html(value: Any) -> str:
        text = str(value or "")
        parts = re.split(r"(\*\*[^*]{1,48}\*\*)", text)
        rendered_parts: list[str] = []
        for part in parts:
            if part.startswith("**") and part.endswith("**"):
                rendered_parts.append(f'<strong class="keyword-highlight">{e(part[2:-2])}</strong>')
            else:
                rendered_parts.append(highlight_plain_text(part))
        return "".join(rendered_parts)

    def first_section_image(section: dict[str, Any]) -> dict[str, str] | None:
        image_items = section.get("images")
        if not isinstance(image_items, list):
            image_items = []
        for item in image_items:
            if not isinstance(item, dict):
                continue
            data = image_data_for_item(item, excluded_urls=used_image_urls)
            if data:
                used_image_urls.add(data["image_url"])
                return data

        section_title = str(section.get("title") or "").strip()
        fallback_queries = [
            f"{topic} {section_title} photo",
            f"{topic} {section_title} photograph",
            f"{topic} close up photo",
            f"{topic} photo",
        ]
        for core_query in subject_core_queries[:3]:
            fallback_queries.extend(
                [
                    f"{core_query} {section_title} photograph",
                    f"{core_query} close up photograph",
                    f"{core_query} photograph",
                    f"{core_query} {section_title} realistic scientific illustration",
                    f"{core_query} lifelike reconstruction",
                ]
            )
        for query in fallback_queries:
            if not query.strip():
                continue
            data = image_data_for_item(
                {
                    "title": f"{section_title or topic} 사진",
                    "caption": f"{section_title or topic}을 실제 사진으로 살펴봅니다.",
                    "query": query,
                },
                excluded_urls=used_image_urls,
            )
            if data:
                used_image_urls.add(data["image_url"])
                return data
        fallback_title = section_title or topic or "시각자료"
        illustration_queries = [
            f"{topic} {section_title} realistic scientific illustration",
            f"{topic} {section_title} life restoration",
            f"{topic} {section_title} reconstruction",
        ]
        for core_query in subject_core_queries[:3]:
            illustration_queries.extend(
                [
                    f"{core_query} {section_title} realistic scientific illustration",
                    f"{core_query} {section_title} life restoration",
                    f"{core_query} scientific illustration",
                    f"{core_query} reconstruction",
                ]
            )
        for query in illustration_queries:
            if not query.strip():
                continue
            resolved = resolve_commons_illustration(query, excluded_urls=used_image_urls)
            if resolved:
                used_image_urls.add(resolved["image_url"])
                return {
                    "title": f"{section_title or topic} illustration",
                    "caption": f"{section_title or topic}을 이해하기 위한 위키미디어 기반 복원도/과학 일러스트입니다.",
                    "query": query,
                    **resolved,
                }
        fallback_url = fallback_visual_url(fallback_title, len(used_image_urls))
        used_image_urls.add(fallback_url)
        return {
            "title": fallback_title,
            "caption": f"{fallback_title}을 이해하기 위한 실사풍 참고 시각자료입니다.",
            "query": f"{topic} {section_title} realistic scientific illustration",
            "image_url": fallback_url,
            "source_url": "",
            "source_title": "GumaTutorDoc generated fallback visual",
            "credit": "",
        }

    def photo_notes(section: dict[str, Any], image: dict[str, str] | None) -> list[str]:
        notes: list[str] = []
        for item in section.get("images") or []:
            if isinstance(item, dict):
                raw_notes = item.get("notes") or item.get("observations") or item.get("photo_notes")
                if isinstance(raw_notes, str):
                    raw_notes = [raw_notes]
                if isinstance(raw_notes, list):
                    notes.extend(str(note).strip() for note in raw_notes if str(note).strip())
        if image and image.get("caption"):
            notes.insert(0, str(image.get("caption")).strip())
        examples = section.get("examples")
        if isinstance(examples, list):
            notes.extend(str(example).strip() for example in examples if str(example).strip())
        if len(notes) < 2:
            title = str(section.get("title") or topic or "사진").strip()
            notes.extend(
                [
                    f"{title}의 모습을 사진에서 직접 확인해 보세요.",
                    "사진 속 모양과 설명을 서로 비교하며 살펴보세요.",
                ]
            )
        deduped: list[str] = []
        for note in notes:
            if note and note not in deduped:
                deduped.append(note)
        return deduped[:3]

    def section_points(section: dict[str, Any]) -> list[str]:
        paragraphs = section.get("paragraphs")
        if not isinstance(paragraphs, list):
            return []
        points: list[str] = []
        for paragraph in paragraphs:
            text = re.sub(r"\s+", " ", str(paragraph or "").strip())
            if not text:
                continue
            sentences = re.findall(r"[^.!?\n\r]+[.!?]?", text)
            for sentence in sentences:
                sentence = sentence.strip()
                if sentence:
                    points.append(sentence)
        return points[:5]

    def section_page_html(section: dict[str, Any], idx: int) -> str:
        image = first_section_image(section)
        image_source_html = ""
        if image:
            source_bits = []
            if image.get("source_url"):
                source_label = image.get("source_title") or "자료 출처"
                source_bits.append(
                    f'<a href="{e(image.get("source_url"))}" target="_blank" rel="noopener noreferrer">{e(source_label)}</a>'
                )
            if image.get("credit"):
                source_bits.append(e(image.get("credit")))
            image_source_html = f'<small>{" · ".join(source_bits)}</small>' if source_bits else ""
        image_html = (
            f"""
            <figure class="topic-photo">
              <img src="{e(image.get("image_url"))}" alt="{e(image.get("title"))}" loading="eager" decoding="async" referrerpolicy="no-referrer">
              {image_source_html}
            </figure>
            """
            if image
            else """
            <figure class="topic-photo photo-missing">
              <div>사진을 찾는 중입니다</div>
            </figure>
            """
        )
        points = section_points(section)
        return f"""
        <section class="block topic-page">
          <div class="topic-title">
            <div class="page-kicker">내용 {idx}</div>
            <h2>{e(section.get("title"))}</h2>
          </div>
          {image_html}
          <div class="topic-copy">
            <ul class="topic-points">
              {"".join(f"<li>{rich_text_html(point)}</li>" for point in points)}
            </ul>
          </div>
        </section>
        """

    content_sections = "\n".join(
        section_page_html(section, idx)
        for idx, section in enumerate(pack.get("content_sections", []), start=1)
    )

    vocabulary = "\n".join(
        f"""
        <tr>
          <th>{e(item.get("term"))}</th>
          <td>{e(item.get("meaning"))}</td>
        </tr>
        """
        for item in pack.get("vocabulary", [])
    )

    quiz = "\n".join(
        f"""
        <section class="quiz-item">
          <h3>문제 {idx}</h3>
          <p>{e(item.get("question"))}</p>
          {list_html(item.get("choices", []), "choices")}
          <details>
            <summary>정답 보기</summary>
            <p><strong>{e(item.get("answer"))}</strong></p>
            <p>{e(item.get("explanation"))}</p>
          </details>
        </section>
        """
        for idx, item in enumerate(pack.get("quiz", []), start=1)
    )

    source_section = (
        f"""
      <section class="block">
        <h2>참고자료</h2>
        {sources}
      </section>
        """
        if sources
        else ""
    )

    return f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{e(pack.get("title"))}</title>
  <style>
    :root {{
      color-scheme: dark;
      --ink: #f8fafc;
      --muted: #a1a1aa;
      --line: rgba(255, 255, 255, 0.12);
      --paper: rgba(255, 255, 255, 0.055);
      --paper-strong: rgba(255, 255, 255, 0.08);
      --bg: #050505;
      --primary: #10b981;
      --primary-soft: rgba(16, 185, 129, 0.12);
      --primary-line: rgba(16, 185, 129, 0.34);
      --blue: #60a5fa;
      --rose: #fb7185;
      --amber: #fbbf24;
      --peach: rgba(251, 191, 36, 0.11);
    }}
    * {{ box-sizing: border-box; }}
    html {{
      scroll-snap-type: y proximity;
      background: var(--bg);
    }}
    body {{
      margin: 0;
      font-family: "Malgun Gothic", "Apple SD Gothic Neo", system-ui, sans-serif;
      color: var(--ink);
      background:
        radial-gradient(circle at 18% 12%, rgba(16, 185, 129, 0.14), transparent 30vw),
        radial-gradient(circle at 84% 8%, rgba(96, 165, 250, 0.12), transparent 28vw),
        var(--bg);
      line-height: 1.68;
    }}
    .page {{
      width: min(1180px, calc(100% - 32px));
      margin: 0 auto;
      padding: 32px 0 72px;
    }}
    header {{
      min-height: min(58vw, 620px);
      display: flex;
      flex-direction: column;
      justify-content: center;
      padding: 40px 0;
      border-bottom: 1px solid var(--primary-line);
      scroll-snap-align: start;
    }}
    .meta {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-bottom: 18px;
      color: var(--muted);
      font-size: 14px;
    }}
    .pill {{
      border: 1px solid var(--line);
      border-radius: 999px;
      padding: 4px 11px;
      background: rgba(255, 255, 255, 0.06);
    }}
    h1 {{
      margin: 0;
      font-size: clamp(34px, 6.5vw, 72px);
      line-height: 1.12;
      letter-spacing: 0;
    }}
    .subtitle {{
      max-width: 780px;
      margin: 18px 0 0;
      color: var(--muted);
      font-size: clamp(18px, 2.2vw, 26px);
    }}
    main {{
      display: grid;
      gap: 22px;
      margin-top: 24px;
    }}
    section.block {{
      background: var(--paper);
      border: 1px solid var(--line);
      border-radius: 18px;
      padding: clamp(20px, 3vw, 42px);
      min-height: min(720px, calc((100vw - 48px) * 0.5625));
      display: flex;
      flex-direction: column;
      justify-content: center;
      box-shadow: 0 24px 80px rgba(0, 0, 0, 0.32);
      scroll-snap-align: start;
    }}
    h2 {{
      margin: 0 0 18px;
      font-size: clamp(24px, 3.2vw, 38px);
      line-height: 1.3;
      letter-spacing: 0;
    }}
    h3 {{
      margin: 0 0 10px;
      font-size: clamp(19px, 2.2vw, 28px);
      line-height: 1.35;
      letter-spacing: 0;
    }}
    p {{
      margin: 0 0 12px;
      font-size: clamp(16px, 1.55vw, 22px);
    }}
    ul {{ margin: 0; padding-left: 22px; }}
    .summary-list {{
      display: grid;
      gap: 12px;
      padding: 0;
      list-style: none;
      counter-reset: summary;
    }}
    .summary-list li {{
      counter-increment: summary;
      position: relative;
      padding: 14px 16px 14px 54px;
      border-radius: 12px;
      background: var(--primary-soft);
      border: 1px solid var(--primary-line);
      font-size: clamp(16px, 1.55vw, 22px);
    }}
    .summary-list li::before {{
      content: counter(summary);
      position: absolute;
      left: 16px;
      top: 16px;
      width: 26px;
      height: 26px;
      border-radius: 50%;
      background: var(--primary);
      color: white;
      display: grid;
      place-items: center;
      font-size: 14px;
      font-weight: 700;
    }}
    .block.topic-page {{
      aspect-ratio: 16 / 9;
      min-height: auto;
      display: grid;
      grid-template:
        "title title" auto
        "photo copy" minmax(0, 1fr)
        / minmax(0, 7fr) minmax(0, 3fr);
      grid-template-columns: minmax(0, 7fr) minmax(0, 3fr);
      gap: 14px 18px;
      justify-content: stretch;
      align-items: stretch;
      overflow: hidden;
    }}
    .page-kicker {{
      color: var(--primary);
      font-size: 13px;
      font-weight: 800;
      letter-spacing: 1.5px;
      margin-bottom: 6px;
      text-transform: uppercase;
    }}
    .topic-title {{
      grid-area: title;
      padding: clamp(12px, 1.5vw, 20px) clamp(16px, 2vw, 28px);
      border: 1px solid var(--primary-line);
      border-radius: 16px;
      background: linear-gradient(135deg, rgba(16, 185, 129, 0.16), rgba(59, 130, 246, 0.08));
    }}
    .topic-title h2 {{
      margin: 0;
      font-size: clamp(26px, 3.4vw, 42px);
      line-height: 1.2;
    }}
    .topic-copy {{
      grid-area: copy;
      min-height: 0;
      overflow: hidden;
      display: flex;
      flex-direction: column;
      justify-content: center;
      padding: clamp(14px, 1.8vw, 26px);
      border: 1px solid var(--primary-line);
      border-radius: 16px;
      background: var(--primary-soft);
    }}
    .topic-points {{
      display: grid;
      gap: 6px;
      padding: 0;
      margin: 0;
      list-style: none;
    }}
    .topic-points li {{
      position: relative;
      padding-left: 18px;
      color: var(--ink);
      font-size: clamp(13px, 1.12vw, 16px);
      line-height: 1.38;
    }}
    .keyword-highlight {{
      color: #fbbf24;
      font-weight: 800;
      padding: 0 0.08em;
      text-shadow: 0 0 14px rgba(251, 191, 36, 0.22);
    }}
    .topic-points li::before {{
      content: "";
      position: absolute;
      left: 0;
      top: 0.66em;
      width: 6px;
      height: 6px;
      border-radius: 999px;
      background: var(--primary);
    }}
    .topic-photo {{
      grid-area: photo;
      position: relative;
      min-width: 0;
      min-height: 0;
      margin: 0;
      border: 1px solid var(--line);
      border-radius: 16px;
      overflow: hidden;
      background: #000;
    }}
    .topic-photo img {{
      display: block;
      width: 100%;
      height: 100%;
      object-fit: contain;
      background: #000;
    }}
    .topic-photo small {{
      position: absolute;
      left: 10px;
      right: 10px;
      bottom: 10px;
      padding: 6px 8px;
      border-radius: 8px;
      color: rgba(255, 255, 255, 0.78);
      background: rgba(0, 0, 0, 0.54);
      font-size: 11px;
      line-height: 1.35;
    }}
    .topic-photo a {{
      color: #a7f3d0;
      text-decoration: none;
    }}
    .photo-missing {{
      display: grid;
      place-items: center;
      color: var(--muted);
      background: rgba(255, 255, 255, 0.045);
    }}
    .examples {{
      display: grid;
      gap: 8px;
      margin-top: 10px;
      padding: 0;
      list-style: none;
    }}
    .examples li {{
      background: var(--peach);
      border-left: 4px solid var(--amber);
      border-radius: 10px;
      padding: 10px 12px;
      color: #fde68a;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: clamp(16px, 1.5vw, 21px);
    }}
    th, td {{
      border-bottom: 1px solid var(--line);
      padding: 11px 10px;
      text-align: left;
      vertical-align: top;
    }}
    th {{
      width: 160px;
      color: var(--blue);
    }}
    .quiz-item {{
      border: 1px solid var(--line);
      border-radius: 14px;
      padding: 18px;
      margin-top: 14px;
      background: var(--paper-strong);
    }}
    .choices {{
      margin: 8px 0 12px;
    }}
    details {{
      border-top: 1px solid var(--line);
      padding-top: 10px;
    }}
    summary {{
      cursor: pointer;
      color: var(--rose);
      font-weight: 700;
    }}
    .sources li {{
      margin-bottom: 6px;
    }}
    footer {{
      margin-top: 22px;
      color: var(--muted);
      font-size: 13px;
    }}
    @media (max-width: 820px) and (orientation: portrait) {{
      html {{ scroll-snap-type: none; }}
      .page {{
        width: min(100% - 20px, 1180px);
        padding: 18px 0 44px;
      }}
      header {{
        min-height: 70vh;
        padding: 24px 0;
      }}
      section.block {{
        min-height: auto;
        border-radius: 14px;
        padding: 20px;
      }}
      .block.topic-page {{
        aspect-ratio: 16 / 9;
        grid-template:
          "title title" auto
          "photo copy" minmax(0, 1fr)
          / minmax(0, 7fr) minmax(0, 3fr);
        grid-template-columns: minmax(0, 7fr) minmax(0, 3fr);
        gap: 8px 10px;
      }}
      .topic-title {{
        padding: 8px 10px;
        border-radius: 12px;
      }}
      .topic-title h2 {{
        font-size: clamp(14px, 4.3vw, 22px);
      }}
      .topic-copy {{
        overflow: hidden;
        padding: 10px;
        border-radius: 12px;
      }}
      .topic-points {{
        gap: 3px;
      }}
      .topic-points li {{
        padding-left: 12px;
        font-size: clamp(9px, 2.6vw, 13px);
        line-height: 1.25;
      }}
      .topic-photo {{
        width: 100%;
        height: 100%;
        border-radius: 12px;
      }}
      th {{
        width: 104px;
      }}
      th, td {{
        padding: 10px 6px;
      }}
    }}
    @media (orientation: landscape) and (max-height: 560px) {{
      html {{
        scroll-snap-type: y mandatory;
      }}
      body {{
        line-height: 1.35;
      }}
      .page {{
        width: min(calc(100vw - 16px), calc((100vh - 16px) * 16 / 9));
        padding: 8px 0 28px;
      }}
      header {{
        min-height: calc(100vh - 16px);
        padding: 14px 0;
      }}
      h1 {{
        font-size: clamp(26px, 9vh, 44px);
      }}
      .subtitle {{
        font-size: clamp(13px, 3.4vh, 18px);
      }}
      section.block {{
        min-height: auto;
        padding: clamp(8px, 2.2vh, 14px);
        border-radius: 12px;
      }}
      .block.topic-page {{
        aspect-ratio: 16 / 9;
        grid-template:
          "title title" auto
          "photo copy" minmax(0, 1fr)
          / minmax(0, 7fr) minmax(0, 3fr);
        grid-template-columns: minmax(0, 7fr) minmax(0, 3fr);
        gap: clamp(4px, 1.1vh, 7px);
      }}
      .page-kicker {{
        font-size: clamp(8px, 2vh, 10px);
        margin-bottom: 2px;
      }}
      .topic-title {{
        padding: clamp(5px, 1.2vh, 8px) clamp(7px, 1.8vh, 12px);
        border-radius: 10px;
      }}
      .topic-title h2 {{
        font-size: clamp(13px, 4vh, 21px);
      }}
      .topic-copy {{
        overflow: hidden;
        padding: clamp(6px, 1.5vh, 10px);
        border-radius: 10px;
      }}
      .topic-points {{
        gap: 2px;
      }}
      .topic-points li {{
        padding-left: 12px;
        font-size: clamp(9px, 2.45vh, 13px);
        line-height: 1.22;
      }}
      .topic-points li::before {{
        width: 4px;
        height: 4px;
      }}
      .topic-photo {{
        border-radius: 10px;
      }}
      .topic-photo small {{
        display: none;
      }}
    }}
  </style>
</head>
<body class="doc-view">
  <div class="page">
    <header>
      <div class="meta">
        <span class="pill">{e(APP_TITLE)}</span>
        <span class="pill">{e(pack.get("grade"))}</span>
        <span class="pill">문서 ID {e(task_id[:8])}</span>
      </div>
      <h1>{e(pack.get("title"))}</h1>
      <p class="subtitle">{e(pack.get("subtitle"))}</p>
    </header>
    <main>
      <section class="block">
        <h2>요약</h2>
        {summary}
      </section>
      {content_sections}
      <section class="block">
        <h2>단어 정리</h2>
        <table>
          <tbody>{vocabulary}</tbody>
        </table>
      </section>
      <section class="block">
        <h2>간단한 퀴즈</h2>
        {quiz}
      </section>
      {source_section}
    </main>
    <footer>생성일 {e(now_iso())}</footer>
  </div>
  <script>
    (() => {{
      async function lockLandscape() {{
        try {{
          if (screen.orientation && screen.orientation.lock) {{
            await screen.orientation.lock("landscape");
          }}
        }} catch (error) {{
        }}
      }}
      lockLandscape();
      document.addEventListener("click", lockLandscape, {{ once: true }});
      document.addEventListener("touchend", lockLandscape, {{ once: true }});
    }})();
  </script>
</body>
</html>
"""


def pack_thumbnail_url(pack: dict[str, Any]) -> str:
    for section in pack.get("content_sections") or []:
        if not isinstance(section, dict):
            continue
        for item in section.get("images") or []:
            if isinstance(item, dict):
                image_url = str(item.get("image_url") or "").strip()
                if image_url and not image_url.startswith("data:"):
                    return image_url
    return ""


def task_with_thumbnail(task: dict[str, Any]) -> dict[str, Any]:
    cloned = dict(task)
    result = dict(cloned.get("result") or {})
    if result.get("thumbnail_url"):
        cloned["result"] = result
        return cloned

    json_path = Path(result.get("json_path") or "")
    if json_path.exists():
        try:
            pack = json.loads(json_path.read_text(encoding="utf-8-sig"))
            if isinstance(pack, dict):
                thumbnail_url = pack_thumbnail_url(pack)
                if thumbnail_url:
                    result["thumbnail_url"] = thumbnail_url
        except Exception as exc:
            print(f"[tasks] thumbnail load failed: {exc}")
    if not result.get("thumbnail_url"):
        html_path = Path(result.get("html_path") or "")
        if html_path.exists():
            try:
                html_text = html_path.read_text(encoding="utf-8", errors="ignore")
                match = re.search(r'<img[^>]+src="([^"]+)"', html_text, re.IGNORECASE)
                if match and not match.group(1).startswith("data:"):
                    result["thumbnail_url"] = html.unescape(match.group(1))
            except Exception as exc:
                print(f"[tasks] thumbnail html scan failed: {exc}")
    cloned["result"] = result
    return cloned


def save_pack(task_id: str, pack: dict[str, Any]) -> dict[str, str]:
    slug = safe_slug(pack.get("topic") or pack.get("title") or task_id)
    output_dir = OUTPUT_DIR / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{slug}_{task_id[:8]}"
    output_dir.mkdir(parents=True, exist_ok=True)

    html_text = render_material_html(pack, task_id)
    html_path = output_dir / "index.html"
    json_path = output_dir / "content.json"
    html_path.write_text(html_text, encoding="utf-8")
    json_path.write_text(json.dumps(pack, ensure_ascii=False, indent=2), encoding="utf-8")

    return {
        "html_path": str(html_path),
        "json_path": str(json_path),
        "output_dir": str(output_dir),
        "title": str(pack.get("title") or pack.get("topic")),
        "topic": str(pack.get("topic") or ""),
        "grade": str(pack.get("grade") or ""),
        "thumbnail_url": pack_thumbnail_url(pack),
    }


def process_task(task_id: str, payload: dict[str, Any]) -> None:
    topic = str(payload.get("topic", "")).strip()
    grade = str(payload.get("grade", "초3")).strip() or "초3"
    quiz_count = int(payload.get("quiz_count", 5) or 5)
    quiz_count = max(1, min(quiz_count, 7))

    try:
        update_task(task_id, status="processing", percent=15, progress="주제와 대상 수준을 정리하는 중...")
        reference = fetch_wiki_reference(topic)
        if gemini_client:
            progress = "위키 자료를 바탕으로 학습자료 초안을 생성하는 중..." if reference else "AI로 학습자료 초안을 생성하는 중..."
            update_task(task_id, percent=35, progress=progress)
            pack = generate_with_gemini(topic, grade, quiz_count, reference=reference)
        else:
            update_task(task_id, percent=35, progress="AI 키가 없어 기본 템플릿을 생성하는 중...")
            pack = generate_fallback_pack(topic, grade, quiz_count)
        pack = apply_wiki_reference(pack, reference)

        update_task(task_id, percent=75, progress="HTML 문서로 저장하는 중...")
        result = save_pack(task_id, pack)
        update_task(
            task_id,
            status="completed",
            percent=100,
            progress="완료",
            result=result,
            completed_at=now_iso(),
        )
    except Exception as exc:
        update_task(
            task_id,
            status="failed",
            percent=100,
            progress="실패",
            error=str(exc),
        )


def worker_loop() -> None:
    while True:
        task_id, payload = task_queue.get()
        try:
            process_task(task_id, payload)
        finally:
            task_queue.task_done()


@app.route("/")
def index():
    return send_file(ROOT / "index.html")


@app.route("/process", methods=["POST"])
def process():
    data = request.get_json(silent=True) or {}
    topic = str(data.get("topic", "")).strip()
    if not topic:
        return jsonify({"success": False, "error": "주제를 입력하세요."}), 400

    grade = str(data.get("grade", "초3")).strip() or "초3"
    quiz_count = int(data.get("quiz_count", 5) or 5)
    task_id = str(uuid.uuid4())

    with task_lock:
        task_status[task_id] = {
            "task_id": task_id,
            "status": "queued",
            "percent": 5,
            "progress": "대기 중...",
            "topic": topic,
            "grade": grade,
            "quiz_count": max(1, min(quiz_count, 7)),
            "created_at": now_iso(),
            "updated_at": now_iso(),
            "result": {},
        }
        save_task_status()

    task_queue.put((task_id, task_status[task_id].copy()))
    return jsonify({"success": True, "task_id": task_id})


@app.route("/task/<task_id>")
def get_task(task_id: str):
    with task_lock:
        task = task_status.get(task_id)
        if not task:
            return jsonify({"error": "작업을 찾을 수 없습니다."}), 404
        return jsonify(task)


@app.route("/tasks")
def get_tasks():
    with task_lock:
        tasks = [task_with_thumbnail(task) for task in task_status.values()]
    tasks.sort(key=lambda item: item.get("created_at", ""), reverse=True)
    return jsonify({"tasks": tasks})


@app.route("/view/<task_id>")
def view_result(task_id: str):
    with task_lock:
        task = task_status.get(task_id)
    if not task:
        return "작업을 찾을 수 없습니다.", 404
    if task.get("status") != "completed":
        return "아직 완료되지 않은 작업입니다.", 400

    html_path = Path(task.get("result", {}).get("html_path", ""))
    json_path = Path(task.get("result", {}).get("json_path", ""))
    if html_path.exists():
        return html_path.read_text(encoding="utf-8")
    if json_path.exists():
        try:
            pack = json.loads(json_path.read_text(encoding="utf-8-sig"))
            if isinstance(pack, dict):
                return render_material_html(pack, task_id)
        except Exception as exc:
            print(f"[view] dynamic render failed: {exc}")
    if not html_path.exists():
        return "HTML 파일을 찾을 수 없습니다.", 404
    return html_path.read_text(encoding="utf-8")


@app.route("/download/<task_id>")
def download_result(task_id: str):
    with task_lock:
        task = task_status.get(task_id)
    if not task or task.get("status") != "completed":
        return jsonify({"success": False, "error": "완료된 작업을 찾을 수 없습니다."}), 404

    output_dir = Path(task.get("result", {}).get("output_dir", ""))
    if not output_dir.exists():
        return jsonify({"success": False, "error": "출력 폴더를 찾을 수 없습니다."}), 404

    zip_path = DATA_DIR / f"{task_id}.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in output_dir.rglob("*"):
            if path.is_file():
                archive.write(path, path.relative_to(output_dir))
    title = safe_slug(task.get("result", {}).get("title", "learning_material"))
    return send_file(zip_path, as_attachment=True, download_name=f"{title}.zip")


@app.route("/delete/<task_id>", methods=["POST"])
def delete_task(task_id: str):
    with task_lock:
        task = task_status.get(task_id)
        if not task:
            return jsonify({"success": False, "error": "작업을 찾을 수 없습니다."}), 404
        output_dir = Path(task.get("result", {}).get("output_dir", ""))
        if output_dir.exists() and output_dir.is_dir():
            for path in sorted(output_dir.rglob("*"), reverse=True):
                if path.is_file():
                    path.unlink()
                elif path.is_dir():
                    path.rmdir()
            output_dir.rmdir()
        del task_status[task_id]
        save_task_status()
    return jsonify({"success": True})


@app.route("/output/<path:filename>")
def serve_output(filename: str):
    return send_from_directory(OUTPUT_DIR, filename)


load_task_status()
threading.Thread(target=worker_loop, daemon=True).start()


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=False)
