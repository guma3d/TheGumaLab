from qdrant_client import QdrantClient
import json

tp_str = '["73673ea3-51fa-44d9-9198-30549d562a35", "cc9776d6-68fb-4d87-9eed-35804fadd7a4", "9e1c4a16-6c84-4869-aa57-30e3bb9706ce", "a5ec75ff-ddb5-4bce-92e1-43cb4d75d272"]'
target = json.loads(tp_str)

c = QdrantClient("http://qdrant:6333")
ret = c.retrieve("gumaphoto_hybrid_kr", ids=target, with_payload=True)
print("Retrieved:", len(ret))
for r in ret:
    print("Found ID:", r.id, "fpath:", getattr(r, "payload", {}).get("filepath", "NONE"))
