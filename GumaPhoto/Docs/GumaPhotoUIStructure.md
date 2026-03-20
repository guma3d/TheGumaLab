# 📱 GumaPhoto 프론트엔드 UI 계층 구조도 (SPA Architecture)

GumaPhoto(`index.html`)의 프론트엔드는 모바일과 데스크톱 모두에서 부드럽게 렌더링되도록 **SPA (Single Page Application)** 탭 라우팅 체계 및 '독립적 Z-인덱스 모달(Modal)' 체계로 완전히 진화했습니다.

## 🌳 1. 전체 화면 DOM 트리 (Hierarchy Tree)

```text
📦 <body> (전체 화면의 컨테이너)
 ┃
 ┣━ 🗂️ [1] <div class="main-layout"> (메인 레이아웃 뼈대)
 ┃   ┃
 ┃   ┣━ 🟢 <header class="top-header"> (상단 내비게이션 바 / 스크롤 시 고정, z-index: 100)
 ┃   ┃   ┣━ 🔄 로고 영역 (<i class="fa-solid fa-camera-retro"></i> + Guma Family) - 클릭 시 앱 초기화(하드 리로드)
 ┃   ┃   ┗━ 🎛️ 우측 상단 버튼 (흰색 업로드 구름, 초록색 AI 검색 돋보기 등 네이티브 즉시 연동 버튼)
 ┃   ┃
 ┃   ┣━ ☁️ <div id="upload-progress-container"> (대량 업로드 진행률 바 / 팝업 애니메이션 처리)
 ┃   ┃
 ┃   ┗━ 🖼️ <main class="gallery-main"> (SPA 컨텐츠 렌더링 뷰)
 ┃       ┣━ 📸 <div id="home"> (메인 갤러리 및 검색 결과 탭)
 ┃       ┃   ┣━ 🏷️ <div id="timeline-header"> (상단 가로형 즐겨찾기 태그 슬라이더)
 ┃       ┃   ┣━ 🧱 <div id="gallery-grid"> (최신/태그 기반 기본 갤러리)
 ┃       ┃   ┗━ 🧱 <div id="search-grid"> (AI 자연어 검색 결과 Masonry 진열대)
 ┃       ┃
 ┃       ┣━ 🪄 <div id="feedback"> (프리미엄 자율 진화 학습 탭 - 글라스모피즘 카드 레이아웃)
 ┃       ┃   ┣━ 🎯 <div id="fb-unknown-photo-container"> (미분류 사진 1장 집중 뷰 및 정답 폼)
 ┃       ┃   ┗━ 🔲 <div id="fb-temptest-results"> (임계치 85% 이상의 유사 사진 체크박스 그리드 선택 레이어)
 ┃       ┗━ 📊 <div id="system"> (프리미엄 시스템 모니터링 탭 - 네온 카드 디자인의 AI/DB 헬스 체크)
 ┃
 ┣━ 🛠️ [2] <nav id="bottom-nav"> (모바일 전용 하단 내비게이션 바 / z-index: 150)
 ┃   ┣━ 스크롤 감지 반응형 (내리면 숨기고 올리면 등장)
 ┃   ┗━ 📱 Home, Feedback, System 3개 탭 브릿지 버튼
 ┃
 ┗━ ⬛ [3] 팝업 모달 레이어 (클릭 시 화면 전체를 덮는 오버레이 컴포넌트 / z-index: 1000+)
     ┣━ 🔍 <div id="search-modal"> (자연어 검색 전용 입력 팝업)
     ┣━ 📸 <div id="photo-modal"> (사진 상세 뷰 / 다운로드, 삭제 기능 통합 모달)
     ┣━ 📱 <div id="ios-share-sheet"> (iOS 사파리 스타일의 터치 최적화 네이티브 액션 시트 - 공유/저장/복사)
     ┗━ 🚨 <div id="delete-confirm-modal"> (삭제 재확인 경고창 / z-index: 2000)
```

## 💡 2. 넥스트레벨 아키텍처 특장점 핵심 요약

### 1) SPA 라우팅 교대근무 (View Swapping)
과거 각종 모달로 띄우던 복잡한 도구들(피드백, 시스템 뷰)을 메인 `<main>` 내부의 독립된 `#home`, `#feedback`, `#system` 탭(Div)으로 이주시키고 부드러운 자바스크립트 View Router(`switchView`)를 도입했습니다. 어떤 탭을 누르거나 검색을 실행하더라도, 즉각적으로 기존 탭이 `.hidden` 처리되며 React 수준의 부드러운 페이지 전환 창을 완성했습니다.

### 2) 글라스모피즘 & 프리미엄 테마 (Premium SaaS UX)
투박하던 텍스트 위주의 `System` 탭과 `Feedback` 탭을 고급 SaaS 대시보드 형식으로 전면 재설계했습니다. 반투명한 블러 컨테이너(`backdrop-filter: blur(20px)`), 두꺼운 그림자, 유기적인 애플리케이션 그라디언트 및 모서리 곡률(`border-radius`)을 아낌없이 사용하여 네이티브 모바일 애플리케이션 급의 시각적 즐거움과 안정감을 부여했습니다.

### 3) 네이티브 액션 융합 (Native Function Injection)
상단 로고와 하단 Home 탭 터치 한 번으로 복잡한 캐시를 파괴하고 가장 깨끗한 초기 상태(`location.reload()`)로 돌아갈 수 있으며, `Upload` 트리거 버튼을 누르는 순간 중간 탭 화면 없이 기기 "사진 보관함(Native Upload Picker)"이 즉시 로드 및 자동 전송되는 원스텝 숏컷 기술까지 통합해 두었습니다. 또한 피드백 탭에서는 검색(Scan by Similarity) 후 사용자가 직접 유사 사진들을 `체크박스`로 취사선택할 수 있는 반응형 큐레이션 레이어(`#fb-temptest-results`)가 새롭게 융합되었습니다.
