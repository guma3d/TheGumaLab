"""
Phase 1c (증권) — 전계좌 조회 → 종합자산 조회로 보유종목 전체 출력.

Usage (on HomeServer):
    cd /d D:\\TheGumaLab\\GumaSpending
    python fetch_holdings.py

Prerequisites:
    - register_securities.py 실행 완료 → connected_ids_securities.json 존재
    - 계좌비밀번호 입력 (RSA 암호화 후 전송)
"""

from __future__ import annotations

import getpass
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from easycodefpy import Codef, ServiceType, encrypt_rsa

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

SCRIPT_DIR = Path(__file__).parent
CONNECTED_IDS_PATH = SCRIPT_DIR / "connected_ids_securities.json"

# 상품유형코드 → 한글
PRODUCT_TYPE_MAP = {
    "01": "주식",
    "02": "펀드",
    "03": "CMA",
    "04": "예외주식",
    "05": "신탁/퇴직연금",
    "06": "채권",
    "07": "RP",
    "08": "CD/CP",
    "09": "ELS/DLS",
    "10": "해외원펀드",
    "11": "Wrap",
    "12": "위험RP",
    "13": "연금저축",
    "14": "신용융자",
    "99": "기타",
}


def load_credentials() -> tuple[str, str, str, str]:
    env_path = SCRIPT_DIR / ".env"
    load_dotenv(env_path)
    client_id     = os.getenv("CODEF_CLIENT_ID",     "").strip()
    client_secret = os.getenv("CODEF_CLIENT_SECRET", "").strip()
    public_key    = os.getenv("CODEF_PUBLIC_KEY",    "").strip()
    env_mode      = os.getenv("CODEF_ENV", "demo").strip()
    return client_id, client_secret, public_key, env_mode


def load_connected_ids() -> dict:
    if not CONNECTED_IDS_PATH.exists():
        sys.exit(f"[ERROR] {CONNECTED_IDS_PATH} not found. Run register_securities.py first.")
    return json.loads(CONNECTED_IDS_PATH.read_text(encoding="utf-8"))


def call_api(codef: Codef, path: str, params: dict) -> dict:
    raw = codef.request_product(path, ServiceType.DEMO, params)
    try:
        return json.loads(raw)
    except (ValueError, TypeError):
        print(f"[WARN] Non-JSON response from {path}:\n{raw[:300]}")
        return {}


def main() -> int:
    client_id, client_secret, public_key, env_mode = load_credentials()

    connected_data = load_connected_ids()
    if not connected_data:
        sys.exit("[ERROR] connected_ids_securities.json is empty. Run register_securities.py first.")

    # 첫 번째 등록된 증권사 정보 사용
    first_entry = next(iter(connected_data.values()))
    connected_id      = first_entry["connected_id"]
    organization_code = first_entry["organization_code"]
    sec_name          = first_entry["sec_name"]

    print(f"증권사:      {sec_name} ({organization_code})")
    print(f"connectedId: {connected_id[:12]}...{connected_id[-6:]}")
    print()

    codef = Codef()
    codef.public_key = public_key
    codef.set_demo_client_info(client_id, client_secret)

    # ── Step 1: 전계좌 조회 ──────────────────────────────────────────
    print("[1/2] 전계좌 조회 중...")
    account_res = call_api(codef, "/v1/kr/stock/a/account/account-list", {
        "organization": organization_code,
        "connectedId":  connected_id,
    })

    result = account_res.get("result", {})
    if result.get("code") != "CF-00000":
        print(f"[FAIL] 전계좌 조회 실패: {result.get('code')} — {result.get('message')}")
        print(f"       extraMessage = {result.get('extraMessage')}")
        return 1

    accounts = account_res.get("data", [])
    if isinstance(accounts, dict):
        accounts = [accounts]

    print(f"  계좌 {len(accounts)}개 발견:")
    for acc in accounts:
        acc_no      = acc.get("resAccount", "")
        acc_display = acc.get("resAccountDisplay", acc_no)
        acc_name    = acc.get("resAccountName", "")
        val_amt     = acc.get("resValuationAmt", "")
        print(f"    - [{acc_name}] {acc_display}  평가금액={val_amt}")
    print()

    # ── Step 2: 계좌별 종합자산 조회 ────────────────────────────────
    account_password_raw = getpass.getpass("계좌비밀번호 (모든 계좌 공통, 입력 시 화면 미표시): ")
    if not account_password_raw:
        sys.exit("[ERROR] 계좌비밀번호는 필수입니다.")
    account_password_enc = encrypt_rsa(account_password_raw, public_key)
    del account_password_raw

    print()
    print("[2/2] 종합자산 조회 중...")

    all_holdings = []

    for acc in accounts:
        acc_no   = acc.get("resAccount", "")
        acc_name = acc.get("resAccountName", "")
        print(f"\n  계좌: {acc.get('resAccountDisplay', acc_no)} [{acc_name}]")

        holdings_res = call_api(codef, "/v1/kr/stock/a/account/financial-assets", {
            "organization":    organization_code,
            "connectedId":     connected_id,
            "account":         acc_no,
            "accountPassword": account_password_enc,
            "inquiryType":     "0",
        })

        h_result = holdings_res.get("result", {})
        if h_result.get("code") != "CF-00000":
            print(f"    [SKIP] {h_result.get('code')} — {h_result.get('message')}")
            print(f"           extraMessage = {h_result.get('extraMessage')}")
            continue

        items    = holdings_res.get("data", {}).get("resItemList", [])
        deposit  = holdings_res.get("data", {}).get("resDepositReceived", "0")

        if deposit and deposit != "0":
            print(f"    예수금: ₩{int(deposit):,}")

        if not items:
            print("    보유 종목 없음")
            continue

        print(f"    종목 {len(items)}개:")
        for item in items:
            ptype    = item.get("resProductTypeCd", "")
            pname    = PRODUCT_TYPE_MAP.get(ptype, ptype)
            name     = item.get("resItemName", "")
            code     = item.get("resItemCode", "")
            qty      = item.get("resQuantity", "0")
            val_amt  = item.get("resValuationAmt", "0")
            cur_price= item.get("resPresentAmt", "0")
            currency = item.get("resAccountCurrency", "KRW")

            try:
                val_int = int(val_amt) if val_amt else 0
                print(f"      [{pname}] {name} (코드:{code or '-'})  수량={qty}  평가금액=₩{val_int:,}  통화={currency}")
            except ValueError:
                print(f"      [{pname}] {name} (코드:{code or '-'})  수량={qty}  평가금액={val_amt}  통화={currency}")

            all_holdings.append({
                "account":         acc_no,
                "account_name":    acc_name,
                "product_type_cd": ptype,
                "product_type":    pname,
                "name":            name,
                "code":            code,
                "quantity":        qty,
                "valuation_amt":   val_amt,
                "current_price":   cur_price,
                "currency":        currency,
            })

    # ── 결과 저장 ────────────────────────────────────────────────────
    out_path = SCRIPT_DIR / "holdings_result.json"
    out_path.write_text(
        json.dumps(all_holdings, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print()
    print("=" * 50)
    print(f"  총 {len(all_holdings)}개 종목 조회 완료")
    print(f"  결과 저장: {out_path}")
    print("=" * 50)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
