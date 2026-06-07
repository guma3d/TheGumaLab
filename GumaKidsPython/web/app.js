const seasons = {
  season_01: {
    title: "보물 점수 게임",
    chapters: "챕터 1~12",
    lesson: [
      ["1. 오늘의 장면", "주인공이 보물과 함정을 찾아다니며 점수와 체력이 바뀝니다."],
      ["2. 오늘의 코드", "이름, 대사, 점수 같은 값을 바꾸면 게임 화면도 바로 바뀝니다."],
      ["3. 코드가 하는 일", "문자열은 화면의 말이 되고 숫자는 점수, 체력, 속도가 됩니다."],
      ["4. 바꿔보기", "hero_name, hp, speed 값을 바꾸고 업그레이드 적용을 누릅니다."],
      ["5. 미션", "속도를 바꿔 보물을 더 빨리 줍거나 체력을 크게 만들어 봅니다."],
    ],
    fields: [
      ["start_message", "게임 시작 문장", "모험 시작!"],
      ["hero_message", "주인공 대사", "보물을 찾자!"],
      ["hero_name", "주인공 이름", "번개용사"],
      ["start_score", "시작 점수", 10],
      ["score", "현재 점수", 10],
      ["hp", "체력", 100],
      ["potion_heal", "물약 회복량", 20],
      ["speed", "이동 속도", 5],
      ["wind_multiplier", "바람신발 배율", 2],
      ["mission_text", "미션 문장", "번개용사의 미션: 보물 3개 모으기"],
      ["mission_status", "미션 상태 문장", "번개용사 미션: 점수 10, 체력 100"],
      ["portal_hint", "포털 안내 문장", "보물을 모아 포털을 열자"],
      ["starter_chest_label", "보물상자 이름", "보물상자"],
      ["treasure_label", "보물 이름", "보물"],
      ["coin_label", "동전 이름", "동전"],
      ["potion_label", "물약 이름", "체력 물약"],
      ["wind_shoes_label", "바람신발 이름", "바람신발"],
      ["gem_label", "루비 이름", "루비"],
      ["chest_label", "상자 이름", "상자"],
      ["trap_label", "함정 이름", "함정"],
      ["bonus_label", "보너스별 이름", "보너스별"],
      ["portal_label", "포털 이름", "포털"],
      ["starter_chest_point", "보물상자 점수", 10],
      ["treasure_point", "보물 점수", 10],
      ["coin_point", "동전 점수", 5],
      ["gem_point", "루비 점수", 20],
      ["chest_point", "상자 점수", 30],
      ["treasure_1", "계산 보물 1", 10],
      ["treasure_2", "계산 보물 2", 20],
      ["treasure_3", "계산 보물 3", 30],
      ["trap_1", "계산 함정", 20],
      ["current_score", "계산 점수", 40],
      ["trap_damage", "함정 데미지", 20],
      ["trap_speed", "함정 속도", 2],
      ["bonus_multiplier", "보너스 배율", 2],
    ],
  },
  season_02: {
    title: "괴수 러너 성장 게임",
    chapters: "챕터 13~24",
    lesson: [
      ["1. 오늘의 장면", "원숭이가 달리며 고기를 먹고 에너지를 키운 뒤 보스와 싸웁니다."],
      ["2. 오늘의 코드", "입력값, 조건문, 비교 연산으로 성장과 변신, 보스전 규칙을 정합니다."],
      ["3. 코드가 하는 일", "True와 False는 방어막, 대시, 변신 조건처럼 게임 규칙을 켜고 끕니다."],
      ["4. 바꿔보기", "고기 에너지와 변신 에너지 기준을 바꾸고 변신 속도를 비교합니다."],
      ["5. 미션", "원숭이가 고릴라, 공룡으로 두 번 변신하게 만듭니다."],
    ],
    fields: [
      ["baby_name", "원숭이 이름", "꼬마구마"],
      ["runner_title", "출발 문장", "꼬마구마 출동!"],
      ["roar_text", "괴수 대사", "우와앙! 더 커질 거야!"],
      ["favorite_food", "좋아하는 먹이", "고기"],
      ["start_size", "시작 외형 크기", 1],
      ["growth", "현재 성장", 0],
      ["run_speed", "달리기 속도", 5],
      ["snack_score", "첫 에너지 보너스", 10],
      ["meat_score", "고기 에너지", 100],
      ["food_name", "먹이 이름", "고기"],
      ["favorite_bonus", "좋아하는 먹이 보너스", 20],
      ["item_name", "검사용 아이템", "고기"],
      ["bomb_damage", "폭탄 피해", 70],
      ["growth_per_item", "먹이 성장량", 12],
      ["mutation_size", "외형 표시 기준", 60],
      ["gorilla_score", "고릴라 변신 에너지", 200],
      ["dino_score", "공룡 변신 에너지", 500],
      ["mutation_result", "현재 변신 결과", "원숭이"],
      ["hp", "체력", 100],
      ["danger_limit", "위험 체력 기준", 35],
      ["attack_power", "괴수 공격력", 18],
      ["flame_damage", "불꽃 피해", 200],
      ["boss_power", "보스 공격력", 24],
      ["boss_name", "최종 보스 이름", "메카 타이탄"],
      ["has_shield", "장애물 방어막", "false"],
      ["obstacle_result", "장애물 결과", "방어 성공"],
      ["shield_ready", "방어막 준비", "true"],
      ["dash_ready", "대시 준비", "false"],
      ["can_dash_shield", "방어막+대시", "false"],
      ["red_core", "빨간 코어", "true"],
      ["blue_core", "파란 코어", "false"],
      ["has_core_bonus", "변신 코어 보너스", "true"],
      ["item_result", "아이템 계산 결과", 0],
      ["final_attack", "최종 공격 피해", 200],
    ],
  },
  season_03: {
    title: "몬스터 배틀 게임",
    chapters: "챕터 25~36",
    lesson: [
      ["1. 오늘의 장면", "플레이어가 몬스터와 턴제로 싸우고 전투 로그를 확인합니다."],
      ["2. 오늘의 코드", "반복 공격, 아이템 가방, 몬스터 능력치를 코드로 정합니다."],
      ["3. 코드가 하는 일", "반복문은 공격을 여러 번 실행하고 리스트는 아이템을 담습니다."],
      ["4. 바꿔보기", "monster_hp, player_power, combo_count 값을 바꿔 봅니다."],
      ["5. 미션", "몬스터를 몇 턴 만에 이길 수 있는지 실험합니다."],
    ],
    fields: [
      ["monster_name", "몬스터 이름", "슬라임"],
      ["monster_hp", "몬스터 체력", 30],
      ["monster_power", "몬스터 공격력", 5],
      ["player_power", "플레이어 공격력", 5],
      ["combo_count", "연속 공격 횟수", 5],
      ["bag", "아이템 가방", "물약, 검, 열쇠"],
      ["reward_item", "보상 아이템", "황금열쇠"],
    ],
  },
  season_04: {
    title: "미니 어드벤처 게임",
    chapters: "챕터 37~48",
    lesson: [
      ["1. 오늘의 장면", "점프, 인사, 공격, 보물상자 기능을 하나씩 실행합니다."],
      ["2. 오늘의 코드", "함수, 랜덤, 저장 규칙이 작은 어드벤처 게임으로 연결됩니다."],
      ["3. 코드가 하는 일", "함수는 버튼처럼 실행되고 랜덤은 매번 다른 결과를 만듭니다."],
      ["4. 바꿔보기", "dice_min, dice_max, treasure_items, win_score를 바꿔 봅니다."],
      ["5. 미션", "나만의 최종 목표와 보물 목록을 만들어 봅니다."],
    ],
    fields: [
      ["hero_name", "주인공 이름", "보물 사냥꾼"],
      ["final_goal", "최종 목표", "전설의 황금열쇠를 찾아라!"],
      ["dice_min", "랜덤 최소", 1],
      ["dice_max", "랜덤 최대", 6],
      ["treasure_items", "보물 목록", "동전, 보석, 황금열쇠"],
      ["win_score", "승리 점수", 100],
    ],
  },
};

const seasonOneEditPlans = {
  1: { lines: 1, keys: ["start_message"], labels: ["start_message"] },
  2: { lines: 1, keys: ["hero_message"], labels: ["hero_message"] },
  3: { lines: 2, keys: ["hero_name", "hero_message"], labels: ["hero_name", "hero_message"] },
  4: { lines: 2, keys: ["start_score", "starter_chest_point"], labels: ["start_score", "starter_chest_point"] },
  5: { lines: 3, keys: ["score", "treasure_point", "coin_point"], labels: ["score", "treasure_point", "coin_point"] },
  6: { lines: 4, keys: ["score", "hp", "potion_heal", "treasure_point"], labels: ["score", "hp", "potion_heal", "treasure_point"] },
  7: { lines: 5, keys: ["score", "hp", "speed", "wind_multiplier", "coin_point"], labels: ["score", "hp", "speed", "wind_multiplier", "coin_point"] },
  8: { lines: 6, keys: ["hero_name", "hero_message", "start_score", "score", "speed", "mission_text"], labels: ["hero_name", "hero_message", "start_score", "score", "speed", "mission_text"] },
  9: { lines: 7, keys: ["hero_name", "hero_message", "start_score", "score", "hp", "speed", "mission_status"], labels: ["hero_name", "hero_message", "start_score", "score", "hp", "speed", "mission_status"] },
  10: { lines: 8, keys: ["hero_name", "score", "treasure_1", "treasure_2", "treasure_3", "trap_1", "current_score", "hp"], labels: ["hero_name", "score", "treasure_1", "treasure_2", "treasure_3", "trap_1", "current_score", "hp"] },
  11: { lines: 9, keys: ["hero_name", "score", "hp", "treasure_point", "gem_point", "chest_point", "trap_label", "trap_damage", "trap_speed"], labels: ["hero_name", "score", "hp", "treasure_point", "gem_point", "chest_point", "trap_label", "trap_damage", "trap_speed"] },
  12: { lines: 10, keys: ["hero_name", "score", "hp", "speed", "wind_multiplier", "trap_speed", "treasure_point", "gem_point", "trap_damage", "bonus_multiplier"], labels: ["hero_name", "score", "hp", "speed", "wind_multiplier", "trap_speed", "treasure_point", "gem_point", "trap_damage", "bonus_multiplier"] },
};

const seasonOneUnlocks = {
  1: "시작 깃발과 첫 장면이 생깁니다.",
  2: "주인공 말풍선이 캐릭터를 따라다닙니다.",
  3: "주인공 이름표가 생깁니다.",
  4: "보물상자가 생기고 점수가 상태창에 보입니다.",
  5: "보물과 동전을 주워 보상 점수 차이를 비교합니다.",
  6: "체력 숫자와 체력 물약이 추가됩니다.",
  7: "바람신발을 먹으면 이동 속도가 계속 빨라집니다.",
  8: "이름과 문장이 합쳐진 미션 메시지가 게임판에 붙습니다.",
  9: "이름, 점수, 체력이 들어간 미션 상태판이 붙습니다.",
  10: "보물 점수는 더하고 점수 함정은 빼는 계산 미션이 생깁니다.",
  11: "랜덤으로 움직이는 함정과 체력 피해가 들어와 긴장감이 생깁니다.",
  12: "보너스 별, 마법 포털, 승리 연출로 완성됩니다.",
};

const seasonOneChapters = {
  1: {
    title: "게임 화면아 안녕",
    focus: "start_message",
    syntax: "str은 글자를 담는 자료형입니다. 따옴표 안에 있는 말은 파이썬이 계산하지 않고 그대로 기억합니다. start_message는 게임이 시작될 때 보여줄 첫 문장을 담는 변수입니다.",
    pages: [
      ["1. 오늘의 장면", "게임이 시작될 때 화면에 첫 문장이 나타납니다."],
      ["2. 오늘의 코드", "start_message = \"모험 시작!\" 처럼 이름에 글자를 담습니다."],
      ["3. 기술 설명", "str은 문자열 자료형입니다. 따옴표 안에 들어간 글자는 파이썬에서 str 값으로 다룹니다."],
      ["4. 바꿔보기", "따옴표 안의 문장만 바꾸고 업그레이드 적용을 누릅니다."],
      ["5. 미션", "내가 만든 게임 시작 문장을 2개 이상 만들어 봅니다."],
    ],
  },
  2: {
    title: "캐릭터가 말해요",
    focus: "hero_message",
    syntax: "문자열 str은 한 글자도, 긴 문장도 담을 수 있습니다. hero_message에 넣은 글자는 주인공 옆 말풍선에 붙어서 계속 따라다닙니다.",
    pages: [
      ["1. 오늘의 장면", "주인공 옆 말풍선에 보여줄 대사를 정합니다."],
      ["2. 오늘의 코드", "hero_message 변수에 주인공의 말을 저장합니다."],
      ["3. 기술 설명", "문자열은 글자의 묶음입니다. 한글, 영어, 기호도 따옴표 안에 있으면 str입니다."],
      ["4. 바꿔보기", "hero_message 값을 바꾸면 게임 화면 말풍선이 바로 바뀝니다."],
      ["5. 미션", "주인공 성격이 드러나는 짧은 대사를 만들어 봅니다."],
    ],
  },
  3: {
    title: "이름을 바꿔요",
    focus: "hero_name",
    syntax: "변수는 값에 붙이는 이름표입니다. hero_name은 이름표에 보이는 글자이고 hero_message는 말풍선에 보이는 글자입니다. 두 변수 모두 문자열 str을 담습니다.",
    pages: [
      ["1. 오늘의 장면", "캐릭터 이름표와 말풍선을 함께 정합니다."],
      ["2. 오늘의 코드", "hero_name에는 이름을, hero_message에는 주인공 대사를 저장합니다."],
      ["3. 기술 설명", "변수는 값에 붙이는 이름입니다. 문자열 변수는 따옴표 안의 글자를 기억합니다."],
      ["4. 바꿔보기", "hero_name과 hero_message 두 줄을 함께 바꾸고 게임 속 캐릭터를 확인합니다."],
      ["5. 미션", "이름과 대사가 어울리는 주인공 조합 3개를 실험합니다."],
    ],
  },
  4: {
    title: "보상 숫자가 보여요",
    focus: "start_score",
    syntax: "int는 정수 자료형입니다. start_score는 처음 점수이고 starter_chest_point는 보물상자를 얻을 때 더해지는 보상 점수입니다. 계산에 쓰는 숫자는 따옴표 없이 적습니다.",
    pages: [
      ["1. 오늘의 장면", "보물상자를 주우면 상태창의 점수가 올라갑니다."],
      ["2. 오늘의 코드", "start_score는 처음 점수, starter_chest_point는 보물상자 점수입니다."],
      ["3. 기술 설명", "int는 정수 자료형입니다. 10, 0, 100처럼 소수점 없는 숫자를 뜻합니다."],
      ["4. 바꿔보기", "start_score와 starter_chest_point를 바꾸고 보물상자를 주워 점수 변화를 비교합니다."],
      ["5. 미션", "처음 점수와 첫 보상 점수가 잘 어울리는 조합을 정합니다."],
    ],
  },
  5: {
    title: "보상 점수 정하기",
    focus: "treasure_point",
    syntax: "= 는 오른쪽 값을 왼쪽 변수에 넣는 대입 연산자입니다. score는 현재 점수이고 treasure_point와 coin_point는 각각 보물과 동전 보상입니다.",
    pages: [
      ["1. 오늘의 장면", "보물과 동전이 추가되어 서로 다른 점수를 줍니다."],
      ["2. 오늘의 코드", "score는 현재 점수, treasure_point는 보물 점수, coin_point는 동전 점수입니다."],
      ["3. 기술 설명", "= 는 오른쪽 값을 왼쪽 변수에 넣는 대입 연산자입니다. 변수에 저장한 숫자가 게임 규칙이 됩니다."],
      ["4. 바꿔보기", "score, treasure_point, coin_point를 바꾸고 보물/동전을 주워 점수 차이를 봅니다."],
      ["5. 미션", "보물은 크게, 동전은 작게 느껴지는 보상 점수를 정합니다."],
    ],
  },
  6: {
    title: "체력 만들기",
    focus: "hp",
    syntax: "숫자 변수는 게임 규칙을 조절합니다. hp는 주인공 체력이고, potion_heal은 체력 물약을 얻었을 때 회복되는 숫자입니다.",
    pages: [
      ["1. 오늘의 장면", "체력 숫자와 체력 물약이 추가됩니다."],
      ["2. 오늘의 코드", "hp는 기본 체력, potion_heal은 물약 회복량입니다."],
      ["3. 기술 설명", "숫자 변수는 계산할 수 있습니다. 체력, 점수, 속도는 int로 다루기 좋습니다."],
      ["4. 바꿔보기", "hp와 potion_heal을 바꾸고 체력 숫자 변화를 비교합니다."],
      ["5. 미션", "주인공에게 어울리는 기본 체력과 물약 회복량을 정합니다."],
    ],
  },
  7: {
    title: "속도 만들기",
    focus: "speed",
    syntax: "변수 값이 바뀌면 그 변수를 쓰는 계산 결과도 바뀝니다. speed는 기본 이동 속도, wind_multiplier는 바람신발 속도 배율, coin_point는 동전 보상 점수입니다.",
    pages: [
      ["1. 오늘의 장면", "방향키를 누르면 주인공이 움직입니다."],
      ["2. 오늘의 코드", "speed는 기본 속도, wind_multiplier는 바람신발 배율, coin_point는 동전 점수입니다."],
      ["3. 기술 설명", "wind_multiplier가 2이면 바람신발을 먹은 뒤 계속 2배 빠르게 움직입니다."],
      ["4. 바꿔보기", "speed를 4, 6으로 바꾸고 wind_multiplier를 2, 3으로 바꿔 비교합니다."],
      ["5. 미션", "움직이기 좋은 기본 속도, 바람신발 배율, 동전 점수를 함께 정합니다."],
    ],
  },
  8: {
    title: "미션 만들기",
    focus: "mission_text",
    syntax: "str + str은 두 문자열을 이어 붙입니다. hero_name + \"의 미션\" 처럼 변수와 문자열을 합칠 수 있고, hero_name + \" 메롱!\" + hero_name처럼 여러 조각을 이어 붙일 수도 있습니다.",
    pages: [
      ["1. 오늘의 장면", "게임판에 보이는 미션 메시지 문장을 만듭니다."],
      ["2. 오늘의 코드", "mission_text = hero_name + \"의 미션: 보물 3개 모으기\" 는 문자열을 이어 붙입니다."],
      ["3. 기술 설명", "str + str은 두 문자열을 합칩니다. 숫자 더하기와는 결과가 다릅니다."],
      ["4. 바꿔보기", "\"의 미션\" 부분을 바꾸거나 hero_name을 한 번 더 붙여 봅니다."],
      ["5. 미션", "내 이름이 들어간 짧은 미션 메시지를 만들어 봅니다."],
    ],
  },
  9: {
    title: "미션 상태판",
    focus: "mission_status",
    syntax: "f-string은 문자열 안에 변수 값을 넣는 방법입니다. 문자열 앞에 f를 붙이고, 중괄호 안에 hero_name이나 score 같은 변수 이름을 씁니다.",
    pages: [
      ["1. 오늘의 장면", "게임 안에 짧은 미션 상태 문장을 붙입니다."],
      ["2. 오늘의 코드", "f\"{hero_name} 미션: 점수 {score}, 체력 {hp}\" 는 변수 값을 문장 안에 넣습니다."],
      ["3. 기술 설명", "f-string은 문자열 앞에 f를 붙이고 중괄호 안의 변수 값을 글자로 바꿔 넣습니다."],
      ["4. 바꿔보기", "미션 상태 문장의 순서를 바꿔 봅니다."],
      ["5. 미션", "이름, 점수, 체력이 들어간 짧은 미션 상태 문장을 만들어 봅니다."],
    ],
  },
  10: {
    title: "더하기 빼기 마법",
    focus: "current_score",
    syntax: "+ 는 숫자를 더하고 - 는 숫자를 뺍니다. current_score는 보물 점수들을 더하고 함정 점수를 뺀 최종 점수입니다. 아직 함수 def는 쓰지 않고 한 줄 계산식으로 연습합니다.",
    pages: [
      ["1. 오늘의 장면", "보물은 점수를 올리고 점수 함정은 점수를 깎습니다."],
      ["2. 오늘의 코드", "current_score = treasure_1 + treasure_2 + treasure_3 - trap_1 처럼 한 줄로 계산합니다."],
      ["3. 기술 설명", "+ 는 더하기, - 는 빼기입니다. 계산 결과를 current_score에 저장하면 게임 점수로 보여 줍니다."],
      ["4. 바꿔보기", "보물 숫자와 함정 숫자를 바꿔 최종 점수가 어떻게 달라지는지 비교합니다."],
      ["5. 미션", "보물은 기분 좋게 오르고 점수 함정은 아프게 줄어드는 규칙을 만듭니다."],
    ],
  },
  11: {
    title: "랜덤 함정",
    focus: "trap_speed",
    syntax: "random은 매번 다른 값을 뽑는 함수입니다. 함정은 random으로 x축, y축 움직임을 골라 돌아다니고, trap_speed가 클수록 한 번에 더 멀리 움직입니다. 함정에 닿으면 폭파 이펙트가 나오고 게임이 끝납니다.",
    pages: [
      ["1. 오늘의 장면", "함정 하나가 랜덤하게 움직이고, 닿으면 폭발하며 게임이 종료됩니다."],
      ["2. 오늘의 코드", "trap_x_step = random.choice([-1, 0, 1]) * trap_speed 처럼 함정 이동값을 뽑습니다."],
      ["3. 기술 설명", "파이썬에서는 import random 뒤에 random.choice([-1, 0, 1])처럼 쓰면 여러 값 중 하나를 뽑을 수 있습니다."],
      ["4. 바꿔보기", "trap_speed와 trap_damage를 바꾸고 함정 움직임과 체력 감소를 비교합니다."],
      ["5. 미션", "피할 수는 있지만 긴장되는 함정 속도와 폭발 피해량을 정합니다."],
    ],
  },
  12: {
    title: "보너스 점수",
    focus: "bonus_multiplier",
    syntax: "* 는 곱셈 연산자입니다. bonus_multiplier가 2면 현재 점수가 2배, 3이면 3배로 바뀌는 식입니다.",
    pages: [
      ["1. 오늘의 장면", "보너스를 먹으면 현재 점수가 몇 배로 커집니다."],
      ["2. 오늘의 코드", "current_score * bonus_multiplier가 보너스 점수를 만듭니다."],
      ["3. 기술 설명", "* 는 곱셈 연산자입니다. 점수 배율, 공격력 배율 같은 규칙에 씁니다."],
      ["4. 바꿔보기", "bonus_multiplier를 2, 3, 5로 바꿔 보너스 효과를 비교합니다."],
      ["5. 미션", "너무 강하지 않은 보너스 배율을 정합니다."],
    ],
  },
};

const seasonTwoEditPlans = {
  1: { lines: 1, keys: ["baby_name"], labels: ["baby_name"] },
  2: { lines: 2, keys: ["runner_title", "roar_text"], labels: ["runner_title", "roar_text"] },
  3: { lines: 3, keys: ["start_size", "snack_score", "meat_score"], labels: ["start_size", "snack_score", "meat_score"] },
  4: { lines: 4, keys: ["mutation_size", "gorilla_score", "dino_score", "mutation_result"], labels: ["mutation_size", "gorilla_score", "dino_score", "mutation_result"] },
  5: { lines: 5, keys: ["baby_name", "favorite_food", "food_name", "meat_score", "favorite_bonus"], labels: ["baby_name", "favorite_food", "food_name", "meat_score", "favorite_bonus"] },
  6: { lines: 6, keys: ["baby_name", "hp", "danger_limit", "has_shield", "obstacle_result", "run_speed"], labels: ["baby_name", "hp", "danger_limit", "has_shield", "obstacle_result", "run_speed"] },
  7: { lines: 7, keys: ["baby_name", "item_name", "meat_score", "bomb_damage", "item_result", "flame_damage", "boss_power"], labels: ["baby_name", "item_name", "meat_score", "bomb_damage", "item_result", "flame_damage", "boss_power"] },
  8: { lines: 8, keys: ["runner_title", "roar_text", "start_size", "growth", "run_speed", "meat_score", "gorilla_score", "dino_score"], labels: ["runner_title", "roar_text", "start_size", "growth", "run_speed", "meat_score", "gorilla_score", "dino_score"] },
  9: { lines: 9, keys: ["baby_name", "runner_title", "roar_text", "hp", "danger_limit", "run_speed", "flame_damage", "boss_power", "boss_name"], labels: ["baby_name", "runner_title", "roar_text", "hp", "danger_limit", "run_speed", "flame_damage", "boss_power", "boss_name"] },
  10: { lines: 10, keys: ["baby_name", "gorilla_score", "dino_score", "shield_ready", "dash_ready", "can_dash_shield", "hp", "run_speed", "boss_power", "boss_name"], labels: ["baby_name", "gorilla_score", "dino_score", "shield_ready", "dash_ready", "can_dash_shield", "hp", "run_speed", "boss_power", "boss_name"] },
  11: { lines: 10, keys: ["baby_name", "favorite_food", "red_core", "blue_core", "has_core_bonus", "meat_score", "gorilla_score", "dino_score", "flame_damage", "boss_power"], labels: ["baby_name", "favorite_food", "red_core", "blue_core", "has_core_bonus", "meat_score", "gorilla_score", "dino_score", "flame_damage", "boss_power"] },
  12: { lines: 10, keys: ["baby_name", "runner_title", "roar_text", "meat_score", "gorilla_score", "dino_score", "final_attack", "boss_power", "boss_name", "hp"], labels: ["baby_name", "runner_title", "roar_text", "meat_score", "gorilla_score", "dino_score", "final_attack", "boss_power", "boss_name", "hp"] },
};

const seasonTwoUnlocks = {
  1: "원숭이 이름표와 3D 스타일 세로 러너 캐릭터가 등장합니다.",
  2: "괴수가 세로 트랙을 달리며 포효 말풍선을 보여 줍니다.",
  3: "위에서 내려오는 고기 아이템을 먹으면 에너지가 오릅니다.",
  4: "에너지 기준을 넘으면 원숭이가 고릴라로 변신합니다.",
  5: "좋아하는 고기를 먹으면 에너지 보너스를 받습니다.",
  6: "장애물과 체력 경고가 생겨 피해야 할 이유가 생깁니다.",
  7: "첫 보스전이 열리고 공격력과 보스 공격력을 비교합니다.",
  8: "여러 성장 단계가 화면에 확실히 쌓여 보입니다.",
  9: "네 가지 보스 중 현재 챕터에 맞는 보스가 등장합니다.",
  10: "방어막과 대시 조건을 켜고 끄며 러너 구간을 조절합니다.",
  11: "빨간 코어 또는 파란 코어 조건으로 변신 보너스를 실험합니다.",
  12: "세로 러너 구간에서 보스전으로 카메라가 부드럽게 넘어가며 시즌2가 완성됩니다.",
};

const seasonTwoChapters = {
  1: {
    title: "원숭이 출발",
    focus: "baby_name",
    syntax: "input()은 사용자가 넣은 글자를 프로그램으로 가져오는 함수입니다. 웹버전에서는 직접 입력창을 띄우지 않고 baby_name 값을 바꿔 입력 결과처럼 사용합니다.",
    pages: [
      ["1. 오늘의 장면", "원숭이가 세로 러너 트랙에 처음 등장합니다."],
      ["2. 오늘의 코드", "baby_name은 화면 이름표와 게임 저장에 쓰이는 문자열입니다."],
      ["3. 기술 설명", "input()으로 받은 값은 먼저 str, 즉 글자로 들어옵니다."],
      ["4. 바꿔보기", "baby_name을 나만의 괴수 이름으로 바꾸고 게임 화면에서 확인합니다."],
      ["5. 미션", "이름만 바꿔도 내 괴수가 된다는 느낌이 들게 만듭니다."],
    ],
  },
  2: {
    title: "포효 문장",
    focus: "roar_text",
    syntax: "문자열은 따옴표 안에 넣은 글자입니다. roar_text 같은 문자열은 말풍선, 안내문, 보스전 대사처럼 화면에 그대로 보입니다.",
    pages: [
      ["1. 오늘의 장면", "세로 트랙을 달리는 괴수 위에 포효 말풍선이 뜹니다."],
      ["2. 오늘의 코드", "roar_text에 괴수의 대사를 저장합니다."],
      ["3. 기술 설명", "str은 글자 자료형입니다. 숫자 계산은 하지 않고 화면에 말로 보여 주기 좋습니다."],
      ["4. 바꿔보기", "괴수가 성장하고 싶어 하는 문장을 만들어 봅니다."],
      ["5. 미션", "내 괴수 성격이 보이는 짧은 포효를 정합니다."],
    ],
  },
  3: {
    title: "고기 먹고 성장",
    focus: "snack_score",
    syntax: "int()는 글자로 들어온 숫자를 계산 가능한 정수로 바꿉니다. 에너지는 숫자여야 더하고 비교할 수 있습니다.",
    pages: [
      ["1. 오늘의 장면", "위에서 내려오는 고기를 먹으면 에너지가 올라갑니다."],
      ["2. 오늘의 코드", "snack_score와 meat_score는 에너지 보상 숫자입니다."],
      ["3. 기술 설명", "10과 1 같은 정수는 더하기와 비교가 가능합니다."],
      ["4. 바꿔보기", "고기 에너지를 높여 성장 느낌을 바꿔 봅니다."],
      ["5. 미션", "처음에는 작지만 먹을수록 커지는 느낌을 만듭니다."],
    ],
  },
  4: {
    title: "첫 변신 조건",
    focus: "gorilla_score",
    syntax: "if는 조건이 참일 때만 아래 코드를 실행합니다. 에너지가 200 이상이면 고릴라, 500 이상이면 공룡으로 변신하는 규칙을 만들 수 있습니다.",
    pages: [
      ["1. 오늘의 장면", "에너지가 쌓이다가 기준을 넘으면 모습이 달라집니다."],
      ["2. 오늘의 코드", "gorilla_score와 dino_score가 변신에 필요한 에너지 기준입니다."],
      ["3. 기술 설명", "if energy >= dino_score: 는 에너지가 기준보다 크거나 같은지 묻는 조건입니다."],
      ["4. 바꿔보기", "변신 에너지를 낮추거나 높여 변신 속도를 비교합니다."],
      ["5. 미션", "너무 빨리도, 너무 늦게도 아닌 변신 에너지를 찾습니다."],
    ],
  },
  5: {
    title: "좋아하는 먹이",
    focus: "favorite_food",
    syntax: "== 는 두 값이 같은지 비교하는 연산자입니다. favorite_food와 먹은 아이템 이름이 같으면 보너스를 줄 수 있습니다.",
    pages: [
      ["1. 오늘의 장면", "좋아하는 고기를 먹으면 에너지 보너스가 붙습니다."],
      ["2. 오늘의 코드", "favorite_food가 먹은 아이템과 같으면 보너스 성장을 줍니다."],
      ["3. 기술 설명", "= 는 저장, == 는 비교입니다. 두 기호의 뜻이 완전히 다릅니다."],
      ["4. 바꿔보기", "favorite_food와 food_name을 같게 하거나 다르게 만들어 봅니다."],
      ["5. 미션", "내 괴수가 가장 좋아하는 먹이를 정합니다."],
    ],
  },
  6: {
    title: "장애물과 실패",
    focus: "hp",
    syntax: "else는 if 조건이 거짓일 때 실행됩니다. 방어막이 없는데 장애물에 닿으면 체력이 줄어드는 실패 규칙을 만들 수 있습니다.",
    pages: [
      ["1. 오늘의 장면", "세로 트랙에 장애물이 내려오고 체력 경고가 표시됩니다."],
      ["2. 오늘의 코드", "hp와 danger_limit이 위험 상태를 정합니다."],
      ["3. 기술 설명", "if가 성공 길이라면 else는 그렇지 않을 때 가는 길입니다."],
      ["4. 바꿔보기", "체력과 위험 기준을 바꿔 난이도를 조절합니다."],
      ["5. 미션", "실수해도 다시 도전하고 싶은 난이도를 만듭니다."],
    ],
  },
  7: {
    title: "먹이별 결과",
    focus: "flame_damage",
    syntax: "elif는 여러 조건을 차례로 검사합니다. 고기, 2배고기, 폭탄처럼 아이템이나 공격 종류마다 다른 결과를 만들 때 좋습니다.",
    pages: [
      ["1. 오늘의 장면", "먹은 아이템 종류에 따라 에너지가 올라가거나 내려갑니다."],
      ["2. 오늘의 코드", "flame_damage가 보스전 불똥 공격 피해를 만듭니다."],
      ["3. 기술 설명", "if, elif, else는 위에서 아래로 하나씩 확인합니다."],
      ["4. 바꿔보기", "불똥 피해와 보스 공격력을 바꾸고 보스전 결과를 비교합니다."],
      ["5. 미션", "첫 보스를 이길 만큼만 강한 괴수를 만듭니다."],
    ],
  },
  8: {
    title: "성장 단계",
    focus: "growth",
    syntax: "> 와 < 는 숫자의 크기를 비교합니다. 에너지가 낮을 때, 높을 때, 아주 높을 때를 나눠 화면에 다른 괴수를 보여 줄 수 있습니다.",
    pages: [
      ["1. 오늘의 장면", "원숭이, 고릴라, 공룡 단계가 뚜렷하게 보입니다."],
      ["2. 오늘의 코드", "에너지 기준을 이용해 현재 변신 단계를 계산합니다."],
      ["3. 기술 설명", "비교 연산의 결과는 True 또는 False가 됩니다."],
      ["4. 바꿔보기", "시작 성장값을 높여 바로 큰 괴수로 출발해 봅니다."],
      ["5. 미션", "세 단계가 모두 보이는 성장 속도를 찾습니다."],
    ],
  },
  9: {
    title: "보스 게이트",
    focus: "boss_name",
    syntax: ">= 와 <= 는 같은 값도 포함해 비교합니다. 러너 거리가 목표에 닿으면 전투장면으로 넘어갑니다.",
    pages: [
      ["1. 오늘의 장면", "달리기 끝에서 보스 게이트가 열리고 사이드뷰 전투로 전환됩니다."],
      ["2. 오늘의 코드", "boss_name은 마지막 보스 이름을 바꾸는 문자열입니다."],
      ["3. 기술 설명", "distance >= goal은 distance가 goal과 같아도 참입니다."],
      ["4. 바꿔보기", "보스 이름과 보스 공격력을 바꿔 봅니다."],
      ["5. 미션", "내 괴수에게 어울리는 보스 이름을 만듭니다."],
    ],
  },
  10: {
    title: "방어막과 대시",
    focus: "shield_ready",
    syntax: "and는 두 조건이 모두 참일 때만 참입니다. 방어막이 준비되어 있고 대시도 준비되어 있으면 위험한 장애물을 돌파할 수 있습니다.",
    pages: [
      ["1. 오늘의 장면", "방어막과 대시 조건이 러너 구간의 안전장치가 됩니다."],
      ["2. 오늘의 코드", "shield_ready와 dash_ready는 True 또는 False로 켜고 끕니다."],
      ["3. 기술 설명", "and는 양쪽 조건이 모두 True일 때만 성공합니다."],
      ["4. 바꿔보기", "방어막과 대시를 각각 켜고 꺼서 결과를 비교합니다."],
      ["5. 미션", "아이에게 쉬운 모드와 도전 모드를 만들어 봅니다."],
    ],
  },
  11: {
    title: "변신 코어",
    focus: "red_core",
    syntax: "or는 두 조건 중 하나만 참이어도 참입니다. 빨간 코어 또는 파란 코어 중 하나만 있어도 변신 보너스를 줄 수 있습니다.",
    pages: [
      ["1. 오늘의 장면", "변신 코어를 먹으면 성장 보너스와 반짝이는 변신 효과가 생깁니다."],
      ["2. 오늘의 코드", "red_core와 blue_core 중 하나가 True이면 코어 보너스가 켜집니다."],
      ["3. 기술 설명", "or는 선택지 중 하나만 성공해도 지나갈 수 있는 문입니다."],
      ["4. 바꿔보기", "빨간 코어와 파란 코어 값을 바꾸고 변신 보너스를 비교합니다."],
      ["5. 미션", "내 괴수가 좋아하는 변신 코어를 정합니다."],
    ],
  },
  12: {
    title: "괴수 왕 결전",
    focus: "boss_name",
    syntax: "조건문을 조합하면 러너 구간, 에너지 성장, 변신, 보스전이 하나의 게임 흐름으로 이어집니다. 에너지 200 고릴라, 에너지 500 공룡처럼 기준값을 읽는 연습을 합니다.",
    pages: [
      ["1. 오늘의 장면", "세로 러너 트랙에서 성장한 괴수가 최종 보스와 대전격투처럼 싸웁니다."],
      ["2. 오늘의 코드", "이번 챕터는 시즌2에서 만든 조건 규칙을 모두 사용합니다."],
      ["3. 기술 설명", "조건문은 게임 상태를 보고 다음 장면을 고르는 신호등입니다."],
      ["4. 바꿔보기", "보스 이름, 변신 에너지, 방어막, 대시, 공격 피해를 모두 조합합니다."],
      ["5. 미션", "내 괴수가 멋지게 성장하고 최종 보스를 이기는 밸런스를 완성합니다."],
    ],
  },
};

const seasonTwoBosses = [
  { name: "훈련 로봇", className: "bot", hp: 70, power: 7 },
  { name: "빌딩 골렘", className: "golem", hp: 95, power: 10 },
  { name: "번개 드론", className: "drone", hp: 120, power: 13 },
  { name: "메카 타이탄", className: "titan", hp: 150, power: 16 },
];

const projectFiles = [
  { name: "upgrade_zone.py", role: "오늘 바꾸는 웹 업그레이드 코드", editable: true },
  { name: "player_stats.py", role: "캐릭터 이름, 체력, 성장 데이터", editable: false },
  { name: "world_items.py", role: "보물, 먹이, 함정 데이터", editable: false },
  { name: "game_rules.py", role: "에너지, 이동, 조건 규칙", editable: false },
  { name: "save_data.py", role: "챕터별 저장 데이터", editable: false },
];

const state = {
  activeSeason: "season_01",
  activeChapter: 1,
  activeFile: "upgrade_zone.py",
  settings: {},
  save: null,
  game: {},
  lessonPage: 0,
  gameStarted: false,
  startNotice: false,
  gameTimer: null,
};

const audio = {
  context: null,
  music: null,
  musicGain: null,
};

const seasonTwoThree = {
  modulePromise: null,
  renderer: null,
  renderToken: 0,
  panToken: 0,
};

const els = {
  seasonSelect: document.querySelector("#seasonSelect"),
  chapterSelect: document.querySelector("#chapterSelect"),
  saveStatus: document.querySelector("#saveStatus"),
  fileTree: document.querySelector("#fileTree"),
  filePanelToggle: document.querySelector("#filePanelToggle"),
  activeFileLabel: document.querySelector("#activeFileLabel"),
  chapterLabel: document.querySelector("#chapterLabel"),
  seasonTitle: document.querySelector("#seasonTitle"),
  lessonBody: document.querySelector("#lessonBody"),
  prevLesson: document.querySelector("#prevLessonBtn"),
  nextLesson: document.querySelector("#nextLessonBtn"),
  lessonPageLabel: document.querySelector("#lessonPageLabel"),
  codeEditor: document.querySelector("#codeEditor"),
  parsedParams: document.querySelector("#parsedParams"),
  applyUpgrade: document.querySelector("#applyUpgradeBtn"),
  start: document.querySelector("#startGameBtn"),
  hudTitle: document.querySelector("#hudTitle"),
  hudStats: document.querySelector("#hudStats"),
  gameMount: document.querySelector("#gameMount"),
  action: document.querySelector("#actionBtn"),
  reset: document.querySelector("#resetBtn"),
};

function getAudioContext() {
  if (!audio.context) {
    const AudioContextClass = window.AudioContext || window.webkitAudioContext;
    if (!AudioContextClass) return null;
    audio.context = new AudioContextClass();
  }
  if (audio.context.state === "suspended") audio.context.resume();
  return audio.context;
}

function playTone({ frequency = 440, duration = 0.08, type = "square", volume = 0.04, slide = 0 }) {
  const context = getAudioContext();
  if (!context) return;
  const oscillator = context.createOscillator();
  const gain = context.createGain();
  const now = context.currentTime;
  oscillator.type = type;
  oscillator.frequency.setValueAtTime(frequency, now);
  if (slide) oscillator.frequency.exponentialRampToValueAtTime(Math.max(40, frequency + slide), now + duration);
  gain.gain.setValueAtTime(0.0001, now);
  gain.gain.exponentialRampToValueAtTime(volume, now + 0.012);
  gain.gain.exponentialRampToValueAtTime(0.0001, now + duration);
  oscillator.connect(gain);
  gain.connect(context.destination);
  oscillator.start(now);
  oscillator.stop(now + duration + 0.02);
}

function playFootstep() {
  playTone({ frequency: 120 + Math.random() * 34, duration: 0.055, type: "triangle", volume: 0.035, slide: -42 });
}

function playPickupSound(kind) {
  if (kind === "trap") {
    playTone({ frequency: 120, duration: 0.16, type: "sawtooth", volume: 0.055, slide: -72 });
    return;
  }
  playTone({ frequency: 520, duration: 0.08, type: "square", volume: 0.045, slide: 180 });
  window.setTimeout(() => playTone({ frequency: 780, duration: 0.08, type: "square", volume: 0.036, slide: 120 }), 70);
}

function startMusic() {
  const context = getAudioContext();
  if (!context || audio.music) return;
  const gain = context.createGain();
  gain.gain.setValueAtTime(0.018, context.currentTime);
  gain.connect(context.destination);
  audio.musicGain = gain;

  const notes = [196, 247, 294, 247, 220, 262, 330, 262];
  let index = 0;
  audio.music = window.setInterval(() => {
    if (!state.gameStarted) return;
    const frequency = notes[index % notes.length];
    index += 1;
    const oscillator = context.createOscillator();
    const noteGain = context.createGain();
    const now = context.currentTime;
    oscillator.type = "triangle";
    oscillator.frequency.setValueAtTime(frequency, now);
    noteGain.gain.setValueAtTime(0.0001, now);
    noteGain.gain.exponentialRampToValueAtTime(0.75, now + 0.03);
    noteGain.gain.exponentialRampToValueAtTime(0.0001, now + 0.28);
    oscillator.connect(noteGain);
    noteGain.connect(gain);
    oscillator.start(now);
    oscillator.stop(now + 0.32);
  }, 360);
}

function stopMusic() {
  if (audio.music) {
    window.clearInterval(audio.music);
    audio.music = null;
  }
  if (audio.musicGain && audio.context) {
    const now = audio.context.currentTime;
    audio.musicGain.gain.cancelScheduledValues(now);
    audio.musicGain.gain.setValueAtTime(audio.musicGain.gain.value, now);
    audio.musicGain.gain.exponentialRampToValueAtTime(0.0001, now + 0.04);
    window.setTimeout(() => {
      audio.musicGain?.disconnect();
      audio.musicGain = null;
    }, 80);
  }
}

function toNumber(value, fallback) {
  const number = Number(value);
  return Number.isFinite(number) ? number : fallback;
}

function toBool(value) {
  return String(value).trim().toLowerCase() === "true";
}

function listFromText(value) {
  return String(value)
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

function defaultSettings(seasonKey) {
  return Object.fromEntries(seasons[seasonKey].fields.map(([key, , value]) => [key, value]));
}

function getSeasonSave(seasonKey) {
  return state.save?.seasons?.[seasonKey] || {};
}

function setStatus(message) {
  els.saveStatus.textContent = message;
}

function chapterOffset(seasonKey = state.activeSeason) {
  return { season_01: 0, season_02: 12, season_03: 24, season_04: 36 }[seasonKey] || 0;
}

function globalChapterNumber(seasonKey = state.activeSeason, localChapter = state.activeChapter) {
  return chapterOffset(seasonKey) + Number(localChapter);
}

function activeChapterInfo() {
  if (state.activeSeason === "season_01") return seasonOneChapters[state.activeChapter];
  if (state.activeSeason === "season_02") return seasonTwoChapters[state.activeChapter];
  return null;
}

function activeEditPlan() {
  if (state.activeSeason === "season_01") return seasonOneEditPlans[state.activeChapter];
  if (state.activeSeason === "season_02") return seasonTwoEditPlans[state.activeChapter];
  return null;
}

function readFields() {
  state.settings[state.activeSeason] = parseCode(state.activeSeason, els.codeEditor.value);
}

function renderFields() {
  const season = seasons[state.activeSeason];
  const settings = state.settings[state.activeSeason] || defaultSettings(state.activeSeason);
  const chapterInfo = activeChapterInfo();
  const editPlan = activeEditPlan();
  els.chapterLabel.textContent = chapterInfo && editPlan
    ? `챕터 ${globalChapterNumber()} / ${chapterOffset() + 12} · ${editPlan.lines}줄 수정`
    : season.chapters;
  els.seasonTitle.textContent = chapterInfo ? chapterInfo.title : season.title;
  if (!els.parsedParams) return;
  els.parsedParams.innerHTML = "";

  for (const [key, label, value] of season.fields) {
    const wrap = document.createElement("div");
    wrap.className = "param-row";
    wrap.innerHTML = `
      <strong>${label}</strong>
      <span>${settings[key] ?? value}</span>
    `;
    els.parsedParams.appendChild(wrap);
  }
}

function updateSaveSeason(seasonKey, patch) {
  if (!state.save) return;
  state.save.seasons ||= {};
  state.save.seasons[seasonKey] = {
    ...(state.save.seasons[seasonKey] || {}),
    ...patch,
  };
}

function setHud(title, stats) {
  els.hudTitle.textContent = title;
  els.hudStats.innerHTML = "";
  String(stats).split(" · ").forEach((part, index) => {
    if (index > 0) els.hudStats.append(document.createTextNode(" · "));
    const node = document.createElement("span");
    node.className = part.startsWith("점수 ") || part.startsWith("에너지 ") ? "hud-score" : "";
    node.textContent = part;
    els.hudStats.append(node);
  });
}

function renderFileTree() {
  els.activeFileLabel.textContent = state.activeFile;
  els.fileTree.innerHTML = projectFiles
    .map((file) => `
      <button
        type="button"
        data-file="${file.name}"
        class="file-item ${state.activeFile === file.name ? "active" : ""}"
        ${state.gameStarted ? "disabled" : ""}
      >
        <span>${file.name}</span>
        <small>${file.role}</small>
      </button>
    `)
    .join("");
}

function setFilePanelCollapsed(collapsed, persist = true) {
  document.body.classList.toggle("file-tree-collapsed", collapsed);
  if (els.filePanelToggle) {
    els.filePanelToggle.setAttribute("aria-expanded", String(!collapsed));
    els.filePanelToggle.setAttribute("aria-label", collapsed ? "파일트리 펼치기" : "파일트리 접기");
    els.filePanelToggle.title = collapsed ? "파일트리 펼치기" : "파일트리 접기";
  }
  if (persist) localStorage.setItem("guma-file-tree-collapsed", collapsed ? "1" : "0");
}

function initFilePanelState() {
  const saved = localStorage.getItem("guma-file-tree-collapsed");
  setFilePanelCollapsed(saved === null ? true : saved === "1", false);
}

function readOnlyFileContent(fileName) {
  const s = state.settings[state.activeSeason] || defaultSettings(state.activeSeason);
  if (state.activeSeason === "season_02") {
    if (fileName === "player_stats.py") {
      return [
        "# player_stats.py",
        "# 읽기 전용: 시즌 2 괴수의 이름, 체력, 성장 데이터입니다.",
        "",
        `baby_name = "${s.baby_name || "꼬마구마"}"`,
        `roar_text = "${s.roar_text || "우와앙! 더 커질 거야!"}"`,
        `start_size = ${toNumber(s.start_size, 1)}`,
        `growth = ${toNumber(s.growth, 0)}`,
        `hp = ${toNumber(s.hp, 100)}`,
      ].join("\n");
    }
    if (fileName === "world_items.py") {
      return [
        "# world_items.py",
        "# 읽기 전용: 러너 트랙의 먹이, 코어, 장애물 데이터입니다.",
        "",
        `favorite_food = "${s.favorite_food || "고기"}"`,
        `snack_score = ${toNumber(s.snack_score, 10)}`,
        `meat_score = ${toNumber(s.meat_score, 100)}`,
        `growth_per_item = ${toNumber(s.growth_per_item, 12)}`,
        `mutation_size = ${toNumber(s.mutation_size, 60)}`,
        `gorilla_score = ${toNumber(s.gorilla_score, 200)}`,
        `dino_score = ${toNumber(s.dino_score, 500)}`,
        "",
        'runner_items = ["고기", "폭탄", "2배고기", "핵폭탄"]',
      ].join("\n");
    }
    if (fileName === "game_rules.py") {
      return [
        "# game_rules.py",
        "# 읽기 전용: 조건문이 러너 게임 규칙으로 바뀌는 곳입니다.",
        "",
        `run_speed = ${toNumber(s.run_speed, 5)}`,
        `danger_limit = ${toNumber(s.danger_limit, 35)}`,
        `attack_power = ${toNumber(s.attack_power, 18)}`,
        `flame_damage = ${toNumber(s.flame_damage, 200)}`,
        `boss_power = ${toNumber(s.boss_power, 24)}`,
        `target_energy = ${seasonTwoTargetEnergy(seasonTwoChapter(), s)}`,
        `shield_ready = ${toBool(s.shield_ready) ? "True" : "False"}`,
        `dash_ready = ${toBool(s.dash_ready) ? "True" : "False"}`,
        `red_core = ${toBool(s.red_core) ? "True" : "False"}`,
        `blue_core = ${toBool(s.blue_core) ? "True" : "False"}`,
        "",
        "can_dash_shield = shield_ready and dash_ready",
        "has_core_bonus = red_core or blue_core",
        "final_attack = flame_damage",
        "if has_core_bonus:",
        "    final_attack = flame_damage + 50",
      ].join("\n");
    }
    if (fileName === "save_data.py") {
      return [
        "# save_data.py",
        "# 읽기 전용: 시즌 2 저장 데이터 예시입니다.",
        "",
        "save_data = {",
        `    "chapter": ${globalChapterNumber()},`,
        `    "baby_name": "${s.baby_name || "꼬마구마"}",`,
        '    "best_energy": 0,',
        '    "boss_clear": False,',
        "}",
      ].join("\n");
    }
  }
  if (fileName === "player_stats.py") {
    return [
      "# player_stats.py",
      "# 읽기 전용: 주인공 기본 데이터가 모여 있는 파일입니다.",
      "",
      `hero_name = "${s.hero_name || "번개용사"}"`,
      `hp = ${toNumber(s.hp, 100)}`,
      `potion_heal = ${toNumber(s.potion_heal, 20)}`,
      `speed = ${toNumber(s.speed, 5)}`,
      `wind_multiplier = ${toNumber(s.wind_multiplier, 2)}`,
      "",
      "has_wind_shoes = False",
    ].join("\n");
  }
  if (fileName === "world_items.py") {
    return [
      "# world_items.py",
      "# 읽기 전용: 게임 안 아이템과 함정 데이터입니다.",
      "",
      `starter_chest_point = ${toNumber(s.starter_chest_point, 10)}`,
      `treasure_point = ${toNumber(s.treasure_point, 10)}`,
      `coin_point = ${toNumber(s.coin_point, 5)}`,
      `gem_point = ${toNumber(s.gem_point, 20)}`,
      `chest_point = ${toNumber(s.chest_point, 30)}`,
      `trap_damage = ${toNumber(s.trap_damage, 20)}`,
      `trap_speed = ${toNumber(s.trap_speed, 2)}`,
      `bonus_multiplier = ${toNumber(s.bonus_multiplier, 2)}`,
      "",
      "items = [",
      `    "${s.starter_chest_label || "보물상자"}",`,
      `    "${s.treasure_label || "보물"}",`,
      `    "${s.coin_label || "동전"}",`,
      `    "${s.potion_label || "체력 물약"}",`,
      `    "${s.wind_shoes_label || "바람신발"}",`,
      `    "${s.gem_label || "루비"}",`,
      `    "${s.chest_label || "상자"}",`,
      `    "${s.trap_label || "함정"}",`,
      `    "${s.bonus_label || "보너스별"}",`,
      `    "${s.portal_label || "포털"}",`,
      "]",
    ].join("\n");
  }
  if (fileName === "game_rules.py") {
    return [
      "# game_rules.py",
      "# 읽기 전용: 업그레이드 값이 쉬운 계산식으로 바뀌는 곳입니다.",
      "import random",
      "",
      "base_speed = speed",
      "wind_speed = speed * wind_multiplier",
      "",
      "treasure_1 = treasure_point",
      "treasure_2 = gem_point",
      "treasure_3 = chest_point",
      "trap_1 = trap_damage",
      "current_score = treasure_1 + treasure_2 + treasure_3 - trap_1",
      "",
      "potion_hp = hp + potion_heal",
      "",
      "trap_x_step = random.choice([-1, 0, 1]) * trap_speed",
      "trap_y_step = random.choice([-1, 0, 1]) * trap_speed",
      "hp_after_trap = hp - trap_damage",
      "",
      "bonus_score = current_score * bonus_multiplier",
    ].join("\n");
  }
  if (fileName === "save_data.py") {
    return [
      "# save_data.py",
      "# 읽기 전용: 챕터별 저장 데이터 예시입니다.",
      "",
      "save_data = {",
      `    "chapter": ${state.activeChapter},`,
      `    "hero_name": "${s.hero_name || "번개용사"}",`,
      '    "high_score": 0,',
      '    "best_hp": 0,',
      "}",
    ].join("\n");
  }
  return [
    "# GumaKidsPython",
    "",
    "웹버전에서 upgrade_zone.py를 바꾸고 바로 게임 화면에서 확인합니다.",
  ].join("\n");
}

function fileContent(fileName) {
  if (fileName === "upgrade_zone.py") return generateCode(state.activeSeason);
  return readOnlyFileContent(fileName);
}

function currentLessonPages() {
  if (state.activeSeason === "season_01") {
    const chapter = seasonOneChapters[state.activeChapter];
    const plan = seasonOneEditPlans[state.activeChapter];
    const editTargets = plan.labels.join(", ");
    return [
      chapter.pages[0],
      chapter.pages[1],
      ["3. 쉬운 문법", chapter.syntax],
      ["4. 오늘 게임에 생기는 것", seasonOneUnlocks[state.activeChapter]],
      ["5. 오늘 수정할 코드", `오늘은 ${plan.lines}줄을 수정합니다. 코드 화면에서 ${editTargets} 줄을 찾아 값을 바꾸고, 게임 화면에서 바로 확인합니다.`],
      chapter.pages[3],
      chapter.pages[4],
    ];
  }
  if (state.activeSeason === "season_02") {
    const chapter = seasonTwoChapters[state.activeChapter];
    const plan = seasonTwoEditPlans[state.activeChapter];
    const editTargets = plan.labels.join(", ");
    return [
      chapter.pages[0],
      chapter.pages[1],
      ["3. 쉬운 문법", chapter.syntax],
      ["4. 오늘 게임에 생기는 것", seasonTwoUnlocks[state.activeChapter]],
      ["5. 오늘 업그레이드 코드", `오늘은 ${plan.lines}줄을 업그레이드합니다. 코드 화면에서 ${editTargets} 값을 찾아 바꾸고, 러너 게임에서 성장과 변신이 어떻게 달라지는지 확인합니다.`],
      chapter.pages[3],
      chapter.pages[4],
    ];
  }
  return seasons[state.activeSeason].lesson;
}

function renderChapterTabs() {
  const ranges = {
    season_01: [1, 12],
    season_02: [13, 24],
    season_03: [25, 36],
    season_04: [37, 48],
  };
  const [start, end] = ranges[state.activeSeason] || ranges.season_01;
  els.seasonSelect.value = state.activeSeason;
  els.chapterSelect.innerHTML = "";

  for (let chapter = start; chapter <= end; chapter += 1) {
    const localChapter = ((chapter - 1) % 12) + 1;
    const option = document.createElement("option");
    const title = state.activeSeason === "season_01"
      ? seasonOneChapters[localChapter].title
      : state.activeSeason === "season_02"
        ? seasonTwoChapters[localChapter].title
        : `챕터 ${chapter}`;
    option.value = String(localChapter);
    option.textContent = `${chapter}. ${title}`;
    option.selected = localChapter === state.activeChapter;
    els.chapterSelect.appendChild(option);
  }
}

function setLockedControls() {
  const seasonTwoBossActive = state.activeSeason === "season_02" && state.gameStarted && state.game.season_02?.phase === "boss";
  const seasonTwoBossInputLocked = seasonTwoBossActive && seasonTwoInputLocked(state.game.season_02);
  const seasonTwoRunnerActive = state.activeSeason === "season_02" && state.gameStarted && state.game.season_02?.phase === "runner";
  els.start.textContent = seasonTwoBossActive ? "보스전 진행중" : state.gameStarted ? "게임 중지" : "게임 시작";
  els.start.disabled = seasonTwoBossActive;
  els.start.classList.toggle("stop", state.gameStarted && !seasonTwoBossActive);
  els.action.disabled = seasonTwoRunnerActive || seasonTwoBossInputLocked;
  els.codeEditor.disabled = state.gameStarted || state.activeFile !== "upgrade_zone.py";
  els.applyUpgrade.disabled = state.gameStarted;
  els.prevLesson.disabled = state.gameStarted || state.lessonPage === 0;
  els.nextLesson.disabled = state.gameStarted || state.lessonPage === currentLessonPages().length - 1;
  els.seasonSelect.disabled = state.gameStarted;
  els.chapterSelect.disabled = state.gameStarted;
  els.fileTree.querySelectorAll("button").forEach((button) => {
    button.disabled = state.gameStarted;
  });
}

function renderLesson() {
  const lesson = currentLessonPages();
  state.lessonPage = Math.max(0, Math.min(state.lessonPage, lesson.length - 1));
  const [title, body] = lesson[state.lessonPage];
  const dots = lesson
    .map((_, index) => `<span class="lesson-dot ${index === state.lessonPage ? "active" : ""}" aria-hidden="true"></span>`)
    .join("");
  els.lessonBody.innerHTML = `
    <article class="lesson-note active-lesson">
      <div class="lesson-page-art" aria-hidden="true">
        <span class="lesson-sun"></span>
        <span class="lesson-star star-a"></span>
        <span class="lesson-star star-b"></span>
      </div>
      <strong>${title}</strong>
      <p>${body}</p>
      <div class="lesson-progress" aria-hidden="true">${dots}</div>
    </article>
  `;
  els.lessonPageLabel.textContent = `${state.lessonPage + 1} / ${lesson.length}`;
  setLockedControls();
}

function quoteList(text) {
  return listFromText(text).map((item) => `"${item}"`).join(", ");
}

function generateCode(seasonKey) {
  const s = state.settings[seasonKey] || defaultSettings(seasonKey);
  const today = (chapter) => {
    if (seasonKey !== "season_01" || state.activeChapter !== chapter) return null;
    const plan = seasonOneEditPlans[chapter];
    return `# [오늘의 업그레이드: ${plan.lines}줄]\n# ${plan.labels.join(", ")} 값을 바꿔 게임 화면에서 확인합니다.`;
  };
  if (seasonKey === "season_01") {
    const activePlan = seasonOneEditPlans[state.activeChapter] || { lines: 1, keys: [], labels: [] };
    const targetHint = (key) => {
      const index = activePlan.keys.indexOf(key);
      if (index < 0) return null;
      return `# 오늘 줄 ${index + 1}/${activePlan.lines}: ${activePlan.labels[index]}`;
    };
    const startScore = toNumber(s.start_score, 10);
    const score = toNumber(s.score, startScore);
    const hp = toNumber(s.hp, 100);
    const heroName = s.hero_name || "번개용사";
    const missionText = s.mission_text || `${heroName}의 미션: 보물 3개 모으기`;
    const defaultMissionStatus = `${heroName} 미션: 점수 ${score}, 체력 ${hp}`;
    const missionStatus = s.mission_status || s.status_text || defaultMissionStatus;
    const scoreLine = score === startScore ? "score = start_score" : `score = ${score}`;
    const missionLine = missionText === `${heroName}의 미션: 보물 3개 모으기` ? 'mission_text = hero_name + "의 미션: 보물 3개 모으기"' : `mission_text = "${missionText}"`;
    const missionStatusLine = missionStatus === defaultMissionStatus ? 'mission_status = f"{hero_name} 미션: 점수 {score}, 체력 {hp}"' : `mission_status = "${missionStatus}"`;
    return [
      "# 시즌 1: 보물 점수 게임 업그레이드 존",
      "# 전체 코드를 볼 수 있습니다. 오늘 배울 곳은 [오늘의 업그레이드] 아래입니다.",
      "import random",
      "",
      "# =========================",
      "# [챕터 1] 게임 시작 문장",
      today(1),
      "# =========================",
      targetHint("start_message"),
      `start_message = "${s.start_message}"`,
      "",
      "# =========================",
      "# [챕터 2] 주인공 대사",
      today(2),
      "# =========================",
      targetHint("hero_message"),
      `hero_message = "${s.hero_message}"`,
      "",
      "# =========================",
      "# [챕터 3] 주인공 이름",
      today(3),
      "# =========================",
      targetHint("hero_name"),
      `hero_name = "${s.hero_name}"`,
      "",
      "# =========================",
      "# [챕터 4] 시작 점수",
      today(4),
      "# =========================",
      targetHint("start_score"),
      `start_score = ${toNumber(s.start_score, 10)}`,
      targetHint("starter_chest_point"),
      `starter_chest_point = ${toNumber(s.starter_chest_point, 10)}`,
      "",
      "# =========================",
      "# [챕터 5] 보상 점수",
      today(5),
      "# =========================",
      targetHint("score"),
      scoreLine,
      targetHint("treasure_point"),
      `treasure_point = ${toNumber(s.treasure_point, 10)}`,
      targetHint("coin_point"),
      `coin_point = ${toNumber(s.coin_point, 5)}`,
      "",
      "# =========================",
      "# [챕터 6] 체력",
      today(6),
      "# =========================",
      targetHint("hp"),
      `hp = ${toNumber(s.hp, 100)}`,
      targetHint("potion_heal"),
      `potion_heal = ${toNumber(s.potion_heal, 20)}`,
      "",
      "# =========================",
      "# [챕터 7] 이동 속도와 바람신발",
      today(7),
      "# =========================",
      targetHint("speed"),
      `speed = ${toNumber(s.speed, 5)}`,
      targetHint("wind_multiplier"),
      `wind_multiplier = ${toNumber(s.wind_multiplier, 2)}`,
      "",
      "# =========================",
      "# [챕터 8] 미션 만들기",
      today(8),
      "# =========================",
      targetHint("mission_text"),
      missionLine,
      "",
      "# =========================",
      "# [챕터 9] 미션 상태판",
      today(9),
      "# =========================",
      targetHint("mission_status"),
      missionStatusLine,
      "",
      "# =========================",
      "# [화면 이름표] 게임에 보이는 이름",
      "# =========================",
      `starter_chest_label = "${s.starter_chest_label || "보물상자"}"`,
      `treasure_label = "${s.treasure_label || "보물"}"`,
      `coin_label = "${s.coin_label || "동전"}"`,
      `potion_label = "${s.potion_label || "체력 물약"}"`,
      `wind_shoes_label = "${s.wind_shoes_label || "바람신발"}"`,
      `gem_label = "${s.gem_label || "루비"}"`,
      `chest_label = "${s.chest_label || "상자"}"`,
      targetHint("trap_label"),
      `trap_label = "${s.trap_label || "함정"}"`,
      `bonus_label = "${s.bonus_label || "보너스별"}"`,
      `portal_label = "${s.portal_label || "포털"}"`,
      `portal_hint = "${s.portal_hint || "보물을 모아 포털을 열자"}"`,
      "",
      "# =========================",
      "# [챕터 10] 더하기 빼기 마법",
      today(10),
      "# =========================",
      `gem_point = ${toNumber(s.gem_point, 20)}`,
      `chest_point = ${toNumber(s.chest_point, 30)}`,
      `trap_damage = ${toNumber(s.trap_damage, 20)}`,
      "",
      "# 보물은 더하고, 함정은 뺍니다.",
      targetHint("treasure_1"),
      `treasure_1 = ${toNumber(s.treasure_1, toNumber(s.treasure_point, 10))}`,
      targetHint("treasure_2"),
      `treasure_2 = ${toNumber(s.treasure_2, toNumber(s.gem_point, 20))}`,
      targetHint("treasure_3"),
      `treasure_3 = ${toNumber(s.treasure_3, toNumber(s.chest_point, 30))}`,
      targetHint("trap_1"),
      `trap_1 = ${toNumber(s.trap_1, toNumber(s.trap_damage, 20))}`,
      targetHint("current_score"),
      "current_score = treasure_1 + treasure_2 + treasure_3 - trap_1",
      "score = current_score",
      "",
      "# =========================",
      "# [챕터 11] 랜덤 함정",
      today(11),
      "# =========================",
      targetHint("trap_speed"),
      `trap_speed = ${toNumber(s.trap_speed, 2)}`,
      "",
      "trap_x_step = random.choice([-1, 0, 1]) * trap_speed",
      "trap_y_step = random.choice([-1, 0, 1]) * trap_speed",
      "hp_after_trap = hp - trap_damage",
      "",
      "# =========================",
      "# [챕터 12] 보너스 점수",
      today(12),
      "# =========================",
      targetHint("bonus_multiplier"),
      `bonus_multiplier = ${toNumber(s.bonus_multiplier, 2)}`,
      "",
      "bonus_score = current_score * bonus_multiplier",
    ].filter((line) => line !== null).join("\n");
  }
  if (seasonKey === "season_02") {
    const activePlan = seasonTwoEditPlans[state.activeChapter] || { lines: 1, keys: [], labels: [] };
    const targetHint = (key, chapter) => {
      if (chapter !== state.activeChapter) return null;
      const index = activePlan.keys.indexOf(key);
      if (index < 0) return null;
      return `# 오늘 줄 ${index + 1}/${activePlan.lines}: ${activePlan.labels[index]}`;
    };
    return [
      "# 시즌 2: 괴수 러너 성장 게임 업그레이드 존",
      "# 전체 코드를 볼 수 있습니다. 오늘 배울 곳은 [오늘의 업그레이드] 아래입니다.",
      "# 웹버전에서는 input()을 직접 띄우지 않고, 아래 변수 값을 바꿔 입력처럼 사용합니다.",
      "",
      "# =========================",
      "# [챕터 13] 원숭이 이름 입력",
      "# baby_name = input(\"괴수 이름은? \") 와 같은 역할입니다.",
      `# [오늘의 업그레이드: ${activePlan.lines}줄]`,
      "# =========================",
      targetHint("baby_name", 1),
      `baby_name = "${s.baby_name}"`,
      "",
      "# =========================",
      "# [챕터 14] 포효 문자열",
      "# =========================",
      targetHint("runner_title", 2),
      `runner_title = "${s.runner_title}"`,
      targetHint("roar_text", 2),
      `roar_text = "${s.roar_text}"`,
      "",
      "# =========================",
      "# [챕터 15] 숫자 에너지",
      "# snack_score = int(input(\"첫 에너지는? \")) 와 같은 생각입니다.",
      "# =========================",
      targetHint("start_size", 3),
      `start_size = ${toNumber(s.start_size, 1)}`,
      targetHint("snack_score", 3),
      `snack_score = ${toNumber(s.snack_score, 10)}`,
      targetHint("meat_score", 3),
      `meat_score = ${toNumber(s.meat_score, 100)}`,
      "start_energy = hp + snack_score",
      "",
      "# =========================",
      "# [챕터 16] if로 변신 조건 만들기",
      "# =========================",
      targetHint("mutation_size", 4),
      `mutation_size = ${toNumber(s.mutation_size, 60)}`,
      targetHint("gorilla_score", 4),
      `gorilla_score = ${toNumber(s.gorilla_score, 200)}`,
      targetHint("dino_score", 4),
      `dino_score = ${toNumber(s.dino_score, 500)}`,
      "",
      "energy = hp + meat_score",
      targetHint("mutation_result", 4),
      "mutation_result = \"원숭이\"",
      "if energy >= dino_score:",
      "    mutation_result = \"공룡\"",
      "elif energy >= gorilla_score:",
      "    mutation_result = \"고릴라\"",
      "",
      "# =========================",
      "# [챕터 17] == 로 좋아하는 먹이 확인",
      "# =========================",
      targetHint("baby_name", 5),
      `baby_name = "${s.baby_name}"`,
      targetHint("favorite_food", 5),
      `favorite_food = "${s.favorite_food}"`,
      targetHint("food_name", 5),
      `food_name = "${s.food_name || "고기"}"`,
      targetHint("meat_score", 5),
      `meat_score = ${toNumber(s.meat_score, 100)}`,
      targetHint("favorite_bonus", 5),
      `favorite_bonus = ${toNumber(s.favorite_bonus, 20)}`,
      "",
      "food_energy = meat_score",
      "if food_name == favorite_food:",
      "    food_energy = meat_score + favorite_bonus",
      "",
      "# =========================",
      "# [챕터 18] else로 장애물 실패 처리",
      "# =========================",
      targetHint("baby_name", 6),
      `baby_name = "${s.baby_name}"`,
      targetHint("hp", 6),
      `hp = ${toNumber(s.hp, 100)}`,
      targetHint("danger_limit", 6),
      `danger_limit = ${toNumber(s.danger_limit, 35)}`,
      targetHint("has_shield", 6),
      `has_shield = ${toBool(s.has_shield) ? "True" : "False"}`,
      targetHint("run_speed", 6),
      `run_speed = ${toNumber(s.run_speed, 5)}`,
      "",
      targetHint("obstacle_result", 6),
      "obstacle_result = \"방어 성공\"",
      "if has_shield:",
      "    obstacle_result = \"방어막으로 통과\"",
      "else:",
      "    hp = hp - 20",
      "    obstacle_result = \"체력 감소\"",
      "is_danger = hp < danger_limit",
      "",
      "# =========================",
      "# [챕터 19] elif로 먹이별 결과 만들기",
      "# =========================",
      targetHint("baby_name", 7),
      `baby_name = "${s.baby_name}"`,
      targetHint("item_name", 7),
      `item_name = "${s.item_name || "고기"}"`,
      targetHint("meat_score", 7),
      `meat_score = ${toNumber(s.meat_score, 100)}`,
      targetHint("bomb_damage", 7),
      `bomb_damage = ${toNumber(s.bomb_damage, 70)}`,
      targetHint("attack_power", 7),
      `attack_power = ${toNumber(s.attack_power, 18)}`,
      targetHint("flame_damage", 7),
      `flame_damage = ${toNumber(s.flame_damage, 200)}`,
      targetHint("boss_power", 7),
      `boss_power = ${toNumber(s.boss_power, 24)}`,
      "",
      targetHint("item_result", 7),
      "item_result = 0",
      "if item_name == \"고기\":",
      "    item_result = meat_score",
      "elif item_name == \"2배고기\":",
      "    item_result = meat_score * 2",
      "elif item_name == \"폭탄\":",
      "    item_result = -bomb_damage",
      "else:",
      "    item_result = 0",
      "",
      "# =========================",
      "# [챕터 20] > 와 < 로 위험 상태 비교",
      "# =========================",
      targetHint("runner_title", 8),
      `runner_title = "${s.runner_title}"`,
      targetHint("roar_text", 8),
      `roar_text = "${s.roar_text}"`,
      targetHint("start_size", 8),
      `start_size = ${toNumber(s.start_size, 1)}`,
      targetHint("meat_score", 8),
      `meat_score = ${toNumber(s.meat_score, 100)}`,
      targetHint("gorilla_score", 8),
      `gorilla_score = ${toNumber(s.gorilla_score, 200)}`,
      targetHint("dino_score", 8),
      `dino_score = ${toNumber(s.dino_score, 500)}`,
      targetHint("run_speed", 8),
      `run_speed = ${toNumber(s.run_speed, 5)}`,
      targetHint("danger_limit", 8),
      `danger_limit = ${toNumber(s.danger_limit, 35)}`,
      targetHint("growth", 8),
      `growth = ${toNumber(s.growth, 0)}`,
      "",
      "is_danger = hp < danger_limit",
      "is_fast_runner = run_speed > 6",
      "",
      "# =========================",
      "# [챕터 21] >= 로 보스 게이트 열기",
      "# =========================",
      targetHint("baby_name", 9),
      `baby_name = "${s.baby_name}"`,
      targetHint("runner_title", 9),
      `runner_title = "${s.runner_title}"`,
      targetHint("roar_text", 9),
      `roar_text = "${s.roar_text}"`,
      targetHint("hp", 9),
      `hp = ${toNumber(s.hp, 100)}`,
      targetHint("danger_limit", 9),
      `danger_limit = ${toNumber(s.danger_limit, 35)}`,
      targetHint("run_speed", 9),
      `run_speed = ${toNumber(s.run_speed, 5)}`,
      targetHint("flame_damage", 9),
      `flame_damage = ${toNumber(s.flame_damage, 200)}`,
      targetHint("boss_power", 9),
      `boss_power = ${toNumber(s.boss_power, 24)}`,
      targetHint("boss_name", 9),
      `boss_name = "${s.boss_name}"`,
      "",
      "target_energy = dino_score",
      "can_enter_boss_gate = energy >= target_energy",
      "",
      "# =========================",
      "# [챕터 22] and 조건: 방어막과 대시",
      "# =========================",
      targetHint("baby_name", 10),
      `baby_name = "${s.baby_name}"`,
      targetHint("gorilla_score", 10),
      `gorilla_score = ${toNumber(s.gorilla_score, 200)}`,
      targetHint("dino_score", 10),
      `dino_score = ${toNumber(s.dino_score, 500)}`,
      targetHint("shield_ready", 10),
      `shield_ready = ${toBool(s.shield_ready) ? "True" : "False"}`,
      targetHint("dash_ready", 10),
      `dash_ready = ${toBool(s.dash_ready) ? "True" : "False"}`,
      targetHint("hp", 10),
      `hp = ${toNumber(s.hp, 100)}`,
      targetHint("run_speed", 10),
      `run_speed = ${toNumber(s.run_speed, 5)}`,
      targetHint("boss_power", 10),
      `boss_power = ${toNumber(s.boss_power, 24)}`,
      targetHint("boss_name", 10),
      `boss_name = "${s.boss_name}"`,
      "",
      targetHint("can_dash_shield", 10),
      "can_dash_shield = shield_ready and dash_ready",
      "",
      "# =========================",
      "# [챕터 23] or 조건: 변신 코어",
      "# =========================",
      targetHint("baby_name", 11),
      `baby_name = "${s.baby_name}"`,
      targetHint("favorite_food", 11),
      `favorite_food = "${s.favorite_food}"`,
      targetHint("red_core", 11),
      `red_core = ${toBool(s.red_core) ? "True" : "False"}`,
      targetHint("blue_core", 11),
      `blue_core = ${toBool(s.blue_core) ? "True" : "False"}`,
      targetHint("meat_score", 11),
      `meat_score = ${toNumber(s.meat_score, 100)}`,
      targetHint("gorilla_score", 11),
      `gorilla_score = ${toNumber(s.gorilla_score, 200)}`,
      targetHint("dino_score", 11),
      `dino_score = ${toNumber(s.dino_score, 500)}`,
      targetHint("flame_damage", 11),
      `flame_damage = ${toNumber(s.flame_damage, 200)}`,
      targetHint("boss_power", 11),
      `boss_power = ${toNumber(s.boss_power, 24)}`,
      "",
      targetHint("has_core_bonus", 11),
      "has_core_bonus = red_core or blue_core",
      "",
      "# =========================",
      "# [챕터 24] 조건문 종합 보스전",
      "# =========================",
      targetHint("baby_name", 12),
      `baby_name = "${s.baby_name}"`,
      targetHint("runner_title", 12),
      `runner_title = "${s.runner_title}"`,
      targetHint("roar_text", 12),
      `roar_text = "${s.roar_text}"`,
      targetHint("meat_score", 12),
      `meat_score = ${toNumber(s.meat_score, 100)}`,
      targetHint("gorilla_score", 12),
      `gorilla_score = ${toNumber(s.gorilla_score, 200)}`,
      targetHint("dino_score", 12),
      `dino_score = ${toNumber(s.dino_score, 500)}`,
      targetHint("final_attack", 12),
      "final_attack = flame_damage",
      targetHint("boss_power", 12),
      `boss_power = ${toNumber(s.boss_power, 24)}`,
      targetHint("boss_name", 12),
      `boss_name = "${s.boss_name}"`,
      targetHint("hp", 12),
      `hp = ${toNumber(s.hp, 100)}`,
      "",
      "if has_core_bonus and mutation_result == \"공룡\":",
      "    final_attack = flame_damage + 50",
      "elif mutation_result == \"고릴라\":",
      "    final_attack = flame_damage + 20",
      "else:",
      "    final_attack = flame_damage",
    ].filter((line) => line !== null).join("\n");
  }
  if (seasonKey === "season_03") {
    return [
      "# 시즌 3: 몬스터 배틀 게임 업그레이드 존",
      "# 전체 코드를 볼 수 있습니다. 오늘 배울 곳은 [오늘의 업그레이드] 아래입니다.",
      "",
      "# =========================",
      "# [챕터 25] 계속 공격",
      "# [오늘의 업그레이드]",
      "# =========================",
      `monster_name = "${s.monster_name}"`,
      `monster_hp = ${toNumber(s.monster_hp, 30)}`,
      `monster_power = ${toNumber(s.monster_power, 5)}`,
      "",
      "def battle_until_defeat(start_hp):",
      "    logs = []",
      "    hp = start_hp",
      "    while hp > 0:",
      "        hp = hp - player_power",
      "        logs.append(\"공격!\")",
      "    return logs",
      "",
      "# =========================",
      "# [챕터 27] 숫자 반복",
      "# =========================",
      `player_power = ${toNumber(s.player_power, 5)}`,
      `combo_count = ${toNumber(s.combo_count, 5)}`,
      "",
      "def combo_attack():",
      "    logs = []",
      "    for i in range(combo_count):",
      "        logs.append(\"연속 공격!\")",
      "    return logs",
      "",
      "# =========================",
      "# [챕터 31] 아이템 가방",
      "# =========================",
      `bag = [${quoteList(s.bag)}]`,
      "",
      "# =========================",
      "# [챕터 33] 보물 줍기",
      "# =========================",
      `reward_item = "${s.reward_item}"`,
      "",
      "def add_reward_item(current_bag):",
      "    current_bag.append(reward_item)",
      "    return current_bag",
    ].join("\n");
  }
  return [
    "# 시즌 4: 미니 어드벤처 게임 업그레이드 존",
    "# 전체 코드를 볼 수 있습니다. 오늘 배울 곳은 [오늘의 업그레이드] 아래입니다.",
    "",
    "# =========================",
    "# [챕터 37] 점프 버튼",
    "# [오늘의 업그레이드]",
    "# =========================",
    `hero_name = "${s.hero_name}"`,
    "",
    "def jump():",
    "    return \"점프!\"",
    "",
    "def say_hello():",
    "    return \"안녕, 나는 \" + hero_name + \"이야!\"",
    "",
    "def attack(power):",
    "    damage = power * 2",
    "    return damage",
    "",
    "# =========================",
    "# [챕터 41] 랜덤 주사위",
    "# =========================",
    `final_goal = "${s.final_goal}"`,
    `dice_min = ${toNumber(s.dice_min, 1)}`,
    `dice_max = ${toNumber(s.dice_max, 6)}`,
    "",
    "def random_damage():",
    "    return random.randint(dice_min, dice_max)",
    "",
    "# =========================",
    "# [챕터 42] 랜덤 보물상자",
    "# =========================",
    `treasure_items = [${quoteList(s.treasure_items)}]`,
    "",
    "def random_treasure():",
    "    return random.choice(treasure_items)",
    "",
    "# =========================",
    "# [챕터 47] 게임 규칙 정리",
    "# =========================",
    `win_score = ${toNumber(s.win_score, 100)}`,
    "",
    "def check_win(score):",
    "    if score >= win_score:",
    "        return \"승리!\"",
    "    return \"아직 더 모아야 해!\"",
  ].join("\n");
}

function renderCodeEditor() {
  els.codeEditor.value = fileContent(state.activeFile);
  requestAnimationFrame(() => {
    if (state.activeFile !== "upgrade_zone.py") {
      els.codeEditor.scrollTop = 0;
      return;
    }
    const marker = els.codeEditor.value.indexOf("# [오늘의 업그레이드");
    if (marker <= 0) {
      els.codeEditor.scrollTop = 0;
      return;
    }
    const lineCount = els.codeEditor.value.slice(0, marker).split("\n").length;
    const lineHeight = 22;
    els.codeEditor.scrollTop = Math.max(0, (lineCount - 4) * lineHeight);
  });
}

function parseCode(seasonKey, source) {
  const base = { ...(state.settings[seasonKey] || defaultSettings(seasonKey)) };
  const stringAssignments = new Map();
  for (const match of source.matchAll(/^\s*([A-Za-z_]\w*)\s*=\s*["']([^"']*)["']\s*(?:#.*)?$/gm)) {
    stringAssignments.set(match[1], match[2]);
  }
  const stringValue = (name) => {
    return stringAssignments.has(name) ? stringAssignments.get(name) : base[name];
  };
  const numberValue = (name) => {
    const match = source.match(new RegExp(`^\\s*${name}\\s*=\\s*(-?\\d+(?:\\.\\d+)?)`, "m"));
    return match ? Number(match[1]) : base[name];
  };
  const numberAssignments = () => {
    const assignments = new Map();
    for (const match of source.matchAll(/^\s*([A-Za-z_]\w*)\s*=\s*(-?\d+(?:\.\d+)?)\s*(?:#.*)?$/gm)) {
      assignments.set(match[1], Number(match[2]));
    }
    return assignments;
  };
  const evaluateNumberExpression = (name, extra = {}) => {
    const match = source.match(new RegExp(`^\\s*${name}\\s*=\\s*(.+)$`, "m"));
    if (!match) return null;
    const expression = match[1].split("#")[0].trim();
    if (!expression) return null;
    const variables = {
      ...base,
      ...Object.fromEntries(numberAssignments().entries()),
      ...extra,
    };
    const tokens = expression.match(/[+-]|-?\d+(?:\.\d+)?|[A-Za-z_]\w*/g);
    if (!tokens || !tokens.length) return null;
    let sign = 1;
    let total = 0;
    let waitingForValue = true;
    for (const token of tokens) {
      if (token === "+") {
        if (waitingForValue) return null;
        sign = 1;
        waitingForValue = true;
        continue;
      }
      if (token === "-") {
        if (waitingForValue) return null;
        sign = -1;
        waitingForValue = true;
        continue;
      }
      const value = /^-?\d/.test(token) ? Number(token) : variables[token];
      if (typeof value !== "number" || Number.isNaN(value)) return null;
      total += sign * value;
      sign = 1;
      waitingForValue = false;
    }
    return waitingForValue ? null : total;
  };
  const seasonOneScoreValue = (startScore) => {
    const currentScore = evaluateNumberExpression("current_score", { start_score: startScore });
    if (currentScore !== null) return currentScore;
    const numberMatch = source.match(/^\s*score\s*=\s*(-?\d+(?:\.\d+)?)/m);
    if (numberMatch) return Number(numberMatch[1]);
    const startScoreMatch = source.match(/^\s*score\s*=\s*start_score\s*$/m);
    if (startScoreMatch) return startScore;
    return base.score ?? startScore;
  };
  const stringVariables = (extra = {}) => ({
    ...Object.fromEntries(stringAssignments.entries()),
    ...base,
    ...extra,
  });
  const evaluateStringExpression = (name, extra = {}) => {
    const match = source.match(new RegExp(`^\\s*${name}\\s*=\\s*(.+)$`, "m"));
    if (!match) return null;
    const expression = match[1].split("#")[0].trim();
    if (!expression) return null;
    const variables = stringVariables(extra);
    const parts = expression.split("+").map((part) => part.trim()).filter(Boolean);
    if (!parts.length) return null;
    let value = "";
    for (const part of parts) {
      const literal = part.match(/^["']([^"']*)["']$/);
      if (literal) {
        value += literal[1];
        continue;
      }
      const variable = part.match(/^[A-Za-z_]\w*$/);
      if (variable && typeof variables[variable[0]] === "string") {
        value += variables[variable[0]];
        continue;
      }
      return null;
    }
    return value;
  };
  const seasonOneMissionValue = (heroName) => {
    const evaluated = evaluateStringExpression("mission_text", { hero_name: heroName });
    if (evaluated !== null) return evaluated;
    return base.mission_text ?? `${heroName}의 미션: 보물 3개 모으기`;
  };
  const seasonOneMissionStatusValue = (heroName, score, hp) => {
    const literalMatch = source.match(/^\s*(?:mission_status|status_text)\s*=\s*["']([^"']*)["']/m);
    if (literalMatch) return literalMatch[1];
    const fStringMatch = source.match(/^\s*(?:mission_status|status_text)\s*=\s*f["']([^"']*)["']/m);
    if (fStringMatch) {
      return fStringMatch[1]
        .replaceAll("{hero_name}", heroName)
        .replaceAll("{score}", String(score))
        .replaceAll("{hp}", String(hp));
    }
    return base.mission_status ?? base.status_text ?? `${heroName} 미션: 점수 ${score}, 체력 ${hp}`;
  };
  const boolValue = (name) => {
    const match = source.match(new RegExp(`^\\s*${name}\\s*=\\s*(True|False|true|false)`, "m"));
    return match ? String(match[1]).toLowerCase() : base[name];
  };
  const listValue = (name) => {
    const match = source.match(new RegExp(`^\\s*${name}\\s*=\\s*\\[([^\\]]*)\\]`, "m"));
    if (!match) return base[name];
    const items = [...match[1].matchAll(/["']([^"']+)["']/g)].map((entry) => entry[1]);
    return items.length ? items.join(", ") : base[name];
  };

  if (seasonKey === "season_01") {
    const heroName = stringValue("hero_name");
    const startScore = numberValue("start_score");
    const score = seasonOneScoreValue(startScore);
    const currentScore = evaluateNumberExpression("current_score", { start_score: startScore }) ?? score;
    const hp = numberValue("hp");
    return {
      start_message: stringValue("start_message"),
      hero_message: stringValue("hero_message"),
      hero_name: heroName,
      start_score: startScore,
      score,
      current_score: currentScore,
      hp,
      potion_heal: numberValue("potion_heal"),
      speed: numberValue("speed"),
      wind_multiplier: numberValue("wind_multiplier"),
      mission_text: seasonOneMissionValue(heroName),
      mission_status: seasonOneMissionStatusValue(heroName, score, hp),
      portal_hint: stringValue("portal_hint"),
      starter_chest_label: stringValue("starter_chest_label"),
      treasure_label: stringValue("treasure_label"),
      coin_label: stringValue("coin_label"),
      potion_label: stringValue("potion_label"),
      wind_shoes_label: stringValue("wind_shoes_label"),
      gem_label: stringValue("gem_label"),
      chest_label: stringValue("chest_label"),
      trap_label: stringValue("trap_label"),
      bonus_label: stringValue("bonus_label"),
      portal_label: stringValue("portal_label"),
      starter_chest_point: numberValue("starter_chest_point"),
      treasure_point: numberValue("treasure_point"),
      coin_point: numberValue("coin_point"),
      gem_point: numberValue("gem_point"),
      chest_point: numberValue("chest_point"),
      treasure_1: numberValue("treasure_1"),
      treasure_2: numberValue("treasure_2"),
      treasure_3: numberValue("treasure_3"),
      trap_1: numberValue("trap_1"),
      trap_damage: numberValue("trap_damage"),
      trap_speed: numberValue("trap_speed"),
      bonus_multiplier: numberValue("bonus_multiplier"),
    };
  }
  if (seasonKey === "season_02") {
    return {
      baby_name: stringValue("baby_name"),
      runner_title: stringValue("runner_title"),
      roar_text: stringValue("roar_text"),
      favorite_food: stringValue("favorite_food"),
      food_name: stringValue("food_name"),
      item_name: stringValue("item_name"),
      start_size: numberValue("start_size"),
      growth: numberValue("growth"),
      run_speed: numberValue("run_speed"),
      snack_score: numberValue("snack_score"),
      meat_score: numberValue("meat_score"),
      favorite_bonus: numberValue("favorite_bonus"),
      bomb_damage: numberValue("bomb_damage"),
      growth_per_item: numberValue("growth_per_item"),
      mutation_size: numberValue("mutation_size"),
      gorilla_score: numberValue("gorilla_score"),
      dino_score: numberValue("dino_score"),
      hp: numberValue("hp"),
      danger_limit: numberValue("danger_limit"),
      attack_power: numberValue("attack_power"),
      flame_damage: numberValue("flame_damage"),
      boss_power: numberValue("boss_power"),
      boss_name: stringValue("boss_name"),
      mutation_result: stringValue("mutation_result"),
      obstacle_result: stringValue("obstacle_result"),
      item_result: numberValue("item_result"),
      final_attack: numberValue("final_attack"),
      has_shield: boolValue("has_shield"),
      shield_ready: boolValue("shield_ready"),
      dash_ready: boolValue("dash_ready"),
      can_dash_shield: boolValue("can_dash_shield"),
      red_core: boolValue("red_core"),
      blue_core: boolValue("blue_core"),
      has_core_bonus: boolValue("has_core_bonus"),
    };
  }
  if (seasonKey === "season_03") {
    return {
      monster_name: stringValue("monster_name"),
      monster_hp: numberValue("monster_hp"),
      monster_power: numberValue("monster_power"),
      player_power: numberValue("player_power"),
      combo_count: numberValue("combo_count"),
      bag: listValue("bag"),
      reward_item: stringValue("reward_item"),
    };
  }
  return {
    hero_name: stringValue("hero_name"),
    final_goal: stringValue("final_goal"),
    dice_min: numberValue("dice_min"),
    dice_max: numberValue("dice_max"),
    treasure_items: listValue("treasure_items"),
    win_score: numberValue("win_score"),
  };
}

function seasonOneChapter() {
  return Math.max(1, Math.min(12, Number(state.activeChapter) || 1));
}

function seasonOneHas(chapter) {
  return seasonOneChapter() >= chapter;
}

function seasonOneItemsForChapter(chapter, settings = {}) {
  const items = [];
  if (chapter >= 4) items.push({ kind: "starter_chest", x: 40, y: 62, label: settings.starter_chest_label || "보물상자", taken: false });
  if (chapter >= 5) {
    items.push({ kind: "treasure", x: 12, y: 46, label: settings.treasure_label || "보물", taken: false });
    items.push({ kind: "coin", x: 68, y: 46, label: settings.coin_label || "동전", taken: false });
  }
  if (chapter >= 6) items.push({ kind: "potion", x: 12, y: 72, label: settings.potion_label || "체력 물약", taken: false });
  if (chapter >= 7) items.push({ kind: "boost", x: 68, y: 72, label: settings.wind_shoes_label || "바람신발", taken: false });
  if (chapter >= 10) {
    items.push({ kind: "gem", x: 40, y: 34, label: settings.gem_label || "루비", taken: false });
    items.push({ kind: "chest", x: 68, y: 22, label: settings.chest_label || "상자", taken: false });
  }
  if (chapter === 10) items.push({ kind: "score_trap", x: 12, y: 22, label: settings.trap_label || "함정", taken: false });
  if (chapter >= 11) items.push({ kind: "trap", x: 40, y: 44, label: settings.trap_label || "함정", taken: false });
  if (chapter >= 12) {
    items.push({ kind: "bonus", x: 12, y: 22, label: settings.bonus_label || "보너스별", taken: false });
    items.push({ kind: "portal", x: 40, y: 8, label: settings.portal_label || "포털", taken: false });
  }
  return items;
}

function seasonOneItemPoint(kind, settings) {
  if (kind === "starter_chest") return toNumber(settings.starter_chest_point, 10);
  if (kind === "coin") return toNumber(settings.coin_point, 5);
  if (kind === "gem") return toNumber(settings.gem_point, 20);
  if (kind === "chest") return toNumber(settings.chest_point, 30);
  if (kind === "treasure") return toNumber(settings.treasure_point, 10);
  if (kind === "score_trap") return -Math.abs(toNumber(settings.trap_1, toNumber(settings.trap_damage, 20)));
  return 0;
}

function seasonOneRequiredItems(game) {
  return game.items.filter((item) => ["starter_chest", "treasure", "coin", "gem", "chest", "bonus"].includes(item.kind));
}

function seasonOneReadyForPortal(game) {
  return seasonOneRequiredItems(game).every((item) => item.taken);
}

function clampPercent(value, min, max) {
  return Math.max(min, Math.min(max, value));
}

function randomTrapStep(speed) {
  const axisStep = () => Math.floor(Math.random() * 3) - 1;
  const xStep = axisStep();
  const yStep = axisStep();
  if (xStep || yStep) return { x: xStep * speed, y: yStep * speed };
  return { x: speed, y: 0 };
}

function seasonOneReset() {
  const s = state.settings.season_01;
  const chapter = seasonOneChapter();
  state.game.season_01 = {
    x: 40,
    y: 80,
    direction: "down",
    step: 0,
    score: toNumber(s.score, toNumber(s.start_score, 10)),
    hp: toNumber(s.hp, 100),
    maxHp: Math.max(1, toNumber(s.hp, 100)),
    windBoostActive: false,
    combo: 0,
    win: false,
    gameOver: false,
    explosion: null,
    chapter,
    phase: 0,
    message: s.start_message || "모험 시작!",
    collected: {
      score: 0,
      starter_chest: 0,
      treasure: 0,
      coin: 0,
      gem: 0,
      chest: 0,
      potion: 0,
      boost: 0,
      bonus: 0,
      trap: 0,
      score_trap: 0,
    },
    items: seasonOneItemsForChapter(chapter, s),
  };
}

function percentStyle(x, y) {
  return {
    left: `clamp(8px, ${x}%, calc(100% - 86px))`,
    top: `clamp(8px, ${y}%, calc(100% - 86px))`,
  };
}

function addSeasonOneScenery(board, className, text) {
  const node = document.createElement("div");
  node.className = className;
  node.textContent = text;
  board.appendChild(node);
  return node;
}

function seasonOneProp(board, className) {
  const prop = document.createElement("div");
  prop.className = `scene-prop ${className}`;
  board.appendChild(prop);
  return prop;
}

function seasonOneHudStats(settings, game, chapter) {
  const pieces = [];
  if (chapter >= 4) pieces.push(`점수 ${game.score}`);
  if (chapter >= 6) pieces.push(`체력 ${game.hp}/${game.maxHp}`);
  if (chapter >= 7) {
    const windText = game.windBoostActive ? ` · ${settings.wind_shoes_label || "바람신발"} x${toNumber(settings.wind_multiplier, 2)}` : "";
    pieces.push(`속도 ${settings.speed}${windText}`);
  }
  if (chapter >= 10) pieces.push(`콤보 ${game.combo}`);
  if (chapter >= 12 && game.win) pieces.push("포털 개방!");
  if (!pieces.length) pieces.push("시작 장면 제작 중");
  return pieces.join(" · ");
}

function renderSeasonOneScenery(board, settings, game, chapter) {
  if (chapter >= 5) seasonOneProp(board, "coin-road");
  if (chapter >= 8) addSeasonOneScenery(board, "mission-badge", settings.mission_text || `${settings.hero_name || "번개용사"}의 미션: 보물 3개 모으기`);
  if (chapter >= 9) addSeasonOneScenery(board, "mission-status-badge", settings.mission_status || settings.status_text || `${settings.hero_name || "번개용사"} 미션: 점수 ${game.score}, 체력 ${game.hp}`);
  if (chapter >= 10) addSeasonOneScenery(board, "combo-plaque", `콤보 ${game.combo} · 보물 ${game.collected.treasure + game.collected.gem + game.collected.chest}`);
  if (chapter >= 10) seasonOneProp(board, "treasure-gate");
  if (chapter >= 12) {
    seasonOneProp(board, "crystal-left");
    seasonOneProp(board, "crystal-right");
    seasonOneProp(board, "portal-aura");
  }
  if (chapter >= 12) addSeasonOneScenery(board, "portal-hint", game.win ? "클리어!" : (settings.portal_hint || "보물을 모아 포털을 열자"));
}

function updateSeasonOneMovingTraps() {
  if (!state.gameStarted || state.activeSeason !== "season_01") return;
  const g = state.game.season_01;
  if (!g || g.win || g.gameOver || !seasonOneHas(11)) return;
  const trapSpeed = clampPercent(toNumber(state.settings.season_01.trap_speed, 2), 0, 8);
  for (const item of g.items) {
    if (item.kind !== "trap" || item.taken) continue;
    const step = randomTrapStep(trapSpeed);
    item.x = clampPercent(item.x + step.x, 8, 88);
    item.y = clampPercent(item.y + step.y, 12, 80);
  }
  const trap = findCollectableItem(g, ["trap"]);
  if (trap) triggerSeasonOneTrap(trap, state.settings.season_01, g);
  renderSeasonOne();
}

function startGameTimer() {
  if (state.gameTimer) window.clearInterval(state.gameTimer);
  state.gameTimer = null;
  if (!state.gameStarted) return;
  if (state.activeSeason === "season_01" && seasonOneHas(11)) {
    state.gameTimer = window.setInterval(updateSeasonOneMovingTraps, 140);
  }
  if (state.activeSeason === "season_02") {
    state.gameTimer = window.setInterval(updateSeasonTwoRunner, SEASON_TWO_TIMER_MS);
  }
}

function stopGameTimer() {
  if (!state.gameTimer) return;
  window.clearInterval(state.gameTimer);
  state.gameTimer = null;
}

function renderSeasonOne() {
  const s = state.settings.season_01;
  const g = state.game.season_01 || (seasonOneReset(), state.game.season_01);
  const chapter = seasonOneChapter();
  if (g.chapter !== chapter) {
    seasonOneReset();
    renderSeasonOne();
    return;
  }
  const title = chapter >= 8
    ? (s.mission_text || `${s.hero_name || "번개용사"}의 미션`)
    : chapter >= 3
      ? `${s.hero_name || "번개용사"}의 보물 모험`
      : "보물 점수 게임 만들기";
  setHud(
    title,
    seasonOneHudStats(s, g, chapter),
  );
  els.action.textContent = chapter >= 12 ? "수집/포털" : chapter >= 5 ? "보물 줍기" : "확인하기";
  els.gameMount.innerHTML = `<div class="board voxel-board chapter-${chapter} ${g.win ? "game-won" : ""} ${g.gameOver ? "game-over" : ""}" tabindex="0" aria-label="보물 점수 게임판"></div>`;
  const board = els.gameMount.querySelector(".board");
  renderSeasonOneScenery(board, s, g, chapter);

  const hero = document.createElement("div");
  hero.className = `sprite hero voxel-hero facing-${g.direction || "down"} step-${g.step % 2}`;
  const showHeroSpeech = chapter >= 2 && state.gameStarted && !state.startNotice;
  hero.innerHTML = `
    ${showHeroSpeech ? `<span class="hero-speech">${s.hero_message || "보물을 찾자!"}</span>` : ""}
    <span class="hero-shadow"></span>
    <span class="voxel-sword"></span>
    <span class="voxel-body">
      <span class="voxel-head"><span class="voxel-face"></span></span>
      <span class="voxel-chest"></span>
      <span class="voxel-arm arm-left"></span>
      <span class="voxel-arm arm-right"></span>
      <span class="voxel-leg leg-left"></span>
      <span class="voxel-leg leg-right"></span>
    </span>
    ${chapter >= 3 ? `<span class="avatar-name">${s.hero_name || "용사"}</span>` : ""}
  `;
  Object.assign(hero.style, percentStyle(g.x, g.y));
  board.appendChild(hero);

  for (const item of g.items.filter((entry) => !entry.taken)) {
    const sprite = document.createElement("div");
    const category = item.kind === "trap" || item.kind === "score_trap" ? "trap" : "treasure";
    sprite.className = `sprite voxel-item ${category} item-${item.kind}`;
    sprite.innerHTML = `<span class="item-icon"></span><span>${item.label}</span>`;
    Object.assign(sprite.style, percentStyle(item.x, item.y));
    board.appendChild(sprite);
  }

  if (g.explosion) {
    const explosion = document.createElement("div");
    explosion.className = "trap-explosion";
    explosion.innerHTML = `
      <span class="blast-core"></span>
      <span class="blast-ring"></span>
      <span class="blast-ray ray-a"></span>
      <span class="blast-ray ray-b"></span>
      <span class="blast-ray ray-c"></span>
      <strong>BOOM!</strong>
    `;
    Object.assign(explosion.style, percentStyle(g.explosion.x, g.explosion.y));
    board.appendChild(explosion);
  }

  if (g.win) {
    for (let index = 0; index < 8; index += 1) {
      const spark = document.createElement("div");
      spark.className = "firework";
      spark.style.left = `${16 + index * 10}%`;
      spark.style.top = `${16 + (index % 3) * 12}%`;
      spark.style.animationDelay = `${index * 0.08}s`;
      board.appendChild(spark);
    }
  }
  if (state.startNotice) {
    const notice = document.createElement("div");
    notice.className = "start-notice";
    notice.textContent = s.start_message || "모험 시작!";
    board.appendChild(notice);
  }
  board.focus();
}

function moveHero(dx, dy) {
  if (!state.gameStarted) return;
  const s = state.settings.season_01;
  const g = state.game.season_01;
  if (g.win || g.gameOver) return;
  const windMultiplier = g.windBoostActive ? Math.max(1, toNumber(s.wind_multiplier, 2)) : 1;
  const speed = Math.max(1, toNumber(s.speed, 5)) * 1.25 * windMultiplier;
  if (dx < 0) g.direction = "left";
  if (dx > 0) g.direction = "right";
  if (dy < 0) g.direction = "up";
  if (dy > 0) g.direction = "down";
  g.step += 1;
  g.x = Math.max(0, Math.min(90, g.x + dx * speed));
  g.y = Math.max(0, Math.min(82, g.y + dy * speed));
  playFootstep();
  if (seasonOneHas(11)) {
    const trap = findCollectableItem(g, ["trap"]);
    if (trap) triggerSeasonOneTrap(trap, s, g);
  }
  renderSeasonOne();
}

function findCollectableItem(game, kinds = null) {
  const hitbox = { x: 13, y: 16 };
  return game.items
    .filter((item) => !item.taken)
    .filter((item) => !kinds || kinds.includes(item.kind))
    .map((item) => ({
      item,
      dx: Math.abs(item.x - game.x),
      dy: Math.abs(item.y - game.y),
    }))
    .filter(({ dx, dy }) => dx <= hitbox.x && dy <= hitbox.y)
    .sort((a, b) => (a.dx + a.dy) - (b.dx + b.dy))[0]?.item;
}

function triggerSeasonOneTrap(item, settings, game) {
  item.taken = true;
  game.combo = 0;
  game.collected.trap += 1;
  game.explosion = { x: item.x, y: item.y, label: item.label };
  const damage = toNumber(settings.trap_damage, 20);
  game.hp = Math.max(0, game.hp - damage);
  game.gameOver = true;
  state.gameStarted = false;
  state.startNotice = false;
  stopGameTimer();
  stopMusic();
  game.message = `${item.label} 폭발! 피해 ${damage}. 게임 종료!`;
  setStatus("함정에 부딪혀 게임이 종료되었습니다. 다시 시작으로 재도전할 수 있습니다.");
  setLockedControls();
  playPickupSound("trap");
}

function collectSeasonOne() {
  if (!state.gameStarted) return;
  const s = state.settings.season_01;
  const g = state.game.season_01;
  if (g.win || g.gameOver) return;
  const near = findCollectableItem(g);
  if (!near) {
    g.message = s.hero_message || "보물을 찾자!";
    renderSeasonOne();
    return;
  }
  g.collected ||= { score: 0, starter_chest: 0, treasure: 0, coin: 0, gem: 0, chest: 0, potion: 0, boost: 0, bonus: 0, trap: 0, score_trap: 0 };
  if (near.kind === "trap") {
    triggerSeasonOneTrap(near, s, g);
    renderSeasonOne();
    return;
  }
  if (near.kind === "portal") {
    if (seasonOneReadyForPortal(g)) {
      near.taken = true;
      g.win = true;
      g.message = `완성! ${s.hero_name || "용사"}가 ${s.portal_label || "포털"}을 열었어!`;
      playTone({ frequency: 880, duration: 0.16, type: "triangle", volume: 0.06, slide: 240 });
      updateSaveSeason("season_01", {
        high_score: Math.max(getSeasonSave("season_01").high_score || 0, g.score),
        best_hp: Math.max(getSeasonSave("season_01").best_hp || 0, g.hp),
        hero_name: s.hero_name,
      });
    } else {
      g.message = `${s.portal_label || "포털"}이 아직 잠겨 있어. 보물과 보너스를 먼저 모으자!`;
    }
    renderSeasonOne();
    return;
  }
  near.taken = true;
  playPickupSound(near.kind);
  if (near.kind === "potion") {
    g.collected.potion += 1;
    const heal = Math.max(0, toNumber(s.potion_heal, 20));
    g.hp += heal;
    g.maxHp = Math.max(g.maxHp, g.hp);
    g.message = `${near.label}을 마셨어. 체력 +${heal}!`;
  } else if (near.kind === "boost") {
    g.collected.boost += 1;
    g.windBoostActive = true;
    const windMultiplier = Math.max(1, toNumber(s.wind_multiplier, 2));
    g.message = `${near.label} 장착! 이동 속도가 계속 ${windMultiplier}배가 돼.`;
  } else if (near.kind === "bonus") {
    g.collected.bonus += 1;
    g.combo += 1;
    g.score = g.score * toNumber(s.bonus_multiplier, 2);
    g.message = `${near.label}! 점수가 ${toNumber(s.bonus_multiplier, 2)}배가 되었어.`;
  } else if (near.kind === "score_trap") {
    const point = seasonOneItemPoint(near.kind, s);
    g.collected.score_trap += 1;
    g.combo = 0;
    g.score = Math.max(0, g.score + point);
    g.message = `${near.label}을 밟았어. ${point}점`;
    playPickupSound("trap");
  } else {
    const point = seasonOneItemPoint(near.kind, s);
    g.collected[near.kind] = (g.collected[near.kind] || 0) + 1;
    g.combo += 1;
    g.score += point;
    g.message = `${near.label}을 주웠어! +${point}점`;
  }
  updateSaveSeason("season_01", {
    high_score: Math.max(getSeasonSave("season_01").high_score || 0, g.score),
    best_hp: Math.max(getSeasonSave("season_01").best_hp || 0, g.hp),
    hero_name: s.hero_name,
  });
  renderSeasonOne();
}

function seasonTwoChapter() {
  return Math.max(1, Math.min(12, Number(state.activeChapter) || 1));
}

const SEASON_TWO_CHARACTER_SIZE_MULTIPLIER = 0.5;
const SEASON_TWO_ATTACK_EFFECT_MS = 920;
const SEASON_TWO_BOSS_TURN_EFFECT_MS = 1120;
const SEASON_TWO_TURN_NOTICE_MS = 3000;
const SEASON_TWO_TURN_AFTER_EFFECT_DELAY_MS = 720;
const SEASON_TWO_RUNNER_SPEED_MULTIPLIER = 4;
const SEASON_TWO_ITEM_FALL_SPEED_MULTIPLIER = SEASON_TWO_RUNNER_SPEED_MULTIPLIER * 1.05;
const SEASON_TWO_ITEM_SPAWN_INTERVAL_MULTIPLIER = 0.67;
const SEASON_TWO_TIMER_MS = 110;
const SEASON_TWO_RUN_DISTANCE_STEP = 0.42;
const SEASON_TWO_ROAR_SPEECH_MS = 2200;
const SEASON_TWO_PICKUP_GLOW_MS = 2000;
const SEASON_TWO_HIT_EXPLOSION_MS = 760;
const SEASON_TWO_ITEM_COLLISION_MIN_Y = 88;
const SEASON_TWO_ITEM_COLLISION_MAX_Y = 101;
const SEASON_TWO_ITEM_DESPAWN_Y = 124;
const SEASON_TWO_GORILLA_SCORE = 200;
const SEASON_TWO_DINO_SCORE = 500;
const SEASON_TWO_ITEM_VERTICAL_GAP = 18;
const SEASON_TWO_ITEM_SPAWN_Y = -4;
const SEASON_TWO_MIN_TARGET_SECONDS = 30;
const SEASON_TWO_MAX_TARGET_SECONDS = 90;
const SEASON_TWO_EXPECTED_MEAT_COLLECT_RATIO = 0.8;
const SEASON_TWO_MIN_BOSS_MAX_HITS = 2;
const SEASON_TWO_MAX_BOSS_MAX_HITS = 5;
const SEASON_TWO_PREVIEW_KINDS = ["meat", "double_meat", "meat", "double_meat", "bomb"];
const SEASON_TWO_PREVIEW_LANES = [1, 1, 1, 1, 0];
const SEASON_TWO_PREVIEW_Y = [-4, -22, -40, -58, 18];

function seasonTwoHas(chapter) {
  return seasonTwoChapter() >= chapter;
}

function seasonTwoBossForChapter(chapter = seasonTwoChapter(), settings = state.settings.season_02) {
  const config = settings || {};
  const index = Math.min(3, Math.floor((chapter - 1) / 3));
  const base = seasonTwoBosses[index];
  const tunedPower = toNumber(config.boss_power, 24);
  const chapterStep = Math.max(0, chapter - 1);
  const expectedEnergy = seasonTwoExpectedCollectedEnergy(chapter, config, SEASON_TWO_EXPECTED_MEAT_COLLECT_RATIO);
  const expectedEvolution = seasonTwoEvolution(expectedEnergy, config);
  const maxGaugeTiming = { label: "완벽 타이밍", multiplier: 2.65, quality: 1 };
  const maxGaugeDamage = seasonTwoPlayerAttackDamage("flame", maxGaugeTiming, expectedEvolution, config, {
    chapter,
    hp: expectedEnergy,
  });
  const targetHits = seasonTwoBossMaxGaugeHits(chapter);
  return {
    ...base,
    name: chapter >= 12 ? (config.boss_name || base.name) : base.name,
    maxHp: Math.max(base.hp, Math.round(maxGaugeDamage * targetHits)),
    power: Math.max(base.power, tunedPower) + chapterStep * 2,
  };
}

function seasonTwoMutationScores(settings = state.settings.season_02 || {}) {
  const gorillaScore = Math.max(1, toNumber(settings.gorilla_score, SEASON_TWO_GORILLA_SCORE));
  const dinoScore = Math.max(gorillaScore + 1, toNumber(settings.dino_score, SEASON_TWO_DINO_SCORE));
  return { gorillaScore, dinoScore };
}

function seasonTwoEvolution(energy, settings = state.settings.season_02 || {}) {
  const { gorillaScore, dinoScore } = seasonTwoMutationScores(settings);
  if (energy >= dinoScore) return { name: "공룡", className: "dino", scale: 1.36, rank: 3 };
  if (energy >= gorillaScore) return { name: "고릴라", className: "gorilla", scale: 1.18, rank: 2 };
  return { name: "원숭이", className: "monkey", scale: 1, rank: 1 };
}

function seasonTwoVisualSizeCap(energy, settings = state.settings.season_02 || {}) {
  const evolution = seasonTwoEvolution(energy, settings);
  if (evolution.rank >= 3) return 108;
  if (evolution.rank >= 2) return 74;
  return 42;
}

function seasonTwoEnergyVisualSize(energy, settings = state.settings.season_02 || {}) {
  const { gorillaScore, dinoScore } = seasonTwoMutationScores(settings);
  const safeEnergy = Math.max(0, energy);
  if (safeEnergy >= dinoScore) return seasonTwoVisualSizeCap(dinoScore, settings);
  if (safeEnergy >= gorillaScore) return seasonTwoVisualSizeCap(gorillaScore, settings);
  const ratio = Math.max(0, Math.min(1, safeEnergy / Math.max(1, gorillaScore)));
  return Math.max(1, 1 + ratio * 40);
}

function seasonTwoAttackEnergyMultiplier(energy, chapter, settings = state.settings.season_02 || {}) {
  const startEnergy = Math.max(1, toNumber(settings.hp, 100));
  const expectedEnergy = seasonTwoExpectedCollectedEnergy(chapter, settings, SEASON_TWO_EXPECTED_MEAT_COLLECT_RATIO);
  const earnedEnergy = Math.max(0, energy - startEnergy);
  const expectedEarnedEnergy = Math.max(1, expectedEnergy - startEnergy);
  const collectedRatio = Math.max(0, Math.min(1, earnedEnergy / expectedEarnedEnergy));
  return 0.72 + collectedRatio * 0.28;
}

function seasonTwoPlayerAttackDamage(kind, timing, evolution, settings = state.settings.season_02 || {}, game = null) {
  const coreBonusReady = toBool(settings.has_core_bonus) || toBool(settings.red_core) || toBool(settings.blue_core);
  let baseDamage = Math.max(1, toNumber(settings.flame_damage, 200));
  if (coreBonusReady && evolution.rank >= 3) baseDamage += 50;
  else if (evolution.rank === 2) baseDamage += 20;
  const finalAttack = toNumber(settings.final_attack, baseDamage);
  baseDamage = Math.max(1, baseDamage, finalAttack);
  const timingBonus = Math.max(0.35, timing?.multiplier ?? 1);
  const formBonus = evolution.rank >= 3 ? 1 : evolution.rank === 2 ? 0.9 : 0.75;
  const chapter = game?.chapter ?? seasonTwoChapter();
  const energyBonus = seasonTwoAttackEnergyMultiplier(Math.max(0, game?.hp ?? 0), chapter, settings);
  return Math.max(1, Math.round(baseDamage * timingBonus * formBonus * energyBonus));
}

function seasonTwoChapterGrowthMultiplier(chapter) {
  return 1 + Math.max(0, Math.min(11, chapter - 1)) * 0.15;
}

function seasonTwoItemDifficulty(chapter) {
  return Math.max(0, Math.min(1, (chapter - 1) / 11));
}

function seasonTwoRunnerTargetSeconds(chapter) {
  return Math.round(SEASON_TWO_MIN_TARGET_SECONDS + seasonTwoItemDifficulty(chapter) * (SEASON_TWO_MAX_TARGET_SECONDS - SEASON_TWO_MIN_TARGET_SECONDS));
}

function seasonTwoBossMaxGaugeHits(chapter) {
  return SEASON_TWO_MIN_BOSS_MAX_HITS + seasonTwoItemDifficulty(chapter) * (SEASON_TWO_MAX_BOSS_MAX_HITS - SEASON_TWO_MIN_BOSS_MAX_HITS);
}

function seasonTwoItemChances(chapter) {
  const difficulty = seasonTwoItemDifficulty(chapter);
  const nukeChance = chapter >= 10 ? 0.03 + difficulty * 0.03 : 0;
  const doubleMeatChance = chapter >= 7 ? 0.14 + difficulty * 0.12 : 0;
  const bombChance = 0.22 + difficulty * 0.18;
  const meatChance = Math.max(0, 1 - nukeChance - doubleMeatChance - bombChance);
  return { nukeChance, doubleMeatChance, bombChance, meatChance };
}

function seasonTwoRowPairChance(chapter) {
  const difficulty = seasonTwoItemDifficulty(chapter);
  return 0.22 + difficulty * 0.26;
}

function seasonTwoIsMeatKind(kind) {
  return kind === "meat" || kind === "double_meat";
}

function seasonTwoIsBombKind(kind) {
  return kind === "bomb" || kind === "nuke";
}

function seasonTwoRewardKindForChapter(chapter) {
  const difficulty = seasonTwoItemDifficulty(chapter);
  const doubleChance = chapter >= 7 ? 0.18 + difficulty * 0.12 : 0;
  return Math.random() < doubleChance ? "double_meat" : "meat";
}

function seasonTwoPreviewKinds(chapter) {
  const previewCount = Math.min(5, Math.max(2, Math.ceil(chapter / 3)));
  return SEASON_TWO_PREVIEW_KINDS.slice(0, previewCount);
}

function seasonTwoSpawnRate(speed, progress) {
  const baseRate = 24 - Math.round(speed) - Math.floor(progress * 5);
  return Math.max(6, Math.round(baseRate * SEASON_TWO_ITEM_SPAWN_INTERVAL_MULTIPLIER));
}

function seasonTwoExpectedSpawnRows(chapter, settings = state.settings.season_02 || {}) {
  const speed = Math.max(2, Math.min(10, toNumber(settings.run_speed, 5)));
  const tickCount = Math.max(1, Math.round((seasonTwoRunnerTargetSeconds(chapter) * 1000) / SEASON_TWO_TIMER_MS));
  let rows = 0;
  for (let tick = 1; tick <= tickCount; tick += 1) {
    const progress = Math.max(0, Math.min(1, tick / tickCount));
    if (tick % seasonTwoSpawnRate(speed, progress) === 0) rows += 1;
  }
  return rows;
}

function seasonTwoExpectedRowRewardEnergy(chapter, settings = state.settings.season_02 || {}) {
  const meatPoint = Math.max(1, toNumber(settings.meat_score, 100));
  const foodLabel = String(settings.food_name || settings.favorite_food || "고기").trim() || "고기";
  const favoriteBonus = String(settings.favorite_food || "고기").trim() === foodLabel
    ? Math.max(0, toNumber(settings.favorite_bonus, 20))
    : 0;
  const { doubleMeatChance, bombChance, meatChance } = seasonTwoItemChances(chapter);
  const singleRewardEnergy = meatChance * (meatPoint + favoriteBonus) + doubleMeatChance * (meatPoint * 2 + favoriteBonus);
  const rewardChance = meatChance + doubleMeatChance;
  const averageRewardEnergy = rewardChance > 0 ? singleRewardEnergy / rewardChance : meatPoint;
  return singleRewardEnergy + seasonTwoRowPairChance(chapter) * bombChance * averageRewardEnergy;
}

function seasonTwoExpectedPreviewRewardEnergy(chapter, settings = state.settings.season_02 || {}) {
  const meatPoint = Math.max(1, toNumber(settings.meat_score, 100));
  const foodLabel = String(settings.food_name || settings.favorite_food || "고기").trim() || "고기";
  const favoriteBonus = String(settings.favorite_food || "고기").trim() === foodLabel
    ? Math.max(0, toNumber(settings.favorite_bonus, 20))
    : 0;
  return seasonTwoPreviewKinds(chapter).reduce((sum, kind) => {
    if (kind === "double_meat") return sum + meatPoint * 2 + favoriteBonus;
    if (kind === "meat") return sum + meatPoint + favoriteBonus;
    return sum;
  }, 0);
}

function seasonTwoExpectedCollectedEnergy(chapter, settings = state.settings.season_02 || {}, collectRatio = SEASON_TWO_EXPECTED_MEAT_COLLECT_RATIO) {
  const startEnergy = Math.max(1, toNumber(settings.hp, 100));
  const snackBonus = chapter >= 3 ? Math.max(0, toNumber(settings.snack_score, 10)) : 0;
  const rewardEnergy = seasonTwoExpectedPreviewRewardEnergy(chapter, settings)
    + seasonTwoExpectedSpawnRows(chapter, settings) * seasonTwoExpectedRowRewardEnergy(chapter, settings);
  return Math.max(1, Math.round(startEnergy + snackBonus + rewardEnergy * Math.max(0, Math.min(1, collectRatio))));
}

function seasonTwoTargetEnergy(chapter, settings = state.settings.season_02 || {}) {
  return Math.max(1, Math.round(seasonTwoExpectedCollectedEnergy(chapter, settings, SEASON_TWO_EXPECTED_MEAT_COLLECT_RATIO) / 10) * 10);
}

function seasonTwoRunnerGoal(chapter, settings = state.settings.season_02 || {}) {
  const speed = Math.max(2, Math.min(10, toNumber(settings.run_speed, 5)));
  const tickCount = (seasonTwoRunnerTargetSeconds(chapter) * 1000) / SEASON_TWO_TIMER_MS;
  return tickCount * speed * SEASON_TWO_RUN_DISTANCE_STEP * SEASON_TWO_RUNNER_SPEED_MULTIPLIER;
}

function seasonTwoCanAttack(game = state.game.season_02) {
  if (!state.gameStarted || state.activeSeason !== "season_02" || !game || game.phase !== "boss") return false;
  const now = performance.now();
  return game.bossTurn === "player"
    && (game.turnNoticeUntil || 0) <= now
    && (game.pendingTurnAt || 0) <= now
    && (game.attackEffectUntil || 0) <= now
    && (game.bossTurnEffectUntil || 0) <= now;
}

function seasonTwoInputLocked(game = state.game.season_02) {
  if (!game || game.phase !== "boss") return false;
  return !seasonTwoCanAttack(game);
}

function seasonTwoItemFallSpeed(settings, chapter, progress) {
  const runSpeed = Math.max(2, Math.min(10, toNumber(settings.run_speed, 5)));
  const difficulty = seasonTwoItemDifficulty(chapter);
  const curve = Math.max(0, Math.min(1, progress)) ** 2;
  const runSpeedInfluence = (runSpeed - 5) * 0.08;
  return Math.max(0.64, Math.min(4.45, 0.76 + difficulty * 0.18 + runSpeedInfluence + curve * 3.55));
}

function seasonTwoLaneLeft(lane) {
  return [24, 50, 76][Math.max(0, Math.min(2, lane))] || 50;
}

function seasonTwoReset() {
  const s = state.settings.season_02;
  const chapter = seasonTwoChapter();
  const boss = seasonTwoBossForChapter(chapter, s);
  const baseEnergy = Math.max(1, toNumber(s.hp, 100) + (chapter >= 3 ? Math.max(0, toNumber(s.snack_score, 10)) : 0));
  const baseSize = seasonTwoEnergyVisualSize(baseEnergy, s);
  const targetEnergy = seasonTwoTargetEnergy(chapter, s);
  const targetSeconds = seasonTwoRunnerTargetSeconds(chapter);
  state.game.season_02 = {
    chapter,
    phase: "runner",
    lane: 1,
    tick: 0,
    score: 0,
    hp: baseEnergy,
    maxHp: baseEnergy,
    size: baseSize,
    growth: toNumber(s.growth, 0),
    distance: 0,
    goal: seasonTwoRunnerGoal(chapter, s),
    targetEnergy,
    targetSeconds,
    combo: 0,
    items: [],
    boss,
    bossHp: boss.maxHp,
    bossMeterStartedAt: 0,
    bossTurn: "playerNotice",
    turnNoticeKind: "player",
    turnNoticeUntil: 0,
    pendingTurnAt: 0,
    pendingBossDamage: 0,
    lastTiming: null,
    attackKind: "flame",
    nextAttackKind: "flame",
    attackEffectUntil: 0,
    attackEffectQuality: 0,
    bossTurnEffectUntil: 0,
    hitExplosionTarget: "",
    hitExplosionUntil: 0,
    pickupGlowKind: "",
    pickupGlowUntil: 0,
    bossCameraReady: false,
    shieldCharges: toBool(s.shield_ready) ? 2 : 0,
    dashCharges: toBool(s.dash_ready) ? 2 : 0,
    roarSpeechUntil: chapter >= 2 ? performance.now() + SEASON_TWO_ROAR_SPEECH_MS : 0,
    message: s.runner_title || "괴수 러너 출발!",
  };
  const previewKinds = seasonTwoPreviewKinds(chapter);
  const previewCount = previewKinds.length;
  for (let index = 0; index < previewCount; index += 1) {
    createSeasonTwoItemEntry(
      state.game.season_02,
      s,
      previewKinds[index] || "meat",
      SEASON_TWO_PREVIEW_LANES[index] ?? (index % 3),
      SEASON_TWO_PREVIEW_Y[index] ?? (SEASON_TWO_ITEM_SPAWN_Y + index * 18),
    );
  }
}

function seasonTwoItemForChapter(chapter) {
  const roll = Math.random();
  const { nukeChance, doubleMeatChance, bombChance } = seasonTwoItemChances(chapter);
  if (roll < nukeChance) return "nuke";
  if (roll < nukeChance + doubleMeatChance) return "double_meat";
  if (roll < nukeChance + doubleMeatChance + bombChance) return "bomb";
  return "meat";
}

function seasonTwoItemData(kind, settings) {
  const config = settings || {};
  const meatPoint = Math.max(1, toNumber(config.meat_score, 100));
  const foodLabel = String(config.food_name || config.favorite_food || "고기").trim() || "고기";
  const bombDamage = Math.max(1, toNumber(config.bomb_damage, Math.max(30, Math.round(meatPoint * 0.7))));
  const data = {
    meat: { label: foodLabel, point: 0, growth: 0, energy: meatPoint },
    double_meat: { label: `2배${foodLabel}`, point: 0, growth: 0, energy: meatPoint * 2 },
    bomb: { label: "폭탄", point: 0, growth: 0, energy: -bombDamage },
    nuke: { label: "핵폭탄", point: 0, growth: 0, energy: -9999 },
  };
  return data[kind] || data.meat;
}

function createSeasonTwoItemEntry(game, settings, kind, lane, y) {
  const item = seasonTwoItemData(kind, settings);
  const entry = {
    kind,
    label: item.label,
    point: item.point,
    growth: item.growth,
    energy: item.energy,
    lane,
    y,
    id: `${kind}-${game.tick}-${Math.random().toString(36).slice(2, 6)}`,
  };
  game.items.push(entry);
  return entry;
}

function spawnSeasonTwoItem(game, settings, chapter, forcedKind = null) {
  const kind = forcedKind || seasonTwoItemForChapter(chapter);
  const rowKinds = seasonTwoSpawnRowKinds(chapter, kind);
  const spawnSlots = seasonTwoSpawnSlots(game, rowKinds);
  if (!spawnSlots) return null;
  return spawnSlots.map((slot) => createSeasonTwoItemEntry(game, settings, slot.kind, slot.lane, slot.y));
}

function seasonTwoSpawnRowKinds(chapter, primaryKind) {
  if (primaryKind === "nuke" || Math.random() >= seasonTwoRowPairChance(chapter)) return [primaryKind];
  if (seasonTwoIsBombKind(primaryKind)) return [primaryKind, seasonTwoRewardKindForChapter(chapter)];
  return [primaryKind, "bomb"];
}

function seasonTwoSpawnRowAllowed(kinds) {
  if (!Array.isArray(kinds) || kinds.length < 1 || kinds.length > 2) return false;
  if (kinds.length === 1) return true;
  const meatCount = kinds.filter(seasonTwoIsMeatKind).length;
  return meatCount < 2 && kinds.some(seasonTwoIsBombKind);
}

function seasonTwoSpawnSlots(game, kinds) {
  if (!seasonTwoSpawnRowAllowed(kinds)) return null;
  const spawnY = SEASON_TWO_ITEM_SPAWN_Y;
  const blocked = game.items.some((item) => (
    !item.taken
    && Math.abs(item.y - spawnY) < SEASON_TWO_ITEM_VERTICAL_GAP
  ));
  if (blocked) return null;
  const lanePool = kinds.includes("nuke") ? [0, 2] : [0, 1, 2];
  const shuffled = lanePool
    .map((lane) => ({ lane, order: Math.random() }))
    .sort((a, b) => a.order - b.order)
    .map((entry) => entry.lane);
  if (shuffled.length < kinds.length) return null;
  return kinds.map((kind, index) => ({ kind, lane: shuffled[index], y: spawnY }));
}

function collectSeasonTwoItem(item, settings, game) {
  const beforeEvolution = seasonTwoEvolution(game.hp, settings);
  const difficulty = seasonTwoItemDifficulty(game.chapter);
  const markPickupGlow = (kind) => {
    game.pickupGlowKind = kind;
    game.pickupGlowUntil = performance.now() + SEASON_TWO_PICKUP_GLOW_MS;
  };

  if (item.kind === "nuke") {
    const dashShieldReady = toBool(settings.can_dash_shield) || (toBool(settings.shield_ready) && toBool(settings.dash_ready));
    if (dashShieldReady) {
      markPickupGlow("good");
      game.combo = 0;
      game.message = "방어막과 대시가 모두 준비되어 핵폭탄을 돌파했어!";
      playPickupSound("bonus");
      return;
    }
    markPickupGlow("bad");
    game.hp = 0;
    game.size = seasonTwoEnergyVisualSize(game.hp, settings);
    game.combo = 0;
    game.message = "핵폭탄을 먹었어! 거대한 폭발로 게임 실패!";
    playPickupSound("trap");
    finishSeasonTwo("gameOver", "핵폭탄 폭발! 다음에는 피해서 달려 보자!");
    return;
  }

  if (item.kind === "bomb") {
    markPickupGlow("bad");
    const shieldReady = toBool(settings.has_shield);
    const dashShieldReady = toBool(settings.can_dash_shield) || (toBool(settings.shield_ready) && toBool(settings.dash_ready));
    const rawDamage = Math.max(6, Math.round(Math.abs(item.energy) * (1 + difficulty * 0.5)));
    const damage = dashShieldReady ? 0 : shieldReady ? Math.max(1, Math.round(rawDamage * 0.45)) : rawDamage;
    game.hp = Math.max(0, game.hp - damage);
    game.size = seasonTwoEnergyVisualSize(game.hp, settings);
    game.combo = 0;
    const evolution = seasonTwoEvolution(game.hp, settings);
    game.message = damage > 0 ? `폭탄! 에너지 -${damage} · 현재 ${evolution.name}` : "방어막과 대시로 폭탄 피해를 막았어!";
    playPickupSound("trap");
    if (game.hp <= 0) finishSeasonTwo("gameOver", "에너지가 0이 되었어. 고기를 더 모아 보자!");
    return;
  }

  const favoriteFood = String(settings.favorite_food || "고기").trim();
  const favoriteBonus = item.label === favoriteFood || item.label === `2배${favoriteFood}`
    ? Math.max(0, toNumber(settings.favorite_bonus, 20))
    : 0;
  const energyGain = Math.max(1, Math.round(item.energy + favoriteBonus));
  markPickupGlow("good");
  game.hp += energyGain;
  game.maxHp = Math.max(game.maxHp, game.hp);
  game.score = game.hp;
  game.size = seasonTwoEnergyVisualSize(game.hp, settings);
  game.growth = Math.max(0, game.growth + Math.max(1, toNumber(settings.growth_per_item, 12)));
  game.combo += 1;

  const afterEvolution = seasonTwoEvolution(game.hp, settings);
  if (afterEvolution.rank > beforeEvolution.rank) {
    game.message = `${item.label} 획득! 에너지 ${game.hp}, ${koreanDirection(afterEvolution.name)} 변신했어!`;
  } else {
    game.message = `${item.label} 획득! 에너지 +${energyGain}${favoriteBonus ? " · 좋아하는 먹이 보너스!" : ""} · 현재 에너지 ${game.hp}`;
  }
  playPickupSound(item.kind === "double_meat" ? "bonus" : "treasure");
}

function setSeasonTwoTurnNotice(game, kind, duration = SEASON_TWO_TURN_NOTICE_MS) {
  const until = performance.now() + duration;
  game.turnNoticeKind = kind;
  game.turnNoticeUntil = until;
  window.setTimeout(() => {
    const latest = state.game.season_02;
    if (
      state.activeSeason !== "season_02"
      || !latest
      || latest.phase !== "boss"
      || latest.turnNoticeUntil !== until
    ) return;
    renderSeasonTwo();
  }, duration + 40);
  return until;
}

function scheduleSeasonTwoPlayerTurn(game, message = "내 공격 차례! Space 타이밍 공격을 준비해!") {
  game.bossTurn = "playerNotice";
  game.message = message;
  const noticeUntil = setSeasonTwoTurnNotice(game, "player");
  renderSeasonTwo();
  window.setTimeout(() => {
    const latest = state.game.season_02;
    if (
      state.activeSeason !== "season_02"
      || !latest
      || latest.phase !== "boss"
      || latest.bossTurn !== "playerNotice"
      || latest.turnNoticeUntil !== noticeUntil
    ) return;
    latest.bossTurn = "player";
    latest.turnNoticeUntil = 0;
    latest.turnNoticeKind = "player";
    latest.bossMeterStartedAt = performance.now();
    latest.message = "내 공격 차례! Space 타이밍 공격!";
    renderSeasonTwo();
  }, SEASON_TWO_TURN_NOTICE_MS);
}

function scheduleSeasonTwoPlayerTurnAfterDelay(game, message, delay = SEASON_TWO_TURN_AFTER_EFFECT_DELAY_MS) {
  game.bossTurn = "turnDelay";
  game.pendingTurnAt = performance.now() + delay;
  game.turnNoticeKind = "";
  game.turnNoticeUntil = 0;
  game.message = message;
  const turnAt = game.pendingTurnAt;
  window.setTimeout(() => {
    const latest = state.game.season_02;
    if (
      state.activeSeason !== "season_02"
      || !latest
      || latest.phase !== "boss"
      || latest.bossTurn !== "turnDelay"
      || latest.pendingTurnAt !== turnAt
    ) return;
    scheduleSeasonTwoPlayerTurn(latest, message);
  }, delay);
}

function startSeasonTwoBossAttack(expectedDamage, noticeUntil) {
  const g = state.game.season_02;
  if (
    state.activeSeason !== "season_02"
    || !g
    || g.phase !== "boss"
    || g.bossTurn !== "bossNotice"
    || g.turnNoticeUntil !== noticeUntil
  ) return;
  g.bossTurn = "boss";
  g.turnNoticeUntil = 0;
  g.turnNoticeKind = "boss";
  g.bossTurnEffectUntil = performance.now() + SEASON_TWO_BOSS_TURN_EFFECT_MS;
  g.message = `${g.boss.name} 공격!`;
  renderSeasonTwo();
  window.setTimeout(() => {
    resolveSeasonTwoBossTurn(expectedDamage);
  }, Math.max(240, SEASON_TWO_BOSS_TURN_EFFECT_MS - 120));
}

function scheduleSeasonTwoBossTurn(game, bossDamage) {
  const delay = SEASON_TWO_ATTACK_EFFECT_MS + SEASON_TWO_TURN_AFTER_EFFECT_DELAY_MS;
  game.bossTurn = "turnDelay";
  game.pendingBossDamage = bossDamage;
  game.pendingTurnAt = performance.now() + delay;
  game.bossTurnEffectUntil = 0;
  game.turnNoticeKind = "";
  game.turnNoticeUntil = 0;
  game.message += ` · ${game.boss.name}가 반격을 준비 중...`;
  const turnAt = game.pendingTurnAt;
  window.setTimeout(() => {
    const latest = state.game.season_02;
    if (
      state.activeSeason !== "season_02"
      || !latest
      || latest.phase !== "boss"
      || latest.bossTurn !== "turnDelay"
      || latest.pendingTurnAt !== turnAt
    ) return;
    latest.bossTurn = "bossNotice";
    latest.message = `${latest.boss.name} 공격 차례를 조심해!`;
    const noticeUntil = setSeasonTwoTurnNotice(latest, "boss");
    renderSeasonTwo();
    window.setTimeout(() => {
      startSeasonTwoBossAttack(bossDamage, noticeUntil);
    }, SEASON_TWO_TURN_NOTICE_MS);
  }, delay);
}

function enterSeasonTwoBossFight(game, settings) {
  game.phase = "boss";
  game.items = [];
  game.boss = seasonTwoBossForChapter(game.chapter, settings);
  game.bossHp = game.boss.maxHp;
  game.bossMeterStartedAt = performance.now();
  game.bossTurn = "playerNotice";
  game.pendingBossDamage = 0;
  game.lastTiming = null;
  game.attackKind = "flame";
  game.nextAttackKind = "flame";
  game.attackEffectUntil = 0;
  game.attackEffectQuality = 0;
  game.bossTurnEffectUntil = 0;
  game.bossCameraReady = false;
  scheduleSeasonTwoPlayerTurn(game, `${game.boss.name} 등장! 내 공격 차례를 준비해!`);
  stopGameTimer();
  playTone({ frequency: 170, duration: 0.18, type: "sawtooth", volume: 0.05, slide: 220 });
}

function finishSeasonTwo(result, message) {
  const g = state.game.season_02;
  if (!g) return;
  g.phase = result;
  g.message = message;
  g.bossTurn = "done";
  g.pendingBossDamage = 0;
  g.pendingTurnAt = 0;
  g.turnNoticeKind = "";
  g.turnNoticeUntil = 0;
  if (result === "win") g.bossDefeatedAt = performance.now();
  state.gameStarted = false;
  stopGameTimer();
  stopMusic();
  updateSaveSeason("season_02", {
    best_score: Math.max(getSeasonSave("season_02").best_score || 0, g.hp),
    best_energy: Math.max(getSeasonSave("season_02").best_energy || 0, g.hp),
    baby_name: state.settings.season_02.baby_name,
    boss_clear: result === "win" || getSeasonSave("season_02").boss_clear || false,
  });
  setStatus(message);
  setLockedControls();
}

function updateSeasonTwoRunner() {
  if (!state.gameStarted || state.activeSeason !== "season_02") return;
  const s = state.settings.season_02;
  const g = state.game.season_02;
  if (!g || ["win", "gameOver"].includes(g.phase)) return;
  const chapter = seasonTwoChapter();
  if (g.chapter !== chapter) {
    seasonTwoReset();
    renderSeasonTwo();
    return;
  }

  if (g.phase === "boss") {
    stopGameTimer();
    return;
  }

  const speed = Math.max(2, Math.min(10, toNumber(s.run_speed, 5)));
  g.tick += 1;
  g.distance += speed * SEASON_TWO_RUN_DISTANCE_STEP * SEASON_TWO_RUNNER_SPEED_MULTIPLIER;
  const progress = Math.max(0, Math.min(1, g.distance / Math.max(1, g.goal)));
  const spawnRate = seasonTwoSpawnRate(speed, progress);
  if (g.tick % spawnRate === 0) spawnSeasonTwoItem(g, s, chapter);

  const itemFallSpeed = seasonTwoItemFallSpeed(s, chapter, progress) * SEASON_TWO_ITEM_FALL_SPEED_MULTIPLIER;
  for (const item of g.items) {
    item.y += itemFallSpeed;
    if (
      !item.taken
      && item.lane === g.lane
      && item.y >= SEASON_TWO_ITEM_COLLISION_MIN_Y
      && item.y <= SEASON_TWO_ITEM_COLLISION_MAX_Y
    ) {
      item.taken = true;
      collectSeasonTwoItem(item, s, g);
    }
  }
  g.items = g.items.filter((item) => !item.taken && item.y < SEASON_TWO_ITEM_DESPAWN_Y);

  if (g.phase === "runner" && g.distance >= g.goal) {
    if (g.hp >= g.targetEnergy) {
      enterSeasonTwoBossFight(g, s);
    } else {
      finishSeasonTwo("gameOver", `목표 에너지 ${g.targetEnergy}에 부족해. 먹이를 더 모아 보자!`);
    }
  }
  renderSeasonTwo();
}

function seasonTwoMonsterMarkup(name, evolution, extraClass = "", scale = 1) {
  const safeName = name || "괴수";
  return `
    <div class="kaiju-model ${evolution.className} ${extraClass}" style="--monster-scale:${scale * evolution.scale * SEASON_TWO_CHARACTER_SIZE_MULTIPLIER}">
      <span class="kaiju-shadow"></span>
      <span class="kaiju-tail"></span>
      <span class="kaiju-leg leg-a"></span>
      <span class="kaiju-leg leg-b"></span>
      <span class="kaiju-body">
        <span class="kaiju-belly"></span>
        <span class="kaiju-spikes"></span>
      </span>
      <span class="kaiju-head">
        <span class="kaiju-horn horn-a"></span>
        <span class="kaiju-horn horn-b"></span>
        <span class="kaiju-eye eye-a"></span>
        <span class="kaiju-eye eye-b"></span>
        <span class="kaiju-mouth"></span>
      </span>
      <span class="kaiju-arm arm-a"></span>
      <span class="kaiju-arm arm-b"></span>
      <span class="kaiju-name">${safeName}</span>
    </div>
  `;
}

function renderSeasonTwoItems(game) {
  return game.items.map((item) => {
    const left = seasonTwoLaneLeft(item.lane);
    const itemScale = Math.max(0.34, Math.min(1, 0.36 + Math.max(0, item.y) * 0.0068));
    return `<div class="runner-item item-${item.kind}" style="left:${left}%;top:${item.y}%;--item-scale:${itemScale.toFixed(2)}"><span></span><strong>${item.label}</strong></div>`;
  }).join("");
}

function renderSeasonTwoBossBadges(activeBoss) {
  return seasonTwoBosses.map((boss) => `
    <span class="boss-badge ${boss.className === activeBoss.className ? "active" : ""}">${boss.name}</span>
  `).join("");
}

function seasonTwoTimingResult(game) {
  const period = 1500;
  const startedAt = game.bossMeterStartedAt || performance.now();
  const fill = els.gameMount.querySelector(".timing-fill");
  const track = els.gameMount.querySelector(".boss-timing-track");
  const visualPhase = fill && track
    ? Number.parseFloat(getComputedStyle(fill).width) / Math.max(1, Number.parseFloat(getComputedStyle(track).width))
    : null;
  const elapsed = (performance.now() - startedAt) % (period * 2);
  const fallbackPhase = elapsed <= period ? elapsed / period : 2 - elapsed / period;
  const phase = Math.max(0, Math.min(1, Number.isFinite(visualPhase) ? visualPhase : fallbackPhase));
  if (phase >= 0.9) return { label: "완벽 타이밍", multiplier: 2.65, quality: phase };
  if (phase >= 0.72) return { label: "강공격", multiplier: 1.85, quality: phase };
  if (phase >= 0.45) return { label: "보통 공격", multiplier: 1.15, quality: phase };
  return { label: "약한 공격", multiplier: 0.55, quality: phase };
}

function koreanSubject(text) {
  const value = String(text || "");
  const last = [...value].pop();
  const code = last ? last.charCodeAt(0) : 0;
  const hasBatchim = code >= 0xac00 && code <= 0xd7a3 && (code - 0xac00) % 28 !== 0;
  return `${value}${hasBatchim ? "이" : "가"}`;
}

function koreanDirection(text) {
  const value = String(text || "");
  const last = [...value].pop();
  const code = last ? last.charCodeAt(0) : 0;
  const jong = code >= 0xac00 && code <= 0xd7a3 ? (code - 0xac00) % 28 : 0;
  return `${value}${jong && jong !== 8 ? "으로" : "로"}`;
}

function loadSeasonTwoThree() {
  if (!seasonTwoThree.modulePromise) {
    seasonTwoThree.modulePromise = import("/vendor/three.module.min.js");
  }
  return seasonTwoThree.modulePromise;
}

function disposeThreeScene(scene) {
  scene.traverse((object) => {
    if (object.geometry) object.geometry.dispose();
    if (object.material) {
      const materials = Array.isArray(object.material) ? object.material : [object.material];
      materials.forEach((material) => material.dispose());
    }
  });
}

function seasonTwoThreeLaneX(lane) {
  return [-2.25, 0, 2.25][Math.max(0, Math.min(2, lane))] || 0;
}

function seasonTwoThreeItemZ(itemY) {
  return -24 + itemY * 0.32;
}

function makeSeasonTwoThreeMaterial(THREE, color, roughness = 0.72, metalness = 0.05, options = {}) {
  return new THREE.MeshStandardMaterial({
    color,
    roughness,
    metalness,
    flatShading: Boolean(options.flatShading),
    emissive: options.emissive || 0x000000,
    emissiveIntensity: options.emissiveIntensity || 0,
    transparent: Boolean(options.transparent),
    opacity: options.opacity ?? 1,
  });
}

function addSeasonTwoBox(THREE, scene, size, position, color, rotation = [0, 0, 0], materialOptions = {}) {
  const geometry = new THREE.BoxGeometry(size[0], size[1], size[2]);
  const material = makeSeasonTwoThreeMaterial(
    THREE,
    color,
    materialOptions.roughness,
    materialOptions.metalness,
    materialOptions,
  );
  const mesh = new THREE.Mesh(geometry, material);
  mesh.position.set(position[0], position[1], position[2]);
  mesh.rotation.set(rotation[0], rotation[1], rotation[2]);
  mesh.castShadow = true;
  mesh.receiveShadow = true;
  scene.add(mesh);
  return mesh;
}

function addSeasonTwoSphere(THREE, group, radius, position, color, scale = [1, 1, 1], materialOptions = {}) {
  const geometry = new THREE.SphereGeometry(radius, 24, 18);
  const material = makeSeasonTwoThreeMaterial(
    THREE,
    color,
    materialOptions.roughness ?? 0.64,
    materialOptions.metalness ?? 0.02,
    materialOptions,
  );
  const mesh = new THREE.Mesh(geometry, material);
  mesh.position.set(position[0], position[1], position[2]);
  mesh.scale.set(scale[0], scale[1], scale[2]);
  mesh.castShadow = true;
  mesh.receiveShadow = true;
  group.add(mesh);
  return mesh;
}

function addSeasonTwoCylinder(THREE, group, radiusTop, radiusBottom, height, position, color, rotation = [0, 0, 0], radialSegments = 24) {
  const geometry = new THREE.CylinderGeometry(radiusTop, radiusBottom, height, radialSegments);
  const material = makeSeasonTwoThreeMaterial(THREE, color, 0.68, 0.04, { flatShading: true });
  const mesh = new THREE.Mesh(geometry, material);
  mesh.position.set(position[0], position[1], position[2]);
  mesh.rotation.set(rotation[0], rotation[1], rotation[2]);
  mesh.castShadow = true;
  mesh.receiveShadow = true;
  group.add(mesh);
  return mesh;
}

function addSeasonTwoCone(THREE, group, radius, height, position, color, rotation = [0, 0, 0], radialSegments = 18, scale = [1, 1, 1]) {
  const geometry = new THREE.ConeGeometry(radius, height, radialSegments);
  const material = makeSeasonTwoThreeMaterial(THREE, color, 0.62, 0.03, { flatShading: true });
  const mesh = new THREE.Mesh(geometry, material);
  mesh.position.set(position[0], position[1], position[2]);
  mesh.rotation.set(rotation[0], rotation[1], rotation[2]);
  mesh.scale.set(scale[0], scale[1], scale[2]);
  mesh.castShadow = true;
  mesh.receiveShadow = true;
  group.add(mesh);
  return mesh;
}

function createSeasonTwoKaiju3D(THREE, evolution, scale = 1) {
  const colors = {
    monkey: { body: 0xb7793b, dark: 0x7c4a1d, belly: 0xf9d29d, horn: 0xf59e0b, claw: 0xfffbeb, mouth: 0x7f1d1d },
    gorilla: { body: 0x4b5563, dark: 0x1f2937, belly: 0xd1d5db, horn: 0x9ca3af, claw: 0xfffbeb, mouth: 0x111827 },
    dino: { body: 0xef4444, dark: 0xb91c1c, belly: 0xffedd5, horn: 0xf97316, claw: 0xfffbeb, mouth: 0x450a0a },
    baby: { body: 0x22c55e, dark: 0x15803d, belly: 0xfef3c7, horn: 0xfde68a, claw: 0xfffbeb, mouth: 0x7f1d1d },
    kaiju1: { body: 0xfacc15, dark: 0xca8a04, belly: 0xecfccb, horn: 0x22c55e, claw: 0xfffbeb, mouth: 0x7f1d1d },
    kaiju2: { body: 0xef4444, dark: 0xb91c1c, belly: 0xffedd5, horn: 0xf97316, claw: 0xfffbeb, mouth: 0x450a0a },
    grown: { body: 0xfacc15, dark: 0xca8a04, belly: 0xecfccb, horn: 0x22c55e, claw: 0xfffbeb, mouth: 0x7f1d1d },
    mutant: { body: 0xef4444, dark: 0xb91c1c, belly: 0xffedd5, horn: 0xf97316, claw: 0xfffbeb, mouth: 0x450a0a },
    legend: { body: 0x38bdf8, dark: 0x0284c7, belly: 0xf5d0fe, horn: 0xa78bfa, claw: 0xfef9c3, mouth: 0x312e81 },
  };
  const palette = colors[evolution.className] || colors.baby;
  const forms = {
    monkey: {
      body: [0.72, [0, 0.96, 0], [0.78, 0.98, 1.02]],
      belly: [0.34, [0, 0.98, 0.58], [0.78, 0.96, 0.34]],
      head: [0.5, [0, 1.74, 0.42], [1.08, 0.86, 0.92]],
      snout: [0.28, [0, 1.64, 1.02], [1.08, 0.54, 0.74]],
      mouth: [0, 1.54, 1.2],
      eyeY: 1.9,
      hornY: 2.2,
      spikeScale: 0.72,
      tailScale: 0.82,
      legScale: 0.82,
      armScale: 0.78,
      ears: true,
      horns: false,
      spikes: false,
      shoulders: false,
    },
    gorilla: {
      body: [0.82, [0, 1.02, -0.02], [1.18, 1.08, 1.0]],
      belly: [0.38, [0, 1.02, 0.6], [1.02, 1.02, 0.36]],
      head: [0.54, [0, 1.82, 0.36], [1.14, 0.8, 0.88]],
      snout: [0.32, [0, 1.7, 1.0], [1.28, 0.55, 0.72]],
      mouth: [0, 1.58, 1.22],
      eyeY: 1.98,
      hornY: 2.24,
      spikeScale: 0.4,
      tailScale: 0.28,
      legScale: 1.16,
      armScale: 1.78,
      ears: true,
      horns: false,
      spikes: false,
      shoulders: true,
    },
    dino: {
      body: [0.82, [0, 1.14, -0.02], [1.04, 1.34, 1.22]],
      belly: [0.38, [0, 1.14, 0.7], [0.96, 1.18, 0.42]],
      head: [0.58, [0, 2.12, 0.42], [1.08, 0.96, 0.98]],
      snout: [0.34, [0, 1.98, 1.08], [1.18, 0.6, 0.84]],
      mouth: [0, 1.84, 1.3],
      eyeY: 2.26,
      hornY: 2.66,
      spikeScale: 1.38,
      tailScale: 1.24,
      legScale: 1.18,
      armScale: 1.22,
      ears: false,
      horns: true,
      spikes: true,
      shoulders: true,
    },
  };
  forms.baby = forms.monkey;
  forms.kaiju1 = forms.gorilla;
  forms.kaiju2 = forms.dino;
  const form = forms[evolution.className] || forms.monkey;
  const group = new THREE.Group();
  group.scale.setScalar(SEASON_TWO_CHARACTER_SIZE_MULTIPLIER * scale * evolution.scale);
  const legs = [];
  const arms = [];

  const shadow = addSeasonTwoCylinder(THREE, group, 0.8, 0.8, 0.03, [0, 0.03, 0.08], 0x0f172a, [0, 0, 0], 36);
  shadow.scale.set(1.36, 1, 0.72);
  shadow.castShadow = false;
  shadow.receiveShadow = false;
  shadow.material.transparent = true;
  shadow.material.opacity = 0.2;
  shadow.userData.isGroundShadow = true;

  addSeasonTwoSphere(THREE, group, form.body[0], form.body[1], palette.body, form.body[2], { flatShading: true });
  addSeasonTwoSphere(THREE, group, form.belly[0], form.belly[1], palette.belly, form.belly[2], { roughness: 0.76 });
  addSeasonTwoSphere(THREE, group, form.head[0], form.head[1], palette.body, form.head[2], { flatShading: true });
  addSeasonTwoSphere(THREE, group, form.snout[0], form.snout[1], palette.body, form.snout[2], { flatShading: true });
  addSeasonTwoBox(THREE, group, [0.38, 0.08, 0.08], form.mouth, palette.mouth, [0.03, 0, 0], { roughness: 0.52 });

  addSeasonTwoSphere(THREE, group, 0.105, [-0.21, form.eyeY, 1.02], 0xf8fafc, [1, 1, 0.72]);
  addSeasonTwoSphere(THREE, group, 0.105, [0.21, form.eyeY, 1.02], 0xf8fafc, [1, 1, 0.72]);
  addSeasonTwoSphere(THREE, group, 0.048, [-0.21, form.eyeY - 0.01, 1.08], 0x0f172a, [1, 1, 0.7]);
  addSeasonTwoSphere(THREE, group, 0.048, [0.21, form.eyeY - 0.01, 1.08], 0x0f172a, [1, 1, 0.7]);

  if (form.horns) {
    addSeasonTwoCone(THREE, group, 0.1 + evolution.rank * 0.025, 0.28 + evolution.rank * 0.13, [-0.28, form.hornY, 0.34], palette.horn, [0.08, 0, 0.24], 18, [1, 1.1, 0.9]);
    addSeasonTwoCone(THREE, group, 0.1 + evolution.rank * 0.025, 0.28 + evolution.rank * 0.13, [0.28, form.hornY, 0.34], palette.horn, [0.08, 0, -0.24], 18, [1, 1.1, 0.9]);
  }

  if (form.ears) {
    addSeasonTwoSphere(THREE, group, evolution.className === "gorilla" ? 0.18 : 0.15, [-0.45, form.eyeY - 0.04, 0.38], palette.dark, [0.72, 1, 0.72]);
    addSeasonTwoSphere(THREE, group, evolution.className === "gorilla" ? 0.18 : 0.15, [0.45, form.eyeY - 0.04, 0.38], palette.dark, [0.72, 1, 0.72]);
  }

  if (form.spikes) {
    for (const spike of [
      [0, 1.82, -0.52, 0.2, 0.46],
      [0, 1.42, -0.78, 0.18, 0.42],
      [0, 1.04, -0.88, 0.15, 0.34],
    ]) {
      addSeasonTwoCone(THREE, group, spike[3] * form.spikeScale, spike[4] * form.spikeScale, [spike[0], spike[1], spike[2]], palette.horn, [-Math.PI / 2, 0, 0], 16, [0.82, 1, 1]);
    }
  }

  if (form.tailScale > 0.35) {
    addSeasonTwoCylinder(THREE, group, 0.16 * form.tailScale, 0.32 * form.tailScale, 0.92 * form.tailScale, [0, 0.68, -0.9], palette.dark, [Math.PI / 2, 0, 0], 18);
    addSeasonTwoCone(THREE, group, 0.16 * form.tailScale, 0.46 * form.tailScale, [0, 0.68, -1.48], palette.horn, [-Math.PI / 2, 0, 0], 16);
  }

  for (const side of [-1, 1]) {
    legs.push({
      mesh: addSeasonTwoBox(THREE, group, [0.24 * form.legScale, 0.56 * form.legScale, 0.34 * form.legScale], [side * 0.36, 0.48, 0.04], palette.dark, [0.02, 0, side * 0.08], { flatShading: true }),
      side,
    });
    legs.push({
      mesh: addSeasonTwoBox(THREE, group, [0.42 * form.legScale, 0.18 * form.legScale, 0.62 * form.legScale], [side * 0.36, 0.18, 0.34], palette.dark, [0, side * 0.08, 0], { flatShading: true }),
      side,
      foot: true,
    });
    arms.push({
      mesh: addSeasonTwoBox(THREE, group, [0.22 * form.armScale, 0.5 * form.armScale, 0.28 * form.armScale], [side * 0.66, 1.14, 0.18], palette.body, [0.16, 0, side * 0.54], { flatShading: true }),
      side,
    });
    addSeasonTwoCone(THREE, group, 0.07, 0.22, [side * 0.84, 0.86, 0.38], palette.claw, [0, 0, side > 0 ? -Math.PI / 2 : Math.PI / 2], 12);
  }

  if (evolution.rank >= 2) {
    for (const side of [-1, 1]) {
      if (form.horns) {
        addSeasonTwoCone(
          THREE,
          group,
          0.14,
          0.42,
          [side * 0.62, 1.48, -0.06],
          palette.horn,
          [0, 0, side > 0 ? -Math.PI / 2 : Math.PI / 2],
          16,
          [1, 1, 0.8],
        );
      }
      if (form.shoulders) {
        addSeasonTwoSphere(THREE, group, evolution.className === "gorilla" ? 0.34 : 0.22, [side * 0.62, 1.32, -0.04], form.horns ? palette.horn : palette.dark, [1.24, 0.76, 0.88], {
          emissive: form.horns ? palette.horn : 0x000000,
          emissiveIntensity: form.horns ? 0.08 : 0,
        });
      }
    }
    addSeasonTwoBox(THREE, group, evolution.className === "gorilla" ? [0.76, 0.18, 0.18] : [0.52, 0.16, 0.14], evolution.className === "gorilla" ? [0, 1.66, 0.44] : [0, 2.08, 0.62], form.horns ? palette.horn : palette.dark, [0.2, 0, 0], {
      flatShading: true,
    });
  }

  if (evolution.rank >= 3) {
    addSeasonTwoBox(THREE, group, [0.42, 0.22, 0.12], [0, 2.2, 0.8], palette.horn, [0.22, 0, 0], { flatShading: true });
    addSeasonTwoSphere(THREE, group, 0.08, [0, 2.3, 0.82], palette.horn, [1, 1, 1], { emissive: palette.horn, emissiveIntensity: 0.16 });
    for (const side of [-1, 1]) {
      addSeasonTwoBox(THREE, group, [0.14, 0.86, 0.52], [side * 0.84, 1.32, -0.42], palette.dark, [0.28, side * 0.38, side * 0.28], {
        flatShading: true,
        emissive: palette.dark,
        emissiveIntensity: 0.06,
      });
      addSeasonTwoCone(
        THREE,
        group,
        0.18,
        0.56,
        [side * 0.92, 1.92, -0.18],
        palette.horn,
        [0.36, 0, side > 0 ? -0.82 : 0.82],
        16,
        [0.8, 1.25, 0.75],
      );
      addSeasonTwoCone(
        THREE,
        group,
        0.11,
        0.34,
        [side * 0.9, 0.7, 0.46],
        palette.claw,
        [0, 0, side > 0 ? -Math.PI / 2 : Math.PI / 2],
        12,
        [1, 1.2, 0.8],
      );
    }
    addSeasonTwoSphere(THREE, group, 0.16, [0, 1.42, 0.78], 0xfacc15, [1, 0.75, 0.45], {
      emissive: 0xf97316,
      emissiveIntensity: 0.34,
    });
    addSeasonTwoCone(THREE, group, 0.18, 0.68, [0, 2.62, 0.34], 0xf97316, [0, 0, 0], 18, [0.8, 1.28, 0.8]);
  }

  if (evolution.rank >= 4) {
    addSeasonTwoSphere(THREE, group, 0.92, [0, 1.12, 0.02], 0xa5f3fc, [0.9, 0.92, 1.1], {
      roughness: 0.38,
      metalness: 0.02,
      transparent: true,
      opacity: 0.18,
      emissive: 0x38bdf8,
      emissiveIntensity: 0.12,
    });
  }

  group.userData.runParts = { arms, legs };
  group.rotation.y = Math.PI - 0.18;
  group.rotation.x = -0.03;
  return group;
}

function poseSeasonTwoKaijuRun(group, tick = 0, isBossScene = false, isAttacking = false, attackKind = "flame") {
  const phase = tick * 0.72;
  const stride = Math.sin(phase);
  const counterStride = Math.sin(phase + Math.PI);
  const parts = group.userData.runParts || { arms: [], legs: [] };

  if (!isBossScene) {
    group.position.y += Math.abs(stride) * 0.08;
    group.rotation.z = stride * 0.035;
  }

  if (isAttacking) {
    group.position.x += 0.36;
    group.position.y += 0.08;
    group.rotation.z = -0.1;
  }

  parts.legs.forEach((part) => {
    const wave = part.side > 0 ? stride : counterStride;
    part.mesh.rotation.x += wave * (part.foot ? 0.22 : 0.42);
    part.mesh.position.z += wave * (part.foot ? 0.16 : 0.08);
  });

  parts.arms.forEach((part) => {
    const wave = part.side > 0 ? counterStride : stride;
    part.mesh.rotation.x += wave * 0.46;
    part.mesh.rotation.z += part.side * Math.abs(wave) * 0.12;
    if (isAttacking && attackKind === "flame") {
      part.mesh.rotation.x -= 0.24;
      group.rotation.x -= 0.035;
    }
  });
}

function seasonTwoMonsterScale(size, mutationSize, isBossScene) {
  const growthRatio = Math.min(1.35, Math.max(0, size - 1) / Math.max(20, mutationSize));
  const base = isBossScene ? 0.86 : 0.68;
  const visualGrowth = growthRatio * 0.26;
  return Math.min(isBossScene ? 1.24 : 1.1, base + visualGrowth);
}

function createSeasonTwoBoss3D(THREE, boss) {
  const palettes = {
    burger: { body: 0xfb923c, accent: 0xfef3c7, glow: 0xef4444 },
    golem: { body: 0xa16207, accent: 0xfbbf24, glow: 0x22c55e },
    drone: { body: 0x2563eb, accent: 0xa5f3fc, glow: 0x38bdf8 },
    titan: { body: 0x334155, accent: 0x7c3aed, glow: 0xef4444 },
  };
  const palette = palettes[boss.className] || palettes.titan;
  const group = new THREE.Group();
  group.scale.setScalar(1.18);
  addSeasonTwoSphere(THREE, group, 0.86, [0, 1.24, 0], palette.body, [1.0, 1.25, 0.72]);
  addSeasonTwoSphere(THREE, group, 0.5, [0, 2.15, 0.08], palette.body, [1.12, 0.85, 0.78]);
  addSeasonTwoSphere(THREE, group, 0.18, [0, 1.38, 0.52], palette.glow, [1, 1, 0.35]);
  addSeasonTwoBox(THREE, group, [0.34, 0.95, 0.3], [-0.82, 1.12, 0.04], palette.accent, [0, 0, 0.2]);
  addSeasonTwoBox(THREE, group, [0.34, 0.95, 0.3], [0.82, 1.12, 0.04], palette.accent, [0, 0, -0.2]);
  addSeasonTwoBox(THREE, group, [0.32, 0.62, 0.34], [-0.34, 0.36, 0.02], palette.body);
  addSeasonTwoBox(THREE, group, [0.32, 0.62, 0.34], [0.34, 0.36, 0.02], palette.body);
  addSeasonTwoSphere(THREE, group, 0.07, [-0.18, 2.2, 0.52], 0xf8fafc);
  addSeasonTwoSphere(THREE, group, 0.07, [0.18, 2.2, 0.52], 0xf8fafc);
  group.rotation.y = 0.28;
  return group;
}

function createSeasonTwoItem3D(THREE, item) {
  const group = new THREE.Group();
  const kind = item.kind;
  if (kind === "bomb" || kind === "nuke") {
    const shell = kind === "nuke" ? 0x7f1d1d : 0x1f2937;
    const glow = kind === "nuke" ? 0xef4444 : 0xf97316;
    addSeasonTwoSphere(THREE, group, kind === "nuke" ? 0.48 : 0.38, [0, 0.02, 0], shell, [1, 1, 1], {
      roughness: 0.42,
      metalness: 0.08,
      emissive: kind === "nuke" ? 0xdc2626 : 0x000000,
      emissiveIntensity: kind === "nuke" ? 0.28 : 0,
    });
    addSeasonTwoCylinder(THREE, group, 0.08, 0.1, 0.28, [0, 0.42, 0], glow, [0, 0, 0], 16);
    addSeasonTwoSphere(THREE, group, 0.1, [0.12, 0.6, 0.03], 0xfef3c7, [1, 1, 1], {
      emissive: glow,
      emissiveIntensity: 0.3,
    });
    if (kind === "nuke") {
      addSeasonTwoCylinder(THREE, group, 0.56, 0.56, 0.04, [0, -0.02, 0], 0xef4444, [Math.PI / 2, 0, 0], 36);
    }
  } else {
    const meatColor = kind === "double_meat" ? 0xfacc15 : 0xf97316;
    const meatDark = kind === "double_meat" ? 0xca8a04 : 0xb45309;
    addSeasonTwoSphere(THREE, group, kind === "double_meat" ? 0.44 : 0.34, [0.05, 0.02, 0], meatColor, [1.28, 0.9, 0.82], {
      roughness: 0.58,
      emissive: kind === "double_meat" ? 0xfacc15 : 0x000000,
      emissiveIntensity: kind === "double_meat" ? 0.12 : 0,
    });
    addSeasonTwoSphere(THREE, group, 0.22, [0.18, 0.08, 0.08], meatDark, [1, 0.72, 0.72]);
    addSeasonTwoCylinder(THREE, group, 0.08, 0.08, 0.55, [-0.38, 0, 0], 0xfef3c7, [0, 0, Math.PI / 2], 16);
    addSeasonTwoSphere(THREE, group, 0.11, [-0.64, 0.1, 0], 0xfef3c7, [1, 1, 1]);
    addSeasonTwoSphere(THREE, group, 0.11, [-0.64, -0.1, 0], 0xfef3c7, [1, 1, 1]);
    if (kind === "double_meat") {
      addSeasonTwoSphere(THREE, group, 0.13, [0.44, 0.2, 0.02], 0xfef9c3, [1, 1, 1], {
        emissive: 0xfacc15,
        emissiveIntensity: 0.22,
      });
    }
  }
  group.position.set(seasonTwoThreeLaneX(item.lane), 0.72, seasonTwoThreeItemZ(item.y));
  group.scale.setScalar(kind === "nuke" ? 1.42 : kind === "double_meat" ? 1.34 : 1.18);
  group.rotation.y = (item.y + item.lane * 40) * 0.025;
  return group;
}

function addSeasonTwoLaserSegment3D(THREE, scene, start, end, radius, color, opacity, radialSegments = 24) {
  const direction = new THREE.Vector3().subVectors(end, start);
  const length = direction.length();
  if (length <= 0.01) return;
  const geometry = new THREE.CylinderGeometry(radius, radius, length, radialSegments, 1, true);
  const material = new THREE.MeshBasicMaterial({
    color,
    transparent: true,
    opacity,
    depthWrite: false,
    blending: THREE.AdditiveBlending,
  });
  const beam = new THREE.Mesh(geometry, material);
  beam.position.copy(start).add(end).multiplyScalar(0.5);
  beam.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), direction.normalize());
  scene.add(beam);
}

function addSeasonTwoAttack3D(THREE, scene, kind = "flame", quality = 0.6, progress = 1) {
  const power = Math.max(0.45, Math.min(1, quality || 0.6));
  const effectProgress = Math.max(0, Math.min(1, progress ?? 1));
  const grow = effectProgress * effectProgress * (3 - 2 * effectProgress);
  const fadeIn = Math.min(1, effectProgress / 0.16);
  const fadeOut = effectProgress > 0.82 ? Math.max(0, (1 - effectProgress) / 0.18) : 1;
  const opacity = fadeIn * fadeOut;
  const start = new THREE.Vector3(-2.08, 1.42, -0.68);
  const target = new THREE.Vector3(2.22, 1.5, -0.68);
  const beamEnd = start.clone().lerp(target, Math.min(1, grow * 1.08));
  const pulse = 0.86 + Math.sin(effectProgress * Math.PI * 8) * 0.14;
  const laserColor = kind === "flame" ? 0x38bdf8 : 0x67e8f9;

  addSeasonTwoLaserSegment3D(THREE, scene, start, beamEnd, (0.09 + power * 0.055) * pulse, 0x0ea5e9, opacity * 0.18, 28);
  addSeasonTwoLaserSegment3D(THREE, scene, start, beamEnd, (0.052 + power * 0.026) * pulse, laserColor, opacity * 0.44, 24);
  addSeasonTwoLaserSegment3D(THREE, scene, start, beamEnd, (0.018 + power * 0.012) * pulse, 0xf8fafc, opacity * 0.92, 18);

  addSeasonTwoSphere(THREE, scene, 0.14 + power * 0.05, [start.x, start.y, start.z], 0xe0f2fe, [1.28, 0.8, 0.8], {
    emissive: 0x38bdf8,
    emissiveIntensity: 0.68,
    transparent: true,
    opacity: opacity * 0.58,
  });

  for (let index = 0; index < 6; index += 1) {
    const streamT = (effectProgress * 1.45 + index * 0.18) % 1;
    if (streamT > grow) continue;
    const spark = start.clone().lerp(target, streamT);
    spark.y += Math.sin((streamT + index) * Math.PI * 4) * 0.045;
    spark.z += Math.cos((streamT + index) * Math.PI * 3) * 0.045;
    addSeasonTwoSphere(THREE, scene, 0.035 + power * 0.018, [spark.x, spark.y, spark.z], 0xf8fafc, [1.2, 0.8, 1], {
      emissive: 0x67e8f9,
      emissiveIntensity: 0.58,
      transparent: true,
      opacity: opacity * 0.34,
    });
  }

  const impact = Math.max(0, Math.min(1, (grow - 0.82) / 0.18));
  if (impact > 0) {
    addSeasonTwoSphere(THREE, scene, 0.18 + power * 0.13 * impact, [target.x, target.y, target.z], 0xf8fafc, [1.32, 0.82, 1], {
      emissive: 0x22d3ee,
      emissiveIntensity: 0.78,
      transparent: true,
      opacity: opacity * impact * 0.66,
    });
    addSeasonTwoSphere(THREE, scene, 0.34 + power * 0.18 * impact, [target.x, target.y, target.z], 0x38bdf8, [1.22, 0.58, 1], {
      emissive: 0x0ea5e9,
      emissiveIntensity: 0.42,
      transparent: true,
      opacity: opacity * impact * 0.22,
    });
  }
}

function addSeasonTwoHitExplosion3D(THREE, scene, target = "boss") {
  const centerX = target === "player" ? -1.72 : 1.72;
  const baseY = target === "player" ? 1.3 : 1.46;
  for (let index = 0; index < 10; index += 1) {
    const angle = (Math.PI * 2 * index) / 10;
    const radius = 0.18 + (index % 4) * 0.08;
    const color = index % 3 === 0 ? 0xfffbeb : index % 3 === 1 ? 0xfacc15 : 0xef4444;
    addSeasonTwoSphere(
      THREE,
      scene,
      0.14 + (index % 3) * 0.05,
      [centerX + Math.cos(angle) * radius, baseY + Math.sin(angle) * radius, -0.64 + Math.sin(angle) * 0.08],
      color,
      [1.2, 0.9, 1],
      {
        emissive: color,
        emissiveIntensity: 0.6,
        transparent: true,
        opacity: 0.58,
      },
    );
  }
  addSeasonTwoSphere(THREE, scene, 0.42, [centerX, baseY, -0.64], 0xfff7ed, [1.28, 0.84, 1], {
    emissive: 0xf97316,
    emissiveIntensity: 0.7,
    transparent: true,
    opacity: 0.38,
  });
}

function addSeasonTwoPickupGlow3D(THREE, scene, data) {
  const color = data.pickupGlowKind === "bad" ? 0xef4444 : 0x38bdf8;
  const alpha = Math.max(0, Math.min(1, data.pickupGlowAlpha ?? 1));
  const outline = createSeasonTwoKaiju3D(
    THREE,
    data.evolution,
    seasonTwoMonsterScale(data.size, data.mutationSize, data.isBossScene),
  );

  if (data.isBossScene) {
    outline.position.set(-2.45, 0.2, -0.68);
    outline.rotation.y = Math.PI / 2;
    poseSeasonTwoKaijuRun(outline, data.tick, true, data.attackEffectActive, data.attackKind);
  } else {
    outline.position.set(seasonTwoThreeLaneX(data.lane), 0.14, 5.45);
    poseSeasonTwoKaijuRun(outline, data.tick, false, false);
  }

  outline.scale.multiplyScalar(data.isBossScene ? 1.024 : 1.032);
  outline.renderOrder = -1;
  outline.traverse((object) => {
    if (!object.isMesh) return;
    if (object.userData?.isGroundShadow) {
      object.visible = false;
      return;
    }
    const oldMaterials = Array.isArray(object.material) ? object.material : [object.material];
    oldMaterials.forEach((material) => material?.dispose?.());
    object.material = new THREE.MeshBasicMaterial({
      color,
      transparent: true,
      opacity: alpha * 0.26,
      side: THREE.BackSide,
      depthWrite: false,
      blending: THREE.AdditiveBlending,
    });
    object.renderOrder = -1;
    object.castShadow = false;
    object.receiveShadow = false;
  });
  scene.add(outline);
}

function addSeasonTwoBossCounter3D(THREE, scene) {
  for (let index = 0; index < 6; index += 1) {
    const t = index / 5;
    const x = 1.45 - t * 2.9;
    const y = 1.36 + Math.sin(t * Math.PI) * 0.22;
    const color = index % 2 ? 0xef4444 : 0xf97316;
    addSeasonTwoSphere(THREE, scene, 0.22 + t * 0.22, [x, y, -0.66], color, [1.22, 0.8, 0.96], {
      emissive: color,
      emissiveIntensity: 0.48,
      transparent: true,
      opacity: 0.62,
    });
  }
  addSeasonTwoCone(THREE, scene, 0.46, 1.08, [-1.24, 1.34, -0.66], 0xfacc15, [0, 0, Math.PI / 2], 28, [1, 0.72, 1]);
  addSeasonTwoSphere(THREE, scene, 0.58, [-1.58, 1.24, -0.64], 0xffffff, [1.18, 0.74, 0.92], {
    emissive: 0xf97316,
    emissiveIntensity: 0.34,
    transparent: true,
    opacity: 0.44,
  });
}

function addSeasonTwoBossDissolve3D(THREE, scene) {
  for (let index = 0; index < 10; index += 1) {
    const angle = (Math.PI * 2 * index) / 10;
    const radius = 0.24 + (index % 3) * 0.16;
    addSeasonTwoSphere(
      THREE,
      scene,
      0.22 + (index % 4) * 0.06,
      [2.35 + Math.cos(angle) * radius, 1.1 + index * 0.12, -0.78 + Math.sin(angle) * radius * 0.6],
      index % 2 ? 0xf8fafc : 0xfef3c7,
      [1.34, 0.74, 1],
      {
        emissive: index % 2 ? 0xa5f3fc : 0xfacc15,
        emissiveIntensity: 0.12,
        transparent: true,
        opacity: 0.34,
      },
    );
  }
}

function addSeasonTwoThreeWorld(THREE, scene, data) {
  scene.background = new THREE.Color(0x8bdcfb);
  scene.fog = new THREE.Fog(0x8bdcfb, 28, 72);
  scene.add(new THREE.HemisphereLight(0xffffff, 0x7dd3fc, 1.8));
  const sun = new THREE.DirectionalLight(0xffffff, 2.4);
  sun.position.set(6, 10, 8);
  sun.castShadow = true;
  scene.add(sun);
  const rim = new THREE.DirectionalLight(0xa5f3fc, 1.1);
  rim.position.set(-5, 4.2, 6);
  scene.add(rim);
  addSeasonTwoBox(THREE, scene, [18, 0.16, 58], [0, -0.12, -12], 0x7ddf9b, [0, 0, 0], { roughness: 0.9 });
  addSeasonTwoBox(THREE, scene, [7.6, 0.28, 58], [0, 0, -12], 0x475569, [0, 0, 0], { roughness: 0.82 });
  addSeasonTwoBox(THREE, scene, [0.22, 0.08, 58], [-3.95, 0.18, -12], 0x22c55e);
  addSeasonTwoBox(THREE, scene, [0.22, 0.08, 58], [3.95, 0.18, -12], 0x22c55e);
  for (let z = -40; z <= 13; z += 2.6) {
    addSeasonTwoBox(THREE, scene, [0.08, 0.07, 1.1], [-1.27, 0.23, z], 0xfde047);
    addSeasonTwoBox(THREE, scene, [0.08, 0.07, 1.1], [1.27, 0.23, z], 0xfde047);
  }
  for (let i = 0; i < 9; i += 1) {
    const x = -7.4 + i * 1.85;
    const height = 1.2 + ((i * 37) % 5) * 0.42;
    addSeasonTwoBox(THREE, scene, [1.1, height, 0.9], [x, height * 0.5 - 0.04, -38], i % 2 ? 0x93c5fd : 0xbfdbfe, [0, 0, 0], { roughness: 0.88 });
  }
  const sunGeometry = new THREE.SphereGeometry(1.1, 28, 18);
  const sunMaterial = new THREE.MeshBasicMaterial({ color: 0xfde047 });
  const sunMesh = new THREE.Mesh(sunGeometry, sunMaterial);
  sunMesh.position.set(6.6, 7.8, -34);
  scene.add(sunMesh);
  for (const cloud of [[-5.6, 5.3, -23], [-2.7, 6.1, -31], [4.1, 5.6, -26]]) {
    const group = new THREE.Group();
    addSeasonTwoSphere(THREE, group, 0.54, [0, 0, 0], 0xffffff, [1.5, 0.58, 0.5]);
    addSeasonTwoSphere(THREE, group, 0.42, [0.54, 0.08, 0.04], 0xffffff, [1.18, 0.5, 0.44]);
    group.position.set(cloud[0], cloud[1], cloud[2]);
    scene.add(group);
  }
  if (!data.isBossScene) {
    data.items.forEach((item) => scene.add(createSeasonTwoItem3D(THREE, item)));
  }
}

function renderSeasonTwoThreeFrame(THREE, renderer, data, panProgress = 1) {
  const { width, height } = data;
  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(data.isBossScene ? 42 : 58, width / height, 0.1, 100);
  addSeasonTwoThreeWorld(THREE, scene, data);

  const runnerCamera = {
    position: new THREE.Vector3(0, 5.55, 13.6),
    target: new THREE.Vector3(0, 1.02, -5.2),
  };
  const bossCamera = {
    position: new THREE.Vector3(0, 1.9, 10.4),
    target: new THREE.Vector3(0, 1.32, -0.68),
  };
  const eased = panProgress * panProgress * (3 - 2 * panProgress);
  const cameraPosition = data.isBossScene
    ? runnerCamera.position.clone().lerp(bossCamera.position, eased)
    : runnerCamera.position;
  const cameraTarget = data.isBossScene
    ? runnerCamera.target.clone().lerp(bossCamera.target, eased)
    : runnerCamera.target;
  camera.position.copy(cameraPosition);
  camera.lookAt(cameraTarget);

  const player = createSeasonTwoKaiju3D(
    THREE,
    data.evolution,
    seasonTwoMonsterScale(data.size, data.mutationSize, data.isBossScene),
  );
  if (data.isBossScene) {
    player.position.set(-2.45, 0.2, -0.68);
    player.rotation.y = Math.PI / 2;
    poseSeasonTwoKaijuRun(player, data.tick, true, data.attackEffectActive, data.attackKind);
    const boss = createSeasonTwoBoss3D(THREE, data.boss);
    boss.position.set(2.55, 0.18, -0.68);
    boss.rotation.y = -Math.PI / 2;
    if (data.bossTurnEffectActive) {
      boss.position.x -= 0.52;
      boss.position.y += 0.06;
      boss.rotation.z = -0.12;
      boss.scale.multiplyScalar(1.08);
    }
    if (data.phase === "win") {
      addSeasonTwoBossDissolve3D(THREE, scene);
    } else {
      scene.add(boss);
    }
    if (data.attackEffectActive) addSeasonTwoAttack3D(
      THREE,
      scene,
      data.attackKind,
      data.attackEffectQuality,
      data.attackEffectProgress,
    );
    if (data.bossTurnEffectActive) addSeasonTwoBossCounter3D(THREE, scene);
    if (data.hitExplosionActive) addSeasonTwoHitExplosion3D(THREE, scene, data.hitExplosionTarget);
  } else {
    player.position.set(seasonTwoThreeLaneX(data.lane), 0.14, 5.45);
    poseSeasonTwoKaijuRun(player, data.tick, false, false);
  }
  if (data.pickupGlowActive) addSeasonTwoPickupGlow3D(THREE, scene, data);
  scene.add(player);

  renderer.setSize(width, height, false);
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
  renderer.render(scene, camera);
  disposeThreeScene(scene);
}

function renderSeasonTwoThreeScene(data) {
  const mount = els.gameMount.querySelector(".runner-three-layer");
  if (!mount) return;
  const renderToken = ++seasonTwoThree.renderToken;
  const rect = mount.getBoundingClientRect();
  const width = Math.max(2, Math.floor(rect.width));
  const height = Math.max(2, Math.floor(rect.height));
  const frameData = { ...data, width, height };

  loadSeasonTwoThree()
    .then((THREE) => {
      if (!mount.isConnected || renderToken !== seasonTwoThree.renderToken) return;
      if (!seasonTwoThree.renderer) {
        seasonTwoThree.renderer = new THREE.WebGLRenderer({ antialias: true });
        seasonTwoThree.renderer.shadowMap.enabled = true;
        seasonTwoThree.renderer.domElement.className = "runner-three-canvas";
      }
      const renderer = seasonTwoThree.renderer;
      if (renderer.domElement.parentElement !== mount) mount.appendChild(renderer.domElement);
      mount.classList.add("three-ready");
      mount.classList.remove("three-failed");

      if (frameData.isBossScene && !frameData.bossCameraReady) {
        const panToken = ++seasonTwoThree.panToken;
        const startedAt = performance.now();
        const animate = (now) => {
          if (!mount.isConnected || panToken !== seasonTwoThree.panToken) return;
          const progress = Math.min(1, (now - startedAt) / 1250);
          renderSeasonTwoThreeFrame(THREE, renderer, frameData, progress);
          if (progress < 1) window.requestAnimationFrame(animate);
        };
        window.requestAnimationFrame(animate);
        return;
      }
      renderSeasonTwoThreeFrame(THREE, renderer, frameData, 1);
    })
    .catch((error) => {
      mount.dataset.error = String(error?.message || error);
      console.error("Season 2 WebGL 3D render failed", error);
      mount.classList.add("three-failed");
    });
}

function renderSeasonTwo() {
  const s = state.settings.season_02;
  const g = state.game.season_02 || (seasonTwoReset(), state.game.season_02);
  const chapter = seasonTwoChapter();
  if (g.chapter !== chapter) {
    seasonTwoReset();
    renderSeasonTwo();
    return;
  }
  const mutationSize = Math.max(10, toNumber(s.mutation_size, 60));
  g.targetEnergy = seasonTwoTargetEnergy(chapter, s);
  g.targetSeconds = seasonTwoRunnerTargetSeconds(chapter);
  g.size = seasonTwoEnergyVisualSize(g.hp, s);
  const evolution = seasonTwoEvolution(g.hp, s);
  const { gorillaScore, dinoScore } = seasonTwoMutationScores(s);
  const monsterVisualScale = seasonTwoMonsterScale(g.size, mutationSize, g.phase === "boss" || g.phase === "win" || g.phase === "gameOver");
  const progress = Math.min(100, (g.distance / g.goal) * 100);
  const energyPercent = Math.max(0, Math.min(100, (g.hp / Math.max(1, g.targetEnergy)) * 100));
  const hpPercent = Math.max(0, Math.min(100, (g.hp / Math.max(1, g.maxHp)) * 100));
  const bossPercent = Math.max(0, (g.bossHp / Math.max(1, g.boss.maxHp)) * 100);
  const laneLeft = seasonTwoLaneLeft(g.lane);
  const phaseLabel = g.phase === "runner" ? "러너" : g.phase === "boss" ? "보스전" : g.phase === "win" ? "승리" : "도전 종료";
  const isBossScene = g.phase === "boss" || g.phase === "win" || g.phase === "gameOver";
  const now = performance.now();
  const turnNoticeActive = g.phase === "boss" && (g.turnNoticeUntil || 0) > now;
  const bossTurnActive = g.phase === "boss" && g.bossTurn === "boss";
  const bossNoticeActive = g.phase === "boss" && g.bossTurn === "bossNotice";
  const playerNoticeActive = g.phase === "boss" && g.bossTurn === "playerNotice";
  const turnDelayActive = g.phase === "boss" && g.bossTurn === "turnDelay";
  const attackEffectActive = isBossScene && (g.attackEffectUntil || 0) > now;
  const attackEffectProgress = attackEffectActive
    ? Math.max(0, Math.min(1, 1 - ((g.attackEffectUntil - now) / SEASON_TWO_ATTACK_EFFECT_MS)))
    : 0;
  const bossTurnEffectActive = isBossScene && (g.bossTurnEffectUntil || 0) > now;
  const hitExplosionActive = isBossScene && (g.hitExplosionUntil || 0) > now;
  const pickupGlowActive = (g.pickupGlowUntil || 0) > now;
  const pickupGlowProgress = pickupGlowActive
    ? Math.max(0, Math.min(1, 1 - ((g.pickupGlowUntil - now) / SEASON_TWO_PICKUP_GLOW_MS)))
    : 0;
  const pickupGlowFade = pickupGlowActive ? Math.max(0, Math.min(1, (g.pickupGlowUntil - now) / SEASON_TWO_PICKUP_GLOW_MS)) : 0;
  const pickupGlowPulse = pickupGlowActive ? 0.08 + (Math.sin(pickupGlowProgress * Math.PI * 6) ** 2) * 0.92 : 0;
  const pickupGlowAlpha = pickupGlowFade * pickupGlowPulse;
  const attackQuality = Math.max(0, Math.min(1, g.attackEffectQuality || g.lastTiming?.quality || 0));
  const attackClass = attackQuality >= 0.9 ? "perfect" : attackQuality >= 0.72 ? "strong" : "normal";
  const attackKind = g.attackKind || g.lastTiming?.kind || "flame";
  const canPlayerAttack = seasonTwoCanAttack(g);
  const cameraClass = isBossScene ? (g.bossCameraReady ? "camera-settled" : "camera-panning") : "";
  const playerLeft = isBossScene ? 27 : laneLeft;
  const runnerItems = g.phase === "runner" ? renderSeasonTwoItems(g) : "";
  const timingPanel = canPlayerAttack ? `
    <div class="boss-timing-panel">
      <strong>Space 타이밍 공격</strong>
      <div class="boss-timing-track">
        <span class="timing-fill"></span>
        <span class="timing-perfect-zone"></span>
      </div>
      <span>${g.lastTiming ? `${g.lastTiming.label} · ${g.lastTiming.damage} 피해` : "게이지가 오른쪽 끝까지 찰 때 누르면 강공격!"}</span>
    </div>
  ` : "";
  const bossFighter = isBossScene ? `
    <div class="runner-boss">
      <div class="boss-monster boss-${g.boss.className}">
        <span class="boss-core"></span>
        <span class="boss-head"></span>
        <span class="boss-arm arm-left"></span>
        <span class="boss-arm arm-right"></span>
        <strong>${g.boss.name}</strong>
      </div>
    </div>
    <div class="versus-flash">VS</div>
  ` : "";
  const bossAttackEffect = attackEffectActive ? `
    <div class="boss-attack-effect ${attackClass} ${attackKind}">
      <span></span>
      <strong>${g.lastTiming?.damage || ""}</strong>
    </div>
  ` : "";
  const bossCounterEffect = bossTurnEffectActive ? `<div class="boss-counter-effect"><span></span><strong>${g.pendingBossDamage || ""}</strong></div>` : "";
  const hitExplosion = hitExplosionActive ? `<div class="boss-hit-explosion hit-${g.hitExplosionTarget || "boss"}"><span></span><i></i></div>` : "";
  const playerBar = "";
  const roarSpeechActive = state.gameStarted && !isBossScene && s.roar_text && (g.roarSpeechUntil || 0) > now;
  const roarSpeech = roarSpeechActive ? `
    <div class="runner-speech-overlay" style="left:${playerLeft}%">
      <span>${s.baby_name || "괴수"}</span>
      <strong>${s.roar_text}</strong>
    </div>
  ` : "";
  const bossFightHud = isBossScene ? `
    <div class="boss-fight-hud">
      <div class="boss-fight-health player">
        <span>${s.baby_name || "괴수"}</span>
        <div><i style="width:${hpPercent}%"></i></div>
        <strong>${g.hp}/${g.maxHp}</strong>
      </div>
      <div class="boss-fight-round">VS</div>
      <div class="boss-fight-health enemy">
        <span>${g.boss.name}</span>
        <div><i style="width:${bossPercent}%"></i></div>
        <strong>${g.bossHp}/${g.boss.maxHp}</strong>
      </div>
    </div>
  ` : "";
  const turnNoticeKind = g.turnNoticeKind || (bossNoticeActive || bossTurnActive ? "boss" : "player");
  const turnPopup = turnNoticeActive ? `
    <div class="season-two-turn-popup ${turnNoticeKind}">
      <strong>${turnNoticeKind === "boss" ? "보스 공격 차례" : "내 공격 차례"}</strong>
      <span>${turnNoticeKind === "boss" ? `${g.boss.name}의 반격이 시작됩니다` : "Space 타이밍 공격을 준비하세요"}</span>
    </div>
  ` : "";
  const resultPopup = g.phase === "win" ? `
    <div class="season-two-result-popup win">
      <strong>승리!</strong>
      <span>${g.boss.name} 격파! 괴수 러너 클리어!</span>
    </div>
  ` : "";
  setHud(
    s.runner_title || `${s.baby_name} 출동!`,
    `에너지 ${g.hp}/${g.targetEnergy} · ${evolution.name} · ${phaseLabel}`,
  );
  els.action.textContent = turnDelayActive ? "턴 전환 중" : playerNoticeActive ? "내 차례 준비" : bossNoticeActive ? "보스 차례 준비" : bossTurnActive ? "보스 공격 중" : g.phase === "boss" ? "Space 타이밍 공격" : g.phase === "runner" ? "← → 이동으로 먹기" : "결과 확인";
  const boardClass = `kaiju-runner-game chapter-${chapter} phase-${g.phase} ${cameraClass} ${turnNoticeActive ? `turn-notice turn-${turnNoticeKind}` : ""} ${attackEffectActive ? `attack-strike attack-${attackKind}` : ""} ${turnDelayActive ? "turn-delay" : ""} ${bossTurnActive ? "boss-turn-active" : ""} ${bossTurnEffectActive ? "boss-counter-strike" : ""} ${hitExplosionActive ? `hit-explosion hit-${g.hitExplosionTarget || "boss"}` : ""} ${pickupGlowActive ? `pickup-glow pickup-${g.pickupGlowKind || "good"}` : ""}`.trim();

  els.gameMount.innerHTML = `
    <div class="${boardClass}">
      <div class="runner-three-layer" aria-label="시즌2 3D 게임 장면">
        <span class="runner-three-badge">WebGL 3D</span>
      </div>
      ${roarSpeech}
      ${bossFightHud}
      <div class="runner-sky">
        <span class="runner-cloud cloud-a"></span>
        <span class="runner-cloud cloud-b"></span>
        <span class="runner-sun"></span>
        <div class="runner-city"></div>
      </div>
      <div class="runner-world">
        <div class="runner-road">
          <span class="lane-line lane-one"></span>
          <span class="lane-line lane-two"></span>
          <span class="boss-gate" style="--gate-glow:${progress}%">${g.boss.name}</span>
          ${runnerItems}
          <div class="runner-kaiju" style="left:${playerLeft}%">
            ${roarSpeechActive ? `<span class="kaiju-speech">${s.roar_text}</span>` : ""}
            ${seasonTwoMonsterMarkup(s.baby_name, evolution, isBossScene ? "fighter-model" : "", monsterVisualScale)}
            ${playerBar}
          </div>
          ${bossFighter}
        </div>
      </div>
      ${bossAttackEffect}
      ${bossCounterEffect}
      ${hitExplosion}
      ${turnPopup}
      ${resultPopup}
      ${timingPanel}
      <div class="runner-dashboard">
        <div>
          <strong>${g.message}</strong>
          <span>${isBossScene ? `${turnDelayActive ? "다음 차례 준비 중" : bossNoticeActive ? "보스가 공격을 준비 중" : bossTurnActive ? "보스 공격을 피하는 중" : playerNoticeActive ? "내 공격 차례 준비" : "내 공격 차례"} · 내 에너지 ${g.hp} · 보스 에너지 ${g.bossHp}/${g.boss.maxHp}` : `← → 좌우 이동 · 에너지 ${gorillaScore} 고릴라 · 에너지 ${dinoScore} 공룡`}</span>
        </div>
        <div class="runner-energy-goal">${isBossScene ? `내 에너지 ${g.hp} · 보스 ${g.bossHp}/${g.boss.maxHp}` : `목표 에너지 ${g.targetEnergy} · 예상 ${g.targetSeconds}초`}</div>
        <div class="${isBossScene ? "boss-badges" : "runner-bars"}">
          ${isBossScene ? renderSeasonTwoBossBadges(g.boss) : `
          <span class="runner-bar"><i style="width:${progress}%"></i></span>
          <span class="runner-bar hp"><i style="width:${energyPercent}%"></i></span>
          `}
        </div>
      </div>
    </div>
  `;
  renderSeasonTwoThreeScene({
    boss: g.boss,
    bossCameraReady: g.bossCameraReady,
    evolution,
    isBossScene,
    attackEffectActive,
    attackEffectProgress,
    attackEffectQuality: attackQuality,
    attackKind,
    bossTurnEffectActive,
    bossTurnActive,
    hitExplosionActive,
    hitExplosionTarget: g.hitExplosionTarget || "boss",
    pickupGlowActive,
    pickupGlowAlpha,
    pickupGlowKind: g.pickupGlowKind || "good",
    items: g.items.map((item) => ({ ...item })),
    lane: g.lane,
    mutationSize,
    size: g.size,
    tick: g.tick,
    phase: g.phase,
  });
  if (isBossScene && !g.bossCameraReady) {
    window.setTimeout(() => {
      const board = els.gameMount.querySelector(".kaiju-runner-game.camera-panning");
      if (!board) return;
      board.classList.remove("camera-panning");
      board.classList.add("camera-settled");
      g.bossCameraReady = true;
    }, 1250);
  }
  setLockedControls();
}

function moveSeasonTwoLane(delta) {
  if (!state.gameStarted || state.activeSeason !== "season_02") return;
  const g = state.game.season_02;
  if (!g || g.phase !== "runner") return;
  g.lane = Math.max(0, Math.min(2, g.lane + delta));
  g.message = `${g.lane === 0 ? "왼쪽" : g.lane === 1 ? "가운데" : "오른쪽"} 레인으로 이동!`;
  playFootstep();
  renderSeasonTwo();
}

function resolveSeasonTwoBossTurn(expectedDamage) {
  const g = state.game.season_02;
  if (state.activeSeason !== "season_02" || !g || g.phase !== "boss" || g.bossTurn !== "boss") return;
  const damage = Math.max(1, Math.round(expectedDamage || g.pendingBossDamage || 1));
  g.hp = Math.max(0, g.hp - damage);
  g.size = seasonTwoEnergyVisualSize(g.hp, state.settings.season_02);
  g.hitExplosionTarget = "player";
  g.hitExplosionUntil = performance.now() + SEASON_TWO_HIT_EXPLOSION_MS;
  g.pendingBossDamage = 0;
  if (g.hp <= 0) {
    finishSeasonTwo("gameOver", `${g.boss.name}에게 졌어. 러너 구간에서 고기를 더 모아 에너지를 키워 보자!`);
  } else {
    scheduleSeasonTwoPlayerTurnAfterDelay(g, `${g.boss.name} 반격! 내 에너지 -${damage} · 내 공격 차례 준비!`);
  }
  renderSeasonTwo();
}

function seasonTwoAction() {
  if (!state.gameStarted) return;
  const s = state.settings.season_02;
  const g = state.game.season_02;
  if (!g) return;
  if (g.phase === "runner") {
    g.message = "좌우 방향키로 괴수를 움직여 아이템을 먹어 보자!";
    renderSeasonTwo();
    return;
  }
  if (g.phase !== "boss") return;
  if (!seasonTwoCanAttack(g)) return;
  const evolution = seasonTwoEvolution(g.hp, s);
  const timing = seasonTwoTimingResult(g);
  const attackKind = "flame";
  const damage = seasonTwoPlayerAttackDamage(attackKind, timing, evolution, s, g);
  g.bossHp = Math.max(0, g.bossHp - damage);
  g.attackKind = attackKind;
  g.nextAttackKind = "flame";
  g.lastTiming = { label: timing.label, damage, quality: timing.quality, kind: attackKind };
  const now = performance.now();
  g.attackEffectUntil = now + SEASON_TWO_ATTACK_EFFECT_MS;
  g.attackEffectQuality = timing.quality;
  g.hitExplosionTarget = "boss";
  g.hitExplosionUntil = now + SEASON_TWO_HIT_EXPLOSION_MS;
  g.bossMeterStartedAt = performance.now();
  const attackLabel = "불똥";
  g.message = `${timing.label}! ${koreanSubject(evolution.name)} ${attackLabel}로 ${g.boss.name}에게 ${damage} 피해`;
  playTone({ frequency: 240, duration: 0.12, type: "square", volume: 0.05, slide: 320 });
  if (g.bossHp <= 0) {
    finishSeasonTwo("win", `${g.boss.name} 격파! 시즌2 보스전 승리!`);
    renderSeasonTwo();
    return;
  }
  const enrage = 1 + (1 - g.bossHp / Math.max(1, g.boss.maxHp)) * 0.35;
  const bossDamage = Math.max(1, Math.round(g.boss.power * enrage));
  scheduleSeasonTwoBossTurn(g, bossDamage);
  renderSeasonTwo();
  window.setTimeout(() => {
    const latest = state.game.season_02;
    if (state.activeSeason !== "season_02" || !latest || latest.phase !== "boss") return;
    if ((latest.attackEffectUntil || 0) <= performance.now() && (latest.bossTurnEffectUntil || 0) <= performance.now()) renderSeasonTwo();
  }, Math.max(SEASON_TWO_ATTACK_EFFECT_MS, SEASON_TWO_BOSS_TURN_EFFECT_MS) + 120);
}

function seasonThreeReset() {
  const s = state.settings.season_03;
  state.game.season_03 = {
    playerHp: 100,
    monsterHp: toNumber(s.monster_hp, 30),
    turn: 0,
    log: ["전투 시작!"],
  };
}

function renderSeasonThree() {
  const s = state.settings.season_03;
  const g = state.game.season_03 || (seasonThreeReset(), state.game.season_03);
  setHud("몬스터 배틀 게임", `턴 ${g.turn} · 가방 ${s.bag}`);
  els.action.textContent = "공격";
  const monsterMax = Math.max(1, toNumber(s.monster_hp, 30));
  els.gameMount.innerHTML = `
    <div class="battle-grid">
      <div class="fighter">
        <h3>플레이어</h3>
        <div class="fighter-avatar player-avatar">용사</div>
        <p>체력 ${g.playerHp}</p>
        <div class="bar"><span style="width:${Math.max(0, g.playerHp)}%"></span></div>
      </div>
      <div class="fighter">
        <h3>${s.monster_name}</h3>
        <div class="fighter-avatar monster-avatar">${s.monster_name.slice(0, 3)}</div>
        <p>체력 ${Math.max(0, g.monsterHp)}</p>
        <div class="bar"><span style="width:${Math.max(0, (g.monsterHp / monsterMax) * 100)}%"></span></div>
      </div>
    </div>
    <div class="controls">
      <button data-battle="combo" type="button">연속 공격</button>
      <button data-battle="item" type="button">아이템 보기</button>
    </div>
    <div class="message-log">${g.log.slice(-6).map((line) => `<div class="message-line">${line}</div>`).join("")}</div>
  `;
  els.gameMount.querySelector("[data-battle='combo']").addEventListener("click", comboAttack);
  els.gameMount.querySelector("[data-battle='item']").addEventListener("click", showBag);
}

function attackMonster(times = 1) {
  if (!state.gameStarted) return;
  const s = state.settings.season_03;
  const g = state.game.season_03;
  for (let i = 0; i < times; i += 1) {
    if (g.monsterHp <= 0) break;
    g.turn += 1;
    g.monsterHp -= toNumber(s.player_power, 5);
    g.log.push(`${g.turn}턴: ${s.monster_name}에게 공격!`);
    if (g.monsterHp > 0) {
      g.playerHp = Math.max(0, g.playerHp - toNumber(s.monster_power, 5));
      g.log.push(`${s.monster_name}의 반격!`);
    }
  }
  if (g.monsterHp <= 0) {
    g.log.push(`승리! ${s.reward_item}을 얻었어.`);
    updateSaveSeason("season_03", {
      wins: (getSeasonSave("season_03").wins || 0) + 1,
      best_turns: Math.min(getSeasonSave("season_03").best_turns || g.turn, g.turn),
    });
  }
  renderSeasonThree();
}

function comboAttack() {
  if (!state.gameStarted) return;
  attackMonster(Math.max(1, toNumber(state.settings.season_03.combo_count, 5)));
}

function showBag() {
  if (!state.gameStarted) return;
  const g = state.game.season_03;
  g.log.push(`가방: ${listFromText(state.settings.season_03.bag).join(", ")}`);
  renderSeasonThree();
}

function seasonFourReset() {
  state.game.season_04 = {
    score: getSeasonSave("season_04").high_score || 0,
    message: "버튼으로 미니 어드벤처를 시작해 보자.",
  };
}

function renderSeasonFour() {
  const s = state.settings.season_04;
  const g = state.game.season_04 || (seasonFourReset(), state.game.season_04);
  setHud(s.final_goal, `${s.hero_name} · 점수 ${g.score} · 승리 점수 ${s.win_score}`);
  els.action.textContent = "랜덤 보물";
  els.gameMount.innerHTML = `
    <div class="adventure-actions">
      <button data-adventure="jump" type="button">점프</button>
      <button data-adventure="hello" type="button">인사</button>
      <button data-adventure="attack" type="button">공격</button>
      <button data-adventure="save" type="button">점수 저장</button>
    </div>
    <div class="board">
      <div class="sprite hero" style="left:80px;top:160px"><span class="avatar-head"></span><span class="avatar-name">${s.hero_name}</span></div>
      <div class="sprite treasure wide-sprite" style="left:55%;top:120px">보물상자</div>
      <div class="sprite trap wide-sprite" style="left:72%;top:250px">보스</div>
      <div class="message-line" style="position:absolute;left:14px;right:14px;bottom:14px">${g.message}</div>
    </div>
  `;
  els.gameMount.querySelectorAll("[data-adventure]").forEach((button) => {
    button.addEventListener("click", () => runAdventure(button.dataset.adventure));
  });
}

function randomInt(min, max) {
  return Math.floor(Math.random() * (max - min + 1)) + min;
}

function runAdventure(action) {
  if (!state.gameStarted) return;
  const s = state.settings.season_04;
  const g = state.game.season_04;
  if (action === "jump") g.message = "점프!";
  if (action === "hello") g.message = `안녕, 나는 ${s.hero_name}이야!`;
  if (action === "attack") {
    const damage = randomInt(toNumber(s.dice_min, 1), toNumber(s.dice_max, 6));
    g.score += damage;
    g.message = `공격 성공! ${damage}점을 얻었어.`;
  }
  if (action === "save") {
    updateSaveSeason("season_04", {
      high_score: Math.max(getSeasonSave("season_04").high_score || 0, g.score),
      last_goal: s.final_goal,
    });
    g.message = "서버 저장 버튼을 누르면 점수가 저장돼.";
  }
  if (g.score >= toNumber(s.win_score, 100)) g.message = "승리! 보물을 모두 찾았어!";
  renderSeasonFour();
}

function randomTreasure() {
  if (!state.gameStarted) return;
  const s = state.settings.season_04;
  const g = state.game.season_04;
  const items = listFromText(s.treasure_items);
  const item = items[randomInt(0, Math.max(0, items.length - 1))] || "동전";
  g.score += 10;
  g.message = `${item}을 찾았어! 점수 +10`;
  updateSaveSeason("season_04", {
    high_score: Math.max(getSeasonSave("season_04").high_score || 0, g.score),
    last_goal: s.final_goal,
  });
  renderSeasonFour();
}

function renderActiveSeason(reset = false, refreshCode = false) {
  renderChapterTabs();
  renderFileTree();
  renderFields();
  renderLesson();
  if (refreshCode) renderCodeEditor();
  if (reset) state.game[state.activeSeason] = null;
  if (state.activeSeason === "season_01") {
    if (!state.game.season_01) seasonOneReset();
    renderSeasonOne();
  }
  if (state.activeSeason === "season_02") renderSeasonTwo();
  if (state.activeSeason === "season_03") {
    if (!state.game.season_03) seasonThreeReset();
    renderSeasonThree();
  }
  if (state.activeSeason === "season_04") {
    if (!state.game.season_04) seasonFourReset();
    renderSeasonFour();
  }
  setLockedControls();
}

async function loadSave() {
  const profile = "default";
  const response = await fetch(`/api/save?profile=${encodeURIComponent(profile)}`);
  if (!response.ok) throw new Error("저장 정보를 불러오지 못했습니다.");
  state.save = await response.json();
  for (const key of Object.keys(seasons)) {
    state.settings[key] = defaultSettings(key);
  }
  const seasonOne = getSeasonSave("season_01");
  if (seasonOne.hero_name) state.settings.season_01.hero_name = seasonOne.hero_name;
  const seasonTwo = getSeasonSave("season_02");
  if (seasonTwo.baby_name) state.settings.season_02.baby_name = seasonTwo.baby_name;
  const seasonFour = getSeasonSave("season_04");
  if (seasonFour.last_goal) state.settings.season_04.final_goal = seasonFour.last_goal;
  setStatus(`${profile} 저장 정보를 불러왔습니다.`);
  renderActiveSeason(true, true);
}

async function saveToServer() {
  readFields();
  const profile = "default";
  const payload = {
    profile,
    save: {
      seasons: state.save?.seasons || {},
    },
  };
  const response = await fetch("/api/save", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) throw new Error("서버 저장에 실패했습니다.");
  state.save = await response.json();
  setStatus(`${profile} 저장 완료: ${new Date().toLocaleTimeString("ko-KR")}`);
}

els.seasonSelect.addEventListener("change", () => {
  if (state.gameStarted) return;
  stopGameTimer();
  readFields();
  state.activeSeason = els.seasonSelect.value;
  state.activeChapter = 1;
  state.activeFile = "upgrade_zone.py";
  state.lessonPage = 0;
  state.gameStarted = false;
  renderActiveSeason(false, true);
});

els.chapterSelect.addEventListener("change", () => {
  if (state.gameStarted) return;
  stopGameTimer();
  readFields();
  state.activeChapter = Number(els.chapterSelect.value);
  state.lessonPage = 0;
  state.activeFile = "upgrade_zone.py";
  renderActiveSeason(true, true);
});

els.fileTree.addEventListener("click", (event) => {
  const button = event.target.closest("button[data-file]");
  if (!button || state.gameStarted) return;
  if (state.activeFile === "upgrade_zone.py") readFields();
  state.activeFile = button.dataset.file;
  renderActiveSeason(false, true);
});

els.filePanelToggle?.addEventListener("click", () => {
  setFilePanelCollapsed(!document.body.classList.contains("file-tree-collapsed"));
});

els.applyUpgrade.addEventListener("click", () => {
  if (state.gameStarted) return;
  if (state.activeFile !== "upgrade_zone.py") {
    setStatus("업그레이드는 upgrade_zone.py에서만 적용할 수 있습니다.");
    return;
  }
  readFields();
  state.gameStarted = false;
  renderActiveSeason(true, false);
  setStatus("업그레이드를 적용했습니다.");
});

els.start.addEventListener("click", () => {
  if (state.gameStarted) {
    state.gameStarted = false;
    state.startNotice = false;
    stopGameTimer();
    stopMusic();
    renderActiveSeason(false, false);
    setStatus("게임을 중지했습니다. 이제 코드와 강의자료를 조작할 수 있습니다.");
    return;
  }
  readFields();
  state.gameStarted = true;
  state.startNotice = state.activeSeason === "season_01";
  startMusic();
  renderActiveSeason(true, false);
  startGameTimer();
  setStatus("게임을 시작했습니다.");
  if (state.startNotice) {
    window.setTimeout(() => {
      state.startNotice = false;
      if (state.activeSeason === "season_01") renderSeasonOne();
    }, 1200);
  }
});

els.reset.addEventListener("click", () => {
  readFields();
  state.gameStarted = false;
  state.startNotice = false;
  stopGameTimer();
  stopMusic();
  renderActiveSeason(true, false);
});

els.action.addEventListener("click", () => {
  if (!state.gameStarted) {
    setStatus("게임 시작을 먼저 눌러 주세요.");
    return;
  }
  if (state.activeSeason === "season_01") collectSeasonOne();
  if (state.activeSeason === "season_02") seasonTwoAction();
  if (state.activeSeason === "season_03") attackMonster();
  if (state.activeSeason === "season_04") randomTreasure();
});

els.prevLesson.addEventListener("click", () => {
  if (state.gameStarted) return;
  state.lessonPage = Math.max(0, state.lessonPage - 1);
  renderLesson();
});

els.nextLesson.addEventListener("click", () => {
  if (state.gameStarted) return;
  const maxPage = currentLessonPages().length - 1;
  state.lessonPage = Math.min(maxPage, state.lessonPage + 1);
  renderLesson();
});

document.addEventListener("keydown", (event) => {
  if (!["season_01", "season_02"].includes(state.activeSeason)) return;
  if (event.target.closest("textarea, input")) return;
  const isSpace = event.key === " " || event.key === "Space" || event.code === "Space";
  if (["ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight"].includes(event.key) || isSpace) {
    event.preventDefault();
  }
  if (!state.gameStarted) return;
  if (state.activeSeason === "season_01") {
    if (event.key === "ArrowUp") moveHero(0, -1);
    if (event.key === "ArrowDown") moveHero(0, 1);
    if (event.key === "ArrowLeft") moveHero(-1, 0);
    if (event.key === "ArrowRight") moveHero(1, 0);
    if (isSpace) collectSeasonOne();
  }
  if (state.activeSeason === "season_02") {
    const seasonTwoGame = state.game.season_02;
    if (seasonTwoInputLocked(seasonTwoGame)) return;
    if (event.key === "ArrowLeft") moveSeasonTwoLane(-1);
    if (event.key === "ArrowRight") moveSeasonTwoLane(1);
    if (isSpace && seasonTwoGame?.phase === "boss") seasonTwoAction();
  }
});

initFilePanelState();

loadSave().catch(() => {
  state.save = { profile: "default", seasons: {} };
  for (const key of Object.keys(seasons)) state.settings[key] = defaultSettings(key);
  renderActiveSeason(true, true);
});
