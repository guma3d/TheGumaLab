# GumaSpending

개인 카드 소비 추적 서비스. CODEF API로 카드사 거래내역을 자동 수집하고, 카테고리 분류·대시보드를 제공한다.

- **URL**: `gumaspending.guma3d.com` (Phase 2 이후)
- **데이터 소스**: CODEF API (데모 환경: 월 100콜)
- **대상 카드사**: 신한카드, 농협카드, KB국민카드

---

## 현재 상태: Phase 1 (CODEF 검증)

Flask/Docker 스택은 아직 도입하지 않았다. CODEF API 토큰 발급 → 커넥티드 아이디 생성 → 승인내역 조회가 실제로 동작하는지 단계별로 검증한다.

### 실행 방법 (HomeServer SSH)

```bash
# 1. 의존성 설치 (최초 1회)
cd /d D:\TheGumaLab\GumaSpending
pip install -r requirements.txt

# 2. .env 준비 (.env.example 복사 후 실제 값 입력 — git에 절대 커밋 금지)
copy .env.example .env
notepad .env

# 3. 검증 실행
python validate.py
```

### API 콜 예산

| Phase | 예상 콜수 |
|---|---|
| 1. 토큰 검증 | 1 |
| 1. 커넥티드 아이디 등록 (3 카드사) | 3 |
| 1. 승인내역 조회 (카드사당 1회) | 3 |
| **Phase 1 합계** | **~10** (월 100콜 중) |

---

## Phase 2 이후 로드맵

1. Flask + SQLite 기반 거래 저장소
2. 일 1회 배치 동기화 (APScheduler)
3. 카테고리 자동 분류 (키워드 → Gemini)
4. 대시보드 (월별/카테고리별/카드별)
5. Nginx 리버스 프록시 + WebAuthn 인증 연동
6. GitHub Actions 배포 룰 추가
