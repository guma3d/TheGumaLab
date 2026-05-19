# 시즌 2: 던전 선택 게임 업그레이드 존
#
# 챕터 13~24에서 사용하는 파일입니다.
# 던전의 이름, 무기, 문 규칙, 보물상자 규칙을 업그레이드합니다.


# =========================
# [챕터 13] 이름 입력
# =========================
default_name = "용감한 모험가"


def make_enter_message(name):
    return name + " 던전에 입장!"


# =========================
# [챕터 14] 무기 입력
# =========================
default_weapon = "검"


def make_weapon_message(weapon):
    return weapon + " 장착 완료!"


# =========================
# [챕터 15] 공격력 입력
# =========================
power_bonus = 2


def make_damage(power):
    damage = power + power_bonus
    return damage


# =========================
# [챕터 16] 첫 번째 선택
# =========================
has_key = True


def can_open_key_door():
    if has_key:
        return True
    return False


# =========================
# [챕터 17] 비밀번호 맞히기
# =========================
secret_password = "1234"


def is_password_correct(password):
    if password == secret_password:
        return True
    return False


# =========================
# [챕터 18] 아니면 실패
# =========================
locked_message = "문이 잠겼어!"


def password_result_message(password):
    if password == secret_password:
        return "비밀번호 성공! 문이 열렸어!"
    else:
        return locked_message


# =========================
# [챕터 19] 여러 갈림길
# =========================
def weapon_result(weapon):
    if weapon == "검":
        return "검으로 가까운 적을 공격!"
    elif weapon == "활":
        return "활로 멀리 있는 적을 공격!"
    elif weapon == "마법":
        return "마법으로 반짝 공격!"
    else:
        return weapon + "도 멋진 무기야!"


# =========================
# [챕터 20] 크다 작다
# =========================
hp = 100


def hp_warning(current_hp):
    if current_hp < 30:
        return "위험! 체력이 너무 낮아!"
    return "아직 괜찮아!"


# =========================
# [챕터 21] 크거나 같다
# =========================
level = 5
required_level = 5


def can_enter_boss_room(current_level):
    if current_level >= required_level:
        return True
    return False


# =========================
# [챕터 22] 조건 두 개
# =========================
has_gem = False


def can_open_double_lock():
    if has_key and has_gem:
        return True
    return False


# =========================
# [챕터 23] 둘 중 하나
# =========================
red_key = False
blue_key = True


def can_open_color_door():
    if red_key or blue_key:
        return True
    return False


# =========================
# [챕터 24] 던전 보물상자
# =========================
treasure_score = 100


def treasure_box_result():
    if can_open_double_lock():
        return "왕관 보물 획득!", treasure_score * 3
    elif can_open_color_door():
        return "반짝 보석 획득!", treasure_score
    else:
        return "상자가 열리지 않았어.", 0
