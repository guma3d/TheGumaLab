"""GumaEnglish Flask backend — Gemini proxy + static file server.

Reuses the validated prompt functions from PythonPrototype/ directly.
No duplication: the same modules that power the CLI also power the web.
"""
import json
import sys
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "PythonPrototype"))

from gemini_question import generate_question  # noqa: E402
from gemini_eval import evaluate_and_reply  # noqa: E402

STATIC_DIR = ROOT / "static"
STAGES_DIR = ROOT / "Curriculum" / "stages"

app = Flask(__name__, static_folder=None)


@app.get("/")
def index():
    return send_from_directory(STATIC_DIR, "index.html")


@app.get("/<path:path>")
def static_files(path: str):
    return send_from_directory(STATIC_DIR, path)


@app.get("/api/stage/<int:stage_number>")
def api_stage(stage_number: int):
    stage_file = STAGES_DIR / f"stage_{stage_number:03d}.json"
    if not stage_file.exists():
        return jsonify({"error": f"stage {stage_number} not found"}), 404
    return jsonify(json.loads(stage_file.read_text(encoding="utf-8")))


@app.post("/api/gemini/question")
def api_question():
    data = request.get_json(force=True)
    question = generate_question(
        pattern_english=data["pattern"],
        target_sentence=data["target"],
        context_hint=data.get("context"),
        previous_questions=data.get("history", []),
    )
    return jsonify({"question": question})


@app.post("/api/gemini/evaluate")
def api_evaluate():
    data = request.get_json(force=True)
    result = evaluate_and_reply(
        pattern_english=data["pattern"],
        question_asked=data["question"],
        learner_response=data["response"],
    )
    return jsonify(result)


@app.get("/api/health")
def api_health():
    return jsonify({"ok": True})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
