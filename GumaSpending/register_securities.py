"""
Phase 1b (증권) — Register a securities company account with CODEF and obtain a connectedId.

Usage (on HomeServer, requires a TTY for password input):
    cd /d D:\\TheGumaLab\\GumaSpending
    python register_securities.py

The script defaults to 삼성증권 (0240). Re-running for a company that already
has a connectedId will use add_account so all accounts stay under one connectedId.
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


SECURITIES_ORGS: dict[str, str] = {
    "삼성증권":     "0264",
    "한국투자증권": "0243",
    "키움증권":     "0217",
    "미래에셋증권": "0238",
    "NH투자증권":   "0247",
    "신한투자증권": "0227",
    "KB증권":       "0218",
    "대신증권":     "0221",
}

SCRIPT_DIR = Path(__file__).parent
GLOBAL_ENV_PATH = SCRIPT_DIR.parent / ".env"   # D:\TheGumaLab\.env
CONNECTED_IDS_PATH = SCRIPT_DIR / "connected_ids_securities.json"


def load_credentials() -> tuple[str, str, str, str]:
    env_path = GLOBAL_ENV_PATH if GLOBAL_ENV_PATH.exists() else SCRIPT_DIR / ".env"
    if not env_path.exists():
        sys.exit(f"[ERROR] .env not found at {env_path}")
    load_dotenv(env_path)
    print(f"[env] {env_path}")

    client_id     = os.getenv("CODEF_CLIENT_ID",     "").strip()
    client_secret = os.getenv("CODEF_CLIENT_SECRET", "").strip()
    public_key    = os.getenv("CODEF_PUBLIC_KEY",    "").strip()
    env_mode      = os.getenv("CODEF_ENV", "demo").strip()

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


def pick_securities() -> tuple[str, str]:
    # 환경변수로 지정 가능 (비대화형 실행 지원)
    env_org = os.getenv("SAMSUNG_ORG_CODE", "").strip()
    if env_org:
        for name, code in SECURITIES_ORGS.items():
            if code == env_org:
                print(f"증권사 (env): {name} ({code})")
                return name, code
        sys.exit(f"[ERROR] unknown org code: {env_org}")

    # 기본값: 삼성증권
    default = "삼성증권"
    print(f"증권사 기본값 사용: {default} ({SECURITIES_ORGS[default]})")
    return default, SECURITIES_ORGS[default]


def build_account(organization_code: str, login_id: str, encrypted_pw: str) -> dict:
    return {
        "countryCode":    "KR",
        "businessType":   "ST",       # ST = 증권
        "clientType":     "P",
        "organization":   organization_code,
        "loginType":      "1",
        "id":             login_id,
        "password":       encrypted_pw,
    }


def main() -> int:
    client_id, client_secret, public_key, env_mode = load_credentials()
    if env_mode != "demo":
        print(f"[WARN] CODEF_ENV={env_mode}, expected 'demo'.")

    print(f"CODEF_ENV  = {env_mode}")
    print(f"CLIENT_ID  = {client_id[:6]}...{client_id[-4:]}")
    print(f"PUBLIC_KEY = {public_key[:10]}...{public_key[-6:]}  (length={len(public_key)})")

    sec_name, organization_code = pick_securities()
    print(f"\n선택: {sec_name} (organization={organization_code})")

    login_id = os.getenv("SAMSUNG_LOGIN_ID", "").strip() or input(f"{sec_name} 로그인 아이디: ").strip()
    if not login_id:
        sys.exit("[ERROR] login id is required")

    raw_password = os.getenv("SAMSUNG_LOGIN_PW", "").strip() or getpass.getpass(f"{sec_name} 로그인 비밀번호 (입력 시 화면에 표시되지 않음): ")
    if not raw_password:
        sys.exit("[ERROR] password is required")

    print("\n[1/3] RSA 암호화 ...")
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
        print(f"\n[2/3] create_account 호출 (DEMO) ...")
        param = {"accountList": [account]}
        raw_res = codef.create_account(ServiceType.DEMO, param)
    else:
        print(f"\n[2/3] add_account 호출 (DEMO, existing connectedId={primary_connected_id[:8]}...) ...")
        param = {"connectedId": primary_connected_id, "accountList": [account]}
        raw_res = codef.add_account(ServiceType.DEMO, param)

    print(f"    raw response (first 500 chars):\n    {raw_res[:500]}")

    try:
        res = json.loads(raw_res)
    except (ValueError, TypeError):
        sys.exit("[FAIL] response is not valid JSON")

    result = res.get("result", {})
    code    = result.get("code")
    message = result.get("message")
    extra   = result.get("extraMessage")

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
        "sec_name":          sec_name,
        "organization_code": organization_code,
        "connected_id":      new_connected_id,
        "registered_at":     datetime.now().isoformat(timespec="seconds"),
    }
    save_connected_ids(existing)

    print()
    print("=" * 50)
    print(f"  PHASE 1b (ST) PASSED — {sec_name} 등록 완료")
    print("=" * 50)
    print(f"  connectedId = {new_connected_id[:12]}...{new_connected_id[-6:]}")
    print(f"  saved to    = {CONNECTED_IDS_PATH}")
    print()
    print("Next: python fetch_holdings.py 로 보유종목 조회 (Phase 1c)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
