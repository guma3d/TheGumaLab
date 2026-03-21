import uuid
from qdrant_client import QdrantClient

c = QdrantClient('http://qdrant:6333')
uid = str(uuid.uuid5(uuid.NAMESPACE_URL, "/app/data/organized/2017/2017-03_대한민국-부천시/2017-03_148.jpg"))
res = c.retrieve('gumaphoto_hybrid_kr', [uid], with_payload=True)
if res:
    print(res[0].payload)
