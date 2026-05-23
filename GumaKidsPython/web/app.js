const seasons = {
  season_01: {
    title: "보물 점수 게임",
    chapters: "챕터 1~12",
    lesson: [
      ["오늘의 장면", "주인공이 보물과 함정을 찾아다니며 점수와 체력이 바뀝니다."],
      ["오늘의 코드", "이름, 대사, 점수 같은 값을 바꾸면 게임 화면도 바로 바뀝니다."],
      ["미션", "코드 내용을 바꾼 뒤 업그레이드 적용을 누르고 게임을 시작합니다."],
    ],
    fields: [
      ["start_message", "게임 시작 문장", "모험 시작!"],
      ["hero_message", "주인공 대사", "보물을 찾자!"],
      ["hero_name", "주인공 이름", "번개용사"],
      ["start_score", "시작 점수", 10],
      ["hp", "체력", 100],
      ["speed", "이동 속도", 5],
      ["treasure_point", "보물 점수", 10],
      ["trap_damage", "함정 데미지", 20],
      ["bonus_multiplier", "보너스 배율", 2],
    ],
  },
  season_02: {
    title: "던전 선택 게임",
    chapters: "챕터 13~24",
    lesson: [
      ["오늘의 장면", "던전 문, 비밀번호, 보스방 규칙을 골라 결과를 확인합니다."],
      ["오늘의 코드", "조건이 참인지 거짓인지에 따라 다른 문장이 나옵니다."],
      ["미션", "열쇠와 보석 값을 바꾸고 어떤 문이 열리는지 비교합니다."],
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
      ["오늘의 장면", "플레이어가 몬스터와 턴제로 싸우고 전투 로그를 확인합니다."],
      ["오늘의 코드", "반복 공격, 아이템 가방, 몬스터 능력치를 코드로 정합니다."],
      ["미션", "몬스터 체력과 공격력을 바꿔 전투 난이도를 조절합니다."],
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
      ["오늘의 장면", "점프, 인사, 공격, 보물상자 기능을 하나씩 실행합니다."],
      ["오늘의 코드", "함수, 랜덤, 저장 규칙이 작은 어드벤처 게임으로 연결됩니다."],
      ["미션", "승리 점수와 보물 목록을 바꿔 나만의 목표를 만듭니다."],
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

const state = {
  activeSeason: "season_01",
  settings: {},
  save: null,
  game: {},
};

const els = {
  profile: document.querySelector("#profileInput"),
  loadSave: document.querySelector("#loadSaveBtn"),
  save: document.querySelector("#saveBtn"),
  saveStatus: document.querySelector("#saveStatus"),
  tabs: document.querySelectorAll(".season-tabs button"),
  chapterLabel: document.querySelector("#chapterLabel"),
  seasonTitle: document.querySelector("#seasonTitle"),
  lessonBody: document.querySelector("#lessonBody"),
  upgradeFields: document.querySelector("#upgradeFields"),
  codePreview: document.querySelector("#codePreview"),
  applyUpgrade: document.querySelector("#applyUpgradeBtn"),
  start: document.querySelector("#startGameBtn"),
  hudTitle: document.querySelector("#hudTitle"),
  hudStats: document.querySelector("#hudStats"),
  gameMount: document.querySelector("#gameMount"),
  action: document.querySelector("#actionBtn"),
  reset: document.querySelector("#resetBtn"),
};

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
  const next = {};
  for (const input of els.upgradeFields.querySelectorAll("input")) {
    next[input.name] = input.value;
  }
  state.settings[state.activeSeason] = next;
}

function renderFields() {
  const season = seasons[state.activeSeason];
  const settings = state.settings[state.activeSeason] || defaultSettings(state.activeSeason);
  els.chapterLabel.textContent = season.chapters;
  els.seasonTitle.textContent = season.title;
  els.upgradeFields.innerHTML = "";

  for (const [key, label, value] of season.fields) {
    const wrap = document.createElement("div");
    wrap.className = "field";
    wrap.innerHTML = `
      <label for="${key}">${label}</label>
      <input id="${key}" name="${key}" value="${settings[key] ?? value}">
    `;
    els.upgradeFields.appendChild(wrap);
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
  els.hudStats.textContent = stats;
}

function renderLesson() {
  const lesson = seasons[state.activeSeason].lesson;
  els.lessonBody.innerHTML = lesson
    .map(([title, body]) => `
      <article class="lesson-note">
        <strong>${title}</strong>
        <p>${body}</p>
      </article>
    `)
    .join("");
}

function renderCodePreview() {
  const s = state.settings[state.activeSeason] || defaultSettings(state.activeSeason);
  if (state.activeSeason === "season_01") {
    els.codePreview.textContent = [
      "# 시즌 1: 보물 점수 게임 업그레이드 존",
      `start_message = "${s.start_message}"`,
      `hero_message = "${s.hero_message}"`,
      `hero_name = "${s.hero_name}"`,
      `start_score = ${toNumber(s.start_score, 10)}`,
      `hp = ${toNumber(s.hp, 100)}`,
      `speed = ${toNumber(s.speed, 5)}`,
      `treasure_point = ${toNumber(s.treasure_point, 10)}`,
      `trap_damage = ${toNumber(s.trap_damage, 20)}`,
      `bonus_multiplier = ${toNumber(s.bonus_multiplier, 2)}`,
    ].join("\n");
  }
  if (state.activeSeason === "season_02") {
    els.codePreview.textContent = [
      "# 시즌 2: 던전 선택 게임 업그레이드 존",
      `player_name = "${s.player_name}"`,
      `weapon = "${s.weapon}"`,
      `power = ${toNumber(s.power, 10)}`,
      `secret_password = "${s.secret_password}"`,
      `hp = ${toNumber(s.hp, 100)}`,
      `level = ${toNumber(s.level, 5)}`,
      `has_key = ${toBool(s.has_key) ? "True" : "False"}`,
      `has_gem = ${toBool(s.has_gem) ? "True" : "False"}`,
    ].join("\n");
  }
  if (state.activeSeason === "season_03") {
    els.codePreview.textContent = [
      "# 시즌 3: 몬스터 배틀 게임 업그레이드 존",
      `monster = {"name": "${s.monster_name}", "hp": ${toNumber(s.monster_hp, 30)}, "power": ${toNumber(s.monster_power, 5)}}`,
      `player_power = ${toNumber(s.player_power, 5)}`,
      `combo_count = ${toNumber(s.combo_count, 5)}`,
      `bag = [${listFromText(s.bag).map((item) => `"${item}"`).join(", ")}]`,
      `reward_item = "${s.reward_item}"`,
    ].join("\n");
  }
  if (state.activeSeason === "season_04") {
    els.codePreview.textContent = [
      "# 시즌 4: 미니 어드벤처 게임 업그레이드 존",
      `hero_name = "${s.hero_name}"`,
      `final_goal = "${s.final_goal}"`,
      `dice_min = ${toNumber(s.dice_min, 1)}`,
      `dice_max = ${toNumber(s.dice_max, 6)}`,
      `treasure_items = [${listFromText(s.treasure_items).map((item) => `"${item}"`).join(", ")}]`,
      `win_score = ${toNumber(s.win_score, 100)}`,
    ].join("\n");
  }
}

function seasonOneReset() {
  const s = state.settings.season_01;
  state.game.season_01 = {
    x: 70,
    y: 70,
    score: toNumber(s.start_score, 10),
    hp: toNumber(s.hp, 100),
    message: s.start_message || "모험 시작!",
    items: [
      { kind: "treasure", x: 260, y: 110, label: "보물", taken: false },
      { kind: "treasure", x: 520, y: 250, label: "동전", taken: false },
      { kind: "bonus", x: 650, y: 90, label: "보너스", taken: false },
      { kind: "trap", x: 390, y: 300, label: "함정", taken: false },
    ],
  };
}

function renderSeasonOne() {
  const s = state.settings.season_01;
  const g = state.game.season_01 || (seasonOneReset(), state.game.season_01);
  const title = `${s.hero_name || "번개용사"} 등장!`;
  setHud(title, `점수 ${g.score} · 체력 ${g.hp} · 속도 ${s.speed}`);
  els.action.textContent = "보물 줍기";
  els.gameMount.innerHTML = `<div class="board" tabindex="0" aria-label="보물 점수 게임판"></div>`;
  const board = els.gameMount.querySelector(".board");

  const hero = document.createElement("div");
  hero.className = "sprite hero";
  hero.innerHTML = `<span class="avatar-head"></span><span class="avatar-name">${s.hero_name || "용사"}</span>`;
  hero.style.left = `${g.x}px`;
  hero.style.top = `${g.y}px`;
  board.appendChild(hero);

  for (const item of g.items.filter((entry) => !entry.taken)) {
    const sprite = document.createElement("div");
    sprite.className = `sprite ${item.kind === "trap" ? "trap" : "treasure"}`;
    sprite.textContent = item.label;
    sprite.style.left = `${item.x}px`;
    sprite.style.top = `${item.y}px`;
    board.appendChild(sprite);
  }

  const msg = document.createElement("div");
  msg.className = "message-line";
  msg.style.position = "absolute";
  msg.style.left = "14px";
  msg.style.right = "14px";
  msg.style.bottom = "14px";
  msg.textContent = g.message || s.hero_message;
  board.appendChild(msg);
  board.focus();
}

function moveHero(dx, dy) {
  const s = state.settings.season_01;
  const g = state.game.season_01;
  const speed = Math.max(1, toNumber(s.speed, 5)) * 8;
  g.x = Math.max(0, Math.min(720, g.x + dx * speed));
  g.y = Math.max(0, Math.min(320, g.y + dy * speed));
  renderSeasonOne();
}

function collectSeasonOne() {
  const s = state.settings.season_01;
  const g = state.game.season_01;
  const near = g.items.find((item) => !item.taken && Math.abs(item.x - g.x) < 56 && Math.abs(item.y - g.y) < 56);
  if (!near) {
    g.message = s.hero_message || "보물을 찾자!";
    renderSeasonOne();
    return;
  }
  near.taken = true;
  if (near.kind === "trap") {
    g.hp = Math.max(0, g.hp - toNumber(s.trap_damage, 20));
    g.message = `함정! 체력이 ${toNumber(s.trap_damage, 20)} 줄었어.`;
  } else if (near.kind === "bonus") {
    g.score = g.score * toNumber(s.bonus_multiplier, 2);
    g.message = "보너스 보물! 점수가 크게 올랐어.";
  } else {
    g.score += toNumber(s.treasure_point, 10);
    g.message = "보물을 주웠어!";
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
  attackMonster(Math.max(1, toNumber(state.settings.season_03.combo_count, 5)));
}

function showBag() {
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

function renderActiveSeason(reset = false) {
  renderFields();
  renderLesson();
  renderCodePreview();
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
}

async function loadSave() {
  const profile = els.profile.value.trim() || "default";
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
  renderActiveSeason(true);
}

async function saveToServer() {
  readFields();
  const profile = els.profile.value.trim() || "default";
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

els.tabs.forEach((button) => {
  button.addEventListener("click", () => {
    readFields();
    state.activeSeason = button.dataset.season;
    els.tabs.forEach((tab) => tab.classList.toggle("active", tab === button));
    renderActiveSeason();
  });
});

els.applyUpgrade.addEventListener("click", () => {
  readFields();
  renderCodePreview();
  renderActiveSeason(true);
  setStatus("업그레이드를 적용했습니다.");
});

els.upgradeFields.addEventListener("input", () => {
  readFields();
  renderCodePreview();
});

els.start.addEventListener("click", () => {
  readFields();
  renderActiveSeason(true);
  setStatus("게임을 시작했습니다.");
});

els.reset.addEventListener("click", () => {
  renderActiveSeason(true);
});

els.action.addEventListener("click", () => {
  if (state.activeSeason === "season_01") collectSeasonOne();
  if (state.activeSeason === "season_02") runDungeonChoice("password");
  if (state.activeSeason === "season_03") attackMonster();
  if (state.activeSeason === "season_04") randomTreasure();
});

document.addEventListener("keydown", (event) => {
  if (state.activeSeason !== "season_01") return;
  if (event.key === "ArrowUp") moveHero(0, -1);
  if (event.key === "ArrowDown") moveHero(0, 1);
  if (event.key === "ArrowLeft") moveHero(-1, 0);
  if (event.key === "ArrowRight") moveHero(1, 0);
  if (event.key === " ") collectSeasonOne();
});

els.loadSave.addEventListener("click", () => {
  loadSave().catch((error) => setStatus(error.message));
});

els.save.addEventListener("click", () => {
  saveToServer().catch((error) => setStatus(error.message));
});

loadSave().catch(() => {
  state.save = { profile: "default", seasons: {} };
  for (const key of Object.keys(seasons)) state.settings[key] = defaultSettings(key);
  renderActiveSeason(true);
});
