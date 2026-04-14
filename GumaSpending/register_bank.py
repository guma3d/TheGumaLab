"""
Phase 2b — Register a bank account with CODEF and save it to connected_ids.json.

카드와 동일한 패턴:
  - 첫 은행: create_account 또는 기존 connectedId에 add_account
  - 이후: account-list 로 보유 계좌 목록 갱신
  - 결과를 connected_ids.json 에 {type: "bank", accounts: [...]} 로 저장

Usage (HomeServer, TTY 필요):
    cd /d D:\\TheGumaLab\\GumaSpending
    python register_bank.py
"""

from __future__ import annotations

import getpass
import json
import os
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from easycodefpy import Codef, ServiceType, encrypt_rsa

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")


BANK_ORGS: dict[str, str] = {
    "산업은행": "0002",
    "기업은행": "0003",
    "국민은행": "0004",
    "수협은행": "0007",
    "농협은행": "0011",
    "우리은행": "0020",
    "SC제일은행": "0023",
    "한국씨티은행": "0027",
    "대구은행": "0031",
    "부산은행": "0032",
    "광주은행": "0034",
    "제주은행": "0035",
    "전북은행": "0037",
    "경남은행": "0039",
    "새마을금고": "0045",
    "신협": "0048",
    "우체국": "0071",
    "하나은행": "0081",
    "신한은행": "0088",
    "케이뱅크": "0089",
    "카카오뱅크": "0090",
    "토스뱅크": "0092",
}

ACCOUNT_LIST_PATH = "/v1/kr/bank/p/account/account-list"

SCRIPT_DIR = Path(__file__).parent
CONNECTED_IDS_PATH = SCRIPT_DIR / "connected_ids.json"


def load_credentials() -> tuple[str, str, str]:
    env_path = SCRIPT_DIR / ".env"
    if not env_path.exists():
        sys.exit(f"[ERROR] .env not found at {env_path}")
    load_dotenv(env_path)
    cid = os.getenv("CODEF_CLIENT_ID", "").strip()
    csec = os.getenv("CODEF_CLIENT_SECRET", "").strip()
    pub = os.getenv("CODEF_PUBLIC_KEY", "").strip()
    if not cid or not csec or not pub:
        sys.exit("[ERROR] CODEF credentials missing from .env")
    return cid, csec, pub


def load_connected() -> dict:
    if CONNECTED_IDS_PATH.exists():
        return json.loads(CONNECTED_IDS_PATH.read_text(encoding="utf-8"))
    return {}


def save_connected(data: dict) -> None:
    CONNECTED_IDS_PATH.write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def pick_bank() -> tuple[str, str]:
    print("\n등록 가능한 은행:")
    for idx, (name, code) in enumerate(BANK_ORGS.items(), start=1):
        print(f"  {idx:2d}. {name}  ({code})")
    raw = input("\n등록할 은행 번호 또는 이름 (기본: 농협은행): ").strip() or "농협은행"
    if raw.isdigit():
        idx = int(raw) - 1
        items = list(BANK_ORGS.items())
        if not (0 <= idx < len(items)):
            sys.exit(f"[ERROR] invalid index: {raw}")
        return items[idx]
    if raw not in BANK_ORGS:
        sys.exit(f"[ERROR] unknown bank: {raw}")
    return raw, BANK_ORGS[raw]


def fetch_accounts(codef: Codef, org: str, connected_id: str) -> list[dict]:
    raw = codef.request_product(
        ACCOUNT_LIST_PATH,
        ServiceType.DEMO,
        {"organization": org, "connectedId": connected_id},
    )
    try:
        res = json.loads(raw)
    except (ValueError, TypeError):
        print(f"    [FAIL] account-list 응답이 JSON이 아님: {raw[:300]}")
        return []

    code = res.get("result", {}).get("code")
    if code != "CF-00000":
        print(
            f"    [FAIL] account-list {code} - {res.get('result', {}).get('message')}"
        )
        return []

    data = res.get("data") or {}
    accounts = data.get("resDepositTrust") or []
    if isinstance(accounts, dict):
        accounts = [accounts]
    return accounts


def main() -> int:
    client_id, client_secret, public_key = load_credentials()
    print(f"CLIENT_ID = {client_id[:6]}...{client_id[-4:]}")

    bank_name, org = pick_bank()
    print(f"선택: {bank_name} ({org})")

    codef = Codef()
    codef.public_key = public_key
    codef.set_demo_client_info(client_id, client_secret)

    existing = load_connected()
    primary_cid = next(
        (e["connected_id"] for e in existing.values() if e.get("connected_id")), None
    )
    bank_entry = existing.get(org)

    if bank_entry and bank_entry.get("connected_id"):
        print(f"\n[이미 등록됨] connectedId={bank_entry['connected_id'][:10]}...")
        print("계좌 목록만 갱신합니다 (add_account 재호출 없음).")
        connected_id = bank_entry["connected_id"]
    else:
        login_id = input(f"\n{bank_name} 로그인 아이디: ").strip()
        if not login_id:
            sys.exit("[ERROR] login id required")
        raw_pw = getpass.getpass(f"{bank_name} 로그인 비밀번호 (화면 미표시): ")
        if not raw_pw:
            sys.exit("[ERROR] password required")

        print("\n[1/3] RSA 암호화 ...")
        enc_pw = encrypt_rsa(raw_pw, public_key)
        del raw_pw

        account = {
            "countryCode": "KR",
            "businessType": "BK",
            "clientType": "P",
            "organization": org,
            "loginType": "1",
            "id": login_id,
            "password": enc_pw,
        }

        if primary_cid:
            print(f"[2/3] add_account (existing connectedId={primary_cid[:8]}...) ...")
            raw = codef.add_account(
                ServiceType.DEMO,
                {"connectedId": primary_cid, "accountList": [account]},
            )
        else:
            print("[2/3] create_account ...")
            raw = codef.create_account(
                ServiceType.DEMO, {"accountList": [account]}
            )

        try:
            res = json.loads(raw)
        except (ValueError, TypeError):
            sys.exit(f"[FAIL] response not JSON: {raw[:300]}")

        code = res.get("result", {}).get("code")
        if code != "CF-00000":
            print()
            print("=" * 60)
            print(f"  [FAIL] add/create_account: {code}")
            print(f"  message = {res.get('result', {}).get('message')}")
            print(f"  extra   = {res.get('result', {}).get('extraMessage')}")
            for e in (res.get("data") or {}).get("errorList", []) or []:
                print(f"  errorList = {e.get('code')} {e.get('message')}")
            print("=" * 60)
            return 1

        connected_id = (res.get("data") or {}).get("connectedId") or primary_cid
        print(f"      [OK] connectedId = {connected_id[:10]}...")

    print(f"\n[3/3] 보유 계좌 조회 ...")
    accounts = fetch_accounts(codef, org, connected_id)
    if not accounts:
        print("      [WARN] 계좌 0개")
    print(f"      [OK] 계좌 {len(accounts)}개:")
    accounts_out = []
    for a in accounts:
        acc_no = a.get("resAccount", "")
        display = a.get("resAccountDisplay", acc_no)
        name = a.get("resAccountName", "")
        nick = a.get("resAccountNickName", "")
        balance = a.get("resAccountBalance", "0")
        print(f"        - {name} ({nick})  {display}  잔액={balance}")
        accounts_out.append(
            {
                "account_no": acc_no,
                "account_display": display,
                "account_name": name,
                "nickname": nick,
            }
        )

    existing[org] = {
        "type": "bank",
        "card_name": bank_name,  # 호환성: 기존 card_name 필드 재사용
        "organization_code": org,
        "connected_id": connected_id,
        "accounts": accounts_out,
        "registered_at": datetime.now().isoformat(timespec="seconds"),
    }
    save_connected(existing)

    print()
    print("=" * 60)
    print(f"  [OK] {bank_name} 등록 완료 — connected_ids.json 저장")
    print(f"  connectedId = {connected_id[:12]}...{connected_id[-6:]}")
    print(f"  accounts    = {len(accounts_out)}")
    print("=" * 60)
    print("Next: python fetch_bank_transactions.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
