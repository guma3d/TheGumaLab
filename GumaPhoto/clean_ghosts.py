import os
from qdrant_client import QdrantClient

def clean_qdrant_ghosts():
    print("Starting Qdrant Ghost Sweep...")
    qc = QdrantClient('http://qdrant:6333')
    coll = 'gumaphoto_hybrid_kr'
    
    all_points = []
    offset = None
    while True:
        batch, next_offset = qc.scroll(
            collection_name=coll,
            limit=5000,
            with_payload=True,
            with_vectors=False,
            offset=offset
        )
        all_points.extend(batch)
        if next_offset is None:
            break
        offset = next_offset

    ghost_ids = []
    for p in all_points:
        filepath = p.payload.get('filepath', '')
        if not os.path.exists(filepath):
            ghost_ids.append(p.id)
            print(f"Ghost Found: {filepath} (ID: {p.id})")
            
    print(f"Total points: {len(all_points)}")
    print(f"Ghosts to delete: {len(ghost_ids)}")
    
    if ghost_ids:
        # Delete ghost points
        qc.delete(
            collection_name=coll,
            points_selector=ghost_ids
        )
        print("Ghosts successfully deleted from Qdrant.")
    else:
        print("No ghosts found. Database is perfectly clean.")

if __name__ == '__main__':
    clean_qdrant_ghosts()
