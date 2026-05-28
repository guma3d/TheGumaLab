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
      ["speed", "이동 속도", 5],
      ["title", "등장 문장", "번개용사 등장!"],
      ["status_text", "상태창 문장", "번개용사 점수: 10"],
      ["treasure_point", "보물 점수", 10],
      ["trap_damage", "함정 데미지", 20],
      ["bonus_multiplier", "보너스 배율", 2],
    ],
  },
  season_02: {
    title: "던전 선택 게임",
    chapters: "챕터 13~24",
    lesson: [
      ["1. 오늘의 장면", "던전 문, 비밀번호, 보스방 규칙을 골라 결과를 확인합니다."],
      ["2. 오늘의 코드", "조건이 참인지 거짓인지에 따라 다른 문장이 나옵니다."],
      ["3. 코드가 하는 일", "True와 False는 게임 문이 열릴지 닫힐지 정합니다."],
      ["4. 바꿔보기", "has_key, has_gem, level 값을 바꾸고 결과를 비교합니다."],
      ["5. 미션", "열쇠와 보석이 모두 있을 때만 큰 보물상자를 열어 봅니다."],
    ],
    fields: [
      ["player_name", "플레이어 이름", "용감한 모험가"],
      ["weapon", "무기", "검"],
      ["power", "공격력", 10],
      ["secret_password", "비밀번호", "1234"],
      ["hp", "체력", 100],
      ["level", "레벨", 5],
      ["has_key", "열쇠", "true"],
      ["has_gem", "보석", "false"],
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
  4: { lines: 2, keys: ["start_score", "treasure_point"], labels: ["start_score", "treasure_point"] },
  5: { lines: 3, keys: ["start_score", "score", "treasure_point"], labels: ["start_score", "score", "treasure_point"] },
  6: { lines: 4, keys: ["start_score", "score", "hp", "treasure_point"], labels: ["start_score", "score", "hp", "treasure_point"] },
  7: { lines: 5, keys: ["start_score", "score", "hp", "speed", "treasure_point"], labels: ["start_score", "score", "hp", "speed", "treasure_point"] },
  8: { lines: 6, keys: ["hero_name", "hero_message", "start_score", "score", "speed", "title"], labels: ["hero_name", "hero_message", "start_score", "score", "speed", "title"] },
  9: { lines: 7, keys: ["hero_name", "hero_message", "start_score", "score", "hp", "speed", "status_text"], labels: ["hero_name", "hero_message", "start_score", "score", "hp", "speed", "status_text"] },
  10: { lines: 8, keys: ["hero_name", "start_score", "score", "hp", "speed", "title", "status_text", "treasure_point"], labels: ["hero_name", "start_score", "score", "hp", "speed", "title", "status_text", "treasure_point"] },
  11: { lines: 9, keys: ["hero_name", "start_score", "score", "hp", "speed", "title", "status_text", "treasure_point", "trap_damage"], labels: ["hero_name", "start_score", "score", "hp", "speed", "title", "status_text", "treasure_point", "trap_damage"] },
  12: { lines: 10, keys: ["hero_name", "start_score", "score", "hp", "speed", "title", "status_text", "treasure_point", "trap_damage", "bonus_multiplier"], labels: ["hero_name", "start_score", "score", "hp", "speed", "title", "status_text", "treasure_point", "trap_damage", "bonus_multiplier"] },
};

const seasonOneUnlocks = {
  1: "시작 깃발과 첫 장면이 생깁니다.",
  2: "주인공 말풍선이 캐릭터를 따라다닙니다.",
  3: "주인공 이름표가 생깁니다.",
  4: "보물상자가 생기고 점수가 상태창에 보입니다.",
  5: "보물과 동전을 주워 보상 점수 차이를 비교합니다.",
  6: "체력 하트와 체력 표시가 추가됩니다.",
  7: "바람 신발로 이동 속도와 질주 효과가 생깁니다.",
  8: "이름과 문장이 합쳐진 등장 아치가 열립니다.",
  9: "멋진 상태창이 게임 안에 붙습니다.",
  10: "큰 보물 상자와 연속 수집 콤보가 생깁니다.",
  11: "함정과 체력 피해가 들어와 긴장감이 생깁니다.",
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
    syntax: "int는 정수 자료형입니다. start_score는 처음 점수이고 treasure_point는 보물상자를 얻을 때 더해지는 보상 점수입니다. 계산에 쓰는 숫자는 따옴표 없이 적습니다.",
    pages: [
      ["1. 오늘의 장면", "보물상자를 주우면 상태창의 점수가 올라갑니다."],
      ["2. 오늘의 코드", "start_score는 처음 점수, treasure_point는 보상 점수입니다."],
      ["3. 기술 설명", "int는 정수 자료형입니다. 10, 0, 100처럼 소수점 없는 숫자를 뜻합니다."],
      ["4. 바꿔보기", "start_score와 treasure_point를 바꾸고 보물상자를 주워 점수 변화를 비교합니다."],
      ["5. 미션", "처음 점수와 첫 보상 점수가 잘 어울리는 조합을 정합니다."],
    ],
  },
  5: {
    title: "보상 점수 정하기",
    focus: "treasure_point",
    syntax: "= 는 오른쪽 값을 왼쪽 변수에 넣는 대입 연산자입니다. score는 현재 점수이고 treasure_point는 보물 보상입니다. 보물은 treasure_point만큼, 동전은 그 절반만큼 점수를 올립니다.",
    pages: [
      ["1. 오늘의 장면", "보물과 동전이 추가되어 서로 다른 점수를 줍니다."],
      ["2. 오늘의 코드", "score는 현재 점수, treasure_point는 보물을 주울 때 더할 점수입니다."],
      ["3. 기술 설명", "= 는 오른쪽 값을 왼쪽 변수에 넣는 대입 연산자입니다. 변수에 저장한 숫자가 게임 규칙이 됩니다."],
      ["4. 바꿔보기", "score와 treasure_point를 바꾸고 보물/동전을 주워 점수 차이를 봅니다."],
      ["5. 미션", "보물은 크게, 동전은 작게 느껴지는 보상 점수를 정합니다."],
    ],
  },
  6: {
    title: "체력 만들기",
    focus: "hp",
    syntax: "숫자 변수는 게임 규칙을 조절합니다. hp는 주인공 체력이고, 화면의 하트와 HUD 체력 숫자로 확인할 수 있습니다.",
    pages: [
      ["1. 오늘의 장면", "체력 하트와 체력 숫자가 추가됩니다."],
      ["2. 오늘의 코드", "hp = 100은 주인공 체력을 숫자로 저장합니다."],
      ["3. 기술 설명", "숫자 변수는 계산할 수 있습니다. 체력, 점수, 속도는 int로 다루기 좋습니다."],
      ["4. 바꿔보기", "hp를 50, 100, 999로 바꾸고 하트 표시와 체력 숫자를 비교합니다."],
      ["5. 미션", "주인공에게 어울리는 기본 체력을 정합니다."],
    ],
  },
  7: {
    title: "속도 만들기",
    focus: "speed",
    syntax: "변수 값이 바뀌면 그 변수를 쓰는 계산 결과도 바뀝니다. speed가 커지면 방향키 한 번에 움직이는 거리가 커집니다.",
    pages: [
      ["1. 오늘의 장면", "방향키를 누르면 주인공이 움직입니다."],
      ["2. 오늘의 코드", "speed 값이 클수록 한 번에 더 멀리 움직입니다."],
      ["3. 기술 설명", "변수 값을 바꾸면 그 변수를 사용하는 계산 결과도 바뀝니다."],
      ["4. 바꿔보기", "speed를 1, 5, 10으로 바꾸고 조작감을 비교합니다."],
      ["5. 미션", "너무 빠르지 않고 보물을 줍기 좋은 속도를 찾습니다."],
    ],
  },
  8: {
    title: "글자 합체",
    focus: "title",
    syntax: "str + str은 두 문자열을 이어 붙입니다. hero_name + \" 등장!\" 은 이름 뒤에 등장 문장을 붙여 새 문자열을 만듭니다.",
    pages: [
      ["1. 오늘의 장면", "주인공 이름이 들어간 등장 문장을 만듭니다."],
      ["2. 오늘의 코드", "title = hero_name + \" 등장!\" 는 문자열을 이어 붙입니다."],
      ["3. 기술 설명", "str + str은 두 문자열을 합칩니다. 숫자 더하기와는 결과가 다릅니다."],
      ["4. 바꿔보기", "\" 등장!\" 부분을 \" 출발!\" 같은 말로 바꿉니다."],
      ["5. 미션", "내 이름이 들어간 등장 문장을 만들어 봅니다."],
    ],
  },
  9: {
    title: "멋진 상태창",
    focus: "status_text",
    syntax: "f-string은 문자열 안에 변수 값을 넣는 방법입니다. 문자열 앞에 f를 붙이고, 중괄호 안에 hero_name이나 score 같은 변수 이름을 씁니다.",
    pages: [
      ["1. 오늘의 장면", "상태창에 이름과 점수를 함께 보여줍니다."],
      ["2. 오늘의 코드", "f\"{hero_name} 점수: {score}\" 는 변수 값을 문장 안에 넣습니다."],
      ["3. 기술 설명", "f-string은 문자열 앞에 f를 붙이고 중괄호 안의 변수 값을 글자로 바꿔 넣습니다."],
      ["4. 바꿔보기", "상태창 문장의 순서를 바꿔 봅니다."],
      ["5. 미션", "이름, 점수, 체력이 함께 보이는 문장을 상상해 봅니다."],
    ],
  },
  10: {
    title: "더하기 마법",
    focus: "treasure_point",
    syntax: "+ 는 숫자를 더하는 연산자입니다. treasure_point가 커질수록 보물을 주울 때 현재 점수에 더해지는 값도 커집니다.",
    pages: [
      ["1. 오늘의 장면", "보물을 주우면 점수가 올라갑니다."],
      ["2. 오늘의 코드", "current_score + treasure_point가 새 점수를 만듭니다."],
      ["3. 기술 설명", "+ 는 숫자에서는 덧셈 연산자입니다. int + int 결과도 int입니다."],
      ["4. 바꿔보기", "treasure_point를 10, 30, 50으로 바꿔 점수 증가량을 비교합니다."],
      ["5. 미션", "보물 하나가 몇 점이면 게임이 재미있는지 정합니다."],
    ],
  },
  11: {
    title: "빼기 마법",
    focus: "trap_damage",
    syntax: "- 는 숫자를 빼는 연산자입니다. trap_damage가 커지면 함정에 닿았을 때 hp에서 빠지는 숫자가 커집니다.",
    pages: [
      ["1. 오늘의 장면", "함정에 닿으면 체력이 줄어듭니다."],
      ["2. 오늘의 코드", "current_hp - trap_damage가 새 체력을 만듭니다."],
      ["3. 기술 설명", "- 는 숫자에서 뺄셈 연산자입니다. 피해량을 계산할 때 자주 씁니다."],
      ["4. 바꿔보기", "trap_damage를 5, 20, 50으로 바꿔 함정 위험도를 비교합니다."],
      ["5. 미션", "실수 한 번에 게임이 끝나지 않는 피해량을 정합니다."],
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

const projectFiles = [
  { name: "upgrade_zone.py", role: "오늘 바꾸는 웹 업그레이드 코드", editable: true },
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

const els = {
  seasonSelect: document.querySelector("#seasonSelect"),
  chapterSelect: document.querySelector("#chapterSelect"),
  saveStatus: document.querySelector("#saveStatus"),
  fileTree: document.querySelector("#fileTree"),
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

function readFields() {
  state.settings[state.activeSeason] = parseCode(state.activeSeason, els.codeEditor.value);
}

function renderFields() {
  const season = seasons[state.activeSeason];
  const settings = state.settings[state.activeSeason] || defaultSettings(state.activeSeason);
  const chapterInfo = state.activeSeason === "season_01" ? seasonOneChapters[state.activeChapter] : null;
  const editPlan = state.activeSeason === "season_01" ? seasonOneEditPlans[state.activeChapter] : null;
  els.chapterLabel.textContent = chapterInfo ? `챕터 ${state.activeChapter} / 12 · ${editPlan.lines}줄 수정` : season.chapters;
  els.seasonTitle.textContent = chapterInfo ? chapterInfo.title : season.title;
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
    node.className = part.startsWith("점수 ") ? "hud-score" : "";
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

function fileContent(fileName) {
  if (fileName === "upgrade_zone.py") return generateCode(state.activeSeason);
  return [
    "# GumaKidsPython",
    "",
    "웹버전에서 upgrade_zone.py를 바꾸고 바로 게임 화면에서 확인합니다.",
  ].join("\n");
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
      : `챕터 ${chapter}`;
    option.value = String(localChapter);
    option.textContent = `${chapter}. ${title}`;
    option.selected = localChapter === state.activeChapter;
    els.chapterSelect.appendChild(option);
  }
}

function setLockedControls() {
  els.start.textContent = state.gameStarted ? "게임 중지" : "게임 시작";
  els.start.classList.toggle("stop", state.gameStarted);
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
    const heroName = s.hero_name || "번개용사";
    const title = s.title || `${heroName} 등장!`;
    const statusText = s.status_text || `${heroName} 점수: ${score}`;
    const scoreLine = score === startScore ? "score = start_score" : `score = ${score}`;
    const titleLine = title === `${heroName} 등장!` ? 'title = hero_name + " 등장!"' : `title = "${title}"`;
    const statusLine = statusText === `${heroName} 점수: ${score}` ? 'status_text = f"{hero_name} 점수: {score}"' : `status_text = "${statusText}"`;
    return [
      "# 시즌 1: 보물 점수 게임 업그레이드 존",
      "# 전체 코드를 볼 수 있습니다. 오늘 배울 곳은 [오늘의 업그레이드] 아래입니다.",
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
      targetHint("treasure_point"),
      `treasure_point = ${toNumber(s.treasure_point, 10)}`,
      "",
      "# =========================",
      "# [챕터 5] 보상 점수",
      today(5),
      "# =========================",
      targetHint("score"),
      scoreLine,
      "",
      "# =========================",
      "# [챕터 6] 체력",
      today(6),
      "# =========================",
      targetHint("hp"),
      `hp = ${toNumber(s.hp, 100)}`,
      "",
      "# =========================",
      "# [챕터 7] 이동 속도",
      today(7),
      "# =========================",
      targetHint("speed"),
      `speed = ${toNumber(s.speed, 5)}`,
      "",
      "# =========================",
      "# [챕터 8] 글자 합체",
      today(8),
      "# =========================",
      targetHint("title"),
      titleLine,
      "",
      "# =========================",
      "# [챕터 9] 멋진 상태창",
      today(9),
      "# =========================",
      targetHint("status_text"),
      statusLine,
      "",
      "# =========================",
      "# [챕터 10] 더하기 마법",
      today(10),
      "# =========================",
      "def upgrade_score_when_get_treasure(current_score):",
      "    new_score = current_score + treasure_point",
      "    return new_score",
      "",
      "# =========================",
      "# [챕터 11] 빼기 마법",
      today(11),
      "# =========================",
      targetHint("trap_damage"),
      `trap_damage = ${toNumber(s.trap_damage, 20)}`,
      "",
      "def upgrade_hp_when_hit_trap(current_hp):",
      "    new_hp = current_hp - trap_damage",
      "    return new_hp",
      "",
      "# =========================",
      "# [챕터 12] 보너스 점수",
      today(12),
      "# =========================",
      targetHint("bonus_multiplier"),
      `bonus_multiplier = ${toNumber(s.bonus_multiplier, 2)}`,
      "",
      "def upgrade_score_when_get_bonus(current_score):",
      "    new_score = current_score * bonus_multiplier",
      "    return new_score",
    ].filter((line) => line !== null).join("\n");
  }
  if (seasonKey === "season_02") {
    return [
      "# 시즌 2: 던전 선택 게임 업그레이드 존",
      "# 전체 코드를 볼 수 있습니다. 오늘 배울 곳은 [오늘의 업그레이드] 아래입니다.",
      "",
      "# =========================",
      "# [챕터 13] 내 이름으로 시작",
      "# [오늘의 업그레이드]",
      "# =========================",
      `player_name = "${s.player_name}"`,
      "",
      "# =========================",
      "# [챕터 14] 무기 이름 정하기",
      "# =========================",
      `weapon = "${s.weapon}"`,
      "",
      "# =========================",
      "# [챕터 15] 공격력 입력",
      "# =========================",
      `power = ${toNumber(s.power, 10)}`,
      "",
      "# =========================",
      "# [챕터 16] 첫 번째 선택",
      "# =========================",
      `secret_password = "${s.secret_password}"`,
      "",
      "# =========================",
      "# [챕터 20] 크다 작다",
      "# =========================",
      `hp = ${toNumber(s.hp, 100)}`,
      "",
      "# =========================",
      "# [챕터 21] 크거나 같다",
      "# =========================",
      `level = ${toNumber(s.level, 5)}`,
      "",
      "# =========================",
      "# [챕터 22] 조건 두 개",
      "# =========================",
      `has_key = ${toBool(s.has_key) ? "True" : "False"}`,
      "",
      `has_gem = ${toBool(s.has_gem) ? "True" : "False"}`,
      "",
      "def can_open_key_door():",
      "    return has_key",
      "",
      "def is_password_correct(password):",
      "    return password == secret_password",
      "",
      "def can_enter_boss_room(current_level):",
      "    return current_level >= level",
      "",
      "def can_open_double_lock():",
      "    return has_key and has_gem",
    ].join("\n");
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
  const stringValue = (name) => {
    const match = source.match(new RegExp(`^\\s*${name}\\s*=\\s*["']([^"']*)["']`, "m"));
    return match ? match[1] : base[name];
  };
  const numberValue = (name) => {
    const match = source.match(new RegExp(`^\\s*${name}\\s*=\\s*(-?\\d+(?:\\.\\d+)?)`, "m"));
    return match ? Number(match[1]) : base[name];
  };
  const seasonOneScoreValue = (startScore) => {
    const numberMatch = source.match(/^\s*score\s*=\s*(-?\d+(?:\.\d+)?)/m);
    if (numberMatch) return Number(numberMatch[1]);
    const startScoreMatch = source.match(/^\s*score\s*=\s*start_score\s*$/m);
    if (startScoreMatch) return startScore;
    return base.score ?? startScore;
  };
  const seasonOneTitleValue = (heroName) => {
    const literalMatch = source.match(/^\s*title\s*=\s*["']([^"']*)["']/m);
    if (literalMatch) return literalMatch[1];
    const concatMatch = source.match(/^\s*title\s*=\s*hero_name\s*\+\s*["']([^"']*)["']/m);
    if (concatMatch) return `${heroName}${concatMatch[1]}`;
    return base.title ?? `${heroName} 등장!`;
  };
  const seasonOneStatusValue = (heroName, score, hp) => {
    const literalMatch = source.match(/^\s*status_text\s*=\s*["']([^"']*)["']/m);
    if (literalMatch) return literalMatch[1];
    const fStringMatch = source.match(/^\s*status_text\s*=\s*f["']([^"']*)["']/m);
    if (fStringMatch) {
      return fStringMatch[1]
        .replaceAll("{hero_name}", heroName)
        .replaceAll("{score}", String(score))
        .replaceAll("{hp}", String(hp));
    }
    return base.status_text ?? `${heroName} 점수: ${score}`;
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
    const hp = numberValue("hp");
    return {
      start_message: stringValue("start_message"),
      hero_message: stringValue("hero_message"),
      hero_name: heroName,
      start_score: startScore,
      score,
      hp,
      speed: numberValue("speed"),
      title: seasonOneTitleValue(heroName),
      status_text: seasonOneStatusValue(heroName, score, hp),
      treasure_point: numberValue("treasure_point"),
      trap_damage: numberValue("trap_damage"),
      bonus_multiplier: numberValue("bonus_multiplier"),
    };
  }
  if (seasonKey === "season_02") {
    return {
      player_name: stringValue("player_name"),
      weapon: stringValue("weapon"),
      power: numberValue("power"),
      secret_password: stringValue("secret_password"),
      hp: numberValue("hp"),
      level: numberValue("level"),
      has_key: boolValue("has_key"),
      has_gem: boolValue("has_gem"),
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

function seasonOneItemsForChapter(chapter) {
  const items = [];
  if (chapter >= 4) items.push({ kind: "starter_chest", x: 24, y: 40, label: "보물상자", taken: false });
  if (chapter >= 5) {
    items.push({ kind: "treasure", x: 60, y: 28, label: "보물", taken: false });
    items.push({ kind: "coin", x: 72, y: 60, label: "동전", taken: false });
  }
  if (chapter >= 6) items.push({ kind: "heart", x: 18, y: 70, label: "하트", taken: false });
  if (chapter >= 7) items.push({ kind: "boost", x: 40, y: 78, label: "바람신발", taken: false });
  if (chapter >= 10) {
    items.push({ kind: "gem", x: 44, y: 52, label: "루비", taken: false });
    items.push({ kind: "chest", x: 84, y: 38, label: "상자", taken: false });
  }
  if (chapter >= 11) {
    items.push({ kind: "trap", baseX: 50, baseY: 66, x: 50, y: 66, label: "가시함정", patrol: "horizontal", taken: false });
    items.push({ kind: "trap", baseX: 68, baseY: 46, x: 68, y: 46, label: "불꽃함정", patrol: "vertical", taken: false });
  }
  if (chapter >= 12) {
    items.push({ kind: "bonus", x: 84, y: 20, label: "보너스별", taken: false });
    items.push({ kind: "portal", x: 88, y: 76, label: "포털", taken: false });
  }
  return items;
}

function seasonOneItemPoint(kind, settings) {
  const treasurePoint = toNumber(settings.treasure_point, 10);
  if (kind === "starter_chest") return treasurePoint;
  if (kind === "coin") return Math.max(1, Math.round(treasurePoint / 2));
  if (kind === "gem") return treasurePoint * 2;
  if (kind === "chest") return treasurePoint * 3;
  if (kind === "treasure") return treasurePoint;
  return 0;
}

function seasonOneRequiredItems(game) {
  return game.items.filter((item) => ["starter_chest", "treasure", "coin", "gem", "chest", "bonus"].includes(item.kind));
}

function seasonOneReadyForPortal(game) {
  return seasonOneRequiredItems(game).every((item) => item.taken);
}

function seasonOneReset() {
  const s = state.settings.season_01;
  const chapter = seasonOneChapter();
  state.game.season_01 = {
    x: 10,
    y: 18,
    direction: "down",
    step: 0,
    score: toNumber(s.score, toNumber(s.start_score, 10)),
    hp: toNumber(s.hp, 100),
    maxHp: Math.max(1, toNumber(s.hp, 100)),
    boostMoves: 0,
    combo: 0,
    win: false,
    gameOver: false,
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
      heart: 0,
      boost: 0,
      bonus: 0,
      trap: 0,
    },
    items: seasonOneItemsForChapter(chapter),
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
  if (chapter >= 9) pieces.push(settings.status_text || `${settings.hero_name || "번개용사"} 점수: ${game.score}`);
  if (chapter >= 4) pieces.push(`점수 ${game.score}`);
  if (chapter >= 6) pieces.push(`체력 ${game.hp}/${game.maxHp}`);
  if (chapter >= 7) pieces.push(`속도 ${settings.speed}${game.boostMoves ? " · 질주" : ""}`);
  if (chapter >= 10) pieces.push(`콤보 ${game.combo}`);
  if (chapter >= 12 && game.win) pieces.push("포털 개방!");
  if (!pieces.length) pieces.push("시작 장면 제작 중");
  return pieces.join(" · ");
}

function renderSeasonOneScenery(board, settings, game, chapter) {
  if (chapter >= 5) seasonOneProp(board, "coin-road");
  if (chapter >= 6) {
    const hearts = Math.max(1, Math.min(5, Math.ceil(game.hp / Math.max(1, game.maxHp) * 5)));
    addSeasonOneScenery(board, "heart-meter", `${"♥".repeat(hearts)}${"♡".repeat(5 - hearts)}`);
  }
  if (chapter >= 7) seasonOneProp(board, "wind-ring");
  if (chapter >= 8) addSeasonOneScenery(board, "title-arch", settings.title || `${settings.hero_name || "번개용사"} 등장!`);
  if (chapter >= 9) addSeasonOneScenery(board, "status-plaque", settings.status_text || `${settings.hero_name || "번개용사"} 점수: ${game.score}`);
  if (chapter >= 10) addSeasonOneScenery(board, "combo-plaque", `콤보 ${game.combo} · 보물 ${game.collected.treasure + game.collected.gem + game.collected.chest}`);
  if (chapter >= 10) seasonOneProp(board, "treasure-gate");
  if (chapter >= 11) addSeasonOneScenery(board, "danger-lane", "");
  if (chapter >= 12) {
    seasonOneProp(board, "crystal-left");
    seasonOneProp(board, "crystal-right");
    seasonOneProp(board, "portal-aura");
  }
  if (chapter >= 12) addSeasonOneScenery(board, "portal-hint", game.win ? "클리어!" : "보물을 모아 포털을 열자");
}

function updateSeasonOneMovingTraps() {
  if (!state.gameStarted || state.activeSeason !== "season_01") return;
  const g = state.game.season_01;
  if (!g || g.win || g.gameOver || !seasonOneHas(11)) return;
  g.phase = (g.phase || 0) + 0.22;
  for (const item of g.items) {
    if (item.kind !== "trap" || item.taken) continue;
    if (item.patrol === "horizontal") item.x = (item.baseX ?? item.x) + Math.sin(g.phase) * 11;
    if (item.patrol === "vertical") item.y = (item.baseY ?? item.y) + Math.cos(g.phase * 1.25) * 10;
  }
  const trap = findCollectableItem(g, ["trap"]);
  if (trap) triggerSeasonOneTrap(trap, state.settings.season_01, g);
  renderSeasonOne();
}

function startGameTimer() {
  if (state.gameTimer) window.clearInterval(state.gameTimer);
  state.gameTimer = null;
  if (state.activeSeason !== "season_01" || !state.gameStarted || !seasonOneHas(11)) return;
  state.gameTimer = window.setInterval(updateSeasonOneMovingTraps, 140);
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
    ? (s.title || `${s.hero_name || "번개용사"} 등장!`)
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
    ${chapter >= 7 ? "<span class=\"speed-trail\"></span>" : ""}
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
    const category = item.kind === "trap" ? "trap" : "treasure";
    sprite.className = `sprite voxel-item ${category} item-${item.kind}`;
    sprite.innerHTML = `<span class="item-icon"></span><span>${item.label}</span>`;
    Object.assign(sprite.style, percentStyle(item.x, item.y));
    board.appendChild(sprite);
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
  const boost = g.boostMoves > 0 ? 1.85 : 1;
  const speed = Math.max(1, toNumber(s.speed, 5)) * 1.25 * boost;
  if (dx < 0) g.direction = "left";
  if (dx > 0) g.direction = "right";
  if (dy < 0) g.direction = "up";
  if (dy > 0) g.direction = "down";
  g.step += 1;
  if (g.boostMoves > 0) g.boostMoves -= 1;
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
  const damage = toNumber(settings.trap_damage, 20);
  game.hp = Math.max(0, game.hp - damage);
  game.message = `${item.label}! 체력이 ${damage} 줄었어.`;
  playPickupSound("trap");
  if (game.hp <= 0) {
    game.gameOver = true;
    game.message = "체력이 0이 되었어. 다시 시작해서 도전!";
  }
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
  g.collected ||= { score: 0, starter_chest: 0, treasure: 0, coin: 0, gem: 0, chest: 0, heart: 0, boost: 0, bonus: 0, trap: 0 };
  if (near.kind === "trap") {
    triggerSeasonOneTrap(near, s, g);
    renderSeasonOne();
    return;
  }
  if (near.kind === "portal") {
    if (seasonOneReadyForPortal(g)) {
      near.taken = true;
      g.win = true;
      g.message = `완성! ${s.hero_name || "용사"}가 보물 포털을 열었어!`;
      playTone({ frequency: 880, duration: 0.16, type: "triangle", volume: 0.06, slide: 240 });
      updateSaveSeason("season_01", {
        high_score: Math.max(getSeasonSave("season_01").high_score || 0, g.score),
        best_hp: Math.max(getSeasonSave("season_01").best_hp || 0, g.hp),
        hero_name: s.hero_name,
      });
    } else {
      g.message = "포털이 아직 잠겨 있어. 보물과 보너스를 먼저 모으자!";
    }
    renderSeasonOne();
    return;
  }
  near.taken = true;
  playPickupSound(near.kind);
  if (near.kind === "heart") {
    g.collected.heart += 1;
    const heal = 25;
    g.hp = Math.min(g.maxHp, g.hp + heal);
    g.message = `하트를 얻었어. 체력 +${heal}!`;
  } else if (near.kind === "boost") {
    g.collected.boost += 1;
    g.boostMoves = 8;
    g.message = "바람신발 장착! 잠깐 동안 더 빠르게 움직여.";
  } else if (near.kind === "bonus") {
    g.collected.bonus += 1;
    g.combo += 1;
    g.score = g.score * toNumber(s.bonus_multiplier, 2);
    g.message = `보너스별! 점수가 ${toNumber(s.bonus_multiplier, 2)}배가 되었어.`;
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

function renderSeasonTwo() {
  const s = state.settings.season_02;
  setHud("던전 선택 게임", `${s.player_name} · ${s.weapon} · 체력 ${s.hp} · 레벨 ${s.level}`);
  els.action.textContent = "비밀번호 확인";
  els.gameMount.innerHTML = `
    <div class="message-log">
      <div class="dungeon-scene">
        <div class="character-card">
          <div class="character-avatar">${s.player_name.slice(0, 2)}</div>
          <strong>${s.player_name}</strong>
          <span>${s.weapon} 장착</span>
        </div>
        <div class="door-card">던전 문</div>
      </div>
      <div class="message-line">${s.player_name} 님이 ${s.weapon}을 들고 던전에 들어왔어.</div>
      <div class="choice-grid">
        <button data-choice="key" type="button">열쇠 문</button>
        <button data-choice="password" type="button">비밀번호 문</button>
        <button data-choice="level" type="button">보스방</button>
        <button data-choice="treasure" type="button">보물상자</button>
      </div>
      <input id="passwordInput" placeholder="비밀번호를 입력해 봐" value="${s.secret_password}">
      <div id="dungeonResult" class="choice-card">${getSeasonSave("season_02").last_result || "문을 골라 보자."}</div>
    </div>
  `;
  els.gameMount.querySelectorAll("[data-choice]").forEach((button) => {
    button.addEventListener("click", () => runDungeonChoice(button.dataset.choice));
  });
}

function runDungeonChoice(choice) {
  if (!state.gameStarted) return;
  const s = state.settings.season_02;
  const password = els.gameMount.querySelector("#passwordInput")?.value || "";
  let result = "";
  if (choice === "key") result = toBool(s.has_key) ? "열쇠가 있어서 문이 열렸어!" : "열쇠가 없어서 문이 잠겼어.";
  if (choice === "password") result = password === s.secret_password ? "비밀번호 성공!" : "비밀번호가 달라.";
  if (choice === "level") result = toNumber(s.level, 1) >= 5 ? "보스방에 들어갈 수 있어." : "레벨 5가 필요해.";
  if (choice === "treasure") result = toBool(s.has_key) && toBool(s.has_gem) ? "큰 보물상자를 열었어!" : "열쇠와 보석이 둘 다 필요해.";
  els.gameMount.querySelector("#dungeonResult").textContent = result;
  updateSaveSeason("season_02", {
    opened_doors: (getSeasonSave("season_02").opened_doors || 0) + (result.includes("열") || result.includes("성공") ? 1 : 0),
    last_result: result,
  });
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
  if (state.activeSeason === "season_02") runDungeonChoice("password");
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
  if (state.activeSeason !== "season_01") return;
  if (event.target.closest("textarea, input")) return;
  const isSpace = event.key === " " || event.key === "Space" || event.code === "Space";
  if (["ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight"].includes(event.key) || isSpace) {
    event.preventDefault();
  }
  if (!state.gameStarted) return;
  if (event.key === "ArrowUp") moveHero(0, -1);
  if (event.key === "ArrowDown") moveHero(0, 1);
  if (event.key === "ArrowLeft") moveHero(-1, 0);
  if (event.key === "ArrowRight") moveHero(1, 0);
  if (isSpace) collectSeasonOne();
});

loadSave().catch(() => {
  state.save = { profile: "default", seasons: {} };
  for (const key of Object.keys(seasons)) state.settings[key] = defaultSettings(key);
  renderActiveSeason(true, true);
});
