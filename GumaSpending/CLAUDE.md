# GumaSpending — CLAUDE.md

개인 카드 소비 추적·시각화 서비스. CODEF Open API를 통해 카드사 승인내역을
자동 수집하고 월 단위 캘린더 대시보드로 지출을 가시화한다.

**URL**: gumaspending.guma3d.com (예정)
**로컬 포트**: 8060 (예정, GumaStockReport 8050 다음 자리)

> **전역 규칙 참조**
> - 환경변수 / API 키: `GumaSpending/.env` (서비스 로컬) 사용
> - 워크플로우·커밋·배포 규칙: 루트 `CLAUDE.md` 준수

---

## 한눈에 보기

**입력**: 카드사 웹 로그인 ID/PW (최초 1회)
**출력**: 월별 캘린더 뷰 (날짜별 지출 합계 + 날짜 클릭 시 상세 거래)
**수집 주기**: 매일 자동 (Windows Task Scheduler / cron 예정)
**현재 지원 카드사**: NH(0304) · 신한(0306) · KB(0301)

---

## 기술 스택 (계획)

- **Backend**: Python Flask (GumaStockReport와 동일 패턴)
- **DB**: SQLite (`spending.db`) — 단일 파일, 백업 간편, 동시성 이슈 없음
- **수집**: `easycodefpy` SDK + CODEF Open API (`development.codef.io` DEMO 모드)
- **Frontend**: Vanilla JS + 다크 테마 (`#050505` + emerald `#10b981`) — GumaStockReport와 동일 디자인 시스템
- **PWA**: manifest + service worker (GumaPhoto 패턴)

## 컨테이너 구성 (계획)

| 컨테이너 | 역할 |
|---|---|
| `gumaspending_web` | Flask 앱 (포트 8060), watchfiles로 자동 재시작 |

Redis 불필요 (캐시는 SQLite + 파일 레벨).

---

## 디렉토리 구조

```
GumaSpending/
├── CLAUDE.md                      # 이 파일
├── README.md                      # 사용자용 요약
├── .env                           # CODEF 크레덴셜 (gitignored)
├── .env.example                   # 템플릿
├── requirements.txt               # requests, python-dotenv, easycodefpy
│
├── validate.py                    # Phase 1a: OAuth 토큰 발급 확인
├── register_card.py               # Phase 1b: 카드사 계정 등록 → connectedId 발급
├── fetch_transactions.py          # Phase 1c: 승인내역 조회 → JSON 저장
│
├── app.py                         # Phase 2: Flask 대시보드 (예정)
├── templates/index.html           # Phase 2: 캘린더 UI (예정)
├── static/                        # Phase 2: manifest, icons (예정)
├── Dockerfile                     # Phase 2 (예정)
├── docker-compose.yml             # Phase 2 (예정)
│
├── connected_ids.json             # (gitignored) 카드사 → connectedId 매핑
├── transactions_{org}_*.json      # (gitignored) 기간별 승인내역 raw
└── spending.db                    # (gitignored) 정규화된 거래 DB (Phase 2)
```

---

## 데이터 흐름

```
[최초 1회]
  register_card.py (대화형)
    → CODEF create_account / add_account
    → connected_ids.json 저장
    → card-list API로 보유카드 검증

[정기 수집]
  fetch_transactions.py (비대화형, cron)
    → connected_ids.json 로딩
    → 카드사별: card-list → 카드별 approval-list 호출
    → transactions_{org}_{YYYYMMDD-YYYYMMDD}.json 저장

[Phase 2]
  Flask app.py
    → transactions_*.json을 spending.db로 정규화 (idempotent upsert)
    → 캘린더 뷰 / 날짜별 상세 / 월 합계 API
```

---

# CODEF 통합 심층 노트

> **이 섹션은 향후 증권/은행 통합 재시도 시 반드시 참고**.
> Phase 1 구축 과정에서 시행착오로 확보한 정보이며 CODEF 공식 문서만으로는
> 얻을 수 없는 실전 정보다.

## 계정 체계

- CODEF 가입 후 마이페이지에서 3가지 크레덴셜 발급:
  - `CODEF_CLIENT_ID` (OAuth client_id)
  - `CODEF_CLIENT_SECRET` (OAuth client_secret)
  - `CODEF_PUBLIC_KEY` (RSA 공개키, 비밀번호 암호화용 — PEM body만, 헤더/푸터 제외)
- **요금제**: DEMO 무료, PRODUCT 유료 (월 100건 기본 플랜). DEMO는 월 호출 제한이
  불명확하며 카드 경로는 실제 동작, 증권 경로는 제한적.

## 3가지 환경 (ServiceType)

| Service | Domain | 용도 | 실제 동작 여부 |
|---|---|---|---|
| `DEMO` | `development.codef.io` | 개발/테스트 | **카드: 실제 동작** · **증권: 제한** |
| `PRODUCT` | `api.codef.io` | 정식 서비스 | 유료 플랜 |
| `SANDBOX` | `sandbox.codef.io` | SDK 테스트 | 고정 가짜 응답 |

**핵심 발견 — DEMO 카드 경로는 진짜**: CODEF DEMO는 단순 목업이 아니라 실제
카드사 사이트에 실제 로그인을 시도한다. 실제 NH/신한/KB ID/PW를 넣으면
**실제 승인내역 데이터가 반환됨**. 이는 SDK 문서에 명시되지 않은 동작이며
Phase 1c에서 NH 5장·신한 3장·KB 1장 수집으로 검증됨.

## businessType 별 동작 차이 ⚠️

DEMO 모드에서 `businessType`에 따라 동작이 완전히 다르다:

| businessType | 의미 | DEMO 동작 | 검증 상태 |
|---|---|---|---|
| `CD` | 카드 (Card) | **실계정 수용** → 실 데이터 | ✅ NH/신한/KB 성공 |
| `ST` | 증권 (Stock) | **실계정 거부** → `CF-04000/CF-00007` | ❌ 삼성증권 실패 |
| `BK` | 은행 (Bank) | **실계정 수용** → 실 데이터 | ✅ 농협은행 성공 |

### 증권 실패 사례 (참고용)

Phase 1 작업 중 Gram PC에서 삼성증권 통합 시도 → 실패 후 GumaSpending 전체
일시 삭제 (`06c1b0b`). 정확한 실패 양상은 아래와 같음:

```json
// DEMO create_account 시도
{
  "accountList": [{
    "countryCode": "KR",
    "businessType": "ST",       // 증권
    "clientType": "P",
    "organization": "0264",     // 삼성증권
    "loginType": "1",           // ID/PW
    "id": "<실제 삼성증권 ID>",
    "password": "<RSA 암호화된 실제 PW>"
  }]
}
```

```json
// 응답
{
  "result": {
    "code": "CF-04000",
    "message": "사용자 계정정보 등록에 실패했습니다.",
    "extraMessage": ""
  },
  "data": {
    "successList": [],
    "errorList": [{
      "code": "CF-00007",
      "message": "요청 파라미터가 올바르지 않습니다.",
      "businessType": "ST",
      "organization": "0264",
      "loginType": "1",
      "clientType": "P"
    }]
  }
}
```

**해석 (추정)**: CODEF DEMO의 증권 경로는 카드처럼 실사이트 로그인을 수행
하지 않고, CODEF가 미리 등록한 각 증권사별 테스트 계정만 받는다. 실 계정은
파라미터 검증 단계(`CF-00007`)에서 거부.

### 증권 재시도 전략 (향후)

1. **PRODUCT 모드로 승격** — 유료 플랜 가입 후 `ServiceType.PRODUCT`로 호출.
   비용: 월 100콜 기본 ~₩XXk (공식 가격표 확인 필요). 가장 확실한 경로.
2. **다른 증권사 시도** — 삼성증권(0264) 외 한국투자(0243)/키움(0217)/
   미래에셋(0238) 등. CODEF의 DEMO 커버리지가 증권사별로 다를 수 있음.
3. **loginType 변경** — `"0"` 공동인증서 경로. 인증서 파일(DER 포맷) 업로드
   필요, 매년 갱신. 자동화 유지보수 비용 큼.
4. **다른 인증 경로** — 간편인증(카카오/PASS) loginType `"6"`. 2-way 콜백
   필요하고 매 호출마다 폰 승인 필요 → 자동화 취지 무너짐.

### 사용 가능한 증권사 organization 코드

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

## 사용 가능한 카드사 organization 코드

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

## loginType 값

| 값 | 의미 | 비고 |
|---|---|---|
| `"0"` | 공동인증서 (구 공인인증서) | 인증서 파일 업로드 필요, 매년 갱신 |
| `"1"` | ID/PW | **자동화 친화적** — GumaSpending 채택 |
| `"6"` | 간편인증 (카카오톡/네이버/PASS) | 2-way 콜백 필요, 매 호출 폰 승인 |

## connectedId 모델

- **하나의 connectedId**에 여러 카드사 계정을 **`add_account`로 추가** 가능.
- GumaSpending 현재 상태: NH + 신한 + KB가 모두 `9LlJh6SrkiSaR.5P9yJmb3`
  하나에 묶여있음.
- `connected_ids.json`은 `{organization_code: {card_name, connected_id, ...}}`
  구조이지만 여러 entry가 **같은 connected_id 값**을 공유한다. 이는 정상.

## register_card.py 분기 로직

```python
primary_connected_id = 기존_파일_첫_엔트리의_connected_id  # None if empty
if primary_connected_id is None:
    codef.create_account(DEMO, {"accountList": [account]})
else:
    codef.add_account(DEMO, {"connectedId": primary_connected_id,
                              "accountList": [account]})
```

- 최초 실행은 `create_account` → 새 connectedId 발급
- 이후 실행은 `add_account` → 기존 connectedId에 추가만 함
- 따라서 **첫 카드 등록 후에는 실수로 create를 다시 호출하지 않게 됨**

## API 엔드포인트 맵 (`businessType=CD` 카드)

| 용도 | Path | 필수 파라미터 | 비고 |
|---|---|---|---|
| 보유카드 조회 | `/v1/kr/card/p/account/card-list` | organization, connectedId | 카드사별 cardNo/cardPassword 옵션 |
| 등록여부 확인 | `/v1/kr/card/p/user/registration-status` | organization, connectedId | `resRegistrationStatus` `"0"`/`"1"` |
| 승인내역 (raw) ⭐ | `/v1/kr/card/p/account/approval-list` | organization, connectedId, startDate, endDate, orderBy | 개별 승인건 — 실시간 지출 추적 핵심 |
| 청구내역 (월별) | `/v1/kr/card/p/account/billing-list` | organization, connectedId | 월별 명세서 — 일시불/할부/리볼빙/연회비 |
| 한도조회 | `/v1/kr/card/p/account/limit` | organization, connectedId | 총/일시불/할부/단기대출 한도 |
| 실적조회 | `/v1/kr/card/p/account/result-check-list` | organization, connectedId | 카드 혜택 실적 충족여부 |

### 승인내역 조회 기간 제약

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

`fetch_transactions.py`는 기본 30일을 한 chunk로 호출. 92일 초과 요청은
argparse 단계에서 거부. 장기 백필이 필요하면 chunk 루프를 추가해야 함.

### 과금 단위

결과 **5000건 단위로 1콜 과금**. 예: 3000건 = 1콜, 5500건 = 2콜. 개인
사용 패턴은 대부분 월 100건 미만 → 사실상 1콜.

## 은행 통합 (`businessType=BK`)

카드와 동일한 패턴으로 DEMO에서 실계정 동작 확인 (2026-04 농협은행 검증).
카드와 달리 **출금/입금이 구분되므로 출금만 "지출"로 집계**하며, 카드 청구금
출금(예: `NH카드대금`)은 카드 approval-list 데이터와 **이중 집계 위험**이 있어
ingestion 단계에서 제외 처리한다.

### 사용 가능한 은행 organization 코드

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

### API 엔드포인트 (`businessType=BK`)

| 용도 | Path | 필수 파라미터 | 비고 |
|---|---|---|---|
| 보유계좌 조회 | `/v1/kr/bank/p/account/account-list` | organization, connectedId | `resDepositTrust` 배열로 반환 |
| 거래내역 ⭐ | `/v1/kr/bank/p/account/transaction-list` | organization, connectedId, account, startDate, endDate, orderBy, inquiryType | 출금/입금 분리 |

### transaction-list 응답 필드

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

### 이중 집계 방지 패턴

`app.py`의 `BANK_DEDUP_PATTERNS` 에 포함된 키워드가 `resAccountDesc1~4` 조합
내에 등장하면 해당 은행 출금 건을 SKIP:

```python
BANK_DEDUP_PATTERNS = ["카드대금", "카드결제", "신용카드", "체크카드", "카드자동"]
```

이유: 카드 청구대금이 통장에서 빠져나가는 이벤트는 카드 approval-list의
승인건 합계와 **같은 돈의 다른 시점 기록**이므로, 둘 다 집계하면 월 지출이
2배가 됨. 카드 approval 데이터가 더 정밀(건별 가맹점명/카테고리 포함)하므로
그쪽을 신뢰하고 은행 쪽 카드대금은 버린다.

### 농협은행 실전 특이사항

- 계좌 목록은 `data.resDepositTrust` (예금/저축), 대출은 `data.resLoan`
- 계좌번호는 하이픈 제거 형식(`resAccount`)과 하이픈 포함(`resAccountDisplay`)
  둘 다 반환
- `inquiryType="1"` 전체, `"2"` 입금만, `"3"` 출금만

---

## 카드사별 실전 특이사항

### NH카드
- `approval-list`에 **`cardNo` 필수**. PDF 스펙에는 선택(△)으로 표기돼있으나
  실제로는 필수. 빠뜨리면 `CF-13100` "카드번호를 입력하지 않았습니다".
- 해결: `card-list` 호출로 `resCardNo` 먼저 획득 후 카드별 반복 호출.
- `fetch_transactions.py`가 이 패턴 구현.

### 신한카드
- NH와 동일한 cardNo 반복 패턴.
- **신한Pay머니 모바일** 같은 가상/모바일 카드는 `approval-list`에서
  `CF-13101` "카드번호 List에 입력된 카드번호와 일치하는 정보가 없습니다"
  반환. 실물 카드 체계와 다른 계정 구조라 승인내역 조회 불가.
- `fetch_transactions.py`의 `SKIPPABLE_CODES`에 `CF-13101` 등록 → 경고 후 다음 카드 진행.

### KB카드
- 기본은 ID/PW 통과. 하지만 조회 시점에 **[카드소지확인]** 페이지로 리다이렉트
  되는 경우가 있고 이 경우 `CF-12108` 반환.
- 해결 필요 시: `cardNo`(전체) + **`cardPassword`(실물카드 4자리 PIN 중 앞 2자리)**
  RSA 암호화 후 파라미터에 추가.
- 쿠팡와우카드는 리다이렉트 없이 통과 — 모든 카드 그런 것은 아님.
- 향후 다른 KB 카드 등록 시 `CF-12108` 발생하면 `fetch_transactions.py`에
  KB 분기 추가해 cardPassword 입력 경로 구현 필요.

### 현대카드 (미검증)
- ID 로그인 시 `cardNo`(전체) + `cardPassword`(4자리 전체) **필수** (PDF 명시).
- 미입력 시 `CF-12401` 반환. 카드 비밀번호 3회 오류 시 계정 잠김 → `CF-12834`.
- 현대카드 등록은 `register_card.py`를 확장해야 가능.

### 씨티은행 (미검증)
- **SMS 추가 인증** 요청 가능성. 로그인 디바이스 변경 시 설정된 휴대폰 번호로
  SMS 코드 전송 요청. CODEF 서버가 여러 대 운영되어 반복 호출 시에도 발생 가능.
- 우회: 공동인증서(`loginType=0`) 사용.

## 에러 코드 요약

| 코드 | 의미 | 대응 |
|---|---|---|
| `CF-00000` | 성공 | — |
| `CF-00007` | 요청 파라미터 불일치 | businessType/loginType/카드사별 필수값 재확인 |
| `CF-04000` | 계정 등록 실패 (상위 코드) | `data.errorList`의 세부 코드 확인 |
| `CF-12040` | 대상 계정 없음 | 체크카드만 있는 경우 등 (한도/실적) |
| `CF-12100` | 존재하지 않는 사용자 | DEMO에서 실계정이 거부된 증권 케이스 유사 |
| `CF-12108` | 카드소지확인 페이지 리다이렉트 | KB — cardNo+cardPassword 추가 |
| `CF-12401` | 카드 비밀번호 미입력 | 현대 — cardPassword 필수 |
| `CF-12834` | 계정 잠김 | 카드 비밀번호 3회 오류 → 카드사 고객센터 해제 필요 |
| `CF-13100` | 카드번호 미입력 | NH — cardNo 필수 |
| `CF-13101` | 카드번호 List 불일치 | 신한 Pay머니 등 가상카드 — skip |

## RSA 암호화 패턴

```python
from easycodefpy import encrypt_rsa
encrypted_pw = encrypt_rsa(raw_password, public_key)  # base64 문자열 반환
```

- 카드 비밀번호(4자리 PIN)도 동일 방식으로 암호화.
- 공개키는 `.env`에서 한 줄로 로드 (PEM body, 헤더/푸터 제외).

---

## 환경변수

`.env` 파일 (GumaSpending/.env, **gitignored**):

```
CODEF_CLIENT_ID=<발급받은 client_id>
CODEF_CLIENT_SECRET=<발급받은 client_secret>
CODEF_ENV=demo
CODEF_PUBLIC_KEY=<PEM body 한 줄, 헤더/푸터 제외>
```

**중요**: 루트 `D:\TheGumaLab\.env`가 아닌 **서비스 로컬 .env 사용**. 과거
Gram에서 글로벌 .env로 리팩터 시도했으나 증권 삭제 시 CODEF 키도 루트에서
지워졌고, 서비스 로컬 파일은 보존됐기 때문. 관심사 분리 원칙상 CODEF 키는
GumaSpending 내부에 격리.

## 배포 (Phase 2 완료 시)

```bat
pull_update.bat GumaSpending
```

소스는 bind mount, watchfiles로 자동 재시작 예정. 초기 이미지 빌드:
```bash
ssh HomeServer "cd /d D:\TheGumaLab\GumaSpending && docker compose up --build -d"
```

`.github/workflows/deploy.yml`의 `PROJECTS` 목록에 `GumaSpending` 추가 필요
(Phase 2 시작 시 반영).

---

## 현재 구현 상태

### ✅ Phase 1a — OAuth 토큰 발급 검증
- `validate.py`
- `oauth.codef.io/oauth/token` → bearer token 200 OK
- 재현 가능: `python validate.py`

### ✅ Phase 1b — 카드사 등록 + 보유카드 검증
- `register_card.py` (대화형, TTY 필요)
- `create_account` (첫 카드) / `add_account` (추가 카드) 자동 분기
- [3/3]에서 `card-list` 호출로 등록 즉시 검증
- 결과: NH 5장 + 신한 3장 + KB 1장, 단일 connectedId에 묶임

### ✅ Phase 1c — 승인내역 수집
- `fetch_transactions.py` (비대화형, cron/Task Scheduler 가능)
- 카드사별 `card-list → per-card approval-list` 반복
- `memberStoreInfoType=1`로 가맹점 사업자번호/업종/주소 수집
- 결과 JSON: `transactions_{org}_{YYYYMMDD-YYYYMMDD}.json`
- 검증: 30일치 86건 / ₩2,999,394 수집 성공

### ⏳ Phase 2 — Flask 캘린더 대시보드
- 월 단위 캘린더 뷰 (날짜별 합계)
- 날짜 클릭 → 해당 일자 상세 거래 모달/패널
- 월 합계 헤더
- GumaStockReport와 동일 디자인 시스템 (다크 테마, emerald accent, Outfit 폰트, FontAwesome)

### ⏳ Phase 3 — 가시화 심화 (향후)
- 카테고리 자동 분류 (가맹점 업종 필드 활용)
- 카드별/월별 추이 그래프
- Nginx 리버스 프록시 + `gumaspending.guma3d.com` 연결
- 수집 스케줄러 (매일 자동 실행)

---

## 주의사항

- `connected_ids.json`, `transactions_*.json`, `spending.db`는 **민감 정보**
  (카드사 인증 토큰 + 개인 지출 이력) — 루트 `.gitignore`에 등록됨. 커밋 금지.
- CODEF API 예산(월 100콜) 주의. 각 실행이 card-list(1) + approval-list(N)
  소모. 현재 카드 9장 기준 매일 수집 시 월 ~300콜 → PRODUCT 플랜 승격 또는
  수집 주기 조정 필요.
- 카드 비밀번호(PIN) 필요한 카드사(현대/일부 KB)는 getpass 2차 입력 경로
  추가 필요.
- CODEF DEMO는 불안정할 수 있음. 실서비스로 쓰려면 PRODUCT 승격 권장.
- 본 문서의 organization 코드·에러 코드는 2026-04 기준. CODEF가 추가 코드나
  정책 변경할 수 있으니 재시도 시 확인.
