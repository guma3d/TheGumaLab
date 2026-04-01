import json, re

try:
    with open('/app/data/caches/themes_cache.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    print(f"Total themes in cache: {len(data)}")
    loc_count = sum(1 for t in data if bool(re.search(r'[가-힣]', t.get('title', ''))))
    print(f"Location themes: {loc_count}")
except Exception as e:
    print(e)
