import json
from qdrant_client import QdrantClient
import sys

client = QdrantClient("http://qdrant:6333", timeout=10)
fake_list = ["735d9cee-76a3-5a9c-ab09-64f35d02d969"]

res = client.retrieve("gumaphoto_hybrid_kr", ids=fake_list, with_payload=True)
print("Num ret:", len(res))
if res:
    print("ID 0 payload keys:", list(res[0].payload.keys()))
