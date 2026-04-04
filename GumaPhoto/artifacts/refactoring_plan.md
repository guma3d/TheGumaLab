# `script_app_v2.js` (2,241 lines) 리팩토링 및 모듈화 계획서

현재 `script_app_v2.js`는 하나의 파일에 수많은 기능(상태 관리, API 통신, DOM 조작, 컴포넌트 이벤트)이 혼재된 **갓 클래스(God Class)** 성격을 띠고 있습니다. 유지 보수의 한계점을 극복하고 코드 생산성을 높이기 위해 **Vanilla JS (ES6 Module)** 기반의 구조적 리팩토링을 제안합니다.

---

## 1. 리팩토링 전략의 핵심 목표

1. **관심사의 분리 (Separation of Concerns):** UI를 그리는 로직(View), 데이터를 가져오는 로직(Network), 애플리케이션의 상태(State)를 분리합니다.
2. **ES6 모듈화 (`import / export`):** HTML에 `<script type="module" src="main.js">`를 도입하여, 기능별로 쪼개진 JS 파일들을 계층적으로 불러옵니다.
3. **이벤트 위임과 상태 단방향 흐름 제어:** 무분별한 전역 변수를 없애고, 상태 변화에 따라 UI만 업데이트 되도록 구조를 단방향으로 맞춥니다.

---

## 2. 모듈 분리 구조 (Directory Tree)

거대한 코드를 아래와 같이 4가지 계층으로 쪼개어 `frontend/` 폴더 내에 배치합니다.

```text
frontend/
 │
 ├── main.js                  # [Entry Point] 앱 초기화 및 각 핵심 모듈들의 조율 역할
 │
 ├── state/                   # [상태 관리 계층]
 │    ├── store.js            # 전역 상태 (현재 쿼리, 검색 필터, 선택된 인물, 갤러리 배열 등)
 │
 ├── api/                     # [네트워크 계층]
 │    ├── endpoints.js        # API 주소 상수 모음
 │    ├── fetcher.js          # API 호출 함수들 (search, get_filters, submit_feedback 등)
 │
 ├── components/              # [UI 컴포넌트 & DOM 조작 계층]
 │    ├── gallery.js          # 메이슨리(Masonry) 레이아웃, 무한 스크롤, 렌더링 로직
 │    ├── searchBar.js        # 검색창, 헤더 애니메이션, 입력 폼 제어
 │    ├── filterSidebar.js    # 사이드바 패널, Date/Location/이름 필터링 선택 로직
 │    ├── feedbackModal.js    # 얼굴 피드백 팝업, 캔버스 크롭 로직, 정답 제출
 │    ├── lightbox.js         # 이미지 클릭 시 전체 화면 확대 및 캐러셀 로직
 │    └── themeCarousel.js    # Guma Family 타임라인 및 랜덤 테마 레이아웃 제어
 │
 └── utils/                   # [유틸리티 계층]
      ├── helpers.js          # 날짜 포맷팅, 디바운스(Debounce), 모바일 감지 함수 등
      └── dom.js              # 돔 생성(createElement), 뱃지(Badge) 생성 등 헬퍼
```

---

## 3. 단계별 마이그레이션(Migration) 실행 계획

### Phase 1: 기반 인프라 마련 (Risk: Low)
- 현재 `script_app_v2.js` 내부에서 사용 중인 수많은 순수 유틸리티 함수(예: 디바운싱, 시간 포맷 변환, DOM 헬퍼)들을 `utils/helpers.js`로 분리합니다.
- `index.html`의 스크립트 로드 방식을 `<script type="module" src="frontend/main.js"></script>`로 변경하여 모듈 환경을 준비합니다. (기존 코드가 동작하도록 과도기를 거칩니다).

### Phase 2: 상태 관리와 네트워크 계층 독립 (Risk: Medium)
- 파일 내에 흩어져 있는 전역 변수들(`currentPage`, `currentQuery`, `advancedStatsData`, `selectedFeedbackTarget` 등)을 `state/store.js`의 객체 형태로 캡슐화합니다.
- 백엔드와 통신하는 `fetch()` 함수 호출 부분들을 전부 `api/fetcher.js`로 분리하여, UI 로직과 통신 로직이 섞여 있는 현상을 제거합니다.

### Phase 3: UI 컴포넌트 쪼개기 (Risk: High)
- 가장 거대한 파편인 프론트엔드 기능을 컴포넌트별로 파일로 나눕니다.
  - **피드백 팝업:** 얼굴 크롭 캔버스와 오타 검증 로직은 뚝 떼어내서 `feedbackModal.js`로 옮깁니다. (약 400줄 절감)
  - **검색 및 필터링:** 필터 드롭다운과 검색바 애니메이션 관련 코드를 분리합니다. (약 300줄 절감)
  - **메이슨리 갤러리:** HTML 조립 엔진 로직을 `gallery.js`로 분할합니다. (약 500줄 절감)

### Phase 4: 메인 오케스트레이터 구성 및 구버전 삭제 (Risk: Medium)
- 가벼워진 `main.js` 파일이 각 컴포넌트들을 Import한 뒤, 초기 이벤트 리스너 내부에서 조립하여 앱을 구동하게 합니다.
- 기존의 레거시 `script_app_v2.js` 파일을 시스템에서 완전히 소거합니다.

---

## 4. 리팩토링 후 기대효과

- **디버깅 속도 비약적 향상:** "얼굴 크롭이 안돼!" -> 해당 로직이 2천 줄짜리 코드 어딘가에 있는 게 아니라, 직관적으로 `components/feedbackModal.js`만 켜서 수정하면 됩니다.
- **성능 (코드 스플리팅):** 당장은 Vanilla JS 모듈 매핑이지만, 향후 필요할 때 로딩을 최적화하기 좋습니다.
- **가독성:** 비즈니스 시나리오(API 통신)와 디자인 랜더링(DOM 접근)이 깨끗하게 분리됩니다.
