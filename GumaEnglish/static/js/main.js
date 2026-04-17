import { fetchStage } from "/js/api.js?v=7";
import { speak, listenOnce, speechSupported } from "/js/voice.js?v=7";

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
};

function pick(arr) { return arr[Math.floor(Math.random() * arr.length)]; }

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

function totalRounds() { return state.sentences.length * PHASES.length; }
function currentPhase() { return PHASES[state.idx % PHASES.length]; }
function currentSentence() { return state.sentences[Math.floor(state.idx / PHASES.length)]; }

async function loadStage(num) {
  state.stage = await fetchStage(num);
  state.sentences = state.stage.pattern.sentences;
  $("stage-num").textContent = state.stage.stageNumber;
  $("robot-name").textContent = state.stage.robotName;
  $("pattern-en").textContent = state.stage.pattern.english;
  $("pattern-ko").textContent = state.stage.pattern.korean;
}

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

function renderRoundUI() {
  const phase = currentPhase();
  const sent = currentSentence();

  $("round-label").textContent = `라운드 ${state.idx + 1} / ${totalRounds()}`;
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

async function runCurrentRound() {
  if (state.cancelled) return;
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

  await autoListen();
}

async function autoListen() {
  if (state.cancelled) return;
  state.busy = true;
  showStatus("지금 따라 말해보세요!", "listening", MIC_HTML);

  try {
    const heard = await listenOnce({ lang: "en-US" });
    if (state.cancelled) return;
    await evaluateAnswer(heard);
  } catch (err) {
    if (state.cancelled) return;
    // STT 실패 — 자동 재시도
    showStatus("음성이 잘 들리지 않았어요. 다시 들어볼게요.", "miss", "");
    await sleep(1000);
    if (!state.cancelled) await runCurrentRound();
  } finally {
    state.busy = false;
  }
}

async function evaluateAnswer(heard) {
  const sent = currentSentence();
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
    await runCurrentRound(); // auto-retry same round
  }
}

function sleep(ms) { return new Promise((r) => setTimeout(r, ms)); }

function advanceToNext() {
  state.idx += 1;
  if (state.idx >= totalRounds()) {
    finishStage();
  } else {
    runCurrentRound();
  }
}

function finishStage() {
  state.cancelled = true;
  $("practice").hidden = true;
  $("start-btn").hidden = false;
  showBanner("이 스테이지 학습을 모두 마쳤어요!");
  speak("잘 했어요! 오늘 학습 끝!", { lang: "ko-KR" });
}

async function startPractice() {
  $("start-btn").hidden = true;
  $("banner").hidden = true;
  $("practice").hidden = false;
  state.idx = 0;
  state.cancelled = false;
  renderRoundUI();
  showStatus("안내를 듣고 있어요…", "listening", WAVE_HTML);
  await speak(INTRO_KO, { lang: "ko-KR" });
  if (state.cancelled) return;
  await runCurrentRound();
}

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
}

main();
