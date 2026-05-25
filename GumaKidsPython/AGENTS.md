# AGENTS.md - GumaKidsPython 작업 지침

이 문서는 Codex가 `GumaKidsPython` 프로젝트를 이어서 작업할 때 가장 먼저 확인할 단일 기준 문서다.
기존에 여러 문서로 나뉘어 있던 핵심 내용을 이 파일로 통합한다.

## 프로젝트 목적

- 초등학교 3학년 아이가 파이썬을 "문법 공부"가 아니라 "게임 업그레이드 놀이"로 배우게 한다.
- 전체 과정은 48챕터, 4개 시즌, 시즌당 12챕터다.
- 아이는 게임 전체를 처음부터 만들지 않는다.
- 완성된 게임에서 `upgrade_zone.py`의 작은 코드만 바꾸고, 결과를 바로 확인한다.
- 교재와 앱에서는 "수정"보다 "업그레이드"라는 표현을 사용한다.

## 현재 상태

- 기준 작성일: 2026-05-26
- 프로젝트 위치: `C:\Users\guma3d\Documents\TheGumaLab\GumaKidsPython`
- 48챕터 전체 커리큘럼 설계 완료
- 4개 시즌 게임 기획 완료
- 시즌 1~4 `tkinter` 게임 구현 완료
- 시즌 1~4 웹앱 1차 구현 완료
- Flask 서버 저장 API 1차 구현 완료
- `Guma Python Lab` 3분할 학습 앱 프로토타입 구현 완료
- 챕터 1 강의자료 PDF/PNG 8페이지 샘플 제작 완료
- 다음 큰 작업: 챕터 1 앱 수업 흐름 검증, 챕터 2~3 강의자료 제작

## 폴더 구조

```text
GumaKidsPython/
  AGENTS.md
  COURSE_PLAN.md
  app/
    guma_python_lab.py
    README.md
  Docs/
    season_01/
      chapter_01.pdf
      chapter_01_p01.png ... chapter_01_p08.png
  games/
    season_01_treasure_score/
    season_02_dungeon_choice/
    season_03_monster_battle/
    season_04_mini_adventure/
  tools/
    generate_chapter_01_pdf.py
  web/
    index.html
    style.css
    app.js
  server.py
  docker-compose.yml
```

## 시즌 구성

| 시즌 | 챕터 | 게임 | 주요 학습 |
|---|---:|---|---|
| 시즌 1 | 1~12 | 보물 점수 게임 | 출력, 문자열, 숫자, 변수, 계산 |
| 시즌 2 | 13~24 | 던전 선택 게임 | 입력, 조건문, 비교, 논리 연산 |
| 시즌 3 | 25~36 | 몬스터 배틀 게임 | 반복문, 리스트, 딕셔너리 |
| 시즌 4 | 37~48 | 미니 어드벤처 게임 | 함수, 랜덤, 시간, 파일, 예외, 종합 |

## 공통 게임 구조

각 시즌 폴더는 같은 구조를 가진다.

```text
main.py                  # 게임 실행 시작점
upgrade_zone.py          # 아이가 챕터별로 바꾸는 코드
engine.py                # 숨겨진 게임 엔진
upgrade_zone_original.py # 복구용 원본
README.md                # 시즌별 실행 설명
```

작업 원칙:

- `upgrade_zone.py`는 아이가 직접 보는 파일이므로 단순하고 읽기 쉽게 유지한다.
- `engine.py`는 아이가 보지 않는 숨겨진 엔진이다. 꼭 필요한 경우에만 수정한다.
- `upgrade_zone_original.py`는 부모용 복구 파일이다.
- 한 챕터에서 새 개념은 하나만 다룬다.
- 초반 챕터는 1줄 수정, 중반은 2~5줄 수정, 후반은 작은 기능 작성 수준을 넘지 않게 한다.
- 게임 기능을 추가해도 설치 부담을 만들지 않는다. 기본은 표준 라이브러리와 `tkinter`다.

## Guma Python Lab 앱

실행 파일: `app/guma_python_lab.py`

현재 앱 구성:

- 왼쪽 위: 가로형 강의자료 PNG/PDF 미리보기
- 왼쪽 아래: 시즌 1 보물 점수 게임 화면
- 오른쪽: 파이썬 코드 편집 화면
- 화면 비율: 좌우 50:50, 왼쪽 상하 50:50 고정
- UI 테마: 앱 크롬과 코드 편집기는 Dark 테마
- 강의자료와 게임 화면은 밝고 아기자기한 색감 유지
- 챕터 선택: 작은 드롭다운
- 코드 저장 위치: `user_saves/season_01/chapter_XX/upgrade_zone.py`
- `Play`를 누르면 현재 챕터 코드가 저장되고 게임화면에 즉시 반영

앱은 `tkinter`와 `Pillow`를 사용한다.

## 교재/PDF 원칙

- PDF는 공부 교재보다 게임 퀘스트북처럼 느껴지게 만든다.
- 앱용 강의자료는 가로형 PDF/PNG 페이지를 기준으로 제작한다.
- 각 챕터 강의자료는 5페이지 안팎을 기본으로 하며 최대 10페이지를 넘기지 않는다.
- 챕터 1처럼 개념 설명이 필요한 경우 8페이지 구성까지 늘릴 수 있다.
- 따라 치는 코드는 가능한 1~3줄 수준으로 유지한다.
- 실제 게임 화면과 오늘 바꿀 코드가 명확히 연결되어야 한다.
- `engine.py` 설명을 길게 넣지 않는다.
- 퀴즈는 초등 3학년이 말로 답할 수 있는 수준으로 만든다.
- 정답은 퀴즈 페이지에 바로 노출하지 않고 마지막 정답/해설 페이지에 둔다.

기본 챕터 흐름:

1. 표지: 오늘의 게임, 오늘의 업그레이드
2. 오늘의 코드
3. 코드가 한 일 또는 파이썬 개념
4. 바꿔보기 또는 Play 해보기
5. 업그레이드 미션과 퀴즈
6. 정답과 짧은 해설

## 실행 명령

프로젝트 루트:

```powershell
cd C:\Users\guma3d\Documents\TheGumaLab\GumaKidsPython
```

Guma Python Lab 실행:

```powershell
python .\app\guma_python_lab.py
```

챕터 1 강의자료 재생성:

```powershell
python .\tools\generate_chapter_01_pdf.py
```

웹앱 로컬 실행:

```powershell
python .\server.py
```

시즌 게임 실행 예시:

```powershell
cd C:\Users\guma3d\Documents\TheGumaLab\GumaKidsPython\games\season_01_treasure_score
python .\main.py
```

게임 창 없이 빠른 확인:

```powershell
python .\main.py --check
```

## 검증 명령

앱과 강의자료 생성 스크립트:

```powershell
python -m py_compile .\app\guma_python_lab.py .\tools\generate_chapter_01_pdf.py
```

시즌 게임 폴더에서:

```powershell
python -m py_compile .\main.py .\engine.py .\upgrade_zone.py .\upgrade_zone_original.py
python .\main.py --check
```

Windows 터미널에서 한글 출력이 `UnicodeEncodeError`를 낼 수 있다. 이 경우 코드 문제로 단정하지 말고 UTF-8 출력을 지정해서 다시 확인한다.

```powershell
$env:PYTHONIOENCODING='utf-8'
python .\main.py --check
```

최근 검증 상태:

- 2026-05-26 기준 앱과 강의자료 생성 스크립트 `py_compile` 통과
- 챕터 1 PDF/PNG 8페이지 재생성 확인

## 웹앱 메모

- `server.py` Flask 서버 구현 완료
- `web/` 아래 시즌 1~4 웹앱 1차 구현 완료
- 저장 API: `GET /api/save?profile=default`, `POST /api/save`
- 저장 파일 위치: `data/saves/<profile>.json`
- 배포 주소: `https://gumakidspython.guma3d.com`
- 홈서버 Docker 포트: `5057:5000`

## 다음 작업

1. 챕터 1을 앱에서 실제 수업처럼 실행해 화면, 문장 길이, 버튼 흐름을 확인한다.
2. 챕터 2~3 PDF/PNG 샘플을 제작한다.
3. PDF 스타일과 난이도를 확정한다.
4. 시즌 1 전체 12챕터 PDF로 확장한다.
5. 시즌 2~4 PDF 제작으로 확장한다.

## 주의 사항

- 아이가 실수해도 다시 실행하면 된다는 느낌을 유지한다.
- 에러 메시지나 복구 설명은 부모가 따라 할 수 있게 짧고 명확하게 작성한다.
- 게임의 난이도보다 학습 개념의 명확성을 우선한다.
- 새 산출물을 만들면 이 `AGENTS.md`의 현재 상태와 다음 작업도 함께 업데이트한다.
- 커밋이나 압축본에는 실행에 불필요한 `__pycache__` 폴더를 포함하지 않는다.
