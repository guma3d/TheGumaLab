import os
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PayloadSchemaType

COLLECTION_NAME = "gumaphoto_hybrid_kr"

class QdrantStore:
    def __init__(self, url):
        print(f"[*] 벡터 DB (Qdrant) 접속 초기화... ({url})")
        self.q_client = QdrantClient(url=url, timeout=60)
        self._init_collection()
        
    def _init_collection(self):
        if not self.q_client.collection_exists(collection_name=COLLECTION_NAME):
            self.q_client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config={
                    "scene": VectorParams(size=768, distance=Distance.COSINE),
                    "face": VectorParams(size=512, distance=Distance.COSINE)
                }
            )
            self.q_client.create_payload_index(COLLECTION_NAME, "original_context", "text")
            self.q_client.create_payload_index(COLLECTION_NAME, "filepath", "keyword")
            self.q_client.create_payload_index(COLLECTION_NAME, "people", field_schema=PayloadSchemaType.KEYWORD)
            self.q_client.create_payload_index(COLLECTION_NAME, "objects", field_schema=PayloadSchemaType.KEYWORD)
            self.q_client.create_payload_index(COLLECTION_NAME, "location", field_schema=PayloadSchemaType.TEXT)
            self.q_client.create_payload_index(COLLECTION_NAME, "caption", field_schema=PayloadSchemaType.TEXT)
            self.q_client.create_payload_index(COLLECTION_NAME, "sort_date", field_schema=PayloadSchemaType.INTEGER)
            print(f"  [+] 신규 Qdrant 멀티-벡터 컬렉션 '{COLLECTION_NAME}' 생성 완료.")
        else:
            print(f"  [-] 기존 Qdrant 컬렉션 '{COLLECTION_NAME}' 을 재사용합니다.")

    def point_exists(self, point_id):
        try:
            records = self.q_client.retrieve(
                collection_name=COLLECTION_NAME,
                ids=[point_id],
                with_payload=False,
                with_vectors=False
            )
            return len(records) > 0
        except Exception:
            return False

    def delete_point(self, point_id):
        try:
            from qdrant_client.http.models import PointIdsList
            self.q_client.delete(collection_name=COLLECTION_NAME, points_selector=PointIdsList(points=[point_id]))
        except Exception: pass

    def upsert_batch(self, points):
        if points:
            self.q_client.upsert(collection_name=COLLECTION_NAME, points=points)
