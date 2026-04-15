# CODEF 통합 심층 노트

> 향후 증권/은행 확장, 신규 카드사 추가, 에러 디버깅 시 반드시 참고.
> Phase 1 구축 과정에서 시행착오로 확보한 실전 정보이며 CODEF 공식 문서만으로는 얻기 어려움.

## 계정 체계

- CODEF 가입 후 마이페이지에서 3가지 크레덴셜 발급:
  - `CODEF_CLIENT_ID` (OAuth client_id)
  - `CODEF_CLIENT_SECRET` (OAuth client_secret)
  - `CODEF_PUBLIC_KEY` (RSA 공개키, 비밀번호 암호화용 — PEM body만, 헤더/푸터 제외)
- **요금제**: DEMO 무료, PRODUCT 유료 (월 100건 기본 플랜). DEMO는 월 호출 제한이 불명확하며 카드 경로는 실제 동작, 증권 경로는 제한적.

## 3가지 환경 (ServiceType)

| Service | Domain | 용도 | 실제 동작 여부 |
|---|---|---|---|
| `DEMO` | `development.codef.io` | 개발/테스트 | **카드/은행: 실제 동작** · **증권: 제한** |
| `PRODUCT` | `api.codef.io` | 정식 서비스 | 유료 플랜 |
| `SANDBOX` | `sandbox.codef.io` | SDK 테스트 | 고정 가짜 응답 |

**핵심 발견 — DEMO 카드/은행 경로는 진짜**: CODEF DEMO는 단순 목업이 아니라 실제 사이트에 실제 로그인을 시도한다. 실제 ID/PW를 넣으면 **실제 거래 데이터가 반환됨**. SDK 문서에 명시되지 않은 동작이며 Phase 1에서 NH 5장·신한 3장·KB 1장·농협은행 통장 2개로 검증됨.

## businessType 별 동작 차이 ⚠️

DEMO 모드에서 `businessType`에 따라 동작이 완전히 다르다:

| businessType | 의미 | DEMO 동작 | 검증 상태 |
|---|---|---|---|
| `CD` | 카드 (Card) | **실계정 수용** → 실 데이터 | ✅ NH/신한/KB 성공 |
| `ST` | 증권 (Stock) | **실계정 거부** → `CF-04000/CF-00007` | ❌ 삼성증권 실패 |
| `BK` | 은행 (Bank) | **실계정 수용** → 실 데이터 | ✅ 농협은행 성공 |

### 증권 실패 사례 (참고용)

Phase 1 작업 중 Gram PC에서 삼성증권 통합 시도 → 실패 후 GumaSpending 전체 일시 삭제 (`06c1b0b`). 정확한 실패 양상:

```json
// DEMO create_account 요청
{
  "accountList": [{
    "countryCode": "KR",
    "businessType": "ST",
    "clientType": "P",
    "organization": "0264",     // 삼성증권
    "loginType": "1",
    "id": "<실제 ID>",
    "password": "<RSA 암호화>"
  }]
}
```

```json
// 응답
{
  "result": {"code": "CF-04000", "message": "사용자 계정정보 등록에 실패했습니다."},
  "data": {
    "successList": [],
    "errorList": [{
      "code": "CF-00007",
      "message": "요청 파라미터가 올바르지 않습니다.",
      "businessType": "ST", "organization": "0264", "loginType": "1"
    }]
  }
}
```

**해석 (추정)**: CODEF DEMO의 증권 경로는 실사이트 로그인을 수행하지 않고, CODEF가 미리 등록한 증권사별 테스트 계정만 받는다. 실 계정은 파라미터 검증 단계(`CF-00007`)에서 거부.

### 증권 재시도 전략 (향후)

1. **PRODUCT 모드로 승격** — 유료 플랜 가입 후 `ServiceType.PRODUCT`로 호출. 가장 확실한 경로.
2. **다른 증권사 시도** — 삼성증권(0264) 외 한국투자(0243)/키움(0217)/미래에셋(0238) 등. DEMO 커버리지가 증권사별로 다를 수 있음.
3. **loginType 변경** — `"0"` 공동인증서 경로. 인증서 파일(DER) 업로드 필요, 매년 갱신. 자동화 유지보수 비용 큼.
4. **간편인증** — loginType `"6"`. 2-way 콜백 + 매 호출 폰 승인 필요 → 자동화 취지 무너짐.

## organization 코드

### 카드사

| 카드사 | 코드 | 검증 상태 |
|---|---|---|
| KB카드 | 0301 | ✅ 성공 (쿠팡와우) |
| 현대카드 | 0302 | 미검증 — cardNo+cardPassword(4자리) 필수 |
| 삼성카드 | 0303 | 미검증 |
| NH카드 | 0304 | ✅ 성공 (5장) |
| BC카드 | 0305 | 미검증 |
| 신한카드 | 0306 | ✅ 성공 (3장, Pay머니 1장은 CF-13101 skip) |
| 씨티카드 | 0307 | 미검증 — SMS 추가 인증 가능성 |
| 우리카드 | 0309 | 미검증 |
| 롯데카드 | 0311 | 미검증 |
| 하나카드 | 0313 | 미검증 |
| 전북카드 | 0315 | 미검증 |
| 광주카드 | 0316 | 미검증 |
| 수협카드 | 0320 | 미검증 |
| 제주카드 | 0321 | 미검증 |

### 은행

| 은행 | 코드 | 검증 상태 |
|---|---|---|
| 산업은행 | 0002 | 미검증 |
| 기업은행 | 0003 | 미검증 |
| 국민은행 | 0004 | 미검증 |
| 수협은행 | 0007 | 미검증 |
| 농협은행 | 0011 | ✅ 성공 (자립예탁금/주거래우대통장) |
| 우리은행 | 0020 | 미검증 |
| SC제일은행 | 0023 | 미검증 |
| 한국씨티은행 | 0027 | 미검증 |
| 우체국 | 0071 | 미검증 |
| 하나은행 | 0081 | 미검증 |
| 신한은행 | 0088 | 미검증 |
| 케이뱅크 | 0089 | 미검증 |
| 카카오뱅크 | 0090 | 미검증 |
| 토스뱅크 | 0092 | 미검증 |

### 증권사

| 증권사 | 코드 |
|---|---|
| 삼성증권 | 0264 |
| 한국투자증권 | 0243 |
| 키움증권 | 0217 |
| 미래에셋증권 | 0238 |
| NH투자증권 | 0247 |
| 신한투자증권 | 0227 |
| KB증권 | 0218 |
| 대신증권 | 0221 |

## loginType 값

| 값 | 의미 | 비고 |
|---|---|---|
| `"0"` | 공동인증서 | 인증서 파일 업로드, 매년 갱신 |
| `"1"` | ID/PW | **자동화 친화적** — GumaSpending 채택 |
| `"6"` | 간편인증 (카카오/네이버/PASS) | 2-way 콜백, 매 호출 폰 승인 |

## connectedId 모델

- **하나의 connectedId**에 여러 카드사/은행 계정을 `add_account`로 추가 가능.
- GumaSpending 현재 상태: NH + 신한 + KB + 농협은행이 모두 `9LlJh6SrkiSaR.5P9yJmb3` 하나에 묶여있음.
- `connected_ids.json`은 `{organization_code: {card_name, connected_id, ...}}` 구조지만 여러 entry가 **같은 connected_id 값**을 공유. 정상.

### register_card.py 분기 로직

```python
primary_connected_id = 기존_파일_첫_엔트리의_connected_id  # None if empty
if primary_connected_id is None:
    codef.create_account(DEMO, {"accountList": [account]})
else:
    codef.add_account(DEMO, {"connectedId": primary_connected_id,
                              "accountList": [account]})
```

- 최초 실행은 `create_account` → 새 connectedId 발급
- 이후 실행은 `add_account` → 기존 connectedId에 추가
- **첫 카드 등록 후에는 실수로 create를 다시 호출하지 않게 됨**

## API 엔드포인트 맵

### 카드 (`businessType=CD`)

| 용도 | Path | 필수 파라미터 | 비고 |
|---|---|---|---|
| 보유카드 조회 | `/v1/kr/card/p/account/card-list` | organization, connectedId | 카드사별 cardNo/cardPassword 옵션 |
| 등록여부 확인 | `/v1/kr/card/p/user/registration-status` | organization, connectedId | `resRegistrationStatus` `"0"`/`"1"` |
| 승인내역 (raw) ⭐ | `/v1/kr/card/p/account/approval-list` | organization, connectedId, startDate, endDate, orderBy | 개별 승인건 — 실시간 지출 추적 핵심 |
| 청구내역 (월별) | `/v1/kr/card/p/account/billing-list` | organization, connectedId | 월별 명세서 — 일시불/할부/리볼빙/연회비 |
| 한도조회 | `/v1/kr/card/p/account/limit` | organization, connectedId | 총/일시불/할부/단기대출 |
| 실적조회 | `/v1/kr/card/p/account/result-check-list` | organization, connectedId | 카드 혜택 실적 충족여부 |

### 은행 (`businessType=BK`)

| 용도 | Path | 필수 파라미터 | 비고 |
|---|---|---|---|
| 보유계좌 조회 | `/v1/kr/bank/p/account/account-list` | organization, connectedId | `resDepositTrust` 배열로 반환 |
| 거래내역 ⭐ | `/v1/kr/bank/p/account/transaction-list` | organization, connectedId, account, startDate, endDate, orderBy, inquiryType | 출금/입금 분리 |

## 승인내역 조회 기간 제약

| 카드사 | 최대 과거 | 단일 호출 chunk |
|---|---|---|
| 신한 | 6개월 | 3개월 |
| NH | 12개월 | 92일 |
| KB | 12개월 | 92일 |
| 하나 | 18개월 | — |
| 롯데 | 6개월 | — |
| 광주 | 10년 | — |
| 전북 | 4년 | — |
| 제주 | 제한 없음 | — |

`fetch_transactions.py`는 기본 30일을 한 chunk로 호출. 92일 초과 요청은 argparse 단계에서 거부. 장기 백필이 필요하면 chunk 루프 추가해야 함.

## 과금 단위

결과 **5,000건 단위로 1콜 과금**. 예: 3,000건 = 1콜, 5,500건 = 2콜. 개인 사용 패턴은 대부분 월 100건 미만 → 사실상 1콜.

## 은행 transaction-list 응답 필드

| 필드 | 의미 |
|---|---|
| `resAccountTrDate` | 거래일자 YYYYMMDD |
| `resAccountTrTime` | 거래시각 HHMMSS |
| `resAccountOut` | 출금액 (지출) |
| `resAccountIn` | 입금액 |
| `resAccountDesc1` | 적요1 (비어있는 경우 많음) |
| `resAccountDesc2` | 적요2 — 거래 유형 (예: "스마트당행", "NH카드대금") |
| `resAccountDesc3` | 적요3 — 거래 상대방 (예: "장성욱", "NH농협카드") |
| `resAccountDesc4` | 적요4 — 처리 지점 (예: "농협 000998") |
| `resAfterTranBalance` | 거래 후 잔액 |

- 계좌번호: 하이픈 제거 형식(`resAccount`)과 하이픈 포함(`resAccountDisplay`) 둘 다 반환
- `inquiryType="1"` 전체, `"2"` 입금만, `"3"` 출금만

## 이중 집계 방지 패턴

`app.py`의 `BANK_DEDUP_PATTERNS` 에 포함된 키워드가 `resAccountDesc1~4` 조합 내에 등장하면 해당 은행 출금 건을 SKIP:

```python
BANK_DEDUP_PATTERNS = ["카드대금", "카드결제", "신용카드", "체크카드", "카드자동"]
```

**이유**: 카드 청구대금이 통장에서 빠져나가는 이벤트는 카드 approval-list의 승인건 합계와 **같은 돈의 다른 시점 기록**이므로, 둘 다 집계하면 월 지출이 2배. 카드 approval 데이터가 더 정밀(건별 가맹점명/카테고리 포함)하므로 그쪽을 신뢰하고 은행 쪽 카드대금은 버린다.

## 카드사별 실전 특이사항

### NH카드
- `approval-list`에 **`cardNo` 필수**. PDF 스펙에는 선택(△)으로 표기돼있으나 실제로는 필수. 빠뜨리면 `CF-13100` "카드번호를 입력하지 않았습니다".
- 해결: `card-list` 호출로 `resCardNo` 먼저 획득 후 카드별 반복 호출.

### 신한카드
- NH와 동일한 cardNo 반복 패턴.
- **신한Pay머니 모바일** 같은 가상/모바일 카드는 `CF-13101` "카드번호 List에 입력된 카드번호와 일치하는 정보가 없습니다" 반환. 실물 카드 체계와 다른 계정 구조.
- `fetch_transactions.py`의 `SKIPPABLE_CODES`에 `CF-13101` 등록 → 경고 후 다음 카드 진행.

### KB카드
- 기본은 ID/PW 통과. 하지만 조회 시점에 **[카드소지확인]** 페이지로 리다이렉트되는 경우가 있고 이 경우 `CF-12108` 반환.
- 해결: `cardNo`(전체) + **`cardPassword`(실물카드 4자리 PIN 중 앞 2자리)** RSA 암호화 후 파라미터에 추가.
- 쿠팡와우카드는 리다이렉트 없이 통과 — 모든 카드 그런 것 아님.

### 현대카드 (미검증)
- ID 로그인 시 `cardNo`(전체) + `cardPassword`(4자리 전체) **필수** (PDF 명시).
- 미입력 시 `CF-12401`. 카드 비밀번호 3회 오류 시 계정 잠김 → `CF-12834`.
- 현대 등록은 `register_card.py` 확장 필요.

### 씨티카드 (미검증)
- **SMS 추가 인증** 요청 가능성. 로그인 디바이스 변경 시 SMS 코드 전송.
- 우회: 공동인증서(`loginType=0`) 사용.

## 에러 코드 요약

| 코드 | 의미 | 대응 |
|---|---|---|
| `CF-00000` | 성공 | — |
| `CF-00007` | 요청 파라미터 불일치 | businessType/loginType/카드사별 필수값 재확인 |
| `CF-04000` | 계정 등록 실패 (상위 코드) | `data.errorList`의 세부 코드 확인 |
| `CF-12040` | 대상 계정 없음 | 체크카드만 있는 경우 등 (한도/실적) |
| `CF-12100` | 존재하지 않는 사용자 | DEMO에서 실계정 거부 증권 케이스 유사 |
| `CF-12108` | 카드소지확인 페이지 리다이렉트 | KB — cardNo+cardPassword 추가 |
| `CF-12401` | 카드 비밀번호 미입력 | 현대 — cardPassword 필수 |
| `CF-12834` | 계정 잠김 | 카드 PIN 3회 오류 → 고객센터 해제 |
| `CF-13100` | 카드번호 미입력 | NH — cardNo 필수 |
| `CF-13101` | 카드번호 List 불일치 | 신한 Pay머니 등 가상카드 — skip |

## RSA 암호화 패턴

```python
from easycodefpy import encrypt_rsa
encrypted_pw = encrypt_rsa(raw_password, public_key)  # base64 문자열
```

- 카드 비밀번호(4자리 PIN)도 동일 방식으로 암호화.
- 공개키는 `.env`에서 한 줄로 로드 (PEM body, 헤더/푸터 제외).

---

*본 문서의 organization 코드·에러 코드는 2026-04 기준. CODEF가 코드나 정책을 변경할 수 있으니 재시도 시 확인.*
