"""
Phase 1b — Register a card company account with CODEF and obtain a connectedId.

This script is interactive: you'll be prompted for the card company login ID
and password at runtime. Credentials are NOT stored anywhere; only the
returned connectedId is persisted to connected_ids.json.

Usage (on HomeServer, requires a TTY for password input):
    cd /d D:\\TheGumaLab\\GumaSpending
    pip install -r requirements.txt
    python register_card.py

The script defaults to NH카드 (0304) but you can pick any card company at the
prompt. Re-running for a card that already has a connectedId will use
add_account instead of create_account so all cards stay under one connectedId.
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


CARD_ORGS: dict[str, str] = {
    "KB카드": "0301",
    "현대카드": "0302",
    "삼성카드": "0303",
    "NH카드": "0304",
    "BC카드": "0305",
    "신한카드": "0306",
    "씨티카드": "0307",
    "우리카드": "0309",
    "롯데카드": "0311",
    "하나카드": "0313",
    "전북카드": "0315",
    "광주카드": "0316",
    "수협카드": "0320",
    "제주카드": "0321",
}

SCRIPT_DIR = Path(__file__).parent
CONNECTED_IDS_PATH = SCRIPT_DIR / "connected_ids.json"


def load_credentials() -> tuple[str, str, str, str]:
    env_path = SCRIPT_DIR / ".env"
    if not env_path.exists():
        sys.exit(f"[ERROR] .env not found at {env_path}")
    load_dotenv(env_path)

    client_id = os.getenv("CODEF_CLIENT_ID", "").strip()
    client_secret = os.getenv("CODEF_CLIENT_SECRET", "").strip()
    public_key = os.getenv("CODEF_PUBLIC_KEY", "").strip()
    env_mode = os.getenv("CODEF_ENV", "demo").strip()

    if not client_id or client_id.startswith("your_"):
        sys.exit("[ERROR] CODEF_CLIENT_ID is not set in .env")
    if not client_secret or client_secret.startswith("your_"):
        sys.exit("[ERROR] CODEF_CLIENT_SECRET is not set in .env")
    if not public_key or public_key.startswith("your_"):
        sys.exit("[ERROR] CODEF_PUBLIC_KEY is not set in .env")

    return client_id, client_secret, public_key, env_mode


def load_connected_ids() -> dict:
    if CONNECTED_IDS_PATH.exists():
        return json.loads(CONNECTED_IDS_PATH.read_text(encoding="utf-8"))
    return {}


def save_connected_ids(data: dict) -> None:
    CONNECTED_IDS_PATH.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def pick_card() -> tuple[str, str]:
    print()
    print("등록 가능한 카드사:")
    for idx, (name, code) in enumerate(CARD_ORGS.items(), start=1):
        print(f"  {idx:2d}. {name}  ({code})")
    print()
    raw = input("등록할 카드사 번호 또는 이름 (기본: NH카드): ").strip() or "NH카드"

    if raw.isdigit():
        idx = int(raw) - 1
        items = list(CARD_ORGS.items())
        if not (0 <= idx < len(items)):
            sys.exit(f"[ERROR] invalid index: {raw}")
        return items[idx]

    if raw not in CARD_ORGS:
        sys.exit(f"[ERROR] unknown card name: {raw}")
    return raw, CARD_ORGS[raw]


def build_account(organization_code: str, login_id: str, encrypted_pw: str) -> dict:
    return {
        "countryCode": "KR",
        "businessType": "CD",
        "clientType": "P",
        "organization": organization_code,
        "loginType": "1",
        "id": login_id,
        "password": encrypted_pw,
    }


def main() -> int:
    client_id, client_secret, public_key, env_mode = load_credentials()
    if env_mode != "demo":
        print(f"[WARN] CODEF_ENV={env_mode}, expected 'demo'. Continuing with DEMO ServiceType.")

    print(f"CODEF_ENV  = {env_mode}")
    print(f"CLIENT_ID  = {client_id[:6]}...{client_id[-4:]}")
    print(f"PUBLIC_KEY = {public_key[:10]}...{public_key[-6:]}  (length={len(public_key)})")

    card_name, organization_code = pick_card()
    print(f"\n선택: {card_name} (organization={organization_code})")

    login_id = input(f"{card_name} 로그인 아이디: ").strip()
    if not login_id:
        sys.exit("[ERROR] login id is required")

    raw_password = getpass.getpass(f"{card_name} 로그인 비밀번호 (입력 시 화면에 표시되지 않음): ")
    if not raw_password:
        sys.exit("[ERROR] password is required")

    print("\n[1/2] RSA 암호화 ...")
    encrypted_pw = encrypt_rsa(raw_password, public_key)
    del raw_password
    print(f"    encrypted length = {len(encrypted_pw)}")

    codef = Codef()
    codef.public_key = public_key
    codef.set_demo_client_info(client_id, client_secret)

    existing = load_connected_ids()
    primary_connected_id = next(
        (entry["connected_id"] for entry in existing.values() if entry.get("connected_id")),
        None,
    )

    account = build_account(organization_code, login_id, encrypted_pw)

    if primary_connected_id is None:
        print(f"\n[2/2] create_account 호출 (DEMO) ...")
        param = {"accountList": [account]}
        raw_res = codef.create_account(ServiceType.DEMO, param)
    else:
        print(f"\n[2/2] add_account 호출 (existing connectedId={primary_connected_id[:8]}...) ...")
        param = {"connectedId": primary_connected_id, "accountList": [account]}
        raw_res = codef.add_account(ServiceType.DEMO, param)

    print(f"    raw response (first 500 chars):\n    {raw_res[:500]}")

    try:
        res = json.loads(raw_res)
    except (ValueError, TypeError):
        sys.exit("[FAIL] response is not valid JSON")

    result = res.get("result", {})
    code = result.get("code")
    message = result.get("message")
    extra = result.get("extraMessage")

    if code != "CF-00000":
        print()
        print("=" * 50)
        print(f"  [FAIL] CODEF returned error: {code}")
        print(f"  message      = {message}")
        print(f"  extraMessage = {extra}")
        print("=" * 50)
        return 1

    data = res.get("data", {})
    new_connected_id = data.get("connectedId") or primary_connected_id
    if not new_connected_id:
        print("[FAIL] no connectedId in response data")
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return 1

    existing[organization_code] = {
        "card_name": card_name,
        "organization_code": organization_code,
        "connected_id": new_connected_id,
        "registered_at": datetime.now().isoformat(timespec="seconds"),
    }
    save_connected_ids(existing)

    print()
    print("=" * 50)
    print(f"  PHASE 1b PASSED — {card_name} 등록 완료")
    print("=" * 50)
    print(f"  connectedId = {new_connected_id[:12]}...{new_connected_id[-6:]}")
    print(f"  saved to    = {CONNECTED_IDS_PATH}")
    print()
    print("Next: python fetch_transactions.py 로 승인내역 조회 (Phase 1c)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
