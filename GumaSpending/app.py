"""
GumaSpending — Flask calendar dashboard.

Loads transactions_*.json files produced by fetch_transactions.py into SQLite,
then serves a month-grid calendar UI and detail-per-day API.
"""

from __future__ import annotations

import glob
import json
import os
import sqlite3
from datetime import date, datetime
from pathlib import Path

from flask import Flask, jsonify, render_template, send_from_directory

APP_DIR = Path(__file__).resolve().parent
DB_PATH = APP_DIR / "spending.db"
TX_GLOB = str(APP_DIR / "transactions_*.json")

ORG_NAMES = {
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
}

app = Flask(__name__)
app.config["JSON_AS_ASCII"] = False


def _db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _db() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS transactions (
                org TEXT NOT NULL,
                card_name TEXT,
                sub_card_name TEXT,
                card_no_masked TEXT,
                used_date TEXT NOT NULL,
                used_time TEXT,
                store_name TEXT,
                store_category TEXT,
                amount INTEGER NOT NULL,
                cancel_yn TEXT,
                approval_no TEXT,
                PRIMARY KEY (org, approval_no, used_date, used_time)
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_used_date ON transactions(used_date)")
        conn.commit()


def _mask(card_no: str) -> str:
    if not card_no or len(card_no) < 8:
        return card_no or ""
    return f"{card_no[:4]}****{card_no[-4:]}"


def reload_transactions() -> dict:
    """Re-scan transactions_*.json files and upsert into SQLite."""
    init_db()
    inserted = 0
    skipped_cancel = 0
    files = sorted(glob.glob(TX_GLOB))

    with _db() as conn:
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

                used_date_raw = tx.get("resUsedDate", "")
                if len(used_date_raw) == 8:
                    used_date = f"{used_date_raw[:4]}-{used_date_raw[4:6]}-{used_date_raw[6:8]}"
                else:
                    used_date = used_date_raw

                row = (
                    org,
                    card_name,
                    tx.get("resCardName", ""),
                    _mask(tx.get("resCardNo", "")),
                    used_date,
                    tx.get("resUsedTime", ""),
                    tx.get("resMemberStoreName", ""),
                    tx.get("resMemberStoreBusinessType", ""),
                    amount,
                    tx.get("resCancelYN", "N"),
                    tx.get("resApprovalNo", ""),
                )
                try:
                    conn.execute(
                        """
                        INSERT OR REPLACE INTO transactions
                        (org, card_name, sub_card_name, card_no_masked,
                         used_date, used_time, store_name, store_category,
                         amount, cancel_yn, approval_no)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        row,
                    )
                    inserted += 1
                except sqlite3.Error as e:
                    print(f"[WARN] insert failed: {e}")
        conn.commit()

    return {
        "files": len(files),
        "inserted_or_updated": inserted,
        "skipped_cancel": skipped_cancel,
    }


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
            SELECT org, card_name, SUM(amount) AS total, COUNT(*) AS cnt
            FROM transactions
            WHERE used_date >= ? AND used_date < ?
            GROUP BY org, card_name
            ORDER BY total DESC
            """,
            (start, end),
        ).fetchall()

    days = {r["used_date"]: {"total": r["total"], "count": r["cnt"]} for r in rows}
    return jsonify(
        {
            "ym": ym,
            "month_total": month_total_row["total"],
            "month_count": month_total_row["cnt"],
            "days": days,
            "by_card": [dict(r) for r in by_card_rows],
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
            SELECT org, card_name, sub_card_name, card_no_masked, used_time,
                   store_name, store_category, amount
            FROM transactions
            WHERE used_date = ?
            ORDER BY used_time DESC
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


if __name__ == "__main__":
    reload_transactions()
    port = int(os.getenv("PORT", "8060"))
    app.run(host="0.0.0.0", port=port, debug=False)
