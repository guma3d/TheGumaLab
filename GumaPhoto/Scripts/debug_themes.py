import json
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue

client = QdrantClient(url="http://localhost:6333")

try:
    with open('/app/data/available_tags.json', 'r', encoding='utf-8') as f:
        tag_data = json.load(f)
        
    valid_locations = [loc for loc in tag_data.get("locations", []) if loc and "Unknown" not in loc and "정보없음" not in loc]
    
    print(f"Total valid locations in available_tags.json: {len(valid_locations)}")
    
    failed_locs = []
    success_locs = []
    
    for loc in valid_locations:
        q_filter = Filter(must=[FieldCondition(key="location", match=MatchValue(value=loc))])
        res, _ = client.scroll(
            collection_name="gumaphoto_hybrid_kr",
            scroll_filter=q_filter,
            limit=1
        )
        if len(res) == 0:
            failed_locs.append(loc)
        else:
            success_locs.append(loc)
            
    print(f"\nSuccess locations ({len(success_locs)}):")
    for loc in success_locs[:10]:
        print(f" - {loc}")
        
    print(f"\nFailed locations ({len(failed_locs)}):")
    for loc in failed_locs[:10]:
        print(f" - {loc}")

except Exception as e:
    print(f"Error: {e}")
