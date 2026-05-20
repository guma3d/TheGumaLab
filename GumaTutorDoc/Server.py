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
from urllib.parse import quote

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
GUMATUBE_GEMINI_MODEL = "gemini-3.1-flash-lite-preview"


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
    candidate = text.strip()
    fenced = re.search(r"```(?:json)?\s*(.*?)```", candidate, re.DOTALL | re.IGNORECASE)
    if fenced:
        candidate = fenced.group(1).strip()
    if not candidate.startswith("{"):
        start = candidate.find("{")
        end = candidate.rfind("}")
        if start >= 0 and end > start:
            candidate = candidate[start : end + 1]
    parsed = json.loads(candidate)
    if not isinstance(parsed, dict):
        raise ValueError("Gemini response was not a JSON object")
    return parsed


def generate_with_gemini(topic: str, grade: str, quiz_count: int) -> dict[str, Any]:
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
            }
        ],
        "visuals": [
            {
                "title": "이미지 자료 제목",
                "caption": "이미지를 보며 확인할 핵심 내용",
                "prompt": "child friendly educational illustration prompt in English",
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
    user_prompt = (
        f"주제: {topic}\n"
        f"대상 수준: {grade}\n"
        f"퀴즈 수: {quiz_count}\n\n"
        "아래 스키마와 같은 키를 가진 JSON만 반환하세요. "
        "key_points는 4~6개, vocabulary는 4~8개, quiz는 요청한 수만큼 작성하세요. "
        "summary는 전체 내용을 대표하는 중요한 한국어 문장 정확히 5개로 작성하세요. "
        "content_sections는 4~6개로 만들고, 각 항목의 paragraphs에는 디테일한 설명을 2~4문단 넣으세요. "
        "visuals는 아이가 흥미를 느낄 수 있는 사진/그림 자료 아이디어 6~8개로 만들고, prompt는 영어 이미지 생성 프롬프트로 작성하세요. "
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
            },
            {
                "title": "더 깊게 생각해보기",
                "paragraphs": [
                    "이 주제가 우리 생활, 자연, 역사, 기술 중 어디와 연결되는지 생각해봅니다.",
                    "궁금한 점을 질문으로 바꾸면 다음에 찾아볼 내용이 더 분명해집니다.",
                ],
                "examples": ["왜 그럴까?", "언제 생길까?", "어디에서 볼 수 있을까?"],
            },
        ],
        "visuals": [
            {
                "title": f"{topic} 전체 그림",
                "caption": "주제를 한 장면으로 떠올려보는 이미지입니다.",
                "prompt": f"child friendly colorful educational illustration about {topic}, clear main subject, bright classroom style",
            },
            {
                "title": "핵심 개념 장면",
                "caption": "가장 중요한 개념을 그림으로 확인합니다.",
                "prompt": f"simple educational diagram for children explaining {topic}, colorful, clear, no text",
            },
            {
                "title": "생활 속 예시",
                "caption": "우리 주변에서 비슷한 모습을 찾아봅니다.",
                "prompt": f"child friendly real life example of {topic}, bright educational illustration",
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
        normalized_sections.append(
            {
                "title": str(item.get("title") or "자세한 설명").strip(),
                "paragraphs": [str(paragraph).strip() for paragraph in paragraphs if str(paragraph).strip()],
                "examples": [str(example).strip() for example in examples if str(example).strip()],
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
                }
            )
    if not normalized_sections:
        normalized_sections = [
            {
                "title": f"{topic} 자세히 알아보기",
                "paragraphs": [pack["summary"][0]],
                "examples": [],
            }
        ]
    pack["content_sections"] = normalized_sections

    visuals = pack.get("visuals")
    if not isinstance(visuals, list):
        visuals = []
    normalized_visuals = []
    for item in visuals:
        if not isinstance(item, dict):
            continue
        title = str(item.get("title") or "").strip()
        caption = str(item.get("caption") or "").strip()
        prompt = str(item.get("prompt") or title or caption or topic).strip()
        if prompt:
            normalized_visuals.append({"title": title or "이미지 자료", "caption": caption, "prompt": prompt})
    for section in normalized_sections:
        if len(normalized_visuals) >= 6:
            break
        title = section.get("title") or topic
        normalized_visuals.append(
            {
                "title": f"{title} 그림",
                "caption": f"{title}을 이미지로 떠올려봅니다.",
                "prompt": f"child friendly colorful educational illustration about {topic}: {title}, clear, bright, no text",
            }
        )
    while len(normalized_visuals) < 6:
        normalized_visuals.append(
            {
                "title": f"{topic} 이미지 자료",
                "caption": "주제를 더 쉽게 이해하기 위한 그림 자료입니다.",
                "prompt": f"child friendly educational illustration about {topic}, colorful, clear, no text",
            }
        )
    pack["visuals"] = normalized_visuals[:8]

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
<body>
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


def visual_image_url(prompt: str, seed: int) -> str:
    image_prompt = (
        "child friendly educational image, colorful, clear, curious elementary student style, "
        "safe classroom learning material, no text, "
        + str(prompt or "")
    )
    return f"https://image.pollinations.ai/prompt/{quote(image_prompt, safe='')}?width=900&height=520&nologo=true&seed={seed}"


def render_material_html(pack: dict[str, Any], task_id: str) -> str:
    seed_base = int(task_id[:8], 16)
    summary = list_html(pack.get("summary", []), "summary-list")
    sources = list_html(pack.get("sources", []), "sources")

    visuals = "\n".join(
        f"""
        <figure class="visual-card">
          <img src="{e(visual_image_url(item.get("prompt", ""), seed_base + idx))}" alt="{e(item.get("title"))}" loading="lazy" referrerpolicy="no-referrer" onerror="this.onerror=null;this.src='{e(svg_placeholder_url(item.get("title", ""), seed_base + idx))}';">
          <figcaption>
            <strong>{e(item.get("title"))}</strong>
            <span>{e(item.get("caption"))}</span>
          </figcaption>
        </figure>
        """
        for idx, item in enumerate(pack.get("visuals", []), start=1)
    )

    content_sections = "\n".join(
        f"""
        <section class="content-section">
          <h3>{e(section.get("title"))}</h3>
          {"".join(f"<p>{e(paragraph)}</p>" for paragraph in section.get("paragraphs", []))}
          {list_html(section.get("examples", []), "examples") if section.get("examples") else ""}
        </section>
        """
        for section in pack.get("content_sections", [])
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
      color-scheme: light;
      --ink: #172033;
      --muted: #5b6472;
      --line: #dbe3ee;
      --paper: #ffffff;
      --bg: #f6f8fb;
      --teal: #0f766e;
      --blue: #2563eb;
      --rose: #e11d48;
      --amber: #f59e0b;
      --mint: #dff5f1;
      --sky: #e0f2fe;
      --peach: #fff0dc;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: "Malgun Gothic", "Apple SD Gothic Neo", system-ui, sans-serif;
      color: var(--ink);
      background: var(--bg);
      line-height: 1.68;
    }}
    .page {{
      max-width: 1080px;
      margin: 0 auto;
      padding: 36px 18px 72px;
    }}
    header {{
      padding: 30px 0 26px;
      border-bottom: 4px solid var(--teal);
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
      font-size: 23px;
      line-height: 1.3;
      letter-spacing: 0;
    }}
    h3 {{
      margin: 0 0 8px;
      font-size: 19px;
      line-height: 1.35;
      letter-spacing: 0;
    }}
    p {{ margin: 0 0 10px; }}
    ul {{ margin: 0; padding-left: 22px; }}
    .summary-list {{
      display: grid;
      gap: 10px;
      padding: 0;
      list-style: none;
      counter-reset: summary;
    }}
    .summary-list li {{
      counter-increment: summary;
      position: relative;
      padding: 12px 14px 12px 48px;
      border-radius: 8px;
      background: var(--mint);
      border: 1px solid #bfe7df;
    }}
    .summary-list li::before {{
      content: counter(summary);
      position: absolute;
      left: 14px;
      top: 12px;
      width: 24px;
      height: 24px;
      border-radius: 50%;
      background: var(--teal);
      color: white;
      display: grid;
      place-items: center;
      font-size: 13px;
      font-weight: 700;
    }}
    .visual-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
      gap: 14px;
    }}
    .visual-card {{
      margin: 0;
      border: 1px solid var(--line);
      border-radius: 8px;
      overflow: hidden;
      background: #fff;
    }}
    .visual-card img {{
      display: block;
      width: 100%;
      aspect-ratio: 16 / 10;
      object-fit: cover;
      background: var(--sky);
    }}
    figcaption {{
      display: grid;
      gap: 4px;
      padding: 12px;
      font-size: 14px;
      color: var(--muted);
    }}
    figcaption strong {{
      color: var(--ink);
      font-size: 15px;
    }}
    .content-section {{
      border-top: 1px solid var(--line);
      padding-top: 18px;
      margin-top: 18px;
    }}
    .content-section:first-child {{
      border-top: 0;
      padding-top: 0;
      margin-top: 0;
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
      border-radius: 6px;
      padding: 9px 11px;
      color: #573b06;
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
      color: var(--blue);
    }}
    .quiz-item {{
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 16px;
      margin-top: 12px;
      background: #fff;
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
    @media (max-width: 640px) {{
      .page {{ padding: 24px 14px 48px; }}
      h1 {{ font-size: 30px; }}
      section.block {{ padding: 18px; }}
      th {{ width: 110px; }}
    }}
  </style>
</head>
<body>
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
      <section class="block">
        <h2>이미지로 이해하기</h2>
        <div class="visual-grid">
          {visuals}
        </div>
      </section>
      <section class="block">
        <h2>내용</h2>
        {content_sections}
      </section>
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
</body>
</html>
"""


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
    }


def process_task(task_id: str, payload: dict[str, Any]) -> None:
    topic = str(payload.get("topic", "")).strip()
    grade = str(payload.get("grade", "초3")).strip() or "초3"
    quiz_count = int(payload.get("quiz_count", 5) or 5)
    quiz_count = max(1, min(quiz_count, 7))

    try:
        update_task(task_id, status="processing", percent=15, progress="주제와 대상 수준을 정리하는 중...")
        if gemini_client:
            update_task(task_id, percent=35, progress="AI로 학습자료 초안을 생성하는 중...")
            pack = generate_with_gemini(topic, grade, quiz_count)
        else:
            update_task(task_id, percent=35, progress="AI 키가 없어 기본 템플릿을 생성하는 중...")
            pack = generate_fallback_pack(topic, grade, quiz_count)

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
        tasks = list(task_status.values())
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
