from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from Server import TASK_STATUS_FILE, render_material_html  # noqa: E402


def main() -> int:
    if not TASK_STATUS_FILE.exists():
        print("task_status.json not found")
        return 1

    tasks = json.loads(TASK_STATUS_FILE.read_text(encoding="utf-8-sig"))
    updated = 0
    skipped = 0

    for task_id, task in tasks.items():
        result = task.get("result") or {}
        json_path = Path(result.get("json_path") or "")
        html_path = Path(result.get("html_path") or "")
        if not json_path.exists() or not html_path:
            skipped += 1
            continue

        pack = json.loads(json_path.read_text(encoding="utf-8-sig"))
        html_path.parent.mkdir(parents=True, exist_ok=True)
        html_path.write_text(render_material_html(pack, task_id), encoding="utf-8")
        updated += 1

    print(f"updated={updated} skipped={skipped}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
