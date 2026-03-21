import uuid, os
from qdrant_client import QdrantClient

c = QdrantClient('http://qdrant:6333')

targets = [
    "/app/data/organized/2017/2017-03_Unknown-Location/2017-03_01.jpg",
    "/app/data/organized/2017/2017-03_Unknown-Location/2017-03_02.jpg"
]

print('=== TARGET PHOTOS ===\n')
for filepath in targets:
    print(f'---\nFilepath: {filepath}')
    uid = str(uuid.uuid5(uuid.NAMESPACE_URL, filepath))
    res = c.retrieve('gumaphoto_hybrid_kr', [uid], with_payload=True)
    if res:
        print(f'Qdrant Payload: {res[0].payload}\n')
    else:
        print('Qdrant Payload: None\n')
