import os
from qdrant_client import QdrantClient

def check_files():
    q_client = QdrantClient(url="http://localhost:6337")
    
    # 1. Get Qdrant count
    try:
        q_count = q_client.count(collection_name="gumaphoto_hybrid_kr").count
    except Exception as e:
        q_count = f"Error: {e}"
        
    # 2. Get physical count
    physical_count = 0
    target_dir = "D:/Pictures"
    
    for root, dirs, files in os.walk(target_dir):
        # blacklist = ['OriginalSource', 'junk_screenshots', 'b_cuts', 'test_images', '.git', 'uploads_raw', 'enrolled', 'test', 'unknown']
        # dirs[:] = [d for d in dirs if d not in blacklist]
        for f in files:
            if f.lower().endswith(('.jpg', '.jpeg', '.png', '.heic', '.heif')):
                physical_count += 1
                
    # 3. Let's actually check how many Qdrant points have valid physical paths
    # We will sample 1000 from Qdrant and see how many are missing
    batch, _ = q_client.scroll(
        collection_name="gumaphoto_hybrid_kr",
        limit=5000,
        with_payload=["filepath"],
        with_vectors=False
    )
    
    missing_count = 0
    total_sampled = len(batch)
    for p in batch:
        fp = p.payload.get("filepath", "")
        local_fp = fp.replace("/app/data/organized", "D:/Pictures")
        if not os.path.exists(local_fp):
            missing_count += 1

    print(f"Total points in Qdrant DB: {q_count}")
    print(f"Total physical files on disk: {physical_count}")
    print(f"Ghost estimate from sample: {missing_count} ghosts out of {total_sampled} sampled")

check_files()
