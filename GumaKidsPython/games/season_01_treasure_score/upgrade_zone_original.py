# 시즌 1: 보물 점수 게임 업그레이드 존
#
# 이 파일은 원본 백업입니다.
# upgrade_zone.py가 너무 많이 바뀌어서 실행이 안 될 때 이 파일 내용을 복사해 되돌립니다.


start_message = "모험 시작!"
hero_message = "보물을 찾자!"
hero_name = "번개용사"
start_score = 10
score = start_score
hp = 100
speed = 5
title = hero_name + " 등장!"
status_text = f"{hero_name} 점수: {score}"

treasure_point = 10


def upgrade_score_when_get_treasure(current_score):
    new_score = current_score + treasure_point
    return new_score


trap_damage = 20


def upgrade_hp_when_hit_trap(current_hp):
    new_hp = current_hp - trap_damage
    return new_hp


bonus_multiplier = 2


def upgrade_score_when_get_bonus(current_score):
    new_score = current_score * bonus_multiplier
    return new_score
