import sys
import os
sys.path.append('/app')

from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue
import sqlite3
import json

client = QdrantClient('http://gumaphoto_qdrant:6333')
COLLECTION_NAME = 'gumaphoto_hybrid_kr'

points_to_update = []
offset = None
while True:
    record = client.scroll(
        collection_name=COLLECTION_NAME,
        scroll_filter=Filter(
            must=[FieldCondition(key='people', match=MatchValue(value='No Person'))]
        ),
        limit=1000,
        offset=offset,
        with_payload=True
    )
    points = record[0]
    next_page_offset = record[1]
    
    for pt in points:
        new_people = [p if p != 'No Person' else 'No People' for p in pt.payload.get('people', [])]
        points_to_update.append((pt.id, new_people))
        
    if next_page_offset is None:
        break
    offset = next_page_offset

print(f'Found {len(points_to_update)} points in Qdrant to update.')

for pt_id, new_people in points_to_update:
    client.set_payload(collection_name=COLLECTION_NAME, payload={'people': new_people}, points=[pt_id])
    print(f"Updated Qdrant point {pt_id}")
print('Qdrant updated.')

db_path = '/app/data/gumaphoto.db'
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT filepath, metadata_json FROM file_metadata WHERE metadata_json LIKE '%No Person%'")
    rows = cursor.fetchall()
    print(f'Found {len(rows)} rows in SQLite to update.')
    for filepath, metadata_json in rows:
        try:
            meta = json.loads(metadata_json)
            if 'people' in meta and isinstance(meta['people'], list):
                meta['people'] = [p if p != 'No Person' else 'No People' for p in meta['people']]
                cursor.execute('UPDATE file_metadata SET metadata_json = ? WHERE filepath = ?', (json.dumps(meta, ensure_ascii=False), filepath))
        except Exception as e:
            print('SQLite error:', e)
    conn.commit()
    conn.close()
    print('SQLite updated.')

audit_path = '/app/data/audit_trace.json'
if os.path.exists(audit_path):
    with open(audit_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    changed = False
    new_lines = []
    for line in lines:
        try:
            data = json.loads(line)
            if 'people' in data and isinstance(data['people'], list) and 'No Person' in data['people']:
                data['people'] = [p if p != 'No Person' else 'No People' for p in data['people']]
                new_lines.append(json.dumps(data, ensure_ascii=False) + '\n')
                changed = True
            else:
                new_lines.append(line)
        except:
            new_lines.append(line)
    if changed:
        with open(audit_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        print('audit_trace.json updated.')
print('Migration completed.')
