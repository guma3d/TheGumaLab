from qdrant_client import QdrantClient
qdrant = QdrantClient(url="http://qdrant:6333")
res, _ = qdrant.scroll(collection_name="gumaphoto_hybrid_kr", limit=5000)
locs = set(p.payload.get("location") for p in res if p.payload and p.payload.get("location"))
print("DB locations sample:")
print(list(locs)[:20])
