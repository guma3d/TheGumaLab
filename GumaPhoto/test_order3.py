from qdrant_client import QdrantClient
from qdrant_client.http.models import OrderBy, Direction
import time

client = QdrantClient("http://qdrant:6333", timeout=60)
try:
    info = client.get_collection("gumaphoto_hybrid_kr")
    print("Collection status:", info.status)
    print("Payload schema:", info.payload_schema)
except Exception as e:
    print(e)

try:
    res, _ = client.scroll(
        collection_name="gumaphoto_hybrid_kr", 
        limit=5, 
        with_payload=True, 
        order_by=OrderBy(key="sort_date", direction=Direction.DESC)
    )
    print("Latest 5 photos by sort_date:")
    for hit in res:
        print(hit.payload.get("sort_date"), hit.payload.get("filepath"))
except Exception as e:
    print("Query error:", e)
