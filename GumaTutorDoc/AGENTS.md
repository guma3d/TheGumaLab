# GumaTutorDoc 작업 지침

## 프로젝트 목적

- `GumaTutorDoc`은 주제를 입력하면 학습자료와 간단한 퀴즈를 HTML로 생성해 저장하는 Flask 웹서비스다.
- 현재 기본 흐름은 `주제 입력 -> 학습자료/퀴즈 생성 -> HTML 저장/열람`이다.
- 기존 파충류 PDF 보고서 생성 기능은 보존 대상이며, 새 웹서비스 흐름과 분리해서 다룬다.

## 주요 파일과 역할

- `Server.py`: Flask 서버, 작업 큐, Gemini 생성, Wikimedia Commons 이미지 검색, HTML/JSON 저장.
- `index.html`: 입력 화면과 저장 문서 목록 UI.
- `script.js`: 작업 생성 요청, 상태 폴링, 목록 갱신, 보기/다운로드/삭제 동작.
- `style.css`: 웹 UI 스타일.
- `requirements.txt`: Python 실행 의존성.
- `docker-compose.yml`: 홈서버 Docker 서비스 정의.
- `tools/`: 기존 파충류 PDF 생성 스크립트.
- `outputs/html/`: 웹서비스가 생성한 HTML/JSON 저장 위치.
- `outputs/pdfs/`: 검수 완료된 파충류 PDF 최종본 보관 위치.
- `data/task_status.json`: 작업 상태와 저장 문서 인덱스. 런타임 산출물이므로 필요 이상으로 직접 수정하지 않는다.

## 실행 및 배포 메모

- 로컬 실행:

```powershell
python -m pip install -r requirements.txt
python .\Server.py
```

- 기본 로컬 URL은 `http://localhost:5000`이다.
- Docker 기본 포트 매핑은 `8084:5000`이다.
- 홈서버 컨테이너 이름은 `gumatutordoc_app`이다.
- 공개 URL은 `https://gumatutordoc.guma3d.com/`로 취급한다.
- Docker/컨테이너 상태 확인과 배포 작업은 로컬이 아니라 홈서버에서 수행한다.

## AI 생성 동작

- 상위 폴더 또는 프로젝트 폴더의 `.env`에 `GEMINI_API_KEY`가 있으면 Gemini로 실제 학습자료를 생성한다.
- `GEMINI_API_KEY`가 없으면 사실 설명을 생성하지 않고 기본 템플릿 HTML만 만든다.
- 선택 환경변수:

```env
GUMATUTORDOC_MODEL=gemini-3.5-flash
PORT=5000
```

- API 키, 토큰, `.env` 내용은 절대 출력하거나 커밋하지 않는다.

## 기존 파충류 PDF 자산

- 원래 목적은 초등학교 3학년 발표용 가족 활동 자료로, 신기한 파충류 14종의 TV 표시용 가로형 PDF 보고서를 만드는 것이었다.
- 최종 PDF 14개는 `outputs/pdfs/`에 보관되어 있으며, 각 PDF는 7페이지 구성이다.
- 재생성 스크립트는 아래 명령으로 실행한다.

```powershell
python .\tools\generate_reptile_pdfs_detailed.py
```

- `assets/curated_overrides/`의 직접 고른 이미지는 품질 검수된 핵심 자료이므로 임의 교체하지 않는다.
- 특히 뿔도마뱀, 바실리스크도마뱀, 아르마딜로도마뱀, 마타마타거북, 가시악마도마뱀, 팬케이크거북, 바다뱀 이미지는 고정 이미지로 취급한다.

## 작업 원칙

- 웹서비스 개선 작업과 기존 PDF 생성 스크립트 작업을 구분해서 변경한다.
- 생성 산출물(`outputs/html/`, `data/task_status.json`)은 사용자가 요청하지 않는 한 커밋 대상으로 보지 않는다.
- 검수 완료 산출물(`outputs/pdfs/`, `outputs/qa/`, `assets/curated_overrides/`)은 삭제하거나 재생성본으로 덮어쓰기 전에 사용자 확인을 받는다.
- HTML 문서 출력은 어린이가 읽기 쉬운 한국어, 짧은 문장, 명확한 퀴즈 해설을 우선한다.
- UI는 입력, 진행 상태, 저장 문서 목록을 빠르게 확인할 수 있는 실용적인 화면을 유지한다.
- 파괴적 작업, 비밀값 변경, 컨테이너/볼륨 삭제, DB/상태 파일 초기화는 사용자 확인 없이 진행하지 않는다.
