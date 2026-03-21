import os
from qdrant_client import QdrantClient
from qdrant_client.http import models

c = QdrantClient('http://qdrant:6333')

def count_qdrant(query_str):
    res = c.scroll(
        collection_name="gumaphoto_hybrid_kr",
        scroll_filter=models.Filter(
            must=[models.FieldCondition(key="people", match=models.MatchValue(value=query_str))]
        ),
        limit=1000,
        with_payload=False
    )
    return len(res[0])

unidentifiable_cnt = count_qdrant("Unidentifiable Person")
noperson_cnt = count_qdrant("No Person")

enrolled_base = "/app/data/enrolled"
enrolled_stats = {}
if os.path.exists(enrolled_base):
    for person in os.listdir(enrolled_base):
        p_path = os.path.join(enrolled_base, person)
        if os.path.isdir(p_path):
            files = [f for f in os.listdir(p_path) if f.endswith(('.jpg', '.jpeg', '.png'))]
            enrolled_stats[person] = len(files)

print("=== FEEDBACK PROGRESS REPORT ===")
print(f"Unidentifiable Person: {unidentifiable_cnt}")
print(f"No Person: {noperson_cnt}")
print("Enrolled Faces per Person:")
for p, count in enrolled_stats.items():
    print(f"  - {p}: {count} faces")
