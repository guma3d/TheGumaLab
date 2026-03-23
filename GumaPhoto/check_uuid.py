from qdrant_client import QdrantClient
import uuid

def check_uuid_match():
    try:
        qc = QdrantClient('http://qdrant:6333')
        batch, _ = qc.scroll(
            collection_name='gumaphoto_hybrid_kr', 
            limit=5, 
            with_payload=True, 
            with_vectors=False
        )
        
        if batch:
            print(f"Checking {len(batch)} points from Qdrant...\n")
            for i, p in enumerate(batch):
                qdrant_id = p.id
                filepath = p.payload.get('filepath', '')
                uuid5_id = str(uuid.uuid5(uuid.NAMESPACE_URL, filepath))
                
                print(f"--- Point {i+1} ---")
                print(f"Stored Qdrant ID : {qdrant_id}")
                print(f"Calculated UUID5 : {uuid5_id}")
                print(f"Filepath         : {filepath}")
                if str(qdrant_id) == str(uuid5_id):
                    print("=> MATCH! (UUID5 was used)")
                else:
                    print("=> MISMATCH! (UUID4 or other was used)")
        else:
            print("Qdrant is empty.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    check_uuid_match()
