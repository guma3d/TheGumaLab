# 시즌 2 원본 백업입니다.

default_name = "용감한 모험가"


def make_enter_message(name):
    return name + " 던전에 입장!"


default_weapon = "검"


def make_weapon_message(weapon):
    return weapon + " 장착 완료!"


power_bonus = 2


def make_damage(power):
    damage = power + power_bonus
    return damage


has_key = True


def can_open_key_door():
    if has_key:
        return True
    return False


secret_password = "1234"


def is_password_correct(password):
    if password == secret_password:
        return True
    return False


locked_message = "문이 잠겼어!"


def password_result_message(password):
    if password == secret_password:
        return "비밀번호 성공! 문이 열렸어!"
    else:
        return locked_message


def weapon_result(weapon):
    if weapon == "검":
        return "검으로 가까운 적을 공격!"
    elif weapon == "활":
        return "활로 멀리 있는 적을 공격!"
    elif weapon == "마법":
        return "마법으로 반짝 공격!"
    else:
        return weapon + "도 멋진 무기야!"


hp = 100


def hp_warning(current_hp):
    if current_hp < 30:
        return "위험! 체력이 너무 낮아!"
    return "아직 괜찮아!"


level = 5
required_level = 5


def can_enter_boss_room(current_level):
    if current_level >= required_level:
        return True
    return False


has_gem = False


def can_open_double_lock():
    if has_key and has_gem:
        return True
    return False


red_key = False
blue_key = True


def can_open_color_door():
    if red_key or blue_key:
        return True
    return False


treasure_score = 100


def treasure_box_result():
    if can_open_double_lock():
        return "왕관 보물 획득!", treasure_score * 3
    elif can_open_color_door():
        return "반짝 보석 획득!", treasure_score
    else:
        return "상자가 열리지 않았어.", 0
