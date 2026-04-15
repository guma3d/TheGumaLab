"""
GumaSpending — Flask calendar dashboard.

Loads transactions_*.json (card) and bank_transactions_*.json (bank) into
SQLite, then serves a month-grid calendar UI and detail-per-day API.

Bank withdrawals with descriptions matching BANK_DEDUP_PATTERNS (e.g., 카드대금)
are skipped at ingestion time to avoid double-counting with card approval data.
"""

from __future__ import annotations

import glob
import json
import os
import re
import sqlite3
import unicodedata
from datetime import date, datetime
from pathlib import Path

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from flask import Flask, jsonify, render_template, send_from_directory

from fetch_bank_transactions import run as run_bank_fetch
from fetch_transactions import run as run_card_fetch

APP_DIR = Path(__file__).resolve().parent
DB_PATH = APP_DIR / "spending.db"
CARD_TX_GLOB = str(APP_DIR / "transactions_*.json")
BANK_TX_GLOB = str(APP_DIR / "bank_transactions_*.json")

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

BANK_DEDUP_PATTERNS = [
    "카드대금",
    "카드결제",
    "카드출금",
    "카드자동",
    "신용카드",
    "체크카드",
]
_DEDUP_RE = re.compile("|".join(BANK_DEDUP_PATTERNS))

# store_category 접미사가 "체크"/"신용"이면 카드 approval과 중복.
# 예) "NH체크", "NH신용", "KB체크" — 은행 쪽 기록은 skip.
_CARD_CATEGORY_RE = re.compile(r"(체크|신용)$")

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
            if tx.get("resCancelYN") == "Y":
                skipped_cancel += 1
                continue
            try:
                amount = int(tx.get("resUsedAmount", "0") or "0")
            except ValueError:
                amount = 0
            if amount <= 0:
                continue

            used_date = _parse_yyyymmdd(tx.get("resUsedDate", ""))
            used_time = tx.get("resUsedTime", "")
            approval_no = tx.get("resApprovalNo", "")
            card_no = tx.get("resCardNo", "")
            dedup = f"{approval_no}|{used_date}|{used_time}|{card_no[-4:]}"

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
                        tx.get("resCardName", ""),
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


@app.route("/")
def home():
    return render_template("index.html")


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
            """
            SELECT used_date, SUM(amount) AS total, COUNT(*) AS cnt
            FROM transactions
            WHERE used_date >= ? AND used_date < ?
            GROUP BY used_date
            ORDER BY used_date
            """,
            (start, end),
        ).fetchall()

        month_total_row = conn.execute(
            """
            SELECT COALESCE(SUM(amount), 0) AS total, COUNT(*) AS cnt
            FROM transactions
            WHERE used_date >= ? AND used_date < ?
            """,
            (start, end),
        ).fetchone()

        by_card_rows = conn.execute(
            """
            SELECT source, org, card_name, SUM(amount) AS total, COUNT(*) AS cnt
            FROM transactions
            WHERE used_date >= ? AND used_date < ?
            GROUP BY source, org, card_name
            ORDER BY total DESC
            """,
            (start, end),
        ).fetchall()

        by_source_row = conn.execute(
            """
            SELECT source, COALESCE(SUM(amount), 0) AS total, COUNT(*) AS cnt
            FROM transactions
            WHERE used_date >= ? AND used_date < ?
            GROUP BY source
            """,
            (start, end),
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
            """
            SELECT source, org, card_name, sub_card_name, card_no_masked, used_time,
                   store_name, store_category, amount
            FROM transactions
            WHERE used_date = ?
            ORDER BY amount DESC, used_time DESC
            """,
            (ymd,),
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
            """
            SELECT DISTINCT SUBSTR(used_date, 1, 7) AS ym
            FROM transactions
            ORDER BY ym DESC
            """
        ).fetchall()
        grand = conn.execute(
            "SELECT COALESCE(SUM(amount), 0) AS total, COUNT(*) AS cnt FROM transactions"
        ).fetchone()

    return jsonify(
        {
            "grand_total": grand["total"],
            "grand_count": grand["cnt"],
            "months": [r["ym"] for r in months_row],
        }
    )


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


def start_scheduler() -> None:
    scheduler = BackgroundScheduler(timezone="Asia/Seoul")
    scheduler.add_job(
        scheduled_codef_fetch,
        CronTrigger(hour="1,5,9,13,17,21", minute=30, timezone="Asia/Seoul"),
        id="codef_fetch",
        replace_existing=True,
        misfire_grace_time=300,
        coalesce=True,
        max_instances=1,
    )
    scheduler.start()
    job = scheduler.get_job("codef_fetch")
    if job:
        print(f"[scheduler] 다음 실행: {job.next_run_time}", flush=True)


if __name__ == "__main__":
    reload_transactions()
    start_scheduler()
    port = int(os.getenv("PORT", "8060"))
    app.run(host="0.0.0.0", port=port, debug=False)
