from qdrant_client import QdrantClient
from qdrant_client.http.models import Filter, FieldCondition, MatchValue

client = QdrantClient(url='http://qdrant:6333')
collection = 'gumaphoto_hybrid_kr'

points, _ = client.scroll(
    collection_name=collection,
    scroll_filter=Filter(must=[FieldCondition(key='date', match=MatchValue(value='Unknown Date'))]),
    limit=5000,
    with_payload=True
)

counter = 0
for pt in points:
    if pt.payload.get('sort_date') != 0:
        client.set_payload(collection_name=collection, payload={'sort_date': 0}, points=[pt.id])
        counter += 1

print(f"Fixed {counter} Unknown Date photos by forcing sort_date=0.")
