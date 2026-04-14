"""
Phase 2b — DEMO 모드 은행 경로 검증 스크립트.

카드(CD)는 DEMO에서 실계정 수용, 증권(ST)은 거부였음.
은행(BK)이 어느 쪽인지 확인하기 위해 농협은행(0011)으로 1회 테스트.

흐름:
  1. 기존 connectedId 로드 (카드와 같은 ID에 add_account)
     없으면 create_account로 새로 발급
  2. /v1/kr/bank/p/account/account-list 로 보유 계좌 조회
  3. 첫 계좌로 /v1/kr/bank/p/account/transaction-list 최근 30일 호출
  4. 결과 출력 (DEMO가 실데이터를 내주는지 확인)

성공 시: register_bank.py + fetch_bank_transactions.py 로 정식 통합 진행
실패 시: 에러 코드·메시지를 CLAUDE.md에 기록하고 전략 재검토

Usage (HomeServer에서 TTY 필요):
    cd /d D:\\TheGumaLab\\GumaSpending
    python test_bank.py
"""

from __future__ import annotations

import getpass
import json
import sys
from datetime import date, timedelta
from pathlib import Path

from dotenv import load_dotenv
from easycodefpy import Codef, ServiceType, encrypt_rsa

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")


SCRIPT_DIR = Path(__file__).parent
CONNECTED_IDS_PATH = SCRIPT_DIR / "connected_ids.json"
BANK_ORG = "0011"  # 농협은행
BANK_NAME = "농협은행"

ACCOUNT_LIST_PATH = "/v1/kr/bank/p/account/account-list"
TRANSACTION_LIST_PATH = "/v1/kr/bank/p/account/transaction-list"


def load_credentials() -> tuple[str, str, str]:
    env_path = SCRIPT_DIR / ".env"
    if not env_path.exists():
        sys.exit(f"[ERROR] .env not found at {env_path}")
    load_dotenv(env_path)

    import os
    cid = os.getenv("CODEF_CLIENT_ID", "").strip()
    csec = os.getenv("CODEF_CLIENT_SECRET", "").strip()
    pub = os.getenv("CODEF_PUBLIC_KEY", "").strip()
    if not cid or not csec or not pub:
        sys.exit("[ERROR] CODEF credentials missing from .env")
    return cid, csec, pub


def load_existing_connected_id() -> str | None:
    if not CONNECTED_IDS_PATH.exists():
        return None
    data = json.loads(CONNECTED_IDS_PATH.read_text(encoding="utf-8"))
    for entry in data.values():
        if entry.get("connected_id"):
            return entry["connected_id"]
    return None


def dump_result_block(label: str, raw: str) -> dict | None:
    print(f"\n[{label}] raw response (first 800 chars):")
    print(raw[:800])
    try:
        return json.loads(raw)
    except (ValueError, TypeError):
        print(f"[FAIL] {label} 응답이 JSON이 아님")
        return None


def main() -> int:
    client_id, client_secret, public_key = load_credentials()
    print(f"CLIENT_ID = {client_id[:6]}...{client_id[-4:]}")
    print(f"PUB_KEY   = {public_key[:10]}...{public_key[-6:]}  len={len(public_key)}")

    login_id = input(f"\n{BANK_NAME} 로그인 아이디: ").strip()
    if not login_id:
        sys.exit("[ERROR] login id is required")
    raw_pw = getpass.getpass(f"{BANK_NAME} 로그인 비밀번호 (화면에 표시되지 않음): ")
    if not raw_pw:
        sys.exit("[ERROR] password required")

    print("\n[1/4] RSA 암호화 ...")
    enc_pw = encrypt_rsa(raw_pw, public_key)
    del raw_pw
    print(f"      encrypted len = {len(enc_pw)}")

    codef = Codef()
    codef.public_key = public_key
    codef.set_demo_client_info(client_id, client_secret)

    existing_cid = load_existing_connected_id()
    account = {
        "countryCode": "KR",
        "businessType": "BK",
        "clientType": "P",
        "organization": BANK_ORG,
        "loginType": "1",
        "id": login_id,
        "password": enc_pw,
    }

    if existing_cid:
        print(f"\n[2/4] add_account (existing connectedId={existing_cid[:8]}...) ...")
        raw = codef.add_account(
            ServiceType.DEMO,
            {"connectedId": existing_cid, "accountList": [account]},
        )
    else:
        print("\n[2/4] create_account (no existing connectedId) ...")
        raw = codef.create_account(ServiceType.DEMO, {"accountList": [account]})

    res = dump_result_block("add/create_account", raw)
    if res is None:
        return 1

    result = res.get("result", {})
    code = result.get("code")
    if code != "CF-00000":
        print()
        print("=" * 60)
        print(f"  [FAIL] 계정 등록 거부: {code}")
        print(f"  message      = {result.get('message')}")
        print(f"  extraMessage = {result.get('extraMessage')}")
        errors = (res.get("data") or {}).get("errorList") or []
        for e in errors:
            print(f"  errorList    = {e.get('code')} {e.get('message')}")
        print("=" * 60)
        print("  → 증권처럼 DEMO에서 은행 실계정 거부되는 케이스일 수 있음.")
        print("  → CLAUDE.md 에러 코드 섹션에 결과 기록 후 전략 재검토.")
        return 1

    connected_id = (res.get("data") or {}).get("connectedId") or existing_cid
    if not connected_id:
        print("[FAIL] connectedId 누락")
        return 1
    print(f"      [OK] connectedId = {connected_id[:12]}...{connected_id[-6:]}")

    print(f"\n[3/4] 보유 계좌 조회 ({ACCOUNT_LIST_PATH}) ...")
    raw_list = codef.request_product(
        ACCOUNT_LIST_PATH,
        ServiceType.DEMO,
        {"organization": BANK_ORG, "connectedId": connected_id},
    )
    list_res = dump_result_block("account-list", raw_list)
    if list_res is None:
        return 1

    list_code = list_res.get("result", {}).get("code")
    if list_code != "CF-00000":
        print(f"      [FAIL] account-list 실패: {list_code}")
        return 1

    data = list_res.get("data") or {}
    accounts = data.get("resDepositTrust") or data.get("resLoan") or []
    if isinstance(accounts, dict):
        accounts = [accounts]
    print(f"      [OK] 보유 계좌 {len(accounts)}개")
    for i, acc in enumerate(accounts[:5]):
        masked = acc.get("resAccount", "")
        if len(masked) >= 8:
            masked = f"{masked[:4]}****{masked[-4:]}"
        print(
            f"        {i+1}. {acc.get('resAccountName', '(이름 없음)')}  "
            f"{masked}  잔액={acc.get('resAccountBalance', '?')}"
        )

    if not accounts:
        print("\n      [WARN] 조회된 계좌 없음 — 종료")
        return 0

    first = accounts[0]
    account_no = first.get("resAccount", "")
    print(
        f"\n[4/4] 거래내역 조회 ({TRANSACTION_LIST_PATH}) — 첫 계좌 "
        f"{account_no[:4]}****{account_no[-4:]} 최근 30일 ..."
    )
    end = date.today()
    start = end - timedelta(days=30)
    param = {
        "organization": BANK_ORG,
        "connectedId": connected_id,
        "account": account_no,
        "startDate": start.strftime("%Y%m%d"),
        "endDate": end.strftime("%Y%m%d"),
        "orderBy": "1",  # 최신순
        "inquiryType": "1",  # 1=전체
    }
    raw_tx = codef.request_product(TRANSACTION_LIST_PATH, ServiceType.DEMO, param)
    tx_res = dump_result_block("transaction-list", raw_tx)
    if tx_res is None:
        return 1

    tx_code = tx_res.get("result", {}).get("code")
    if tx_code != "CF-00000":
        print(f"      [FAIL] transaction-list 실패: {tx_code}")
        return 1

    tx_data = tx_res.get("data") or {}
    tx_list = tx_data.get("resTrHistoryList") or []
    if isinstance(tx_list, dict):
        tx_list = [tx_list]
    print(f"      [OK] 거래 {len(tx_list)}건")

    out_withdraw = 0
    out_deposit = 0
    for tx in tx_list[:15]:
        d = tx.get("resAccountTrDate", "")
        t = tx.get("resAccountTrTime", "")
        out_amt = tx.get("resAccountOut", "0") or "0"
        in_amt = tx.get("resAccountIn", "0") or "0"
        desc = tx.get("resAccountDesc1") or tx.get("resAccountDesc3") or ""
        try:
            out_withdraw += int(out_amt)
            out_deposit += int(in_amt)
        except ValueError:
            pass
        print(
            f"        {d} {t}  출금={out_amt:>10}  입금={in_amt:>10}  {desc[:30]}"
        )
    if len(tx_list) > 15:
        print(f"        ... 외 {len(tx_list) - 15}건")

    print()
    print("=" * 60)
    print("  ✅ PHASE 2b — 은행 DEMO 경로 검증 성공")
    print(f"  최근 30일 출금 합계 = {out_withdraw:,}원")
    print(f"  최근 30일 입금 합계 = {out_deposit:,}원")
    print("=" * 60)
    print("  → register_bank.py + fetch_bank_transactions.py 로 정식 통합 진행 가능")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
