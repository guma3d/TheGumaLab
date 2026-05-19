# 시즌 3 원본 백업입니다.

monster_hp = 30
player_power = 5


def battle_until_defeat(start_hp):
    hp = start_hp
    logs = []
    while hp > 0:
        hp = hp - player_power
        logs.append("공격! 몬스터 체력: " + str(hp))
    logs.append("몬스터를 쓰러뜨렸어!")
    return logs


def count_attack_turns(start_hp):
    hp = start_hp
    turn = 0
    while hp > 0:
        hp = hp - player_power
        turn = turn + 1
    return turn


combo_count = 5


def combo_attack():
    logs = []
    for i in range(combo_count):
        logs.append(str(i + 1) + "번째 연속 공격!")
    return logs


countdown_start = 3


def boss_countdown():
    logs = []
    for n in range(countdown_start, 0, -1):
        logs.append(str(n))
    logs.append("보스 등장!")
    return logs


escape_word = "도망"


def dungeon_commands(commands):
    logs = []
    for command in commands:
        if command == escape_word:
            logs.append("탈출 성공!")
            break
        logs.append(command + " 실행")
    return logs


trap_tile = "함정"


def collect_path_rewards(path):
    rewards = []
    for tile in path:
        if tile == trap_tile:
            continue
        rewards.append(tile + " 보상")
    return rewards


bag = ["물약", "검", "열쇠"]


def first_item():
    return bag[0]


reward_item = "황금열쇠"


def add_reward_item(current_bag):
    current_bag.append(reward_item)
    return current_bag


discard_item = "낡은검"


def remove_old_item(current_bag):
    if discard_item in current_bag:
        current_bag.remove(discard_item)
    return current_bag


def describe_bag(current_bag):
    logs = []
    for item in current_bag:
        logs.append("가방 안에 " + item + " 있어!")
    return logs


monster = {
    "name": "슬라임",
    "hp": 30,
    "power": 5,
}
