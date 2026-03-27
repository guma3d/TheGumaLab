# 📱 GumaPhoto 프론트엔드 UI 계층 구조도 (SPA Architecture)

GumaPhoto(`index.html`)의 프론트엔드는 모바일과 데스크톱 모두에서 부드럽게 렌더링되도록 **SPA (Single Page Application)** 탭 라우팅 체계 및 '독립적 Z-인덱스 모달(Modal)' 체계로 완전히 진화했습니다.

## 🌳 1. 전체 화면 DOM 트리 (Hierarchy Tree)

```text
📦 <body> (전체 화면의 컨테이너)
 ┃
 ┣━ 🗂️ [1] <div class="main-layout"> (메인 레이아웃 뼈대)
 ┃   ┃
 ┃   ┣━ 🟢 <header class="top-header"> (상단 내비게이션 바 / 스크롤 시 고정, z-index: 100)
 ┃   ┃   ┣━ 🔄 로고 영역 (<i class="fa-solid fa-camera-retro"></i> + Guma Family) - 클릭 시 앱 초기화
 ┃   ┃   ┗━ 🎛️ 우측 상단 버튼 (흰색 업로드 구름, 초록색 검색 버튼 등 네이티브 즉시 연동)
 ┃   ┃
 ┃   ┣━ ☁️ <div id="upload-progress-container"> (대량 업로드 진행률 바 / 팝업 애니메이션 처리)
 ┃   ┃
 ┃   ┗━ 🖼️ <main class="gallery-main"> (SPA 컨텐츠 렌더링 뷰)
 ┃       ┣━ 📸 <div id="home"> (메인 갤러리 및 검색 결과 탭)
 ┃       ┃   ┣━ 🏷️ <div id="timeline-header"> (10개 고정 출력 가로형 즐겨찾기 태그 슬라이더)
 ┃       ┃   ┣━ 🧱 <div id="gallery-grid"> (최신/태그 기반 기본 갤러리)
 ┃       ┃   ┗━ 🧱 <div id="search-grid"> (AI 자연어 검색 결과 Masonry 진열대)
 ┃       ┃
 ┃       ┣━ 🪄 <div id="feedback"> (프리미엄 자율 진화 학습 탭 - 글라스모피즘 1단 집중뷰 카드 레이아웃)
 ┃       ┃   ┣━ 🎯 <div id="fb-unknown-photo-container"> (미분류 사진 1장 집중 뷰 및 정답 폼)
 ┃       ┃   ┗━ 🔲 <div id="fb-temptest-results"> (임계치 85% 이상의 유사 사진 체크박스 그리드 레이어 + 원본 타겟 1장은 무조건 0순위로 강제 포함시켜 Send 블로킹 방어)
 ┃       ┗━ 📊 <div id="system"> (프리미엄 시스템 모니터링 탭 - 네온 카드 디자인의 AI/DB 헬스 체크)
 ┃           ┗━ 📈 <div class="stat-card"> (피드백 기록 열람 전용 Audit Stats Card 탑재 - 터치 시 100% 모달 연동)
 ┃
 ┣━ 🛠️ [2] <nav id="bottom-nav"> (모바일 전용 하단 내비게이션 바 / z-index: 150)
 ┃   ┣━ 스크롤 감지 반응형 (내리면 숨기고 올리면 등장)
 ┃   ┗━ 📱 Home, Feedback, System 3개 탭 브릿지 버튼
 ┃
 ┗━ ⬛ [3] 팝업 모달 레이어 (클릭 시 화면 전체를 덮는 오버레이 컴포넌트 / z-index: 1000+)
     ┣━ 🔍 <div id="search-modal"> (자연어 검색 전용 입력 팝업)
     ┣━ 📸 <div id="photo-modal"> (사진 상세 뷰 / 삭제 및 Blob 변환 네이티브 물리 공유 모달, Panzoom 핀치줌 엔진 적용)
     ┗━ 🚨 <div id="delete-confirm-modal"> (삭제 재확인 경고창 / z-index: 2000)
```

## 💡 2. 넥스트레벨 아키텍처 특장점 핵심 요약

### 1) SPA 라우팅 교대근무 (View Swapping)
과거 각종 모달로 띄우던 복잡한 도구들(피드백, 시스템 뷰)을 메인 `<main>` 내부의 독립된 `#home`, `#feedback`, `#system` 탭(Div)으로 이주시키고 부드러운 자바스크립트 View Router(`switchView`)를 도입했습니다. 탭을 누를 때마다 클래스 교체로 즉각적인 화면 전환 렌더링을 지원하며 React 수준의 부드러움을 완성했습니다. (관련 에셋은 전부 `frontend/` 경로로 서비스 됨)

### 2) 글라스모피즘 & 프리미엄 테마 (Premium SaaS UX)
투박하던 `System` 탭과 `Feedback` 탭을 고급 SaaS 대시보드 형식으로 전면 재설계했습니다. 반투명한 블러 컨테이너(`backdrop-filter: blur(20px)`), 두꺼운 그림자, 유기적인 애플리케이션 그라디언트 및 모서리 곡률(`border-radius`)을 아낌없이 사용하여 네이티브 모바일 애플리케이션 급의 시각적 안정감을 부여했습니다.

### 3) 가로형 10개 강제 보장 및 썸네일(WebP) 하이재킹 최적화
메인 화면 상단의 테마 슬라이더를 무작위로 호출하되, 결과가 미달되더라도 **최종 통과 슬라이더 10개가 무조건 화면을 꽉 채우도록 비동기 풀링(Promise.all) 크기를 증설**해 시각적 여백의 틈을 메웠습니다. 또한, 피드백 Scan 체크박스 화면 등 다량의 사진이 렌더링될 때 무지막지한 20MB 고해상도(`.jpg`) 다운로드를 우회하기 위해, JS 단에서 강제로 `_jpg.webp` 등 경량화 썸네일을 선 채점하도록 URL 하이재킹 + 실패 시 원본(Fallback)을 부르는 안전장치를 통해 UI 렌더링 한계를 돌파했습니다.

### 4) 완벽한 네이티브 모바일 애플리케이션 감성 (PWA + Panzoom + Blob Share)
PWA 스펙의 `apple-touch-icon.png` (다크모드 스파이키 조리개 에디션) 연동을 통해 홈 화면에 완벽한 사이즈로 인스톨을 지원합니다. 또한, `Panzoom.js`를 사용해 사파리 고유의 앱 튕김 현상 없는 핀치줌(두 손가락 확대)을 제공하며, 카카오톡 등에 사진을 공유할 때 의미 없는 링크(URL)가 전송되는 현상을 막기 위해 내부적으로 Fetch-Blob 컨버전을 거친 후 `navigator.share({files})` 규격으로 완벽한 고해상도 물리 원본 파일 다이렉트 전송을 달성했습니다.
