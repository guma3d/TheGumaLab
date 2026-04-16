import { fetchStage } from "/js/api.js";
import { speak, listenOnce, speechSupported } from "/js/voice.js";

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
  $("speak-btn").hidden = false;
  $("speak-btn").disabled = false;
  $("retry-btn").hidden = true;
  $("skip-btn").hidden = true;
  $("next-btn").hidden = true;

  if (phase.playAudio) {
    setTimeout(() => speak(sent.en), 250);
  }
}

async function handleSpeak() {
  if (state.busy) return;
  const sent = currentSentence();
  state.busy = true;
  $("speak-btn").disabled = true;
  $("speak-btn").textContent = "🎤 듣는 중…";
  $("feedback").hidden = true;

  try {
    const heard = await listenOnce({ lang: "en-US" });
    $("transcript").hidden = false;
    $("transcript").textContent = `내가 말한 것: "${heard}"`;

    if (isMatch(heard, sent.en)) {
      showFeedback("정확해요! 잘 말했어요 🎉", "ok");
      $("speak-btn").hidden = true;
      $("next-btn").hidden = false;
    } else {
      showFeedback(`정답: "${sent.en}"`, "miss");
      $("retry-btn").hidden = false;
      $("skip-btn").hidden = false;
      $("speak-btn").hidden = true;
    }
  } catch (err) {
    showFeedback(`음성 인식 실패: ${err.message}`, "miss");
    $("retry-btn").hidden = false;
    $("skip-btn").hidden = false;
    $("speak-btn").hidden = true;
  } finally {
    state.busy = false;
    $("speak-btn").textContent = "🎤 말하기";
    $("speak-btn").disabled = false;
  }
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
  $("speak-btn").hidden = false;
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
  $("practice").hidden = true;
  $("speak-btn").hidden = true;
  $("next-btn").hidden = true;
  $("retry-btn").hidden = true;
  $("skip-btn").hidden = true;
  $("restart-btn").hidden = false;

  const card = $("sentence-en");
  card.textContent = "";
  showFeedback("이 스테이지 연습을 모두 마쳤어요! 🏆", "ok");
  $("feedback").hidden = false;
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

async function main() {
  try {
    await loadStage(1);
  } catch (err) {
    $("pattern-en").textContent = "스테이지 로드 실패";
    $("pattern-ko").textContent = err.message;
    return;
  }

  if (!speechSupported) {
    showFeedback("이 브라우저는 음성 인식을 지원하지 않아요. Chrome/Safari를 이용해주세요.", "miss");
    $("feedback").hidden = false;
    $("start-btn").disabled = true;
  }

  $("start-btn").addEventListener("click", startPractice);
  $("speak-btn").addEventListener("click", handleSpeak);
  $("retry-btn").addEventListener("click", handleRetry);
  $("skip-btn").addEventListener("click", handleNext);
  $("next-btn").addEventListener("click", handleNext);
  $("restart-btn").addEventListener("click", restart);
  $("replay-btn").addEventListener("click", () => speak(currentSentence().en));
}

main();
