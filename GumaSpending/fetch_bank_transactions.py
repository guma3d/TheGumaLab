"""
Phase 2b — Fetch bank withdrawal history from CODEF.

Non-interactive. connected_ids.json 에서 type=bank 엔트리를 찾아 각 계좌별로
transaction-list 를 호출하고 bank_transactions_{org}_{YYYYMMDD-YYYYMMDD}.json
에 저장한다.

Usage:
    python fetch_bank_transactions.py             # 최근 30일, 모든 은행
    python fetch_bank_transactions.py --days 92    # 92일 치
    python fetch_bank_transactions.py --org 0011   # 농협만
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
TRANSACTION_LIST_PATH = "/v1/kr/bank/p/account/transaction-list"
ACCOUNT_LIST_PATH = "/v1/kr/bank/p/account/account-list"


def load_credentials() -> tuple[str, str, str]:
    env_path = SCRIPT_DIR / ".env"
    if not env_path.exists():
        sys.exit(f"[ERROR] .env not found at {env_path}")
    load_dotenv(env_path)
    cid = os.getenv("CODEF_CLIENT_ID", "").strip()
    csec = os.getenv("CODEF_CLIENT_SECRET", "").strip()
    pub = os.getenv("CODEF_PUBLIC_KEY", "").strip()
    if not cid or not csec or not pub:
        sys.exit("[ERROR] CODEF credentials missing")
    return cid, csec, pub


def load_connected() -> dict:
    if not CONNECTED_IDS_PATH.exists():
        sys.exit("[ERROR] connected_ids.json not found")
    return json.loads(CONNECTED_IDS_PATH.read_text(encoding="utf-8"))


def fmt_date(d: date) -> str:
    return d.strftime("%Y%m%d")


def _call(codef: Codef, path: str, param: dict) -> dict | None:
    raw = codef.request_product(path, ServiceType.DEMO, param)
    try:
        return json.loads(raw)
    except (ValueError, TypeError):
        print(f"    [FAIL] non-JSON: {raw[:200]}")
        return None


def refresh_accounts(codef: Codef, org: str, connected_id: str) -> list[dict]:
    """connected_ids.json에 accounts가 없거나 비어있을 때 fallback."""
    res = _call(codef, ACCOUNT_LIST_PATH, {"organization": org, "connectedId": connected_id})
    if res is None:
        return []
    if res.get("result", {}).get("code") != "CF-00000":
        return []
    data = res.get("data") or {}
    accounts = data.get("resDepositTrust") or []
    if isinstance(accounts, dict):
        accounts = [accounts]
    return [
        {
            "account_no": a.get("resAccount", ""),
            "account_display": a.get("resAccountDisplay", ""),
            "account_name": a.get("resAccountName", ""),
            "nickname": a.get("resAccountNickName", ""),
        }
        for a in accounts
    ]


def fetch_one_bank(
    codef: Codef,
    org: str,
    bank_name: str,
    connected_id: str,
    accounts: list[dict],
    start: date,
    end: date,
) -> dict | None:
    print(f"\n[{bank_name}] 계좌 {len(accounts)}개 수집 {fmt_date(start)}~{fmt_date(end)}")

    all_tx: list[dict] = []
    per_account: list[dict] = []
    for acc in accounts:
        acc_no = acc.get("account_no", "")
        display = acc.get("account_display") or acc_no
        name = acc.get("account_name", "")
        nickname = acc.get("nickname", "")
        if not acc_no:
            continue
        masked = f"{acc_no[:4]}****{acc_no[-4:]}" if len(acc_no) >= 8 else acc_no
        print(f"\n  [{name} / {nickname}] {masked}")

        param = {
            "organization": org,
            "connectedId": connected_id,
            "account": acc_no,
            "startDate": fmt_date(start),
            "endDate": fmt_date(end),
            "orderBy": "1",
            "inquiryType": "1",  # 1=전체
        }
        res = _call(codef, TRANSACTION_LIST_PATH, param)
        if res is None:
            continue
        result = res.get("result", {})
        code = result.get("code")
        if code != "CF-00000":
            print(f"    [FAIL] {code} - {result.get('message')}")
            continue

        data = res.get("data") or {}
        tx_list = data.get("resTrHistoryList") or []
        if isinstance(tx_list, dict):
            tx_list = [tx_list]

        out_sum = 0
        in_sum = 0
        for tx in tx_list:
            try:
                out_sum += int(tx.get("resAccountOut", "0") or "0")
                in_sum += int(tx.get("resAccountIn", "0") or "0")
            except ValueError:
                pass
            tx["_account_no"] = acc_no
            tx["_account_display"] = display
            tx["_account_name"] = name
            tx["_account_nickname"] = nickname

        print(
            f"    [OK] {len(tx_list)}건 / 출금 {out_sum:,}원 / 입금 {in_sum:,}원"
        )
        for tx in tx_list[:3]:
            d = tx.get("resAccountTrDate", "")
            t = tx.get("resAccountTrTime", "")
            out_amt = tx.get("resAccountOut", "0")
            desc = tx.get("resAccountDesc3") or tx.get("resAccountDesc2") or ""
            print(f"      {d} {t}  출금={out_amt}  {desc[:30]}")
        if len(tx_list) > 3:
            print(f"      ... 외 {len(tx_list) - 3}건")

        all_tx.extend(tx_list)
        per_account.append(
            {
                "account_no_masked": masked,
                "account_name": name,
                "nickname": nickname,
                "total_count": len(tx_list),
                "withdraw_total": out_sum,
                "deposit_total": in_sum,
            }
        )

    if not all_tx:
        return None

    return {
        "organization": org,
        "bank_name": bank_name,
        "start_date": fmt_date(start),
        "end_date": fmt_date(end),
        "total_count": len(all_tx),
        "per_account": per_account,
        "transactions": all_tx,
    }


def run(days: int = 30, org_filter: str | None = None) -> int:
    if not 1 <= days <= 92:
        raise ValueError("days must be between 1 and 92")

    cid, csec, pub = load_credentials()
    connected = load_connected()

    codef = Codef()
    codef.public_key = pub
    codef.set_demo_client_info(cid, csec)

    end = date.today()
    start = end - timedelta(days=days)

    targets: list[tuple[str, str, str, list[dict]]] = []
    for org, entry in connected.items():
        if entry.get("type") != "bank":
            continue
        if org_filter and org != org_filter:
            continue
        name = entry.get("card_name", f"bank-{org}")
        conn_id = entry.get("connected_id", "")
        accounts = entry.get("accounts") or []
        if not accounts:
            print(f"[{name}] accounts 캐시 없음 — account-list 호출로 복구")
            accounts = refresh_accounts(codef, org, conn_id)
        targets.append((org, name, conn_id, accounts))

    if not targets:
        raise RuntimeError("no bank entries in connected_ids.json (run register_bank.py first)")

    print(f"기간 : {fmt_date(start)} ~ {fmt_date(end)} ({days}일)")
    print(f"대상 : {len(targets)}개 은행")

    results: dict[str, dict] = {}
    for org, name, conn_id, accounts in targets:
        r = fetch_one_bank(codef, org, name, conn_id, accounts, start, end)
        if r is None:
            continue
        out_path = (
            SCRIPT_DIR
            / f"bank_transactions_{org}_{fmt_date(start)}-{fmt_date(end)}.json"
        )
        out_path.write_text(json.dumps(r, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"      saved: {out_path.name}")
        results[org] = r

    print()
    print("=" * 50)
    print(f"  PHASE 2b - {len(results)}/{len(targets)} 은행 수집 완료")
    print("=" * 50)
    grand_out = sum(
        sum(p["withdraw_total"] for p in r["per_account"]) for r in results.values()
    )
    grand_cnt = sum(r["total_count"] for r in results.values())
    print(f"  합계: {grand_cnt}건 / 출금 {grand_out:,}원")
    return 0 if len(results) == len(targets) else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=30, help="lookback days (1-92)")
    ap.add_argument("--org", type=str, default=None, help="bank org filter")
    args = ap.parse_args()
    try:
        return run(days=args.days, org_filter=args.org)
    except (ValueError, RuntimeError) as e:
        sys.exit(f"[ERROR] {e}")


if __name__ == "__main__":
    raise SystemExit(main())
