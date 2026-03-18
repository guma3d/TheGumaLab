from qdrant_client import QdrantClient
from qdrant_client.http.models import OrderBy, Direction

client = QdrantClient("http://qdrant:6333")
res, _ = client.scroll(
    collection_name="gumaphoto_hybrid_kr", 
    limit=10, 
    with_payload=True, 
    order_by=OrderBy(key="date", direction=Direction.DESC)
)
print("Latest 10 photos by date:")
for hit in res:
    print(hit.payload.get("date"), hit.payload.get("filepath"))
