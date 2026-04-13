"""
Phase 1 validation script for CODEF API integration.

Runs a minimal sequence to verify that:
  1. CODEF credentials are valid  (1 API call)
  2. OAuth access token can be issued

At this stage we do NOT attempt connected ID creation or approval history queries —
those require card-company-specific test accounts and RSA-encrypted passwords,
which we wire up only after confirming the base token flow works.

Usage (on HomeServer):
    cd /d D:\\TheGumaLab\\GumaSpending
    pip install -r requirements.txt
    python validate.py

Required environment variables (loaded from .env in the same directory):
    CODEF_CLIENT_ID
    CODEF_CLIENT_SECRET
    CODEF_ENV         (demo | sandbox | production, default: demo)
"""

from __future__ import annotations

import base64
import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv


TOKEN_ENDPOINT = "https://oauth.codef.io/oauth/token"


def load_credentials() -> tuple[str, str, str]:
    env_path = Path(__file__).parent / ".env"
    if not env_path.exists():
        sys.exit(f"[ERROR] .env not found at {env_path}. Copy .env.example and fill in credentials.")
    load_dotenv(env_path)

    client_id = os.getenv("CODEF_CLIENT_ID", "").strip()
    client_secret = os.getenv("CODEF_CLIENT_SECRET", "").strip()
    env_mode = os.getenv("CODEF_ENV", "demo").strip()

    if not client_id or client_id.startswith("your_"):
        sys.exit("[ERROR] CODEF_CLIENT_ID is not set in .env")
    if not client_secret or client_secret.startswith("your_"):
        sys.exit("[ERROR] CODEF_CLIENT_SECRET is not set in .env")

    return client_id, client_secret, env_mode


def fetch_access_token(client_id: str, client_secret: str) -> dict:
    credentials = f"{client_id}:{client_secret}".encode("utf-8")
    basic_auth = base64.b64encode(credentials).decode("ascii")

    headers = {
        "Authorization": f"Basic {basic_auth}",
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json",
    }
    body = "grant_type=client_credentials&scope=read"

    print(f"[1/1] Requesting access token from {TOKEN_ENDPOINT} ...")
    response = requests.post(TOKEN_ENDPOINT, headers=headers, data=body, timeout=15)

    print(f"    status_code = {response.status_code}")
    try:
        payload = response.json()
    except ValueError:
        print(f"    raw body    = {response.text[:500]}")
        response.raise_for_status()
        return {}

    response.raise_for_status()
    return payload


def main() -> int:
    client_id, client_secret, env_mode = load_credentials()
    print(f"CODEF_ENV     = {env_mode}")
    print(f"CLIENT_ID     = {client_id[:6]}...{client_id[-4:]}  (length={len(client_id)})")
    print()

    payload = fetch_access_token(client_id, client_secret)

    access_token = payload.get("access_token")
    expires_in = payload.get("expires_in")
    scope = payload.get("scope")
    token_type = payload.get("token_type")

    if not access_token:
        print("[FAIL] No access_token in response:")
        print(payload)
        return 1

    print()
    print("=" * 50)
    print("  PHASE 1a PASSED — token issuance successful")
    print("=" * 50)
    print(f"  token_type = {token_type}")
    print(f"  scope      = {scope}")
    print(f"  expires_in = {expires_in} seconds")
    print(f"  token      = {access_token[:12]}...{access_token[-6:]}  (length={len(access_token)})")
    print()
    print("Next step: wire up connected ID creation for 신한/농협/KB (Phase 1b).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
