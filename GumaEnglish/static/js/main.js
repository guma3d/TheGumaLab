import { fetchStage } from "/js/api.js?v=8";
import { speak, listenOnce, speechSupported } from "/js/voice.js?v=8";

const $ = (id) => document.getElementById(id);

const PHASES = [
  { id: 1, label: "1단계 · 보고 듣고 따라 말하기", showEn: "full",    playAudio: true  },
  { id: 2, label: "2단계 · 일부만 보고 듣고 말하기", showEn: "partial", playAudio: true  },
  { id: 3, label: "3단계 · 듣고 말하기",             showEn: "hidden",  playAudio: true  },
  { id: 4, label: "4단계 · 보지도 듣지도 않고 말하기", showEn: "hidden",  playAudio: false },
];

const INTRO_KO = "문장을 듣고 똑같이 따라해 주세요.";
const CORRECT_KO = ["정답이에요!", "잘 했어요!", "완벽해요!"];
const WRONG_KO = ["다시 해볼까요?", "한 번 더 들어볼게요.", "천천히 따라해 볼게요."];

const state = {
  stage: null,
  sentences: [],
  idx: 0,
  busy: false,
  cancelled: false,
  // Review mode
  reviewMode: false,
  reviewQueue: [],
  reviewIdx: 0,
};

/* ── Calendar (localStorage) ── */
const STORAGE_KEY = "gumaenglish_completed";

function getCompletedDates() {
  try { return JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]"); }
  catch { return []; }
}

function markTodayCompleted() {
  const today = new Date().toISOString().slice(0, 10);
  const dates = getCompletedDates();
  if (!dates.includes(today)) {
    dates.push(today);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(dates));
  }
}

let calYear, calMonth;

function openCalendar() {
  const now = new Date();
  calYear = now.getFullYear();
  calMonth = now.getMonth();
  renderCalendar();
  $("calendar-modal").hidden = false;
}

function closeCalendar() {
  $("calendar-modal").hidden = true;
}

function renderCalendar() {
  const months = ["1월","2월","3월","4월","5월","6월","7월","8월","9월","10월","11월","12월"];
  $("cal-title").textContent = `${calYear}년 ${months[calMonth]}`;

  const completed = getCompletedDates();
  const now = new Date();
  const todayStr = now.toISOString().slice(0, 10);

  const firstDay = new Date(calYear, calMonth, 1).getDay();
  const daysInMonth = new Date(calYear, calMonth + 1, 0).getDate();

  let html = "";
  // Empty cells before first day
  for (let i = 0; i < firstDay; i++) {
    html += `<div class="day-cell empty"></div>`;
  }

  for (let d = 1; d <= daysInMonth; d++) {
    const dateStr = `${calYear}-${String(calMonth + 1).padStart(2, "0")}-${String(d).padStart(2, "0")}`;
    const dow = new Date(calYear, calMonth, d).getDay();
    const cls = [];
    if (dow === 0) cls.push("sun");
    if (dow === 6) cls.push("sat");
    if (dateStr === todayStr) cls.push("today");
    if (completed.includes(dateStr)) cls.push("completed");
    if (new Date(calYear, calMonth, d) > now && dateStr !== todayStr) cls.push("future");

    html += `<div class="day-cell ${cls.join(" ")}">${d}</div>`;
  }

  $("cal-grid").innerHTML = html;

  // Stats
  const monthCompleted = completed.filter(d => d.startsWith(`${calYear}-${String(calMonth + 1).padStart(2, "0")}`)).length;
  $("cal-stats").innerHTML = `이번 달 학습 완료: <span>${monthCompleted}일</span>`;
}

/* ── Helpers ── */
function pick(arr) { return arr[Math.floor(Math.random() * arr.length)]; }

function shuffle(arr) {
  const a = [...arr];
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}

function normalize(text) {
  return (text || "")
    .toLowerCase()
    .replace(/[^\p{L}\p{N}\s']/gu, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function isMatch(a, b) {
  return normalize(a) === normalize(b);
}

function maskKeyword(sentence, keyword) {
  if (!keyword) return sentence;
  const re = new RegExp(
    keyword.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"),
    "i",
  );
  return sentence.replace(re, (m) => m.replace(/\S/g, "▁"));
}

function sleep(ms) { return new Promise((r) => setTimeout(r, ms)); }

function totalRounds() { return state.sentences.length * PHASES.length; }
function currentPhase() { return PHASES[state.idx % PHASES.length]; }
function currentSentence() { return state.sentences[Math.floor(state.idx / PHASES.length)]; }

/* ── Stage loading ── */
async function loadStage(num) {
  state.stage = await fetchStage(num);
  state.sentences = state.stage.pattern.sentences;
  $("stage-num").textContent = state.stage.stageNumber;
  $("robot-name").textContent = state.stage.robotName;
  $("pattern-en").textContent = state.stage.pattern.english;
  $("pattern-ko").textContent = state.stage.pattern.korean;
}

/* ── UI ── */
function showBanner(text) {
  const el = $("banner");
  el.textContent = text;
  el.hidden = false;
}

const WAVE_HTML = `<div class="wave-bars"><div class="bar"></div><div class="bar"></div><div class="bar"></div><div class="bar"></div><div class="bar"></div></div>`;
const MIC_HTML = `<div class="mic-pulse"><i class="fa-solid fa-microphone"></i></div>`;

function showStatus(text, kind, icon) {
  const area = $("feedback").parentElement;
  area.className = `status-area ${kind}`;
  $("feedback").textContent = text;
  $("status-icon").innerHTML = icon || "";
}

function clearStatus() {
  const area = $("feedback").parentElement;
  area.className = "status-area";
  $("feedback").textContent = "";
  $("status-icon").innerHTML = "";
}

/* ── Round rendering ── */
function renderRoundUI() {
  if (state.reviewMode) {
    renderReviewUI();
    return;
  }

  const phase = currentPhase();
  const sent = currentSentence();

  $("round-label").textContent = `${state.idx + 1} / ${totalRounds()}`;
  $("phase-label").textContent = phase.label;
  $("sentence-ko").textContent = sent.ko;

  const enEl = $("sentence-en");
  if (phase.showEn === "full") {
    enEl.textContent = sent.en;
    enEl.classList.remove("hidden-sentence", "masked-sentence");
  } else if (phase.showEn === "partial") {
    enEl.textContent = maskKeyword(sent.en, sent.keyword);
    enEl.classList.remove("hidden-sentence");
    enEl.classList.add("masked-sentence");
  } else {
    enEl.textContent = "▁ ▁ ▁ ▁ ▁";
    enEl.classList.add("hidden-sentence");
    enEl.classList.remove("masked-sentence");
  }

  $("replay-btn").hidden = !phase.playAudio;
  $("transcript").textContent = "\u00a0";
  clearStatus();
}

function renderReviewUI() {
  const sent = state.reviewQueue[state.reviewIdx];

  $("round-label").textContent = `복습 ${state.reviewIdx + 1} / ${state.reviewQueue.length}`;
  $("phase-label").textContent = "복습 · 기억나는 대로 말하기";
  $("sentence-ko").textContent = sent.ko;

  const enEl = $("sentence-en");
  enEl.textContent = "▁ ▁ ▁ ▁ ▁";
  enEl.classList.add("hidden-sentence");
  enEl.classList.remove("masked-sentence");

  $("replay-btn").hidden = true;
  $("transcript").textContent = "\u00a0";
  clearStatus();
}

/* ── Practice flow ── */
async function runCurrentRound() {
  if (state.cancelled) return;

  if (state.reviewMode) {
    await runReviewRound();
    return;
  }

  const phase = currentPhase();
  const sent = currentSentence();
  renderRoundUI();

  if (phase.playAudio) {
    showStatus("잘 들어보세요…", "listening", WAVE_HTML);
    await speak(sent.en);
    if (state.cancelled) return;
  } else {
    showStatus("안내를 듣고 있어요…", "listening", WAVE_HTML);
    await speak("이번에는 듣지 않고 말해보세요.", { lang: "ko-KR" });
    if (state.cancelled) return;
  }

  await autoListen(sent);
}

async function autoListen(sent) {
  if (state.cancelled) return;
  state.busy = true;
  showStatus("지금 따라 말해보세요!", "listening", MIC_HTML);

  try {
    const heard = await listenOnce({ lang: "en-US" });
    if (state.cancelled) return;
    await evaluateAnswer(heard, sent);
  } catch (err) {
    if (state.cancelled) return;
    showStatus("음성이 잘 들리지 않았어요. 다시 들어볼게요.", "miss", "");
    await sleep(1000);
    if (!state.cancelled) await runCurrentRound();
  } finally {
    state.busy = false;
  }
}

async function evaluateAnswer(heard, sent) {
  $("transcript").textContent = `"${heard}"`;

  if (isMatch(heard, sent.en)) {
    showStatus(`정답: "${sent.en}"`, "ok", "");
    await speak(pick(CORRECT_KO), { lang: "ko-KR" });
    if (state.cancelled) return;
    await sleep(500);
    advanceToNext();
  } else {
    showStatus(`정답은 "${sent.en}" 이에요`, "miss", "");
    await speak(pick(WRONG_KO), { lang: "ko-KR" });
    if (state.cancelled) return;
    await sleep(400);
    await runCurrentRound();
  }
}

function advanceToNext() {
  if (state.reviewMode) {
    state.reviewIdx += 1;
    if (state.reviewIdx >= state.reviewQueue.length) {
      finishStage();
    } else {
      runCurrentRound();
    }
    return;
  }

  state.idx += 1;
  if (state.idx >= totalRounds()) {
    startReview();
  } else {
    runCurrentRound();
  }
}

/* ── Review phase ── */
async function startReview() {
  state.reviewMode = true;
  state.reviewQueue = shuffle(state.sentences);
  state.reviewIdx = 0;

  renderReviewUI();
  showStatus("복습 시간이에요! 기억나는 대로 말해보세요.", "listening", WAVE_HTML);
  await speak("이제 복습 시간이에요. 기억나는 대로 말해보세요.", { lang: "ko-KR" });
  if (state.cancelled) return;
  await runReviewRound();
}

async function runReviewRound() {
  if (state.cancelled) return;
  const sent = state.reviewQueue[state.reviewIdx];
  renderReviewUI();

  showStatus("안내를 듣고 있어요…", "listening", WAVE_HTML);
  await speak("이번에는 듣지 않고 말해보세요.", { lang: "ko-KR" });
  if (state.cancelled) return;

  await autoListen(sent);
}

/* ── Finish ── */
function finishStage() {
  state.cancelled = true;
  state.reviewMode = false;
  $("practice").hidden = true;
  $("start-btn").hidden = false;
  markTodayCompleted();
  showBanner("오늘의 학습을 모두 마쳤어요!");
  speak("잘 했어요! 오늘 학습 끝!", { lang: "ko-KR" });
}

/* ── Start ── */
async function startPractice() {
  $("start-btn").hidden = true;
  $("banner").hidden = true;
  $("practice").hidden = false;
  state.idx = 0;
  state.cancelled = false;
  state.reviewMode = false;
  state.reviewQueue = [];
  state.reviewIdx = 0;
  renderRoundUI();
  showStatus("안내를 듣고 있어요…", "listening", WAVE_HTML);
  await speak(INTRO_KO, { lang: "ko-KR" });
  if (state.cancelled) return;
  await runCurrentRound();
}

/* ── Init ── */
async function main() {
  try {
    await loadStage(1);
  } catch (err) {
    $("pattern-en").textContent = "스테이지 로드 실패";
    $("pattern-ko").textContent = err.message;
    return;
  }

  if (!speechSupported) {
    showBanner("이 브라우저는 음성 인식을 지원하지 않아요. Safari로 gumaenglish.guma3d.com 을 직접 열어주세요.");
    $("start-btn").disabled = true;
  }

  $("start-btn").addEventListener("click", startPractice);
  $("replay-btn").addEventListener("click", () => speak(currentSentence().en));

  // Calendar
  $("calendar-btn").addEventListener("click", openCalendar);
  $("calendar-modal").addEventListener("click", (e) => {
    if (e.target === $("calendar-modal")) closeCalendar();
  });
  $("cal-prev").addEventListener("click", () => {
    calMonth--;
    if (calMonth < 0) { calMonth = 11; calYear--; }
    renderCalendar();
  });
  $("cal-next").addEventListener("click", () => {
    calMonth++;
    if (calMonth > 11) { calMonth = 0; calYear++; }
    renderCalendar();
  });
}

main();
