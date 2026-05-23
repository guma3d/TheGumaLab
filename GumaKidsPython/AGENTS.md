# AGENTS.md - GumaKidsPython 작업 지침

이 문서는 Codex가 `GumaKidsPython` 프로젝트를 이어서 작업할 때 우선 확인할 프로젝트 전용 지침이다.

## 프로젝트 목적

- 초등학교 3학년 아이가 파이썬을 "문법 공부"가 아니라 "게임 업그레이드 놀이"로 배우는 48챕터 PDF 교재와 실습 게임을 만든다.
- 아이는 게임 전체를 처음부터 만들지 않는다.
- 각 시즌별로 완성된 게임을 실행하고, `upgrade_zone.py`의 작은 코드만 바꾸며 결과를 확인한다.
- PDF 교재에서는 "수정"보다 "업그레이드"라는 표현을 사용한다.

## 현재 상태

- 48챕터 전체 커리큘럼 설계 완료.
- 4개 시즌 게임 기획 완료.
- 시즌 1~4 게임 구현 완료.
- 시즌 1~4 웹앱 1차 구현 완료.
- Flask 서버 저장 API 1차 구현 완료.
- 모든 게임은 외부 패키지 없이 기본 파이썬 `tkinter`로 실행한다.
- 다음 큰 작업은 시즌 1 스크린샷 확보와 챕터 1~3 PDF 샘플 제작이다.

## 참고 문서 우선순위

작업을 시작할 때 목적에 따라 다음 문서를 먼저 확인한다.

- 전체 개요와 실행법: `README.md`
- 현재 상태와 이어받기: `HANDOFF.md`
- 48챕터 커리큘럼: `COURSE_PLAN.md`
- 시즌별 게임 설계: `GAME_DESIGN.md`

## 폴더 구조

```text
GumaKidsPython/
  README.md
  HANDOFF.md
  COURSE_PLAN.md
  GAME_DESIGN.md
  AGENTS.md
  games/
    season_01_treasure_score/
    season_02_dungeon_choice/
    season_03_monster_battle/
    season_04_mini_adventure/
  web/
    index.html
    style.css
    app.js
  server.py
  docker-compose.yml
```

각 시즌 폴더는 같은 구조를 가진다.

```text
main.py                  # 게임 실행 시작점
upgrade_zone.py          # 아이가 챕터별로 바꾸는 코드
engine.py                # 숨겨진 게임 엔진
upgrade_zone_original.py # 복구용 원본
README.md                # 시즌별 실행 설명
```

## 시즌 구성

| 시즌 | 챕터 | 게임 | 주요 학습 |
|---|---:|---|---|
| 시즌 1 | 1~12 | 보물 점수 게임 | 출력, 문자열, 숫자, 변수, 계산 |
| 시즌 2 | 13~24 | 던전 선택 게임 | 입력, 조건문, 비교, 논리 연산 |
| 시즌 3 | 25~36 | 몬스터 배틀 게임 | 반복문, 리스트, 딕셔너리 |
| 시즌 4 | 37~48 | 미니 어드벤처 게임 | 함수, 랜덤, 시간, 파일, 예외, 종합 |

## 코드 작업 원칙

- `upgrade_zone.py`는 아이가 직접 보는 파일이므로 항상 단순하고 읽기 쉽게 유지한다.
- `engine.py`는 아이가 보지 않는 숨겨진 엔진이다. 꼭 필요한 경우에만 수정한다.
- `upgrade_zone_original.py`는 부모용 복구 파일이다. `upgrade_zone.py`의 기본값을 바꾸면 함께 맞춰야 하는지 검토한다.
- 한 챕터에서 새 개념은 하나만 다룬다.
- 초반 챕터는 1줄 수정, 중반은 2~5줄 수정, 후반은 작은 기능 작성 수준을 넘지 않게 한다.
- 코드 주석은 아이가 이해할 수 있는 짧고 쉬운 문장으로 쓴다.
- 게임 기능을 추가할 때도 외부 패키지 설치 부담을 만들지 않는다. 기본은 표준 라이브러리와 `tkinter`다.
- 압축본이나 커밋에는 실행에 불필요한 `__pycache__` 폴더를 포함하지 않는다.

## 교재/PDF 작업 원칙

- PDF는 공부 교재보다 게임 퀘스트북처럼 느껴지게 만든다.
- 각 챕터는 이전 시간 복습 페이지를 포함한다.
- 챕터 1은 복습 대신 "파이썬 모험을 시작하기 전에" 페이지로 구성한다.
- 챕터 2부터는 이전 챕터의 핵심 코드 1개만 짧게 복습한다.
- 따라 치는 코드는 가능한 1~3줄 수준으로 유지한다.
- `engine.py` 설명을 길게 넣지 않는다.
- 실제 게임 화면과 오늘 바꿀 코드가 명확히 연결되어야 한다.
- 퀴즈는 초등 3학년이 말로 답할 수 있는 수준으로 만든다.

기본 챕터 구성은 다음 흐름을 따른다.

1. 표지: 오늘의 게임, 오늘의 업그레이드
2. 지난 업그레이드 복습
3. 오늘의 장면
4. 오늘의 마법 코드
5. 코드가 한 일
6. 바꿔보기
7. 업그레이드 미션
8. 퀴즈
9. 정답과 짧은 예고

## 실행 및 검증

각 시즌 폴더에서 실행한다.

```powershell
python .\main.py
```

게임 창을 열지 않고 설정만 확인할 때:

```powershell
python .\main.py --check
```

문법 검사:

```powershell
python -m py_compile .\main.py .\engine.py .\upgrade_zone.py .\upgrade_zone_original.py
```

현재 Windows 터미널 환경에서 한글 출력이 `UnicodeEncodeError`를 낼 수 있다. 이 경우 코드 문제로 단정하지 말고 UTF-8 출력을 지정해서 다시 확인한다.

```powershell
$env:PYTHONIOENCODING='utf-8'
python .\main.py --check
```

4개 시즌 전체를 확인할 때는 각 시즌 폴더에서 `--check`와 `py_compile`을 실행한다.

웹앱 로컬 실행:

```powershell
python .\server.py
```

웹앱 서버 저장 API:

- `GET /api/save?profile=default`
- `POST /api/save`
- 저장 파일 위치: `data/saves/<profile>.json`

배포 주소는 `https://gumakidspython.guma3d.com`이며, 홈서버에서는 Docker 포트 `5057:5000`으로 실행한다.

## 다음 작업 추천 순서

1. 시즌 1 게임을 직접 실행해 화면과 난이도를 확인한다.
2. 시즌 1 게임 스크린샷을 확보한다.
3. 챕터 1 PDF 샘플을 제작한다.
4. 챕터 2~3 PDF 샘플을 제작한다.
5. PDF 스타일과 난이도를 확정한다.
6. 시즌 1 전체 12챕터 PDF로 확장한다.
7. 시즌 2~4 PDF 제작으로 확장한다.

## 주의 사항

- 아이가 실수해도 다시 실행하면 된다는 느낌을 유지한다.
- 에러 메시지나 복구 설명은 부모가 따라 할 수 있게 짧고 명확하게 작성한다.
- 게임의 난이도보다 학습 개념의 명확성을 우선한다.
- 새 산출물을 만들면 관련 문서의 "현재 상태" 또는 "다음 작업"도 업데이트할지 검토한다.
