import os
from qdrant_client import QdrantClient
from qdrant_client.http.models import PointIdsList

QDRANT_URL = os.environ.get("QDRANT_URL", "http://qdrant:6333")
COLLECTION_NAME = "gumaphoto_hybrid_kr"

def remove_integer_ghosts():
    print(f"[*] Connecting to Qdrant at {QDRANT_URL}...")
    client = QdrantClient(url=QDRANT_URL, timeout=60)
    
    integer_ids_to_delete = []
    
    print(f"[*] Scanning collection '{COLLECTION_NAME}' for deprecated Integer IDs (SQLite ghosts)...")
    offset = None
    scanned = 0
    while True:
        records, offset = client.scroll(
            collection_name=COLLECTION_NAME,
            limit=2000,
            offset=offset,
            with_payload=False,
            with_vectors=False
        )
        for record in records:
            if isinstance(record.id, int):
                integer_ids_to_delete.append(record.id)
        
        scanned += len(records)
        print(f"  - Scanned {scanned} points, found {len(integer_ids_to_delete)} integer ghosts so far...")
        
        if offset is None:
            break
            
    print(f"[+] Total ghost Integer IDs found: {len(integer_ids_to_delete)}")
    
    if integer_ids_to_delete:
        print("[*] Commencing mass deletion in batches of 1000...")
        for i in range(0, len(integer_ids_to_delete), 1000):
            batch = integer_ids_to_delete[i:i+1000]
            client.delete(
                collection_name=COLLECTION_NAME,
                points_selector=PointIdsList(points=batch)
            )
            print(f"  - Deleted {len(batch)} points (progress: {min(i+1000, len(integer_ids_to_delete))}/{len(integer_ids_to_delete)})")
            
        print("[+] ✨ Ghost deletion fully completed! Qdrant is now 100% pure UUID.")
    else:
        print("[+] System is already clean! No ghost IDs discovered.")

if __name__ == "__main__":
    remove_integer_ghosts()
