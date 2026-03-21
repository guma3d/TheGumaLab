import uuid, os
from qdrant_client import QdrantClient
from qdrant_client.http import models

c = QdrantClient('http://qdrant:6333')

# We want to find a point where people has "Unidentifiable Person"
res = c.scroll(
    collection_name="gumaphoto_hybrid_kr",
    scroll_filter=models.Filter(
        must=[
            models.FieldCondition(
                key="people",
                match=models.MatchValue(value="Unidentifiable Person")
            )
        ]
    ),
    limit=5,
    with_payload=True
)

print('=== UNIDENTIFIABLE PERSON REPORT ===\n')
for point in res[0]:
    payload = point.payload
    print(f'---\nPoint ID: {point.id}')
    print(f'Filepath: {payload.get("filepath")}')
    print(f'People: {payload.get("people")}')
    print(f'Face_bbox deleted? {"YES (Missing)" if "face_bbox" not in payload else "NO (Still present)"}')
    if "face_bbox" in payload:
        print(f'Face_bbox value: {payload.get("face_bbox")}')
