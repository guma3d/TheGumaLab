# 시즌 4 원본 백업입니다.

import random
import time


def jump():
    return "점프!"


def say_hello():
    return "안녕, 나는 보물 사냥꾼이야!"


def attack(power):
    damage = power * 2
    return damage


def add_score(current_score, gained_score):
    new_score = current_score + gained_score
    return new_score


dice_min = 1
dice_max = 6


def random_damage():
    damage = random.randint(dice_min, dice_max)
    return damage


treasure_items = ["동전", "보석", "황금열쇠"]


def random_treasure():
    item = random.choice(treasure_items)
    return item


boss_wait_seconds = 1


def boss_entrance():
    time.sleep(boss_wait_seconds)
    return "보스 등장!"


score_file = "high_score.txt"


def save_score(score):
    with open(score_file, "w", encoding="utf-8") as file:
        file.write(str(score))
    return "점수 저장 완료!"


def load_score():
    with open(score_file, "r", encoding="utf-8") as file:
        score = int(file.read())
    return score


def safe_number(text):
    try:
        number = int(text)
        return number
    except ValueError:
        return None


win_score = 100
hero_name = "보물 사냥꾼"


def check_win(score):
    if score >= win_score:
        return "승리! 보물을 모두 찾았어!"
    return "아직 더 모아야 해!"


final_goal = "전설의 황금열쇠를 찾아라!"
