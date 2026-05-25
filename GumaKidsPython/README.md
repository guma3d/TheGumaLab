# 초등 3학년 파이썬 게임 업그레이드 강의

초등학교 3학년 아이가 파이썬을 게임 업그레이드 놀이로 배우는 48챕터 강의 프로젝트입니다.

## 현재 상태

- 48챕터 전체 커리큘럼 설계 완료
- 4개 시즌 게임 기획 완료
- 시즌 1~4 게임 구현 완료
- 시즌 1~4 웹앱 1차 구현 완료
- 서버 저장 API 1차 구현 완료
- `Guma Python Lab` 3분할 학습 앱 프로토타입 구현 완료
- 챕터 1 강의자료 PDF/PNG 8페이지 샘플 제작 완료
- 모든 게임은 외부 패키지 없이 기본 파이썬 `tkinter`로 실행
- 다음 큰 작업은 챕터 1 앱 수업 흐름 검증과 챕터 2~3 강의자료 제작

## 폴더 구조

```text
GumaKidsPython/
  README.md
  HANDOFF.md
  COURSE_PLAN.md
  GAME_DESIGN.md
  app/
    guma_python_lab.py
  Docs/
    season_01/
      chapter_01.pdf
  games/
    season_01_treasure_score/
    season_02_dungeon_choice/
    season_03_monster_battle/
    season_04_mini_adventure/
  tools/
    generate_chapter_01_pdf.py
  web/
```

## 게임 실행 방법

VS Code에서 원하는 시즌 폴더를 열고 `main.py`를 실행합니다.

예시:

```powershell
cd C:\Users\guma3d\Documents\TheGumaLab\GumaKidsPython\games\season_01_treasure_score
python .\main.py
```

게임 창을 열지 않고 설정만 확인하려면:

```powershell
python .\main.py --check
```

## Guma Python Lab 실행 방법

3분할 학습 앱 프로토타입을 실행하려면:

앱은 `tkinter`와 `Pillow`를 사용합니다.

```powershell
cd C:\Users\guma3d\Documents\TheGumaLab\GumaKidsPython
python .\app\guma_python_lab.py
```

현재 앱 구성:

- 왼쪽 위: 가로형 강의자료 PNG/PDF 미리보기
- 왼쪽 아래: 시즌 1 보물 점수 게임 화면
- 오른쪽: 파이썬 코드 편집 화면
- 화면 비율: 좌우 50:50, 왼쪽 상하 50:50 고정
- UI 테마: 앱 크롬과 코드 편집기는 Dark 테마, 강의자료와 게임 화면은 밝은 색감 유지
- 챕터 선택: 작은 드롭다운
- 저장 위치: `user_saves/season_01/chapter_XX/upgrade_zone.py`

챕터 1 강의자료는 `Docs/season_01/chapter_01.pdf`와 `chapter_01_p01.png`~`chapter_01_p08.png`로 생성되어 있다.

## 웹앱 실행 방법

로컬에서 웹 버전을 확인하려면:

```powershell
cd C:\Users\guma3d\Documents\TheGumaLab\GumaKidsPython
python .\server.py
```

브라우저에서 `http://127.0.0.1:5000`을 연다.

서버 배포 주소는 `https://gumakidspython.guma3d.com`이다.
저장 데이터는 서버의 `data/saves/` 아래 JSON 파일로 보관한다.

## 각 게임의 공통 파일

| 파일 | 역할 |
|---|---|
| `main.py` | 게임 실행 파일 |
| `upgrade_zone.py` | 아이가 챕터별로 바꾸는 코드 |
| `engine.py` | 숨겨진 게임 엔진 |
| `upgrade_zone_original.py` | 원본 복구용 |
| `README.md` | 시즌별 실행 설명 |

## 웹앱 파일

| 파일 | 역할 |
|---|---|
| `server.py` | Flask 웹 서버와 저장 API |
| `web/index.html` | 웹앱 화면 |
| `web/style.css` | 웹앱 스타일 |
| `web/app.js` | 시즌 1~4 웹 게임 로직 |
| `docker-compose.yml` | 홈서버 Docker 실행 설정 |

## 이어서 할 일

1. 챕터 1 앱 수업 흐름을 실제 사용 기준으로 검증
2. 챕터 2~3 강의자료 PDF/PNG 샘플 제작
3. 챕터 드롭다운과 저장 흐름을 아이 눈높이로 다듬기
4. 시즌 1 전체 12챕터 PDF 제작
5. 시즌 2~4 PDF로 확장

상세 인수인계는 `HANDOFF.md`를 먼저 확인하세요.
