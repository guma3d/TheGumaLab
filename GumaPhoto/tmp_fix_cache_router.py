import re

path = r'd:\TheGumaLab\GumaPhoto\api\routers\feedback.py'
with open(path, 'r', encoding='utf-8') as f:
    code = f.read()

# 기존 복잡한 실시간 검색 로직 전체를 캐시 서비스 연결로 대체
target = r'@router\.get\("/api/feedback_v2/unknown"\).*?return \{"id": None, "message": "No photos require feedback at this time\."\}'

replacement = """@router.get("/api/feedback_v2/unknown")
async def get_unknown_photo():
    if not state.qdrant_client: return {"error": "Qdrant not loaded"}
    
    from api.services.feedback_cache import feedback_cache
    
    try:
        best_candidate = feedback_cache.pop_best()
        
        if best_candidate:
            p = best_candidate["raw"].payload or {}
            url_path = p.get("filepath", "").replace("/app/data/organized", "/photos")
            return {
                "id": best_candidate["raw"].id,
                "url": url_path,
                "issue": best_candidate["issue"],
                "date": p.get("date", ""),
                "location": p.get("location", ""),
                "people": p.get("people", []),
                "face_bbox": p.get("face_bbox", None)
            }
            
        # 캐시가 구축 중이거나 비어있을 경우 Fallback
        return {"id": None, "message": "Cache is building or empty. Please wait a moment."}
        
    except Exception as e:
        print(f"❌ Feedback Cache Fetch Error: {e}")
        return {"id": None, "message": "No photos require feedback at this time."}"""

code = re.sub(target, replacement, code, flags=re.DOTALL)

with open(path, 'w', encoding='utf-8') as f:
    f.write(code)

print("Router updated correctly.")
