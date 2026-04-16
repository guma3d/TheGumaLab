import { fetchStage } from "/js/api.js?v=4";
import { speak, listenOnce, speechSupported } from "/js/voice.js?v=4";

const $ = (id) => document.getElementById(id);

const PHASES = [
  { id: 1, label: "1단계 · 보고 듣고 따라 말하기", showEn: "full",    playAudio: true  },
  { id: 2, label: "2단계 · 일부만 보고 듣고 말하기", showEn: "partial", playAudio: true  },
  { id: 3, label: "3단계 · 듣고 말하기",             showEn: "hidden",  playAudio: true  },
  { id: 4, label: "4단계 · 보지도 듣지도 않고 말하기", showEn: "hidden",  playAudio: false },
];

const state = {
  stage: null,
  sentences: [],
  idx: 0,
  busy: false,
  useVoice: speechSupported,
};

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

function totalRounds() {
  return state.sentences.length * PHASES.length;
}

function currentPhase() {
  return PHASES[state.idx % PHASES.length];
}

function currentSentence() {
  return state.sentences[Math.floor(state.idx / PHASES.length)];
}

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

function renderRound() {
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
  $("transcript").hidden = true;
  $("transcript").textContent = "";
  $("feedback").hidden = true;
  $("feedback").textContent = "";
  $("feedback").className = "feedback";
  $("retry-btn").hidden = true;
  $("skip-btn").hidden = true;
  $("next-btn").hidden = true;

  if (state.useVoice) {
    $("speak-btn").hidden = false;
    $("speak-btn").disabled = false;
    $("text-input-row").hidden = true;
  } else {
    $("speak-btn").hidden = true;
    $("text-input-row").hidden = false;
    $("text-input").value = "";
    $("text-input").disabled = false;
    $("submit-text-btn").disabled = false;
  }

  if (phase.playAudio) {
    setTimeout(() => speak(sent.en), 250);
  }
}

function evaluateAnswer(heard) {
  const sent = currentSentence();
  $("transcript").hidden = false;
  $("transcript").textContent = `내가 말한 것: "${heard}"`;

  if (isMatch(heard, sent.en)) {
    showFeedback("정확해요! 잘 말했어요 🎉", "ok");
    $("speak-btn").hidden = true;
    $("text-input-row").hidden = true;
    $("next-btn").hidden = false;
  } else {
    showFeedback(`정답: "${sent.en}"`, "miss");
    $("retry-btn").hidden = false;
    $("skip-btn").hidden = false;
    $("speak-btn").hidden = true;
    $("text-input-row").hidden = true;
  }
}

async function handleSpeak() {
  if (state.busy) return;
  state.busy = true;
  $("speak-btn").disabled = true;
  $("speak-btn").textContent = "🎤 듣는 중…";
  $("feedback").hidden = true;

  try {
    const heard = await listenOnce({ lang: "en-US" });
    evaluateAnswer(heard);
  } catch (err) {
    // STT가 사용 불가한 상황이면 텍스트 입력으로 전환
    state.useVoice = false;
    showBanner("음성 인식을 사용할 수 없어요. 텍스트로 입력해주세요.");
    $("speak-btn").hidden = true;
    $("text-input-row").hidden = false;
    $("text-input").focus();
  } finally {
    state.busy = false;
    $("speak-btn").textContent = "🎤 말하기";
    $("speak-btn").disabled = false;
  }
}

function handleTextSubmit() {
  const val = $("text-input").value.trim();
  if (!val) return;
  evaluateAnswer(val);
}

function showFeedback(text, kind) {
  const el = $("feedback");
  el.hidden = false;
  el.textContent = text;
  el.className = `feedback ${kind}`;
}

function handleRetry() {
  $("feedback").hidden = true;
  $("transcript").hidden = true;
  $("retry-btn").hidden = true;
  $("skip-btn").hidden = true;
  if (state.useVoice) {
    $("speak-btn").hidden = false;
  } else {
    $("text-input-row").hidden = false;
    $("text-input").value = "";
    $("text-input").focus();
  }
  const phase = currentPhase();
  if (phase.playAudio) speak(currentSentence().en);
}

function handleNext() {
  state.idx += 1;
  if (state.idx >= totalRounds()) {
    finishStage();
  } else {
    renderRound();
  }
}

function finishStage() {
  $("speak-btn").hidden = true;
  $("text-input-row").hidden = true;
  $("next-btn").hidden = true;
  $("retry-btn").hidden = true;
  $("skip-btn").hidden = true;
  $("restart-btn").hidden = false;

  $("sentence-en").textContent = "";
  $("sentence-ko").textContent = "";
  showFeedback("이 스테이지 연습을 모두 마쳤어요! 🏆", "ok");
}

function startPractice() {
  $("start-btn").hidden = true;
  $("restart-btn").hidden = true;
  $("practice").hidden = false;
  state.idx = 0;
  renderRound();
}

function restart() {
  $("feedback").hidden = true;
  $("feedback").textContent = "";
  startPractice();
}

function debug(msg) {
  const el = document.getElementById("fatal-error");
  if (!el) return;
  el.style.background = "#7cf0ff";
  el.style.display = "block";
  const prev = el.textContent;
  el.textContent = (prev ? prev + "\n" : "") + "[debug] " + msg;
}

async function main() {
  debug("main.js v4 loaded; speechSupported=" + speechSupported);

  const required = ["start-btn","speak-btn","retry-btn","skip-btn","next-btn","restart-btn","replay-btn","submit-text-btn","text-input","practice","sentence-en","sentence-ko","feedback","transcript","round-label","phase-label","banner","pattern-en","pattern-ko","stage-num","robot-name"];
  const missing = required.filter((id) => !document.getElementById(id));
  if (missing.length) {
    debug("MISSING elements: " + missing.join(", "));
    return;
  }

  try {
    await loadStage(1);
    debug("stage loaded: " + state.stage.pattern.english);
  } catch (err) {
    debug("loadStage failed: " + err.message);
    $("pattern-en").textContent = "스테이지 로드 실패";
    $("pattern-ko").textContent = err.message;
    return;
  }

  if (!speechSupported) {
    showBanner("이 브라우저는 음성 인식을 지원하지 않아요. 텍스트로 입력해 연습할 수 있어요.");
  }

  $("start-btn").addEventListener("click", () => { debug("start clicked"); startPractice(); });
  $("speak-btn").addEventListener("click", handleSpeak);
  $("retry-btn").addEventListener("click", handleRetry);
  $("skip-btn").addEventListener("click", handleNext);
  $("next-btn").addEventListener("click", handleNext);
  $("restart-btn").addEventListener("click", restart);
  $("replay-btn").addEventListener("click", () => speak(currentSentence().en));
  $("submit-text-btn").addEventListener("click", handleTextSubmit);
  $("text-input").addEventListener("keydown", (e) => {
    if (e.key === "Enter") handleTextSubmit();
  });
  debug("listeners attached; ready");
}

main();
