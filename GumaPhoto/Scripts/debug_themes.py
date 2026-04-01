import json
try:
    with open('/app/data/caches/themes_cache.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    loc_titles = [t.get('title') for t in data if any('\uac00'<=c<='\ud7a3' for c in t.get('title',''))]
    print("Found location themes in cache:")
    for title in loc_titles:
        print(f" - {title}")
except Exception as e:
    print(f"Error: {e}")

