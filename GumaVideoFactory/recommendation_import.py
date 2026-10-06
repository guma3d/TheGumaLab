"""Usage: python recommendation_import.py <researched_batch.json>"""
import sys
from pathlib import Path
from app.core.recommendations import DailyBatch, save_batch
from app.core.categories import PRESETS

if __name__ == "__main__":
    if sys.argv[1:] == ['--living-search-plan']:
        import json
        from app.core.living_research import search_plan
        from app.core.recommendations import now_kst
        print(json.dumps(search_plan(now_kst().date()), ensure_ascii=False, indent=2))
        raise SystemExit(0)
    if sys.argv[1:] == ['--food-search-plan']:
        import json
        from app.core.food_research import search_plan
        from app.core.recommendations import now_kst
        print(json.dumps(search_plan(now_kst().date()), ensure_ascii=False, indent=2))
        raise SystemExit(0)
    batch = DailyBatch.model_validate_json(Path(sys.argv[1]).read_text(encoding="utf-8-sig"))
    # Resources and issued affiliate evidence must pass save_batch before any list write.
    result = save_batch(batch)
    categories = ' / '.join(f"{PRESETS[category]['label']} 1개" for category in PRESETS if any(item.category == category for item in batch.items))
    print(f"{result['date']}: {categories} 저장 완료 (오늘 {result['research_count']}회 조사)")
