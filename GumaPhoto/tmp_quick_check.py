import os, sys
sys.path.insert(0, '/app')
from qdrant_client import QdrantClient
from qdrant_client.http.models import Filter, FieldCondition, MatchText, MatchValue
import time

c = QdrantClient(url='http://qdrant:6333')

print("Fetching unknowns...")
scroll_filter = Filter(
    should=[
        FieldCondition(key="date", match=MatchText(text="Unknown")),
        FieldCondition(key="location", match=MatchText(text="Unknown")),
        FieldCondition(key="location", match=MatchText(text="위치정보없음")),
        FieldCondition(key="people", match=MatchValue(value="Unknown Person")),
        FieldCondition(key="people", match=MatchValue(value="Unknown People"))
    ]
)

batch, _ = c.scroll(
    collection_name="gumaphoto_hybrid_kr",
    scroll_filter=scroll_filter,
    limit=5000,
    with_payload=True,
    with_vectors=False
)

candidates = []
for raw in batch:
    p = raw.payload or {}
    loc = p.get("location", "")
    date_val = p.get("date", "")
    people_val = p.get("people", [])
    
    if "Unknown" in date_val or not date_val: candidates.append({"raw": raw, "issue": "Date"})
    if "위치정보없음" in loc or "Unknown" in loc or not loc: candidates.append({"raw": raw, "issue": "Location"})
    if any(x in ["Unknown Person", "Unknown People"] for x in people_val): candidates.append({"raw": raw, "issue": "People"})

# Just check the first 50 candidates to find a potentially huge cluster
max_size = 0
global_covered = set()

print(f"Testing the first 80 out of {len(candidates)} candidates...", flush=True)

for cand in candidates[:300]:
    tid = cand["raw"].id
    issue_key = cand["issue"]
    
    if f"{tid}_{issue_key}" in global_covered: continue
    
    fb_type = "face" if cand["issue"] in ["Person", "People"] else "scene"
    cutoff = 0.80 if fb_type == "face" else 0.83
    
    rec_res = c.query_points(
        collection_name="gumaphoto_hybrid_kr",
        query=tid,
        using=fb_type,
        limit=10000,
        with_payload=["location", "date", "people"]
    ).points
    
    unresolved_ids = set()
    for h in rec_res:
        if getattr(h, "score", 0.0) < cutoff: continue
        hp = h.payload or {}
        
        if fb_type != "face":
            if "Location" in cand["issue"]:
                loc2 = hp.get("location", "")
                if "Unknown" not in loc2 and "위치정보없음" not in loc2 and loc2.strip() != "": continue
        else:
            p_people = hp.get("people", [])
            if p_people and "Unknown Person" not in p_people and "Unknown People" not in p_people: continue
                
        unresolved_ids.add(str(h.id))
        global_covered.add(f"{str(h.id)}_{issue_key}")
        
    if len(unresolved_ids) > max_size:
        max_size = len(unresolved_ids)
        print(f"Found new maximum: {max_size} photos (Issue: {cand['issue']})", flush=True)

print(f"MAX RESULT = {max_size}", flush=True)
