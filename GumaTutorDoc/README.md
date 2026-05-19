# GumaTutorDoc

주제를 입력하면 학습자료와 간단한 퀴즈를 HTML로 생성해 저장하는 로컬 웹서비스입니다.

기존 파충류 PDF 생성 스크립트는 `tools/`에 보존되어 있고, 새 기본 흐름은 `Server.py`가 담당합니다.

## 웹서비스 실행

```powershell
cd C:\Users\guma3d\Documents\TheGumaLab\GumaTutorDoc
python -m pip install -r requirements.txt
python .\Server.py
```

브라우저에서 `http://localhost:5000`을 엽니다.

## 사용 흐름

1. 주제를 입력합니다. 예: `화산`, `세종대왕`, `분수의 나눗셈`
2. 대상 수준과 퀴즈 수를 선택합니다.
3. 생성 버튼을 누르면 작업이 큐에 등록됩니다.
4. 완료된 문서는 `outputs/html/` 아래에 HTML과 JSON으로 저장됩니다.
5. 메인 화면의 저장 문서 목록에서 언제든지 다시 열 수 있습니다.

## AI 생성 설정

상위 폴더 또는 이 폴더의 `.env`에 `GEMINI_API_KEY`가 있으면 Gemini로 학습자료를 생성합니다.

선택 설정:

```env
GUMATUTORDOC_MODEL=gemini-3.1-flash-lite-preview
PORT=5000
```

`GEMINI_API_KEY`가 없으면 사실 설명을 만들지 않고, 저장/보기 흐름을 확인하는 기본 템플릿 HTML만 생성합니다.

## Docker 실행

```powershell
cd C:\Users\guma3d\Documents\TheGumaLab\GumaTutorDoc
docker compose up -d --build
```

기본 포트는 `8084:5000`입니다.
홈서버 컨테이너 이름은 `gumatutordoc_app`이며 `restart: unless-stopped`로 등록됩니다.
Nginx 라우팅 대상은 `https://gumatutordoc.guma3d.com/`입니다.

## 주요 파일

- `Server.py`: Flask 서버, 작업 큐, AI 생성, HTML 저장
- `index.html`: 입력/목록 UI
- `script.js`: 작업 요청, 상태 폴링, 문서 목록 갱신
- `style.css`: 웹 UI 스타일
- `outputs/html/`: 생성된 HTML 저장 위치
- `data/task_status.json`: 저장 문서와 작업 상태 인덱스

## 기존 파충류 PDF 생성

```powershell
python .\tools\generate_reptile_pdfs_detailed.py
```

최종 검수 PDF는 `outputs/pdfs/`에 보관되어 있습니다.
