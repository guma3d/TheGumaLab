"""Validate the first complete four-character reference collection."""
import hashlib
import json
import struct
from collections import Counter
from pathlib import Path

root = Path(__file__).resolve().parents[1] / 'storage'
items = [json.loads(p.read_text(encoding='utf-8-sig')) for p in (root/'imports').glob('*.json')]
characters = ('adult-man', 'adult-woman', 'boy', 'girl')
report = {'characters': {}, 'total_resources': len(items), 'archived': sum(bool(x.get('archived')) for x in items)}
digests = []
for character in characters:
    selected = [x for x in items if x.get('character_id') == character and not x.get('archived')]
    kinds = Counter(x['kind'] for x in selected)
    assert kinds == {'angle':6, 'expression':4, 'scene':5}, (character, kinds)
    dimensions = set()
    for item in selected:
        data = (root/'assets'/item['file']).read_bytes()
        assert data[:8] == b'\x89PNG\r\n\x1a\n', item['id']
        width, height = struct.unpack('>II', data[16:24])
        assert width >= 1500 and abs(width / height - 16/9) < .01, item['id']
        dimensions.add((width,height))
        digests.append(hashlib.sha256(data).hexdigest())
    report['characters'][character] = {'count':len(selected), 'kinds':dict(kinds), 'dimensions':sorted(dimensions)}
assert len(digests) == len(set(digests)) == 60, 'Missing or duplicate image content'
report['unique_character_images'] = len(digests)
report['review_status'] = 'Generated references; user selection pending. Visual checks do not imply user approval.'
(root/'verification').mkdir(exist_ok=True)
(root/'verification'/'reference-audit.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(report, ensure_ascii=False))
