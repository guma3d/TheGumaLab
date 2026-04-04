from qdrant_client import QdrantClient
from qdrant_client.http.models import Filter, FieldCondition, MatchValue

client = QdrantClient(host='localhost', port=6333)

res = client.scroll(
    collection_name="gumaphoto_hybrid_kr",
    scroll_filter=Filter(
        should=[
            FieldCondition(key="people", match=MatchValue(value="Unknown Person")),
            FieldCondition(key="people", match=MatchValue(value="Unknown People"))
        ]
    ),
    limit=5,
    with_payload=["people"]
)

if res and res[0]:
    for pt in res[0]:
        print(pt.payload)
else:
    print("No points found in Qdrant with Unknown Person / Unknown People")
