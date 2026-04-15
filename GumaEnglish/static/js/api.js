export async function fetchStage(stageNumber) {
  const res = await fetch(`/api/stage/${stageNumber}`);
  if (!res.ok) throw new Error(`stage ${stageNumber} fetch failed: ${res.status}`);
  return res.json();
}

export async function askQuestion({ pattern, examples, context, history }) {
  const res = await fetch("/api/gemini/question", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ pattern, examples, context, history }),
  });
  if (!res.ok) throw new Error(`question api failed: ${res.status}`);
  return (await res.json()).question;
}

export async function evaluateResponse({ pattern, question, response }) {
  const res = await fetch("/api/gemini/evaluate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ pattern, question, response }),
  });
  if (!res.ok) throw new Error(`evaluate api failed: ${res.status}`);
  return res.json();
}
