import sys
sys.path.insert(0, r'd:\TheGumaLab\GumaPhoto')
from qdrant_client import QdrantClient
from api.state import qdrant_client
import api.state as state
# Mock state
state.qdrant_client = QdrantClient("localhost", port=6333)

from api.services.feedback_cache import feedback_cache
import time

print("Forcing direct synchronous cache build for testing...")
start_time = time.time()
feedback_cache._build_cache_worker()
print(f"Build took {time.time() - start_time:.2f} seconds.")
print(f"Queue size: {len(feedback_cache.queue)}")
if feedback_cache.queue:
    print(f"Top 1 match count: {feedback_cache.queue[0].get('match_count')}")
    print(f"Top 2 match count: {feedback_cache.queue[1].get('match_count')}")
