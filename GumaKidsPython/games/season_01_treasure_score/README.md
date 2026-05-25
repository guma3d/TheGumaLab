# 시즌 1: 보물 점수 게임

초등 3학년 파이썬 강의 1~12챕터에서 사용하는 첫 번째 게임입니다.

## 실행 방법

```powershell
cd C:\Users\guma3d\Documents\TheGumaLab\GumaKidsPython\games\season_01_treasure_score
python .\main.py
```

## 조작법

| 키 | 동작 |
|---|---|
| 방향키 | 주인공 이동 |
| 스페이스 | 보물 줍기 또는 대사 보기 |
| R | 다시 시작 |

## 아이가 주로 바꾸는 파일

```text
upgrade_zone.py
```

처음에는 챕터에서 알려준 한 줄만 바꿉니다.

## 부모용 되돌리기

아이가 코드를 많이 바꿔서 실행이 어려워지면 `upgrade_zone_original.py`의 내용을 `upgrade_zone.py`로 되돌립니다.

## 빠른 확인

게임 창을 열지 않고 업그레이드 값만 확인하려면:

```powershell
python .\main.py --check
```
