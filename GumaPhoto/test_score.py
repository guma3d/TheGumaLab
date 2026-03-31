from core.state import state
from qdrant_client import QdrantClient
from qdrant_client.http.models import Filter, FieldCondition, MatchText, MatchValue

state.qdrant_client = QdrantClient(url="http://qdrant:6333")

loc_tests = [
  "미국 뉴욕",
  "미국-뉴욕",
  "베트남 다낭",
  "미국 Paradise Chinatown"
]

for test_loc in loc_tests:
    res_text, _ = state.qdrant_client.scroll(
        collection_name="gumaphoto_hybrid_kr",
        scroll_filter=Filter(must=[FieldCondition(key="location", match=MatchText(text=test_loc))]),
        limit=2
    )

    res_text_replaced, _ = state.qdrant_client.scroll(
        collection_name="gumaphoto_hybrid_kr",
        scroll_filter=Filter(must=[FieldCondition(key="location", match=MatchText(text=test_loc.replace("-", " ")))]),
        limit=2
    )

    print(f"[{test_loc}] MatchText: {len(res_text)} | MatchText(replaced): {len(res_text_replaced)}")
