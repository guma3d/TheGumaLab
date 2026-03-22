import os
from qdrant_client import QdrantClient

QDRANT_URL = os.environ.get("QDRANT_URL", "http://127.0.0.1:6333")
client = QdrantClient(url=QDRANT_URL)

try:
    results, _ = client.scroll(
        collection_name="gumaphoto_hybrid_kr",
        limit=20,
        with_payload=True
    )
    matches = 0
    for r in results:
        p = r.payload
        loc = p.get("location", "")
        if "로스" in loc or "로스앤젤레스" in loc or "Los Angel" in loc:
            print(f"FOUND: {loc} in {p.get('filepath')}")
            matches += 1
            
    print(f"Total matching Los Angeles in first 20 nodes: {matches}")
    
    # Let's search by text explicitly!
    from qdrant_client.http.models import Filter, FieldCondition, MatchText
    res = client.count(
        collection_name="gumaphoto_hybrid_kr", 
        count_filter=Filter(must=[FieldCondition(key="location", match=MatchText(text="로스앤젤레스"))])
    )
    print(f"Total points with 로스앤젤레스 matching text: {res.count}")
    
except Exception as e:
    print(f"Error: {e}")
