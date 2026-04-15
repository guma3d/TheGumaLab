# GumaSpending — CLAUDE.md

개인 카드/은행 소비 추적·시각화 서비스. CODEF Open API로 승인내역·거래내역을 자동 수집하고 월 단위 캘린더 대시보드로 지출을 가시화한다.

- **URL**: gumaspending.guma3d.com (예정)
- **로컬 포트**: 8060
- **현재 지원**: NH카드(0304) · 신한카드(0306) · KB카드(0301) · 농협은행(0011)

> **전역 규칙**: 워크플로우·커밋·배포는 루트 `CLAUDE.md` 준수. 환경변수는 서비스 로컬 `GumaSpending/.env` 사용 (글로벌 `.env` 금지 — 증권 삭제 시 CODEF 키 소실 사고 이력).
> **CODEF 심층 노트**: [docs/codef-integration.md](docs/codef-integration.md) — organization 코드, 에러 코드, 카드사/은행별 특이사항, 증권 재시도 전략, 이중 집계 방지 로직, 실패 사례까지 전부 정리. 신규 카드사/은행 추가 또는 에러 디버깅 시 먼저 참고.

---

## 기술 스택 & 컨테이너

- **Backend**: Python Flask (GumaStockReport와 동일 패턴) + watchfiles 자동 재시작
- **DB**: SQLite (`spending.db`) — 단일 파일, 백업 간편
- **수집**: `easycodefpy` SDK + CODEF (`development.codef.io` DEMO)
- **Frontend**: Vanilla JS + 다크 테마 (`#050505` + emerald `#10b981`) + PWA
- **컨테이너**: `gumaspending_web` (8060). Redis 불필요.

---

## 디렉토리 구조

```
GumaSpending/
├── CLAUDE.md                      # 이 파일 — 핵심 규칙만
├── README.md
├── docs/codef-integration.md      # CODEF 심층 노트 (상세)
├── .env                           # CODEF 크레덴셜 (gitignored)
├── requirements.txt
│
├── validate.py                    # Phase 1a: OAuth 토큰 검증
├── register_card.py               # Phase 1b: 카드사 등록 → connectedId
├── register_bank.py               # Phase 1b: 은행 등록 (BK)
├── fetch_transactions.py          # Phase 1c: 카드 approval-list 수집
├── fetch_bank_transactions.py     # Phase 1c: 은행 transaction-list 수집
│
├── app.py                         # Phase 2: Flask 대시보드
├── templates/index.html
├── static/                        # manifest, icons
├── Dockerfile
├── docker-compose.yml
│
├── connected_ids.json             # (gitignored) 카드/은행 → connectedId
├── transactions_{org}_*.json      # (gitignored) 기간별 raw
└── spending.db                    # (gitignored) 정규화된 DB
```

---

## 데이터 흐름

```
[최초 1회]
  register_card.py / register_bank.py (대화형)
    → CODEF create_account / add_account
    → connected_ids.json 저장

[정기 수집]
  fetch_transactions.py / fetch_bank_transactions.py (비대화형, cron)
    → connected_ids.json 로딩
    → 카드: card-list → per-card approval-list
    → 은행: account-list → per-account transaction-list
    → transactions_{org}_{YYYYMMDD-YYYYMMDD}.json 저장

[대시보드]
  Flask app.py
    → transactions_*.json을 spending.db로 정규화 (idempotent upsert)
    → 은행 출금 중 BANK_DEDUP_PATTERNS 매칭 건은 skip (카드대금 이중 집계 방지)
    → 캘린더 뷰 / 날짜별 상세 / 월 합계 API
```

---

## 핵심 운영 규칙

**DEMO 환경의 businessType 제약**
- 카드(`CD`)·은행(`BK`): 실계정 수용 → 실 데이터 반환 ✅
- 증권(`ST`): 실계정 거부 (`CF-04000/CF-00007`) ❌ — 재시도 시 PRODUCT 승격 필요
- 상세: [docs/codef-integration.md](docs/codef-integration.md) "businessType 별 동작 차이"

**민감 파일 (gitignored, SCP로만 동기화)**
- `.env`, `connected_ids.json`, `transactions_*.json`, `spending.db`
- 실수 커밋 시 즉시 CODEF 키 rotate + 사용자 보고

**API 예산**
- DEMO 월 100콜 (불확실). 결과 5,000건 단위 1콜 과금 → 개인 사용은 사실상 1콜/수집.
- 현재 카드 9장 + 은행 계좌 2개 기준 매일 수집 시 월 ~300콜 예상 → 수집 주기 조정 또는 PRODUCT 승격 검토.

**카드사별 필수 파라미터 (빠뜨리면 실패)**
- NH / 신한: `approval-list`에 `cardNo` 필수 → `card-list` 선행 호출 후 카드별 반복 (`fetch_transactions.py`에 구현됨)
- 신한Pay머니 가상카드: `CF-13101` 반환 → `SKIPPABLE_CODES`로 skip
- KB 일부 카드: `CF-12108` (카드소지확인 리다이렉트) → `cardNo` + `cardPassword`(PIN 앞 2자리) 추가 필요. 쿠팡와우는 불필요.
- 현대(미검증): `cardNo` + `cardPassword`(4자리 전체) 필수. 3회 오류 시 `CF-12834` 잠김.
- 전체 매트릭스: [docs/codef-integration.md](docs/codef-integration.md) "카드사별 실전 특이사항" + "에러 코드 요약"

**은행 이중 집계 방지**
- `BANK_DEDUP_PATTERNS = ["카드대금", "카드결제", "신용카드", "체크카드", "카드자동"]`
- `resAccountDesc1~4` 조합에 매칭되는 출금 건은 SKIP (카드 approval 쪽이 더 정밀하므로 그쪽을 신뢰)

---

## 환경변수

`GumaSpending/.env` (gitignored):

```
CODEF_CLIENT_ID=<client_id>
CODEF_CLIENT_SECRET=<client_secret>
CODEF_ENV=demo
CODEF_PUBLIC_KEY=<PEM body 한 줄, 헤더/푸터 제외>
```

---

## 현재 구현 상태

### ✅ Phase 1a — OAuth 토큰 검증
`validate.py` — `oauth.codef.io/oauth/token` 200 OK 확인.

### ✅ Phase 1b — 계정 등록
- `register_card.py` (대화형): `create_account` (첫 카드) / `add_account` (추가) 자동 분기, `card-list`로 즉시 검증
- `register_bank.py`: 농협은행 2개 계좌 등록
- 결과: NH 5장 + 신한 3장 + KB 1장 + 농협은행 2계좌, **단일 connectedId** `9LlJh6SrkiSaR.5P9yJmb3`에 묶임

### ✅ Phase 1c — 거래내역 수집
- `fetch_transactions.py` (비대화형, cron 가능): 카드사별 `card-list → per-card approval-list` 루프, `memberStoreInfoType=1`로 가맹점 사업자번호/업종/주소 수집
- `fetch_bank_transactions.py`: 농협은행 `transaction-list`, 출금/입금 분리
- 검증: 30일치 카드 86건 / ₩2,999,394 + 은행 거래내역 수집 성공

### ⏳ Phase 2 — Flask 캘린더 대시보드 (진행 중)
- `app.py`, `templates/index.html`, `Dockerfile`, `docker-compose.yml` 스캐폴딩 완료
- 월 캘린더 / 날짜별 상세 / 월 합계 API
- GumaStockReport와 동일 디자인 시스템 (다크 테마, emerald accent, Outfit 폰트, FontAwesome)

### ⏳ Phase 3 — 가시화 심화 (향후)
- 카테고리 자동 분류 (가맹점 업종 필드 + 키워드 → Gemini)
- 카드별/월별 추이 그래프
- Nginx 리버스 프록시 + WebAuthn 인증 연동
- 수집 스케줄러 (매일 자동)

---

## 배포

```bat
pull_update.bat GumaSpending
```

소스는 bind mount + watchfiles 자동 재시작. 초기 이미지 빌드:
```bash
ssh HomeServer "cd /d D:\TheGumaLab\GumaSpending && docker compose up --build -d"
```

`.github/workflows/deploy.yml`의 `PROJECTS` 목록에 `GumaSpending` 등록 필요 (Phase 2 완성 시 반영).
