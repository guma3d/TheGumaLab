"""
Phase 1c — Fetch card approval history (승인내역) from CODEF.

Non-interactive: reads connected_ids.json, calls approval-list API for the given
date range per registered organization, saves result to
transactions_{org}_{YYYYMMDD-YYYYMMDD}.json.

Usage (on HomeServer):
    cd /d D:\\TheGumaLab\\GumaSpending
    python fetch_transactions.py                # 기본: 최근 30일, 등록된 모든 카드사
    python fetch_transactions.py --days 92       # NH/KB 단일 호출 최대치
    python fetch_transactions.py --org 0304      # NH카드만
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import date, timedelta
from pathlib import Path

from dotenv import load_dotenv
from easycodefpy import Codef, ServiceType

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")


SCRIPT_DIR = Path(__file__).parent
CONNECTED_IDS_PATH = SCRIPT_DIR / "connected_ids.json"
APPROVAL_LIST_PATH = "/v1/kr/card/p/account/approval-list"


def load_credentials() -> tuple[str, str, str]:
    env_path = SCRIPT_DIR / ".env"
    if not env_path.exists():
        sys.exit(f"[ERROR] .env not found at {env_path}")
    load_dotenv(env_path)
    client_id = os.getenv("CODEF_CLIENT_ID", "").strip()
    client_secret = os.getenv("CODEF_CLIENT_SECRET", "").strip()
    public_key = os.getenv("CODEF_PUBLIC_KEY", "").strip()
    if not client_id or not client_secret or not public_key:
        sys.exit("[ERROR] CODEF credentials missing from .env")
    return client_id, client_secret, public_key


def load_connected_ids() -> dict:
    if not CONNECTED_IDS_PATH.exists():
        sys.exit(
            f"[ERROR] {CONNECTED_IDS_PATH} not found — run register_card.py first"
        )
    return json.loads(CONNECTED_IDS_PATH.read_text(encoding="utf-8"))


def fmt_date(d: date) -> str:
    return d.strftime("%Y%m%d")


def fetch_one(
    codef: Codef,
    org: str,
    card_name: str,
    connected_id: str,
    start: date,
    end: date,
) -> dict | None:
    param = {
        "organization": org,
        "connectedId": connected_id,
        "startDate": fmt_date(start),
        "endDate": fmt_date(end),
        "orderBy": "1",              # 최신순
        "memberStoreInfoType": "1",  # 사업자번호/업종/주소 포함
        "inquiryType": "0",
    }
    print(f"\n[{card_name}] approval-list {fmt_date(start)} ~ {fmt_date(end)}")
    raw = codef.request_product(APPROVAL_LIST_PATH, ServiceType.DEMO, param)
    try:
        res = json.loads(raw)
    except (ValueError, TypeError):
        print(f"  [FAIL] non-JSON response: {raw[:300]}")
        return None

    result = res.get("result", {})
    code = result.get("code")
    if code != "CF-00000":
        print(f"  [FAIL] {code} - {result.get('message')}")
        print(f"         extraMessage = {result.get('extraMessage')}")
        return None

    data = res.get("data") or []
    if isinstance(data, dict):
        data = [data]

    total_amt = 0
    active_count = 0
    for tx in data:
        if tx.get("resCancelYN") == "Y":
            continue
        try:
            total_amt += int(tx.get("resUsedAmount", "0") or "0")
            active_count += 1
        except ValueError:
            pass

    print(
        f"  [OK] 전체 {len(data)}건 / 유효(취소 제외) {active_count}건 / "
        f"합계 {total_amt:,}원"
    )

    preview = data[:3]
    for tx in preview:
        when = f"{tx.get('resUsedDate', '')} {tx.get('resUsedTime', '')}"
        store = tx.get("resMemberStoreName", "")
        amt = tx.get("resUsedAmount", "0")
        cancel = " (취소)" if tx.get("resCancelYN") == "Y" else ""
        print(f"      {when}  {store}  {amt}원{cancel}")
    if len(data) > 3:
        print(f"      ... 외 {len(data) - 3}건")

    return {
        "organization": org,
        "card_name": card_name,
        "start_date": fmt_date(start),
        "end_date": fmt_date(end),
        "total_count": len(data),
        "active_count": active_count,
        "active_total_amount": total_amt,
        "transactions": data,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--days", type=int, default=30, help="lookback days (default 30, max 92)"
    )
    ap.add_argument(
        "--org", type=str, default=None, help="organization code filter (e.g. 0304)"
    )
    args = ap.parse_args()

    if not 1 <= args.days <= 92:
        sys.exit("[ERROR] --days must be between 1 and 92 (single-chunk limit)")

    client_id, client_secret, public_key = load_credentials()
    connected = load_connected_ids()

    codef = Codef()
    codef.public_key = public_key
    codef.set_demo_client_info(client_id, client_secret)

    end_date = date.today()
    start_date = end_date - timedelta(days=args.days)

    targets = []
    for org, entry in connected.items():
        if args.org and org != args.org:
            continue
        targets.append((org, entry["card_name"], entry["connected_id"]))

    if not targets:
        sys.exit("[ERROR] no matching organizations in connected_ids.json")

    print(f"조회 기간 : {fmt_date(start_date)} ~ {fmt_date(end_date)} ({args.days}일)")
    print(f"대상 카드사: {len(targets)}개")

    results: dict[str, dict] = {}
    for org, card_name, connected_id in targets:
        r = fetch_one(codef, org, card_name, connected_id, start_date, end_date)
        if r is None:
            continue
        out_path = (
            SCRIPT_DIR
            / f"transactions_{org}_{fmt_date(start_date)}-{fmt_date(end_date)}.json"
        )
        out_path.write_text(
            json.dumps(r, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"      saved: {out_path.name}")
        results[org] = r

    print()
    print("=" * 50)
    print(
        f"  PHASE 1c - {len(results)}/{len(targets)} 카드사 승인내역 조회 완료"
    )
    print("=" * 50)
    grand_total = sum(r["active_total_amount"] for r in results.values())
    grand_count = sum(r["active_count"] for r in results.values())
    print(f"  합계: {grand_count}건 / {grand_total:,}원")
    return 0 if len(results) == len(targets) else 1


if __name__ == "__main__":
    raise SystemExit(main())
