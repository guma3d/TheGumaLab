"""GumaEnglish Flask backend — static file + stage JSON server.

현재는 AI 대화 기능 없이 "보고/듣고 따라 말하기 → 점진적 힌트 제거" 방식의
기본 연습 루프만 제공. Gemini 연동은 차후 대화 기능 추가 시 재도입.
"""
import json
from pathlib import Path

from flask import Flask, jsonify, send_from_directory

ROOT = Path(__file__).resolve().parent
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


@app.get("/api/health")
def api_health():
    return jsonify({"ok": True})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
