"""
One-shot backfill — 과거 데이터를 청킹으로 수집.

CODEF 단일 호출 한계(92일)를 넘어서는 기간을 92일 청크로 나눠 반복 호출.
기존 fetch_transactions.run() / fetch_bank_transactions.run()의 30일 정기
수집은 건드리지 않고, 최초 1회 장기 백필 전용으로 사용.

각 청크는 transactions_{org}_{YYYYMMDD-YYYYMMDD}.json / bank_transactions_*
형식으로 저장되며, spending.db의 dedup_key upsert가 중복을 흡수한다.

Usage:
    python backfill.py --days 365
    python backfill.py --days 180 --skip-bank
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, timedelta

from easycodefpy import Codef

from fetch_bank_transactions import fetch_one_bank, refresh_accounts
from fetch_transactions import (
    SCRIPT_DIR,
    fetch_one as fetch_one_card,
    fmt_date,
    load_connected_ids,
    load_credentials,
)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

CHUNK_DAYS = 92


def make_chunks(start: date, end: date) -> list[tuple[date, date]]:
    chunks: list[tuple[date, date]] = []
    cursor = start
    while cursor <= end:
        chunk_end = min(cursor + timedelta(days=CHUNK_DAYS - 1), end)
        chunks.append((cursor, chunk_end))
        cursor = chunk_end + timedelta(days=1)
    return chunks


def backfill_cards(codef: Codef, connected: dict, chunks: list[tuple[date, date]]) -> None:
    for org, entry in connected.items():
        if entry.get("type") == "bank":
            continue
        name = entry["card_name"]
        conn_id = entry["connected_id"]
        for i, (s, e) in enumerate(chunks, 1):
            print(f"\n=== [{name}] 청크 {i}/{len(chunks)}: {fmt_date(s)}~{fmt_date(e)} ===")
            r = fetch_one_card(codef, org, name, conn_id, s, e)
            if r is None:
                continue
            out_path = SCRIPT_DIR / f"transactions_{org}_{fmt_date(s)}-{fmt_date(e)}.json"
            out_path.write_text(json.dumps(r, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"      saved: {out_path.name}")


def backfill_banks(codef: Codef, connected: dict, chunks: list[tuple[date, date]]) -> None:
    for org, entry in connected.items():
        if entry.get("type") != "bank":
            continue
        name = entry.get("card_name", f"bank-{org}")
        conn_id = entry.get("connected_id", "")
        accounts = entry.get("accounts") or []
        if not accounts:
            print(f"\n[{name}] accounts 캐시 없음 — account-list 호출")
            accounts = refresh_accounts(codef, org, conn_id)
        for i, (s, e) in enumerate(chunks, 1):
            print(f"\n=== [{name}] 청크 {i}/{len(chunks)}: {fmt_date(s)}~{fmt_date(e)} ===")
            r = fetch_one_bank(codef, org, name, conn_id, accounts, s, e)
            if r is None:
                continue
            out_path = SCRIPT_DIR / f"bank_transactions_{org}_{fmt_date(s)}-{fmt_date(e)}.json"
            out_path.write_text(json.dumps(r, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"      saved: {out_path.name}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, required=True, help="backfill lookback days (1-730)")
    ap.add_argument("--skip-cards", action="store_true")
    ap.add_argument("--skip-bank", action="store_true")
    args = ap.parse_args()

    if not 1 <= args.days <= 730:
        sys.exit("[ERROR] days must be between 1 and 730")

    cid, csec, pub = load_credentials()
    connected = load_connected_ids()

    codef = Codef()
    codef.public_key = pub
    codef.set_demo_client_info(cid, csec)

    end = date.today()
    start = end - timedelta(days=args.days)
    chunks = make_chunks(start, end)

    print(f"백필 기간: {fmt_date(start)} ~ {fmt_date(end)} ({args.days}일)")
    print(f"청크 수  : {len(chunks)}개 (청크당 최대 {CHUNK_DAYS}일)")

    if not args.skip_cards:
        print("\n" + "=" * 50 + "\n  CARDS\n" + "=" * 50)
        backfill_cards(codef, connected, chunks)

    if not args.skip_bank:
        print("\n" + "=" * 50 + "\n  BANKS\n" + "=" * 50)
        backfill_banks(codef, connected, chunks)

    print("\n완료. /api/refresh 로 DB 재적재 필요.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
