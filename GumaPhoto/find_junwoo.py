from qdrant_client import QdrantClient
import os

print("Searching Qdrant for Junwoo...")
qc = QdrantClient('http://qdrant:6333')
all_points = []
offset = None
while True:
    batch, next_offset = qc.scroll(
        collection_name='gumaphoto_hybrid_kr',
        limit=5000,
        with_payload=True,
        with_vectors=False,
        offset=offset
    )
    all_points.extend(batch)
    if next_offset is None:
        break
    offset = next_offset

for p in all_points:
    people = p.payload.get('people', [])
    if '준우' in people:
        print(f"[{p.id}] {p.payload.get('filepath')} / Loc: {p.payload.get('location')} / Date: {p.payload.get('date')}")
