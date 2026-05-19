# 시즌 4: 미니 어드벤처 게임 업그레이드 존
#
# 챕터 37~48에서 사용하는 파일입니다.
# 함수, 랜덤, 시간, 파일, 예외 처리를 하나의 작은 게임으로 묶습니다.

import random
import time


# =========================
# [챕터 37] 점프 버튼
# =========================
def jump():
    return "점프!"


# =========================
# [챕터 38] 인사 버튼
# =========================
def say_hello():
    return "안녕, 나는 보물 사냥꾼이야!"


# =========================
# [챕터 39] 힘을 넣는 공격
# =========================
def attack(power):
    damage = power * 2
    return damage


# =========================
# [챕터 40] 결과를 돌려줘
# =========================
def add_score(current_score, gained_score):
    new_score = current_score + gained_score
    return new_score


# =========================
# [챕터 41] 랜덤 주사위
# =========================
dice_min = 1
dice_max = 6


def random_damage():
    damage = random.randint(dice_min, dice_max)
    return damage


# =========================
# [챕터 42] 랜덤 보물상자
# =========================
treasure_items = ["동전", "보석", "황금열쇠"]


def random_treasure():
    item = random.choice(treasure_items)
    return item


# =========================
# [챕터 43] 잠깐 기다려
# =========================
boss_wait_seconds = 1


def boss_entrance():
    time.sleep(boss_wait_seconds)
    return "보스 등장!"


# =========================
# [챕터 44] 점수 저장
# =========================
score_file = "high_score.txt"


def save_score(score):
    with open(score_file, "w", encoding="utf-8") as file:
        file.write(str(score))
    return "점수 저장 완료!"


# =========================
# [챕터 45] 점수 불러오기
# =========================
def load_score():
    with open(score_file, "r", encoding="utf-8") as file:
        score = int(file.read())
    return score


# =========================
# [챕터 46] 실수해도 괜찮아
# =========================
def safe_number(text):
    try:
        number = int(text)
        return number
    except ValueError:
        return None


# =========================
# [챕터 47] 게임 규칙 정리
# =========================
win_score = 100
hero_name = "보물 사냥꾼"


def check_win(score):
    if score >= win_score:
        return "승리! 보물을 모두 찾았어!"
    return "아직 더 모아야 해!"


# =========================
# [챕터 48] 최종 완성
# =========================
final_goal = "전설의 황금열쇠를 찾아라!"
