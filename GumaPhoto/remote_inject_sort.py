import os
import re
from qdrant_client import QdrantClient
from qdrant_client.http.models import PayloadSchemaType, PointStruct

client = QdrantClient("http://qdrant:6333")

try:
    client.delete_payload_index("gumaphoto_hybrid_kr", "date")
except: pass
try:
    client.delete_payload_index("gumaphoto_hybrid_kr", "sort_date")
except: pass

print("Deleted old indexes...")

offset = None
count = 0

while True:
    records, next_offset = client.scroll(
        collection_name="gumaphoto_hybrid_kr",
        limit=500,
        offset=offset,
        with_payload=True,
        with_vectors=True
    )
    if not records:
        break
        
    pts = []
    import datetime
    for hit in records:
        date_str = hit.payload.get("date", "")
        sort_date = 0
        if date_str:
            match = re.search(r'(19|20)\d{2}(-\d{2})?(-\d{2})?', date_str)
            if match:
                full = match.group(0)
                parts = full.split('-')
                year = int(parts[0])
                month = int(parts[1]) if len(parts) > 1 else 1
                day = int(parts[2]) if len(parts) > 2 else 1
                sort_date = year * 10000 + month * 100 + day
        
        if sort_date == 0:
            filepath = hit.payload.get("filepath", "")
            if os.path.exists(filepath):
                try:
                    dt = datetime.datetime.fromtimestamp(os.path.getmtime(filepath))
                    sort_date = dt.year * 10000 + dt.month * 100 + dt.day
                except Exception as e:
                    sort_date = 0
        
        # Merge sort_date into payload
        payload = dict(hit.payload)
        payload["sort_date"] = sort_date
        pts.append(PointStruct(id=hit.id, vector=hit.vector, payload=payload))
        
    client.upsert(collection_name="gumaphoto_hybrid_kr", points=pts)
    count += len(pts)
    print(f"Updated {count} points...")
    offset = next_offset
    if not offset:
        break

print(f"Total updated: {count}")
try:
    client.create_payload_index("gumaphoto_hybrid_kr", "sort_date", field_schema=PayloadSchemaType.INTEGER)
    print("Created sort_date int index")
except Exception as e:
    print(e)
