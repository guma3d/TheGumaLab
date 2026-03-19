import time
from qdrant_client import QdrantClient
from qdrant_client.http.models import OrderBy, Direction, PayloadSchemaType

client = QdrantClient("http://qdrant:6333")
try:
    client.delete_payload_index("gumaphoto_hybrid_kr", "date")
    time.sleep(1)
except: pass

try:
    client.create_payload_index("gumaphoto_hybrid_kr", "date", field_schema=PayloadSchemaType.DATETIME)
    print("Created date datetime index")
except Exception as e:
    print("Date index might exist:", e)

res, _ = client.scroll(
    collection_name="gumaphoto_hybrid_kr", 
    limit=5, 
    with_payload=True, 
    order_by=OrderBy(key="date", direction=Direction.DESC)
)
print("Latest 5 photos by date:")
for hit in res:
    print(hit.payload.get("date"), hit.payload.get("filepath"))
