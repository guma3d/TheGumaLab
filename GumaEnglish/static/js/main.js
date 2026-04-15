import { fetchStage, askQuestion, evaluateResponse } from "/js/api.js";
import { speak, listenOnce, speechSupported } from "/js/voice.js";

const $ = (id) => document.getElementById(id);

const state = {
  stage: null,
  roundIdx: 0,
  history: [],
  currentQuestion: null,
  busy: false,
};

function addBubble(who, text, extraClass = "") {
  const div = document.createElement("div");
  div.className = `bubble ${who} ${extraClass}`.trim();
  div.textContent = text;
  $("chat-log").appendChild(div);
  div.scrollIntoView({ behavior: "smooth", block: "end" });
  return div;
}

function addMeta(html) {
  const div = document.createElement("div");
  div.className = "bubble meta";
  div.innerHTML = html;
  $("chat-log").appendChild(div);
}

function setBusy(flag) {
  state.busy = flag;
  $("text-input").disabled = flag;
  $("send-btn").disabled = flag;
  $("mic-btn").disabled = flag;
}

async function loadStage(num) {
  state.stage = await fetchStage(num);
  $("stage-num").textContent = state.stage.stageNumber;
  $("robot-name").textContent = state.stage.robotName;
  $("pattern-en").textContent = state.stage.pattern.english;
  $("pattern-ko").textContent = state.stage.pattern.korean;
  const ul = $("examples");
  ul.innerHTML = "";
  for (const s of state.stage.pattern.sentences) {
    const li = document.createElement("li");
    li.innerHTML = `${s.en}<span class="ko">${s.ko}</span>`;
    ul.appendChild(li);
  }
}

function currentContext() {
  const contexts = state.stage.weeks[0].practiceContexts;
  return contexts[state.roundIdx % contexts.length];
}

async function startRound() {
  $("start-btn").hidden = true;
  $("next-btn").hidden = true;
  $("restart-btn").hidden = true;
  $("input-row").hidden = false;
  $("text-input").focus();
  setBusy(true);

  const pending = addBubble("guma", "…");
  try {
    const question = await askQuestion({
      pattern: state.stage.pattern.english,
      examples: state.stage.pattern.sentences.map((s) => s.en),
      context: currentContext(),
      history: state.history,
    });
    state.currentQuestion = question;
    state.history.push(question);
    pending.textContent = question;
    speak(question);
  } catch (err) {
    pending.textContent = `(질문 생성 실패: ${err.message})`;
  } finally {
    setBusy(false);
  }
}

async function sendResponse(text) {
  if (!text || state.busy) return;
  addBubble("kid", text);
  $("text-input").value = "";
  $("input-row").hidden = true;
  setBusy(true);

  const pending = addBubble("guma", "…");
  try {
    const result = await evaluateResponse({
      pattern: state.stage.pattern.english,
      question: state.currentQuestion,
      response: text,
    });
    pending.textContent = result.reply;
    speak(result.reply);
    const markClass = result.used_pattern ? "mark-ok" : "mark-miss";
    const markText = result.used_pattern ? "✓ 패턴 사용" : "△ 패턴 다시";
    addMeta(`<span class="${markClass}">${markText}</span>`);
  } catch (err) {
    pending.textContent = `(평가 실패: ${err.message})`;
  } finally {
    setBusy(false);
  }

  state.roundIdx += 1;
  const totalRounds = state.stage.pattern.sentences.length;
  if (state.roundIdx < totalRounds) {
    $("next-btn").hidden = false;
  } else {
    addMeta(`<strong>이 스테이지 연습 완료!</strong>`);
    $("restart-btn").hidden = false;
  }
}

async function handleMic() {
  if (state.busy) return;
  const micBtn = $("mic-btn");
  micBtn.classList.add("recording");
  try {
    const text = await listenOnce({ lang: "en-US" });
    $("text-input").value = text;
    await sendResponse(text);
  } catch (err) {
    addMeta(`(음성 인식 실패: ${err.message})`);
  } finally {
    micBtn.classList.remove("recording");
  }
}

function restart() {
  state.roundIdx = 0;
  state.history = [];
  state.currentQuestion = null;
  $("chat-log").innerHTML = "";
  $("restart-btn").hidden = true;
  startRound();
}

async function main() {
  try {
    await loadStage(1);
  } catch (err) {
    addBubble("guma", `스테이지 로드 실패: ${err.message}`);
    return;
  }

  if (!speechSupported) {
    $("mic-btn").hidden = true;
    addMeta("이 브라우저는 음성 인식을 지원하지 않아요. 텍스트로 연습하세요.");
  }

  $("start-btn").addEventListener("click", startRound);
  $("next-btn").addEventListener("click", startRound);
  $("restart-btn").addEventListener("click", restart);
  $("send-btn").addEventListener("click", () =>
    sendResponse($("text-input").value.trim())
  );
  $("text-input").addEventListener("keydown", (e) => {
    if (e.key === "Enter") sendResponse($("text-input").value.trim());
  });
  $("mic-btn").addEventListener("click", handleMic);
}

main();
