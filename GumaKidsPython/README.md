# 초등 3학년 파이썬 게임 업그레이드 강의

초등학교 3학년 아이가 파이썬을 게임 업그레이드 놀이로 배우는 48챕터 강의 프로젝트입니다.

## 현재 상태

- 48챕터 전체 커리큘럼 설계 완료
- 4개 시즌 게임 기획 완료
- 시즌 1~4 게임 구현 완료
- 모든 게임은 외부 패키지 없이 기본 파이썬 `tkinter`로 실행
- 다음 큰 작업은 챕터 1~3 PDF 샘플 제작

## 폴더 구조

```text
python_kids_course/
  README.md
  HANDOFF.md
  COURSE_PLAN.md
  GAME_DESIGN.md
  games/
    season_01_treasure_score/
    season_02_dungeon_choice/
    season_03_monster_battle/
    season_04_mini_adventure/
```

## 게임 실행 방법

VS Code에서 원하는 시즌 폴더를 열고 `main.py`를 실행합니다.

예시:

```powershell
cd E:\Codex\python_kids_course\games\season_01_treasure_score
python .\main.py
```

게임 창을 열지 않고 설정만 확인하려면:

```powershell
python .\main.py --check
```

## 각 게임의 공통 파일

| 파일 | 역할 |
|---|---|
| `main.py` | 게임 실행 파일 |
| `upgrade_zone.py` | 아이가 챕터별로 바꾸는 코드 |
| `engine.py` | 숨겨진 게임 엔진 |
| `upgrade_zone_original.py` | 원본 복구용 |
| `README.md` | 시즌별 실행 설명 |

## 이어서 할 일

1. 챕터 1~3 PDF 샘플 제작
2. 아이 눈높이에 맞는 페이지 톤 검증
3. 시즌 1 전체 12챕터 PDF 제작
4. 시즌 2~4 PDF로 확장

상세 인수인계는 `HANDOFF.md`를 먼저 확인하세요.
