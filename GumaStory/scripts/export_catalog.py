"""Export portable generation metadata; large originals remain in storage."""
import hashlib
import json
from collections import Counter
from pathlib import Path

project = Path(__file__).resolve().parents[1]
storage = project / 'storage'
items = []
for path in sorted((storage / 'imports').glob('*.json')):
    item = json.loads(path.read_text(encoding='utf-8-sig'))
    original = storage / 'assets' / item['file']
    with original.open('rb') as stream:
        item['sha256'] = hashlib.file_digest(stream, 'sha256').hexdigest()
    item['bytes'] = original.stat().st_size
    items.append(item)
counts = Counter(x['character_id'] for x in items if x.get('character_id') and not x.get('archived'))
result = {'active_character_counts': dict(counts), 'items': items}
destination = project / 'reference-catalog.json'
destination.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'catalog': str(destination), 'total':len(items), 'active_characters':dict(counts)}, ensure_ascii=False))
