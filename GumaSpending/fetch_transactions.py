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
CARD_LIST_PATH = "/v1/kr/card/p/account/card-list"

# 카드 자체 구조 문제로 approval-list가 실패하는 정상 케이스.
# 치명적 에러가 아닌 경고로 분류하고 다음 카드로 넘어간다.
SKIPPABLE_CODES = {
    "CF-13101",  # 카드번호 List 불일치 — 모바일 Pay/가상카드 등
    "CF-13100",  # 카드번호 미입력 — 기본적으로 우리가 넣지만 일부 카드에서 발생 가능
}


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


def _call(codef: Codef, path: str, param: dict) -> dict | None:
    raw = codef.request_product(path, ServiceType.DEMO, param)
    try:
        return json.loads(raw)
    except (ValueError, TypeError):
        print(f"  [FAIL] non-JSON response from {path}: {raw[:300]}")
        return None


def fetch_card_list(codef: Codef, org: str, connected_id: str) -> list[dict]:
    res = _call(codef, CARD_LIST_PATH, {"organization": org, "connectedId": connected_id})
    if res is None:
        return []
    result = res.get("result", {})
    if result.get("code") != "CF-00000":
        print(
            f"  [FAIL] card-list {result.get('code')} - {result.get('message')}"
        )
        print(f"         extraMessage = {result.get('extraMessage')}")
        return []
    data = res.get("data") or []
    if isinstance(data, dict):
        data = [data]
    return data


def fetch_one(
    codef: Codef,
    org: str,
    card_name: str,
    connected_id: str,
    start: date,
    end: date,
) -> dict | None:
    print(f"\n[{card_name}] card-list 조회 ...")
    cards = fetch_card_list(codef, org, connected_id)
    if not cards:
        print("  [FAIL] 보유카드 없음 — 승인내역 조회 불가")
        return None
    print(f"  [OK] 카드 {len(cards)}개 확인")

    all_tx: list[dict] = []
    per_card_summary: list[dict] = []
    for card in cards:
        card_no = card.get("resCardNo", "")
        sub_name = card.get("resCardName", "(이름 없음)")
        masked = f"{card_no[:4]}****{card_no[-4:]}" if len(card_no) >= 8 else card_no
        print(
            f"\n  [{sub_name} {masked}] approval-list "
            f"{fmt_date(start)} ~ {fmt_date(end)}"
        )
        param = {
            "organization": org,
            "connectedId": connected_id,
            "cardNo": card_no,
            "startDate": fmt_date(start),
            "endDate": fmt_date(end),
            "orderBy": "1",              # 최신순
            "memberStoreInfoType": "1",  # 사업자번호/업종/주소 포함
            "inquiryType": "0",
        }
        res = _call(codef, APPROVAL_LIST_PATH, param)
        if res is None:
            continue
        result = res.get("result", {})
        code = result.get("code")
        if code != "CF-00000":
            tag = "SKIP" if code in SKIPPABLE_CODES else "FAIL"
            print(f"    [{tag}] {code} - {result.get('message')}")
            if result.get("extraMessage"):
                print(f"           extraMessage = {result.get('extraMessage')}")
            continue

        data = res.get("data") or []
        if isinstance(data, dict):
            data = [data]

        # card-list의 카드명을 각 거래에 주입 (approval-list는 빈 문자열 반환하는 경우 있음)
        for tx in data:
            if not (tx.get("resCardName") or "").strip():
                tx["resCardName"] = sub_name

        sub_total = 0
        sub_active = 0
        for tx in data:
            if tx.get("resCancelYN") == "Y":
                continue
            try:
                sub_total += int(tx.get("resUsedAmount", "0") or "0")
                sub_active += 1
            except ValueError:
                pass

        print(
            f"    [OK] 전체 {len(data)}건 / 유효 {sub_active}건 / "
            f"합계 {sub_total:,}원"
        )
        for tx in data[:3]:
            when = f"{tx.get('resUsedDate', '')} {tx.get('resUsedTime', '')}"
            store = tx.get("resMemberStoreName", "")
            amt = tx.get("resUsedAmount", "0")
            cancel = " (취소)" if tx.get("resCancelYN") == "Y" else ""
            print(f"        {when}  {store}  {amt}원{cancel}")
        if len(data) > 3:
            print(f"        ... 외 {len(data) - 3}건")

        all_tx.extend(data)
        per_card_summary.append(
            {
                "card_no_masked": masked,
                "sub_card_name": sub_name,
                "total_count": len(data),
                "active_count": sub_active,
                "active_total_amount": sub_total,
            }
        )

    active_total = sum(s["active_total_amount"] for s in per_card_summary)
    active_count = sum(s["active_count"] for s in per_card_summary)

    return {
        "organization": org,
        "card_name": card_name,
        "start_date": fmt_date(start),
        "end_date": fmt_date(end),
        "total_count": len(all_tx),
        "active_count": active_count,
        "active_total_amount": active_total,
        "per_card": per_card_summary,
        "transactions": all_tx,
    }


def run(days: int = 30, org_filter: str | None = None) -> int:
    if not 1 <= days <= 92:
        raise ValueError("days must be between 1 and 92 (single-chunk limit)")

    client_id, client_secret, public_key = load_credentials()
    connected = load_connected_ids()

    codef = Codef()
    codef.public_key = public_key
    codef.set_demo_client_info(client_id, client_secret)

    end_date = date.today()
    start_date = end_date - timedelta(days=days)

    targets = []
    for org, entry in connected.items():
        if entry.get("type") == "bank":
            continue
        if org_filter and org != org_filter:
            continue
        targets.append((org, entry["card_name"], entry["connected_id"]))

    if not targets:
        raise RuntimeError("no matching card organizations in connected_ids.json")

    print(f"조회 기간 : {fmt_date(start_date)} ~ {fmt_date(end_date)} ({days}일)")
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


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--days", type=int, default=30, help="lookback days (default 30, max 92)"
    )
    ap.add_argument(
        "--org", type=str, default=None, help="organization code filter (e.g. 0304)"
    )
    args = ap.parse_args()
    try:
        return run(days=args.days, org_filter=args.org)
    except (ValueError, RuntimeError) as e:
        sys.exit(f"[ERROR] {e}")


if __name__ == "__main__":
    raise SystemExit(main())
