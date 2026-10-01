"""Usage: python recommendation_import.py <researched_batch.json>"""
import sys
from pathlib import Path
from app.core.recommendations import DailyBatch, save_batch
from app.core.categories import PRESETS

if __name__ == "__main__":
    batch = DailyBatch.model_validate_json(Path(sys.argv[1]).read_text(encoding="utf-8-sig"))
    result = save_batch(batch)
    categories = ' / '.join(f"{preset['label']} 5개" for preset in PRESETS.values())
    print(f"{result['date']}: {categories} 저장 완료 (오늘 {result['research_count']}회 조사)")
