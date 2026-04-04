# 🚀 GumaPhoto Architecture & Technical Specifications

> **GumaPhoto**는 개인 사진 라이브러리를 위한 초경량, 초고속, AI 기반 지능형 갤러리 플랫폼입니다. PWA(Progressive Web App)를 기반으로 네이티브 모바일 앱과 같은 부드러운 사용성을 제공하며, 딥러닝 기반의 얼굴 인식 및 시맨틱 검색 기능을 내장하고 있습니다.

---

## 1. 🏗️ Core Architecture (기술 스택)

- **Backend**: FastAPI (Python), 비동기 처리 및 마이크로서비스 아키텍처
- **Database**: Qdrant (Vector DB - 시맨틱 검색 및 메타데이터 필터링), SQLite (메타데이터 및 로깅)
- **Background Task**: Celery, Redis (사진 인덱싱, 얼굴 학습, 데이터 캐시 베이킹)
- **Frontend**: Vanilla Javascript (ES6 Modules), CSS3, Service Worker (PWA)
- **Media Engine**: Pillow, Pillow-HEIF (iOS 고해상도 heic 파싱 및 썸네일 생성 웹 최적화)
- **Infrastructure**: Docker, Docker Compose (모든 서비스의 컨테이너화)

---

## 2. 🧠 AI & Computer Vision Pipeline (데이터 인덱싱)

사진이 업로드되거나 백그라운드 인덱서가 동작하면, 모든 사진은 다음의 딥러닝 파이프라인을 거칩니다.

1. **InsightFace 얼굴 인식 시스템**
   - `train_faces.py` 스크립트를 통해 사전에 등록된 Guma Family(성욱, 준우, 송이, 지우 등)의 얼굴 임베딩을 학습합니다.
   - 사진 내 인물들의 **BBox(Bounding Box)** 를 추출하여 저장하고, 피드백 시스템에서 크롭 된 인물 사진을 보여주는 데 활용됩니다.
   - 미확인 인물은 `Unknown` 또는 `인물식별불가` 상태로 격리됩니다.

2. **OpenAI CLIP (시맨틱/장면 검색)**
   - 사진의 분위기, 상황, 오브젝트 등을 벡터화하여 Qdrant DB에 `Payload`와 함께 저장합니다. (예: "밤에 와인을 마시는 장면")

3. **Geocoding & EXIF 파싱**
   - 사진의 GPS 위도/경도 데이터를 역지오코딩하여 주소(Location)로 변환합니다. 변환 결과는 `osm_cache.json`에 영구 저장되어 API 트래픽을 아낍니다.

---

## 3. ⚡ Ultra-Fast Caching System (Guma Family & 테마 엔진)

모바일 Safari 등 클라이언트의 브라우저 렌더링 한계를 극복하기 위해, **사전 베이킹(Pre-baking)** 기반의 고도화된 캐시 아키텍처를 운용합니다. 모든 무거운 작업은 매일 새벽 3시(또는 인덱싱 직후) Celery 워커가 백그라운드에서 처리합니다.

- **`timeline_cache.json` & `/api/family_tags`**
  - Guma Family의 주요 5개 태그(`recent`, `성욱`, `준우`, `지우`, `송이`)를 클라이언트에 전달하기 위해 백엔드에서 미리 인물 필터링(Solo Shot)을 마친 캐시 파일입니다.
  - 프론트엔드 최초 구동 시 단 **1번의 GET 요청** 만으로 모든 태그별 초기 로딩 20장을 즉시 메모리로 가져옵니다. 탭 간 이동 시 API 호출이 영구히 발생하지 않아 0.01초의 응답 속도를 보장합니다.

- **`image_meta_cache.json`**
  - HEIC 원본 사진을 매번 열어 `width`, `height`를 추출하는 극심한 병목(동기적 블로킹) 현상을 막기 위해 해상도 메타데이터만을 별도로 저장하는 캐시입니다. Qdrant 검색 시 원본 파일에 접근하지 않고 이 캐시와 병합하여 결과를 반환합니다.

- **`themes_cache.json`**
  - AI가 자동으로 묶은 "2024 겨울 일본여행" 등 9개의 앨범 컬렉션을 매일 새로 갱신하여 클라이언트에 1 뭉텅이로 전달합니다.

---

## 4. 🔄 Self-Healing Feedback System v2.0

AI 태깅의 오류를 유저가 직접 지속적으로 교정하고, Qdrant 벡터 검색 모델을 고도화하는 셀프 힐링(Self-Healing) 머신러닝 피드백 큐(Queue) 시스템입니다.

- **Disk-Persistent Queue (`feedback_queue.json`)**
  - 기존의 느린 실시간 Qdrant Full Scan 쿼리 연산을 제거하고, 새벽 시간에 비동기로 가장 교정이 필요한 피드백 클러스터(Top 300)를 디스크에 구워 놓습니다.
  - 3대 피드백 타입(`Time/Location`, `Person`, `Scene`)을 라운드로빈 방식으로 UI에 노출하여 지루함을 덜어줍니다.
- **BBox 유효성 검증**
  - 사람 피드백(`Person`)의 경우, 확실하게 크롭할 `face_bbox` 좌표가 DB에 존재하는 사진만 필터링하여 사용자에게 확대 UI를 제공합니다.

---

## 5. 🌍 3D Earth Hybrid Map (CesiumJS)

- **CesiumJS 3D 하이브리드 글로브**
  - 단순히 2D 점을 찍는 것이 아니라, 3D 위성 지도상에 보유한 모든 사진들의 위치정보(GeoJSON)를 Marker Clusterer(군집화) 방식으로 오버레이합니다.
  - API는 `GET /api/map/geojson`을 호출하여 캐시 된 공간 좌표 데이터를 가져옵니다. (Qdrant의 위치 Payload 사용)

---

## 6. 📱 Frontend Mobile Optimization (엔지니어링 코어)

- **Vanilla UI & PWA (Service Worker)**
  - 리액트 등 무거운 프레임워크를 사용하지 않고 순수 JS로 DOM을 직접 컨트롤합니다.
  - `sw.js` 메커니즘을 통해 정적 파일을 프론트엔드에 강력하게 캐싱합니다. (업데이트 시 버전 `v=상향` 적용 필수)
- **Infinite Lazy Loading**
  - 초과 페칭으로 인한 모바일 메모리 오버플로우 방지를 위해, `renderGallery` 는 항상 `t_limit = 20` 단위를 유지하여 화면 스크롤 지점을 계산한 뒤 부드럽게 추가 렌더링 됩니다.
- **Native iOS Feel**
  - 사진 롱-터치 시 iOS 고유의 선택 동작이 작동하지 못하도록 `user-select: none`, `-webkit-touch-callout: none` CSS 방어막을 쳐서 앱과 똑같은 햅틱 체감을 유지합니다.
