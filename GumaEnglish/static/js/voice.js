const SpeechRecognition =
  window.SpeechRecognition || window.webkitSpeechRecognition;

export const speechSupported = !!SpeechRecognition;

export function speak(text, { lang = "en-US", rate = 0.95 } = {}) {
  if (!("speechSynthesis" in window)) return;
  try { window.speechSynthesis.cancel(); } catch {}
  const u = new SpeechSynthesisUtterance(text);
  u.lang = lang;
  u.rate = rate;
  window.speechSynthesis.speak(u);
}

export function listenOnce({ lang = "en-US" } = {}) {
  return new Promise((resolve, reject) => {
    if (!SpeechRecognition) {
      reject(new Error("SpeechRecognition not supported"));
      return;
    }
    const rec = new SpeechRecognition();
    rec.lang = lang;
    rec.interimResults = false;
    rec.maxAlternatives = 1;

    let settled = false;
    rec.onresult = (e) => {
      settled = true;
      resolve(e.results[0][0].transcript);
    };
    rec.onerror = (e) => {
      settled = true;
      reject(new Error(e.error || "speech error"));
    };
    rec.onend = () => {
      if (!settled) reject(new Error("no speech detected"));
    };
    rec.start();
  });
}
