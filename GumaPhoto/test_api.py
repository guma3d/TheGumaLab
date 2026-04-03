import sys
import asyncio
from qdrant_client import QdrantClient

def run_test():
    qdrant_client = QdrantClient("localhost", port=6333)
    from qdrant_client.http.models import Filter, FieldCondition, MatchText, MatchValue
    
    unknowns, _ = qdrant_client.scroll(
        collection_name="gumaphoto_hybrid_kr",
        scroll_filter=Filter(
            should=[
                FieldCondition(key="date", match=MatchText(text="Unknown")),
                FieldCondition(key="location", match=MatchText(text="Unknown")),
                FieldCondition(key="location", match=MatchText(text="위치정보없음")),
                FieldCondition(key="people", match=MatchValue(value="Unknown Person")),
                FieldCondition(key="people", match=MatchValue(value="Unknown People"))
            ]
        ),
        limit=500,
        with_payload=True,
        with_vectors=False
    )
    
    import random
    random.shuffle(unknowns)
    candidates = []
    for raw_target in unknowns:
        p = raw_target.payload or {}
        loc = p.get("location", "")
        date_val = p.get("date", "")
        people_val = p.get("people", [])
        
        issues = []
        if "Unknown" in date_val or not date_val: issues.append("Date")
        if "위치정보없음" in loc or "Unknown" in loc or not loc: issues.append("Location")
            
        has_unknown_person = False
        for person in people_val:
            if person in ["Unknown Person", "Unknown People"]:
                has_unknown_person = True
                break
        if has_unknown_person: issues.append("People")
            
        if issues:
            candidates.append({"raw": raw_target, "issue": random.choice(issues)})
        
        if len(candidates) >= 50:
            break

    best_score = -1
    best_cand = None
    scores = []
    
    for cand in candidates:
        target_id = cand["raw"].id
        fb_type = "face" if cand["issue"] in ["Person", "People"] else "scene"
        cutoff = 0.80 if fb_type == "face" else 0.83
        
        try:
            rec_res = qdrant_client.query_points(
                collection_name="gumaphoto_hybrid_kr",
                query=target_id,
                using=fb_type,
                limit=100,
                with_payload=True
            ).points
            
            match_count = 0
            for h in rec_res:
                if getattr(h, "score", 0.0) < cutoff: continue
                hp = h.payload or {}
                if fb_type != "face":
                    if "Location" in cand["issue"]:
                        loc2 = hp.get("location", "")
                        if "Unknown" not in loc2 and "위치정보없음" not in loc2 and loc2.strip() != "": continue
                    elif "Date" in cand["issue"]:
                        dt2 = hp.get("date", "")
                        if "Unknown" not in dt2 and not dt2.endswith("-Unknown"): continue
                else:
                    p_people = hp.get("people", [])
                    if p_people and "Unknown Person" not in p_people and "Unknown People" not in p_people: continue
                match_count += 1
            scores.append(match_count)
            if match_count > best_score:
                best_score = match_count
                best_cand = cand
        except Exception as e:
            pass

    print("Scores out of 50 candidates:", sorted(scores, reverse=True))
    if best_cand:
        print("Best match count:", best_score, "Issue:", best_cand['issue'])

run_test()
