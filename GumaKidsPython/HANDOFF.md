# 인수인계 메모

작성일: 2026-05-19  
프로젝트 위치: `E:\Codex\python_kids_course`

## 프로젝트 목적

초등학교 3학년 아이가 파이썬을 게임 업그레이드 방식으로 배우는 48챕터 PDF 교재와 실습 게임을 만든다.

아이는 게임 전체를 처음부터 만들지 않는다.  
각 시즌별로 미리 완성된 게임을 실행하고, `upgrade_zone.py`의 작은 코드만 바꾸며 결과를 본다.

## 확정된 교육 구조

- 총 48챕터
- 주 3회 기준 약 16주 과정
- 4개 시즌 게임 사용
- 각 시즌은 12챕터
- 각 챕터는 이전 시간 복습 페이지를 포함
- 초반은 1줄 수정, 중반은 2~5줄 수정, 후반은 작은 기능 작성

## 구현 완료된 게임

| 시즌 | 챕터 | 게임 | 상태 |
|---|---:|---|---|
| 시즌 1 | 1~12 | 보물 점수 게임 | 구현 완료 |
| 시즌 2 | 13~24 | 던전 선택 게임 | 구현 완료 |
| 시즌 3 | 25~36 | 몬스터 배틀 게임 | 구현 완료 |
| 시즌 4 | 37~48 | 미니 어드벤처 게임 | 구현 완료 |

## 웹앱 상태

- `server.py` Flask 서버 구현 완료
- `web/` 아래 시즌 1~4 웹앱 1차 구현 완료
- `POST /api/save`, `GET /api/save` 서버 저장 API 구현 완료
- 저장 데이터 위치: `data/saves/<profile>.json`
- 공개 주소 예정: `https://gumakidspython.guma3d.com`
- Docker 포트 매핑: `5057:5000`
- Nginx 라우팅: `gumakidspython.guma3d.com` -> `host.docker.internal:5057`

## 실행 환경

- Python 3.14.2에서 검증
- 외부 패키지 없음
- `tkinter` 사용
- Windows PowerShell 기준 명령 작성

## 전체 검증 명령

각 시즌 폴더에서 실행:

```powershell
python .\main.py --check
```

문법 검사 예시:

```powershell
python -m py_compile .\main.py .\engine.py .\upgrade_zone.py .\upgrade_zone_original.py
```

웹 서버 문법 검사:

```powershell
python -m py_compile .\server.py
```

웹 서버 실행:

```powershell
python .\server.py
```

## 마지막 검증 상태

2026-05-19 기준으로 다음 검증을 완료했다.

- 시즌 1~4 주요 파이썬 파일 `py_compile` 통과
- 시즌 1 `python .\main.py --check` 통과
- 시즌 2 `python .\main.py --check` 통과
- 시즌 3 `python .\main.py --check` 통과
- 시즌 4 `python .\main.py --check` 통과

압축본에는 실행에 불필요한 `__pycache__` 폴더를 포함하지 않는다.

## 게임별 실행 경로

```powershell
cd E:\Codex\python_kids_course\games\season_01_treasure_score
python .\main.py

cd E:\Codex\python_kids_course\games\season_02_dungeon_choice
python .\main.py

cd E:\Codex\python_kids_course\games\season_03_monster_battle
python .\main.py

cd E:\Codex\python_kids_course\games\season_04_mini_adventure
python .\main.py
```

## 중요한 설계 결정

- `upgrade_zone.py`는 아이가 보는 파일이다.
- `engine.py`는 아이가 보지 않아도 되는 숨겨진 게임 엔진이다.
- `upgrade_zone_original.py`는 복구용 원본이다.
- 모든 시즌 게임은 같은 파일 구조를 가진다.
- PDF 교재에는 "수정"보다 "업그레이드"라는 표현을 사용한다.
- 각 챕터 시작부에는 짧은 복습 페이지를 넣는다.
- 앱용 강의 PDF는 챕터당 기본 5페이지 안팎으로 구성하되, 필요하면 늘릴 수 있다.
- 단, 한 챕터 PDF는 최대 10페이지를 넘기지 않는다.
- 쉬운 코드 수정 미션만 넣지 말고, 해당 챕터의 파이썬 개념 설명도 짧게 포함한다.

## 다음 작업

가장 먼저 할 일은 챕터 1~3 PDF 샘플 제작이다.

샘플 PDF에서 확인할 것:

- 아이가 부담 없이 읽을 수 있는 문장 길이인지
- 이전 시간 복습 페이지가 충분히 짧은지
- 따라 치는 코드가 1~3줄 수준인지
- 실제 게임 화면과 코드 설명이 잘 연결되는지
- 퀴즈가 너무 어렵지 않은지

## 추천 제작 순서

1. 시즌 1 게임 스크린샷 확보
2. 챕터 1 PDF 샘플 제작
3. 챕터 2~3 PDF 샘플 제작
4. PDF 스타일 확정
5. 시즌 1 전체 12챕터 제작
6. 시즌 2~4 순서로 확장

## 주의할 점

- `upgrade_zone.py`의 코드는 아이가 직접 만지므로 너무 복잡하게 만들지 않는다.
- PDF에는 `engine.py` 설명을 길게 넣지 않는다.
- 실패했을 때 다시 실행하면 된다는 느낌을 계속 준다.
- 게임 기능을 더 추가하더라도, 한 챕터에서 새 개념은 하나만 다룬다.
