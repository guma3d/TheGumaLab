"""
GumaSpending — Flask calendar dashboard.

Loads transactions_*.json (card) and bank_transactions_*.json (bank) into
SQLite, then serves a month-grid calendar UI and detail-per-day API.

Bank withdrawals with descriptions matching BANK_DEDUP_PATTERNS (e.g., 카드대금)
are skipped at ingestion time to avoid double-counting with card approval data.
"""

from __future__ import annotations

import calendar as calendar_mod
import glob
import json
import os
import re
import sqlite3
import time
import unicodedata
from datetime import date, datetime, timedelta
from pathlib import Path

import requests as http_requests
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from flask import Flask, jsonify, render_template, request, send_from_directory

from fetch_bank_transactions import run as run_bank_fetch
from fetch_transactions import (
    load_connected_ids,
    load_credentials as load_codef_credentials,
    run as run_card_fetch,
)

APP_DIR = Path(__file__).resolve().parent
DB_PATH = APP_DIR / "spending.db"
CARD_TX_GLOB = str(APP_DIR / "transactions_*.json")
BANK_TX_GLOB = str(APP_DIR / "bank_transactions_*.json")

EXCLUDED_STORE_NAMES = ("정자아이파크입주자대표회의",)
_EXCL_CLAUSE = " AND store_name NOT IN (" + ",".join("?" * len(EXCLUDED_STORE_NAMES)) + ")"

ORG_NAMES = {
    # cards
    "0301": "KB카드",
    "0302": "현대카드",
    "0303": "삼성카드",
    "0304": "NH카드",
    "0305": "BC카드",
    "0306": "신한카드",
    "0307": "씨티카드",
    "0309": "우리카드",
    "0311": "롯데카드",
    "0313": "하나카드",
    # banks
    "0002": "산업은행",
    "0003": "기업은행",
    "0004": "국민은행",
    "0007": "수협은행",
    "0011": "농협은행",
    "0020": "우리은행",
    "0023": "SC제일은행",
    "0027": "한국씨티은행",
    "0071": "우체국",
    "0081": "하나은행",
    "0088": "신한은행",
    "0089": "케이뱅크",
    "0090": "카카오뱅크",
    "0092": "토스뱅크",
}

# NH카드 세부 카드명: card-list에서는 이름이 나오지만 approval-list에서는 빈 문자열.
# 카드번호 끝 4자리 → 실제 카드명 매핑.
NH_CARD_NAMES = {
    "4256": "올바른GLOBAL체크",
    "0653": "채움 BAZIC",
    "6377": "채움 뉴 후불 하이패스",
    "1224": "채움 BAZIC",
}

BANK_DEDUP_PATTERNS = [
    "카드대금",
    "카드결제",
    "카드출금",
    "카드자동",
    "신용카드",
    "체크카드",
]
_DEDUP_RE = re.compile("|".join(BANK_DEDUP_PATTERNS))

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
_GEMINI_MODELS = [
    "gemini-3.1-flash-lite-preview",
    "gemini-2.5-flash-lite",
    "gemini-2.5-flash",
    "gemini-2.0-flash-lite",
    "gemini-2.0-flash",
]

# 본인 명의 계좌 간 이체 필터 — .env의 OWNER_NAME과 일치하는 store_name은 skip.
# 여러 명의가 있으면 쉼표로 구분: OWNER_NAME=홍길동,Hong Gil Dong
_OWNER_NAMES: set[str] = {
    unicodedata.normalize("NFKC", n.strip())
    for n in os.getenv("OWNER_NAME", "").split(",")
    if n.strip()
}

# store_category 접미사가 "체크"/"신용"이면 카드 approval과 중복.
# 예) "NH체크", "NH신용", "KB체크" — 은행 쪽 기록은 skip.
_CARD_CATEGORY_RE = re.compile(r"(체크|신용)$")

UI_VERSION = "9"

app = Flask(__name__)
app.config["JSON_AS_ASCII"] = False


def _db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Drop-and-recreate — spending.db is fully derived from JSON files."""
    with _db() as conn:
        conn.execute("DROP TABLE IF EXISTS transactions")
        conn.execute(
            """
            CREATE TABLE transactions (
                source TEXT NOT NULL,           -- 'card' | 'bank'
                org TEXT NOT NULL,
                card_name TEXT,                 -- 카드사/은행 이름
                sub_card_name TEXT,             -- 세부 카드명 / 계좌명
                card_no_masked TEXT,            -- 마스킹된 카드번호/계좌번호
                used_date TEXT NOT NULL,        -- YYYY-MM-DD
                used_time TEXT,                 -- HHMMSS
                store_name TEXT,                -- 가맹점명 / 이체적요
                store_category TEXT,            -- 업종 / 거래타입
                amount INTEGER NOT NULL,        -- 금액 (출금/승인)
                dedup_key TEXT NOT NULL         -- 중복 제거용 키
            )
            """
        )
        conn.execute(
            "CREATE UNIQUE INDEX idx_dedup ON transactions(source, org, dedup_key)"
        )
        conn.execute("CREATE INDEX idx_used_date ON transactions(used_date)")
        conn.commit()


def _mask(card_no: str) -> str:
    if not card_no or len(card_no) < 8:
        return card_no or ""
    return f"{card_no[:4]}****{card_no[-4:]}"


def _parse_yyyymmdd(raw: str) -> str:
    if len(raw) == 8:
        return f"{raw[:4]}-{raw[4:6]}-{raw[6:8]}"
    return raw


def _ingest_cards(conn: sqlite3.Connection) -> dict:
    inserted = 0
    skipped_cancel = 0
    files = sorted(glob.glob(CARD_TX_GLOB))
    for path in files:
        try:
            payload = json.loads(Path(path).read_text(encoding="utf-8"))
        except (OSError, ValueError) as e:
            print(f"[WARN] failed to read {path}: {e}")
            continue

        org = payload.get("organization", "")
        card_name = payload.get("card_name", "")
        for tx in payload.get("transactions", []):
            cancel_yn = (tx.get("resCancelYN") or "").strip()
            if cancel_yn in ("Y", "1"):
                skipped_cancel += 1
                continue
            try:
                amount = int(tx.get("resUsedAmount", "0") or "0")
            except ValueError:
                amount = 0
            # 부분 환불: cancelAmount만큼 차감
            try:
                cancel_amt = int(tx.get("resCancelAmount", "0") or "0")
            except ValueError:
                cancel_amt = 0
            if cancel_amt > 0:
                amount -= cancel_amt
            if amount <= 0:
                skipped_cancel += 1
                continue

            used_date = _parse_yyyymmdd(tx.get("resUsedDate", ""))
            used_time = tx.get("resUsedTime", "")
            approval_no = tx.get("resApprovalNo", "")
            card_no = tx.get("resCardNo", "")
            dedup = f"{approval_no}|{used_date}|{used_time}|{card_no[-4:]}"

            # NH카드 sub_card_name fallback: approval-list는 빈 문자열 반환
            sub_card = (tx.get("resCardName") or "").strip()
            if not sub_card and org == "0304" and len(card_no) >= 4:
                sub_card = NH_CARD_NAMES.get(card_no[-4:], "")

            try:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO transactions
                    (source, org, card_name, sub_card_name, card_no_masked,
                     used_date, used_time, store_name, store_category,
                     amount, dedup_key)
                    VALUES ('card', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        org,
                        card_name,
                        sub_card,
                        _mask(card_no),
                        used_date,
                        used_time,
                        tx.get("resMemberStoreName", ""),
                        tx.get("resMemberStoreBusinessType", ""),
                        amount,
                        dedup,
                    ),
                )
                inserted += 1
            except sqlite3.Error as e:
                print(f"[WARN] card insert failed: {e}")

    return {"files": len(files), "inserted": inserted, "skipped_cancel": skipped_cancel}


def _ingest_banks(conn: sqlite3.Connection) -> dict:
    inserted = 0
    skipped_dedup = 0
    skipped_deposit = 0
    files = sorted(glob.glob(BANK_TX_GLOB))
    for path in files:
        try:
            payload = json.loads(Path(path).read_text(encoding="utf-8"))
        except (OSError, ValueError) as e:
            print(f"[WARN] failed to read {path}: {e}")
            continue

        org = payload.get("organization", "")
        bank_name = payload.get("bank_name", "")
        for tx in payload.get("transactions", []):
            try:
                out_amt = int(tx.get("resAccountOut", "0") or "0")
            except ValueError:
                out_amt = 0
            if out_amt <= 0:
                skipped_deposit += 1
                continue

            desc1 = (tx.get("resAccountDesc1") or "").strip()
            desc2 = (tx.get("resAccountDesc2") or "").strip()
            desc3 = (tx.get("resAccountDesc3") or "").strip()
            desc4 = (tx.get("resAccountDesc4") or "").strip()
            desc_all = unicodedata.normalize(
                "NFKC", " ".join(filter(None, [desc1, desc2, desc3, desc4]))
            )

            if _DEDUP_RE.search(desc_all):
                skipped_dedup += 1
                continue

            store_name = desc3 or desc1 or desc2 or "(내역 없음)"
            store_category = desc2 or desc4 or ""

            if _OWNER_NAMES and unicodedata.normalize("NFKC", store_name.strip()) in _OWNER_NAMES:
                skipped_dedup += 1
                continue

            if _CARD_CATEGORY_RE.search(unicodedata.normalize("NFKC", store_category)):
                skipped_dedup += 1
                continue

            used_date = _parse_yyyymmdd(tx.get("resAccountTrDate", ""))
            used_time = tx.get("resAccountTrTime", "")
            account_no = tx.get("_account_no", "")
            account_name = tx.get("_account_name", "")
            balance_after = tx.get("resAfterTranBalance", "")
            dedup = f"{account_no}|{used_date}|{used_time}|{out_amt}|{balance_after}"

            try:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO transactions
                    (source, org, card_name, sub_card_name, card_no_masked,
                     used_date, used_time, store_name, store_category,
                     amount, dedup_key)
                    VALUES ('bank', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        org,
                        bank_name,
                        account_name,
                        _mask(account_no),
                        used_date,
                        used_time,
                        store_name,
                        store_category,
                        out_amt,
                        dedup,
                    ),
                )
                inserted += 1
            except sqlite3.Error as e:
                print(f"[WARN] bank insert failed: {e}")

    return {
        "files": len(files),
        "inserted": inserted,
        "skipped_dedup": skipped_dedup,
        "skipped_deposit": skipped_deposit,
    }


def reload_transactions() -> dict:
    """Drop and re-ingest all transactions from JSON files."""
    init_db()
    with _db() as conn:
        card_stats = _ingest_cards(conn)
        bank_stats = _ingest_banks(conn)
        conn.commit()
    return {"card": card_stats, "bank": bank_stats}


# ── AI 분석 ──────────────────────────────────────────────────────────────────

def ensure_analyses_table() -> None:
    """analyses 테이블 생성 (transactions 새로고침에도 유지)."""
    with _db() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS analyses (
                ym TEXT PRIMARY KEY,
                content TEXT NOT NULL,
                generated_at TEXT NOT NULL
            )
            """
        )
        conn.commit()


def _prepare_month_data(ym: str) -> dict:
    """Gemini 프롬프트용 월별 집계 데이터 구성."""
    y, m = map(int, ym.split("-"))
    start = f"{ym}-01"
    next_m = m + 1 if m < 12 else 1
    next_y = y if m < 12 else y + 1
    end = f"{next_y:04d}-{next_m:02d}-01"

    with _db() as conn:
        total_row = conn.execute(
            "SELECT COALESCE(SUM(amount),0), COUNT(*) FROM transactions "
            "WHERE used_date>=? AND used_date<?" + _EXCL_CLAUSE,
            (start, end, *EXCLUDED_STORE_NAMES),
        ).fetchone()
        source_rows = conn.execute(
            "SELECT source, COALESCE(SUM(amount),0), COUNT(*) FROM transactions "
            "WHERE used_date>=? AND used_date<?" + _EXCL_CLAUSE + " GROUP BY source",
            (start, end, *EXCLUDED_STORE_NAMES),
        ).fetchall()
        store_rows = conn.execute(
            "SELECT store_name, store_category, SUM(amount) AS total, COUNT(*) AS cnt "
            "FROM transactions WHERE used_date>=? AND used_date<?" + _EXCL_CLAUSE + " "
            "GROUP BY store_name ORDER BY total DESC LIMIT 20",
            (start, end, *EXCLUDED_STORE_NAMES),
        ).fetchall()

        # 전후 월 정기 이체 컨텍스트 (같은 store_name이 월에 걸쳐 밀림 감지)
        # 조건: 100만원 이상 대형 이체 OR 키워드 매칭 정기 이체 (관리비, 생활비 등)
        _RECURRING_KW = ["관리비", "생활비"]
        kw_clause = " OR ".join("store_name LIKE ?" for _ in _RECURRING_KW)
        kw_params = [f"%{kw}%" for kw in _RECURRING_KW]
        big_bank_names = conn.execute(
            "SELECT DISTINCT store_name FROM transactions "
            "WHERE source='bank' AND used_date>=? AND used_date<? "
            f"AND (amount>=1000000 OR ({kw_clause}))"
            + _EXCL_CLAUSE,
            (start, end, *kw_params, *EXCLUDED_STORE_NAMES),
        ).fetchall()

        adjacent_context: list[dict] = []
        if big_bank_names:
            prev_m = m - 1 if m > 1 else 12
            prev_y = y if m > 1 else y - 1
            prev_start = f"{prev_y:04d}-{prev_m:02d}-01"
            next_next_m = next_m + 1 if next_m < 12 else 1
            next_next_y = next_y if next_m < 12 else next_y + 1
            next_end = f"{next_next_y:04d}-{next_next_m:02d}-01"

            for (name,) in big_bank_names:
                rows = conn.execute(
                    "SELECT used_date, amount FROM transactions "
                    "WHERE source='bank' AND store_name=? AND used_date>=? AND used_date<? "
                    "ORDER BY used_date",
                    (name, prev_start, next_end),
                ).fetchall()
                if rows:
                    months_map: dict[str, list] = {}
                    for rd, ra in rows:
                        mk = rd[:7]
                        months_map.setdefault(mk, []).append({"date": rd, "amount": ra})
                    adjacent_context.append({"name": name, "months": months_map})

    return {
        "ym": ym,
        "total": total_row[0],
        "count": total_row[1],
        "by_source": {r[0]: {"total": r[1], "count": r[2]} for r in source_rows},
        "top_stores": [
            {"name": r[0], "category": r[1] or "기타", "total": r[2], "count": r[3]}
            for r in store_rows
        ],
        "adjacent_transfers": adjacent_context,
    }


def _build_prompt(data: dict, is_current: bool) -> str:
    """월별 데이터로 Gemini 프롬프트 생성."""
    y, m = map(int, data["ym"].split("-"))
    month_name = f"{y}년 {m}월"
    card_total = data["by_source"].get("card", {}).get("total", 0)
    bank_total = data["by_source"].get("bank", {}).get("total", 0)

    stores_text = "\n".join(
        f"  {i+1}. {s['name']} ({s['category']}): {s['total']:,}원 ({s['count']}건)"
        for i, s in enumerate(data["top_stores"])
    )

    lines = [
        f"당신은 개인 재무 분석가입니다. 아래는 {month_name} 실제 지출 데이터입니다.",
        "",
        f"[총 지출] {data['total']:,}원 ({data['count']}건)",
        f"  - 카드 승인: {card_total:,}원",
        f"  - 계좌 출금/현금: {bank_total:,}원",
        "",
        "[주요 지출처 Top 20]",
        stores_text,
    ]

    # 전후 월 대형 정기 이체 컨텍스트
    adj = data.get("adjacent_transfers", [])
    if adj:
        lines += ["", "[대형 정기 이체 — 전월/당월/차월 비교]"]
        for item in adj:
            lines.append(f"  ▸ {item['name']}:")
            for mk in sorted(item["months"]):
                entries = item["months"][mk]
                total = sum(e["amount"] for e in entries)
                dates = ", ".join(e["date"] for e in entries)
                lines.append(f"    {mk}: {len(entries)}건 {total:,}원 ({dates})")
        lines += [
            "",
            "※ 위 정기 이체가 한 달에 2회 발생하면 전후 달에 0회인 경우가 많습니다.",
            "  이 경우 실질적으로 월 1회 비용이므로 해당 월 지출이 과대 계상된 것이 아닙니다.",
            "  분석 시 이 맥락을 반드시 반영해주세요.",
        ]

    exclusion_rules = [
        "",
        "[분석 제외 규칙 — 반드시 지켜주세요]",
        "- 편의점 지출(GS25, CU, 세븐일레븐, 이마트24 등)은 불가피한 소비이므로 분석·조언에서 언급하지 마세요.",
        "- '편의점', 'GS25', 'CU', '세븐일레븐' 같은 단어를 출력에 포함하지 마세요.",
    ]

    common_sections = [
        "",
        "아래 정확한 형식으로 한국어 분석을 작성해주세요.",
        "",
        "1. 분석 요약",
        "- 이달 지출의 종합 의견을 작성하세요.",
        "- 아래 '주요 특이점'과 '일반적인 지출' 양쪽을 모두 고려한 전체적인 평가입니다.",
        "- 특이 지출이 있으면 해당 금액을 제외했을 때의 실질 생활비도 언급해주세요.",
        "",
        "2. 주요 특이점",
        "- 매월 반복되지 않는 비정기·특수 지출을 정리하세요.",
        "- 예: 여행, 자동차 수리/정비, 세금, 대출 상환, 경조사, 큰 가전 구입, 보험료, 의료비 등",
        "- 각 항목에 가맹점명과 금액을 명시하세요.",
        "- 해당 월에 특이 지출이 없으면 '이달은 특별한 비정기 지출이 없었습니다'로 짧게 마무리하세요.",
        "",
        "3. 일반적인 지출",
        "- 매월 반복되는 고정·생활 지출을 정리하세요.",
        "- 예: 생활비 이체, 공과금, 통신비, 주유비, 식비, 교통비, 마트/장보기, 구독료 등",
        "- 전월 대비 눈에 띄게 늘거나 줄었다면 언급해주세요.",
    ]

    if is_current:
        today = date.today()
        days_passed = today.day
        days_in_month = calendar_mod.monthrange(y, m)[1]
        days_left = days_in_month - days_passed
        daily_avg = data["total"] // days_passed if days_passed > 0 else 0
        projected = daily_avg * days_in_month
        lines += exclusion_rules + [
            "",
            f"[현재 기준] {month_name} {today.day}일 (경과 {days_passed}일, 남은 {days_left}일)",
            f"  - 일평균 지출: {daily_avg:,}원 / 이달 말 예상 누적: {projected:,}원",
        ] + common_sections + [
            "",
            "추가 요청 (현재 진행 중인 달이므로):",
            "- '1. 분석 요약'에 남은 기간 소비 조언과 이달 말 예상 총 지출도 포함해주세요.",
            "- '3. 일반적인 지출'에서 남은 일수 대비 일평균을 고려한 조언도 추가해주세요.",
        ]
    else:
        lines += exclusion_rules + common_sections

    lines += [
        "",
        "작성 규칙:",
        "- 섹션 제목은 반드시 `1. 분석 요약`, `2. 주요 특이점`, `3. 일반적인 지출` 형태로 시작하세요 (번호 + 점 + 공백 + 제목).",
        "- 섹션 본문은 `- `로 시작하는 불릿 항목으로만 작성하세요. 문단(paragraph)은 사용하지 마세요.",
        "- 중요한 키워드(금액, 가맹점명, 주의 문구 등)는 **볼드**로 강조하세요. 예: **350,000원**, **쿠팡**, **전월 대비 20% 증가**",
        "- 각 불릿은 한 문장~두 문장으로 간결하게 작성하세요.",
    ]
    return "\n".join(lines)


def _call_gemini(prompt: str) -> str:
    """Gemini REST API 호출 (모델 폴백 체인)."""
    if not GEMINI_API_KEY:
        return "GEMINI_API_KEY가 설정되지 않았습니다."
    for model in _GEMINI_MODELS:
        try:
            url = (
                f"https://generativelanguage.googleapis.com/v1beta/models/"
                f"{model}:generateContent?key={GEMINI_API_KEY}"
            )
            resp = http_requests.post(
                url,
                json={"contents": [{"parts": [{"text": prompt}]}]},
                timeout=30,
            )
            if resp.status_code == 200:
                return resp.json()["candidates"][0]["content"]["parts"][0]["text"]
            if resp.status_code in (429, 503):
                print(f"[gemini] {model} {resp.status_code} — 다음 모델 시도", flush=True)
                continue
            return f"API 오류 ({resp.status_code}): {resp.text[:200]}"
        except Exception as e:
            print(f"[gemini] {model} 실패: {e}", flush=True)
            continue
    return "AI 분석을 일시적으로 사용할 수 없습니다. 잠시 후 다시 시도해주세요."


@app.route("/api/analyze/<ym>", methods=["GET"])
def api_analyze_get(ym: str):
    """캐시된 분석 조회."""
    with _db() as conn:
        row = conn.execute(
            "SELECT content, generated_at FROM analyses WHERE ym=?", (ym,)
        ).fetchone()
    if row:
        return jsonify({"ym": ym, "content": row[0], "generated_at": row[1], "cached": True})
    return jsonify({"ym": ym, "content": None, "cached": False})


@app.route("/api/analyze/<ym>", methods=["POST"])
def api_analyze_post(ym: str):
    """AI 분석 생성 (force=1이면 캐시 무시)."""
    force = request.args.get("force", "0") == "1"
    if not force:
        with _db() as conn:
            row = conn.execute(
                "SELECT content, generated_at FROM analyses WHERE ym=?", (ym,)
            ).fetchone()
        if row:
            return jsonify({"ym": ym, "content": row[0], "generated_at": row[1], "cached": True})

    today = date.today()
    current_ym = f"{today.year:04d}-{today.month:02d}"
    data = _prepare_month_data(ym)
    if data["total"] == 0:
        return jsonify({"error": "해당 월의 지출 데이터가 없습니다."}), 404

    content = _call_gemini(_build_prompt(data, is_current=(ym == current_ym)))
    now_str = datetime.now().isoformat()
    with _db() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO analyses (ym, content, generated_at) VALUES (?,?,?)",
            (ym, content, now_str),
        )
        conn.commit()
    return jsonify({"ym": ym, "content": content, "generated_at": now_str, "cached": False})


@app.route("/")
def home():
    resp = render_template("index.html", v=UI_VERSION)
    return resp, 200, {"Cache-Control": "no-cache, must-revalidate"}


@app.route("/sw.js")
def serve_sw():
    response = send_from_directory("static", "sw.js")
    response.headers["Content-Type"] = "application/javascript"
    response.headers["Service-Worker-Allowed"] = "/"
    return response


@app.route("/api/month/<ym>")
def api_month(ym: str):
    """Day-level aggregates + month total for a given YYYY-MM."""
    try:
        year, month = map(int, ym.split("-"))
    except ValueError:
        return jsonify({"error": "invalid ym format, expected YYYY-MM"}), 400

    start = f"{year:04d}-{month:02d}-01"
    next_month = month + 1 if month < 12 else 1
    next_year = year if month < 12 else year + 1
    end = f"{next_year:04d}-{next_month:02d}-01"

    with _db() as conn:
        rows = conn.execute(
            f"""
            SELECT used_date, SUM(amount) AS total, COUNT(*) AS cnt
            FROM transactions
            WHERE used_date >= ? AND used_date < ?{_EXCL_CLAUSE}
            GROUP BY used_date
            ORDER BY used_date
            """,
            (start, end, *EXCLUDED_STORE_NAMES),
        ).fetchall()

        month_total_row = conn.execute(
            f"""
            SELECT COALESCE(SUM(amount), 0) AS total, COUNT(*) AS cnt
            FROM transactions
            WHERE used_date >= ? AND used_date < ?{_EXCL_CLAUSE}
            """,
            (start, end, *EXCLUDED_STORE_NAMES),
        ).fetchone()

        by_card_rows = conn.execute(
            f"""
            SELECT source, org, card_name, sub_card_name,
                   SUM(amount) AS total, COUNT(*) AS cnt
            FROM transactions
            WHERE used_date >= ? AND used_date < ?{_EXCL_CLAUSE}
            GROUP BY source, org, card_name, sub_card_name
            ORDER BY total DESC
            """,
            (start, end, *EXCLUDED_STORE_NAMES),
        ).fetchall()

        by_source_row = conn.execute(
            f"""
            SELECT source, COALESCE(SUM(amount), 0) AS total, COUNT(*) AS cnt
            FROM transactions
            WHERE used_date >= ? AND used_date < ?{_EXCL_CLAUSE}
            GROUP BY source
            """,
            (start, end, *EXCLUDED_STORE_NAMES),
        ).fetchall()

    days = {r["used_date"]: {"total": r["total"], "count": r["cnt"]} for r in rows}
    by_card = []
    for r in by_card_rows:
        d = dict(r)
        d["org_name"] = ORG_NAMES.get(d["org"], d["org"])
        by_card.append(d)

    return jsonify(
        {
            "ym": ym,
            "month_total": month_total_row["total"],
            "month_count": month_total_row["cnt"],
            "days": days,
            "by_card": by_card,
            "by_source": {r["source"]: {"total": r["total"], "count": r["cnt"]} for r in by_source_row},
        }
    )


@app.route("/api/day/<ymd>")
def api_day(ymd: str):
    """Detailed transactions for a single day."""
    try:
        datetime.strptime(ymd, "%Y-%m-%d")
    except ValueError:
        return jsonify({"error": "invalid ymd format"}), 400

    with _db() as conn:
        rows = conn.execute(
            f"""
            SELECT source, org, card_name, sub_card_name, card_no_masked, used_time,
                   store_name, store_category, amount
            FROM transactions
            WHERE used_date = ?{_EXCL_CLAUSE}
            ORDER BY amount DESC, used_time DESC
            """,
            (ymd, *EXCLUDED_STORE_NAMES),
        ).fetchall()

    txs = []
    for r in rows:
        d = dict(r)
        d["org_name"] = ORG_NAMES.get(d["org"], d["org"])
        txs.append(d)

    total = sum(r["amount"] for r in rows)
    return jsonify({"date": ymd, "total": total, "count": len(txs), "transactions": txs})


@app.route("/api/summary")
def api_summary():
    """Overall totals + available months (for month-picker)."""
    with _db() as conn:
        months_row = conn.execute(
            f"""
            SELECT DISTINCT SUBSTR(used_date, 1, 7) AS ym
            FROM transactions
            WHERE 1=1{_EXCL_CLAUSE}
            ORDER BY ym DESC
            """,
            EXCLUDED_STORE_NAMES,
        ).fetchall()
        grand = conn.execute(
            f"SELECT COALESCE(SUM(amount), 0) AS total, COUNT(*) AS cnt FROM transactions "
            f"WHERE 1=1{_EXCL_CLAUSE}",
            EXCLUDED_STORE_NAMES,
        ).fetchone()

    return jsonify(
        {
            "grand_total": grand["total"],
            "grand_count": grand["cnt"],
            "months": [r["ym"] for r in months_row],
        }
    )


@app.route("/api/analyze/backfill", methods=["POST"])
def api_analyze_backfill():
    """과거 월 분석을 백그라운드 스레드로 순차 생성. force=1이면 기존 분석도 재생성."""
    import threading

    force = request.args.get("force", "0") == "1"

    def _run():
        with _db() as conn:
            all_months = [
                r[0]
                for r in conn.execute(
                    "SELECT DISTINCT SUBSTR(used_date,1,7) FROM transactions ORDER BY 1"
                ).fetchall()
            ]
            analyzed = {
                r[0] for r in conn.execute("SELECT ym FROM analyses").fetchall()
            }
        today = date.today()
        current_ym = f"{today.year:04d}-{today.month:02d}"
        if force:
            targets = [m for m in all_months if m < current_ym]
        else:
            targets = [m for m in all_months if m < current_ym and m not in analyzed]
        label = "force-backfill" if force else "backfill"
        print(f"[{label}] 대상 {len(targets)}개월: {targets}", flush=True)
        for i, ym in enumerate(targets):
            try:
                data = _prepare_month_data(ym)
                if data["total"] == 0:
                    print(f"[{label}] {ym} 데이터 없음 skip", flush=True)
                    continue
                content = _call_gemini(_build_prompt(data, is_current=False))
                now_str = datetime.now().isoformat()
                with _db() as conn:
                    conn.execute(
                        "INSERT OR REPLACE INTO analyses (ym,content,generated_at) VALUES (?,?,?)",
                        (ym, content, now_str),
                    )
                    conn.commit()
                ok = "OK" if len(content) > 50 else "FAIL"
                print(f"[{label}] [{i+1}/{len(targets)}] {ym} {ok}", flush=True)
            except Exception as e:
                print(f"[{label}] [{i+1}/{len(targets)}] {ym} ERROR: {e}", flush=True)
            time.sleep(2)
        print(f"[{label}] 완료", flush=True)

    threading.Thread(target=_run, daemon=True).start()
    return jsonify({"status": "started", "force": force})


@app.route("/api/refresh", methods=["POST"])
def api_refresh():
    stats = reload_transactions()
    return jsonify(stats)


def scheduled_codef_fetch() -> None:
    print("[scheduler] CODEF 수집 시작", flush=True)
    try:
        run_card_fetch(days=1)
    except SystemExit as e:
        print(f"[scheduler] 카드 수집 SystemExit: {e}", flush=True)
    except Exception as e:
        print(f"[scheduler] 카드 수집 실패: {type(e).__name__}: {e}", flush=True)
    try:
        run_bank_fetch(days=1)
    except SystemExit as e:
        print(f"[scheduler] 은행 수집 SystemExit: {e}", flush=True)
    except Exception as e:
        print(f"[scheduler] 은행 수집 실패: {type(e).__name__}: {e}", flush=True)
    try:
        stats = reload_transactions()
        print(f"[scheduler] DB 재적재 완료: {stats}", flush=True)
    except Exception as e:
        print(f"[scheduler] DB 재적재 실패: {type(e).__name__}: {e}", flush=True)


BACKUP_ROOT = Path("/backups")
BACKUP_RETAIN_DAYS = 30


def scheduled_daily_backup() -> None:
    """수집 JSON + spending.db + connected_ids.json을 /backups/<YYYYMMDD>/로 복제.

    컨테이너에 /backups가 bind mount되어 있어야 호스트 디스크에 저장됨. 최근
    BACKUP_RETAIN_DAYS일만 보관. 파괴적 작업은 하지 않음 — 오래된 폴더만 삭제.
    """
    import shutil
    from datetime import date, timedelta

    if not BACKUP_ROOT.exists():
        print(f"[backup] {BACKUP_ROOT} 마운트 없음 — skip", flush=True)
        return

    stamp = date.today().strftime("%Y%m%d")
    dest = BACKUP_ROOT / stamp
    dest.mkdir(parents=True, exist_ok=True)

    copied = 0
    total_bytes = 0
    patterns = [
        APP_DIR.glob("transactions_*.json"),
        APP_DIR.glob("bank_transactions_*.json"),
        iter([APP_DIR / "spending.db"]),
        iter([APP_DIR / "connected_ids.json"]),
    ]
    for group in patterns:
        for src in group:
            if not src.exists():
                continue
            target = dest / src.name
            shutil.copy2(src, target)
            copied += 1
            total_bytes += target.stat().st_size
    print(f"[backup] {stamp}: {copied}개 / {total_bytes:,}B → {dest}", flush=True)

    cutoff = date.today() - timedelta(days=BACKUP_RETAIN_DAYS)
    for child in BACKUP_ROOT.iterdir():
        if not child.is_dir() or len(child.name) != 8 or not child.name.isdigit():
            continue
        try:
            folder_date = datetime.strptime(child.name, "%Y%m%d").date()
        except ValueError:
            continue
        if folder_date < cutoff:
            shutil.rmtree(child)
            print(f"[backup] 오래된 스냅샷 삭제: {child.name}", flush=True)


def scheduled_bank_backfill() -> None:
    from datetime import date, timedelta

    from easycodefpy import Codef

    from backfill import backfill_banks, make_chunks

    print("[scheduler] 은행 730일 백필 시작", flush=True)
    try:
        cid, csec, pub = load_codef_credentials()
        connected = load_connected_ids()
        codef = Codef()
        codef.public_key = pub
        codef.set_demo_client_info(cid, csec)
        end = date.today()
        start = end - timedelta(days=730)
        backfill_banks(codef, connected, make_chunks(start, end))
        stats = reload_transactions()
        print(f"[scheduler] 은행 백필 완료, DB 재적재: {stats}", flush=True)
    except Exception as e:
        print(f"[scheduler] 은행 백필 실패: {type(e).__name__}: {e}", flush=True)


def scheduled_update_current_analysis() -> None:
    """수집 1시간 후 — 현재 월 분석을 강제 갱신."""
    today = date.today()
    ym = f"{today.year:04d}-{today.month:02d}"
    print(f"[auto-analyze] 현재 월 {ym} 분석 갱신", flush=True)
    try:
        data = _prepare_month_data(ym)
        if data["total"] == 0:
            return
        content = _call_gemini(_build_prompt(data, is_current=True))
        now_str = datetime.now().isoformat()
        with _db() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO analyses (ym, content, generated_at) VALUES (?,?,?)",
                (ym, content, now_str),
            )
            conn.commit()
        print(f"[auto-analyze] {ym} 갱신 완료", flush=True)
    except Exception as e:
        print(f"[auto-analyze] {ym} 갱신 실패: {e}", flush=True)


def scheduled_auto_analyze() -> None:
    """매월 1일 02:00 — 지난달 분석 자동 생성."""
    last_month = date.today().replace(day=1) - timedelta(days=1)
    ym = f"{last_month.year:04d}-{last_month.month:02d}"
    with _db() as conn:
        exists = conn.execute("SELECT 1 FROM analyses WHERE ym=?", (ym,)).fetchone()
    if exists:
        print(f"[auto-analyze] {ym} 이미 분석됨", flush=True)
        return
    print(f"[auto-analyze] {ym} 분석 시작", flush=True)
    try:
        data = _prepare_month_data(ym)
        if data["total"] == 0:
            print(f"[auto-analyze] {ym} 데이터 없음", flush=True)
            return
        content = _call_gemini(_build_prompt(data, is_current=False))
        now_str = datetime.now().isoformat()
        with _db() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO analyses (ym, content, generated_at) VALUES (?,?,?)",
                (ym, content, now_str),
            )
            conn.commit()
        print(f"[auto-analyze] {ym} 완료", flush=True)
    except Exception as e:
        print(f"[auto-analyze] 실패: {e}", flush=True)


def start_scheduler() -> None:
    from datetime import datetime
    from zoneinfo import ZoneInfo

    kst = ZoneInfo("Asia/Seoul")
    scheduler = BackgroundScheduler(timezone=kst)

    # 1회성: 내일 01:00 KST 은행 730일 백필 (CODEF 일 100건 리셋 후)
    scheduler.add_job(
        scheduled_bank_backfill,
        DateTrigger(run_date=datetime(2026, 4, 16, 1, 0, tzinfo=kst)),
        id="bank_backfill_oneshot",
        replace_existing=True,
        misfire_grace_time=3600,
    )

    # 정기: 2026-04-16 16:00 KST부터 매 4시간 (16/20/00/04/08/12)
    scheduler.add_job(
        scheduled_codef_fetch,
        CronTrigger(
            hour="0,4,8,12,16,20",
            minute=0,
            start_date=datetime(2026, 4, 16, 16, 0, tzinfo=kst),
            timezone=kst,
        ),
        id="codef_fetch",
        replace_existing=True,
        misfire_grace_time=300,
        coalesce=True,
        max_instances=1,
    )

    # 수집(0,4,8,12,16,20시) 1시간 후 — 현재 월 분석 갱신
    scheduler.add_job(
        scheduled_update_current_analysis,
        CronTrigger(hour="1,5,9,13,17,21", minute=0, timezone=kst),
        id="update_current_analysis",
        replace_existing=True,
        misfire_grace_time=300,
        coalesce=True,
        max_instances=1,
    )

    # 매월 1일 02:00 KST — 지난달 AI 분석 자동 생성
    scheduler.add_job(
        scheduled_auto_analyze,
        CronTrigger(day=1, hour=2, minute=0, timezone=kst),
        id="auto_analyze",
        replace_existing=True,
        misfire_grace_time=3600,
        coalesce=True,
        max_instances=1,
    )

    # 매일 06:00 KST — 수집 JSON + spending.db 스냅샷 백업
    scheduler.add_job(
        scheduled_daily_backup,
        CronTrigger(hour=6, minute=0, timezone=kst),
        id="daily_backup",
        replace_existing=True,
        misfire_grace_time=3600,
        coalesce=True,
        max_instances=1,
    )

    scheduler.start()
    for job_id in ("bank_backfill_oneshot", "codef_fetch", "daily_backup", "auto_analyze", "update_current_analysis"):
        job = scheduler.get_job(job_id)
        if job:
            print(f"[scheduler] {job_id} 다음 실행: {job.next_run_time}", flush=True)


if __name__ == "__main__":
    ensure_analyses_table()
    reload_transactions()
    start_scheduler()
    port = int(os.getenv("PORT", "8060"))
    app.run(host="0.0.0.0", port=port, debug=False)
