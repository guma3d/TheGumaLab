from __future__ import annotations

import json
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from flask import Flask, jsonify, request, send_from_directory


ROOT = Path(__file__).resolve().parent
WEB_DIR = ROOT / "web"
DATA_DIR = ROOT / "data"
SAVES_DIR = DATA_DIR / "saves"
PROFILE_RE = re.compile(r"^[A-Za-z0-9_-]{1,40}$")


app = Flask(__name__, static_folder=None)
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _profile_name(raw: str | None) -> str:
    profile = (raw or "default").strip()
    if not PROFILE_RE.fullmatch(profile):
        raise ValueError("profile must use letters, numbers, _ or -")
    return profile


def _save_path(profile: str) -> Path:
    return SAVES_DIR / f"{profile}.json"


def _default_save(profile: str) -> dict[str, Any]:
    return {
        "profile": profile,
        "created_at": _now(),
        "updated_at": _now(),
        "seasons": {
            "season_01": {
                "high_score": 0,
                "best_hp": 100,
                "chapter": 1,
                "hero_name": "번개용사",
            },
            "season_02": {"chapter": 13, "opened_doors": 0, "last_result": ""},
            "season_03": {"chapter": 25, "wins": 0, "best_turns": 0},
            "season_04": {"chapter": 37, "high_score": 0, "last_goal": "전설의 황금열쇠를 찾아라!"},
        },
    }


def _read_save(profile: str) -> dict[str, Any]:
    path = _save_path(profile)
    if not path.exists():
        return _default_save(profile)
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        broken = path.with_suffix(f".broken-{datetime.now().strftime('%Y%m%d%H%M%S')}.json")
        path.replace(broken)
        return _default_save(profile)


def _write_save(profile: str, data: dict[str, Any]) -> None:
    SAVES_DIR.mkdir(parents=True, exist_ok=True)
    data["profile"] = profile
    data["updated_at"] = _now()
    target = _save_path(profile)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=SAVES_DIR, delete=False) as temp:
        json.dump(data, temp, ensure_ascii=False, indent=2)
        temp_path = Path(temp.name)
    temp_path.replace(target)


def _merge_dict(base: dict[str, Any], patch: dict[str, Any]) -> dict[str, Any]:
    for key, value in patch.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            _merge_dict(base[key], value)
        else:
            base[key] = value
    return base


@app.after_request
def no_store(response):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


@app.get("/")
def index():
    return send_from_directory(WEB_DIR, "index.html")


@app.get("/<path:path>")
def static_files(path: str):
    return send_from_directory(WEB_DIR, path)


@app.get("/api/health")
def health():
    return jsonify({"ok": True, "service": "GumaKidsPython"})


@app.get("/api/save")
def get_save():
    try:
        profile = _profile_name(request.args.get("profile"))
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    return jsonify(_read_save(profile))


@app.post("/api/save")
def post_save():
    body = request.get_json(silent=True) or {}
    try:
        profile = _profile_name(body.get("profile") or request.args.get("profile"))
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    patch = body.get("save")
    if not isinstance(patch, dict):
        return jsonify({"error": "save must be an object"}), 400

    current = _read_save(profile)
    _merge_dict(current, patch)
    _write_save(profile, current)
    return jsonify(current)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
