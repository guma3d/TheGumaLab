import uuid
from qdrant_client import QdrantClient

filepath = "/app/data/organized/2005/2005-01_Unknown-Location/2005-01_01.jpg"
point_id = str(uuid.uuid5(uuid.NAMESPACE_URL, filepath))
q_client = QdrantClient("http://qdrant:6333", timeout=10)

try:
    records = q_client.retrieve(
        collection_name="gumaphoto_hybrid_kr",
        ids=[point_id],
        with_payload=False,
        with_vectors=False
    )
    print("qdrant_has_vector:", len(records) > 0)
    print("records:", records)
except Exception as e:
    print("Error:", e)
