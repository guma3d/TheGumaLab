from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, List
from core.state import state
import json
import os
import torch
from qdrant_client.http.models import Filter, FieldCondition, MatchText, MatchAny, OrderBy, Direction

router = APIRouter()

class SearchRequest(BaseModel):
    query: str = ""
    offset: int = 0
    limit: int = 50
    people: List[str] = []
    location: str = ""
    objects: List[str] = []
    scene: str = ""
    is_load_more: bool = False
    date: str = ""
    sort: str = "desc"

@router.post("/api/search")
async def perform_search(req: SearchRequest):
    print(f"\n[🔍 Search API] 요청 수신: 쿼리='{req.query}', offset={req.offset}, limit={req.limit}")
    
    if state.qdrant_client is None:
        return {"results": [], "error": "AI Database Not Initialized"}
        
    search_text = req.query.strip()
    
    # [수정] 프론트엔드 UI의 기본 진입점 쿼리 정규화
    # 테마용 쿼리(theme_dummy)는 req.scene에 영문 검색어가 들어있으므로 이를 채택합니다.
    if search_text == "theme_dummy" and req.scene:
        search_text = req.scene.strip()
    elif search_text in ["timeline_dummy", "tag_dummy", "theme_dummy"]:
        search_text = ""
    
    # 1. 쿼리가 없을 경우 (Home 화면 진입 시) -> 단순 필터 + 스크롤 검색
    direct = Direction.ASC if req.sort == "asc" else Direction.DESC
    must_conds = []
    
    # 필터 구성 (UI에서 날아온 location, date, people)
    if req.people:
        must_conds.append(FieldCondition(key="people", match=MatchAny(any=req.people)))
    if req.location and req.location != "All Locations":
        must_conds.append(FieldCondition(key="location", match=MatchText(text=req.location)))
    if req.date and req.date != "All Dates":
        must_conds.append(FieldCondition(key="date", match=MatchText(text=req.date)))
        
    q_filter = Filter(must=must_conds) if must_conds else None

    # 만약 자연어 텍스트 검색어가 아예 없다면 벡터 추출 없이 가볍게 스크롤링
    if not search_text:
        try:
            res_scroll, _ = state.qdrant_client.scroll(
                collection_name="gumaphoto_hybrid_kr",
                scroll_filter=q_filter,
                limit=req.offset + req.limit,
                with_payload=True,
                order_by=OrderBy(key="sort_date", direction=direct)
            )
            raw_results = res_scroll[req.offset:]
            formatted_results = []
            for hit in raw_results:
                payload = hit.payload or {}
                filepath = payload.get("filepath", "")
                if not filepath: continue
                photo_url = filepath.replace("/app/data/organized", "/photos")
                formatted_results.append({
                    "id": hit.id,
                    "score": 1.0,
                    "url": photo_url,
                    "original_path": filepath,
                    "date": payload.get("date", "Unknown"),
                    "location": payload.get("location", "Unknown Location"),
                    "people": payload.get("people", []),
                    "caption": payload.get("caption", ""),
                    "time_of_day": payload.get("time_of_day", "Unknown"),
                    "season": payload.get("season", "Unknown"),
                    "doc_id": hit.id
                })
            print(f"✅ 일반 스크롤 로딩 완료: {len(formatted_results)}건 반환 (쿼리 없음)")
            return {"results": formatted_results}
        except Exception as e:
            print(f"❌ 스크롤 데이터 로딩 에러: {e}")
            return {"results": [], "error": str(e)}

    # 2. 텍스트 검색어가 존재하는 경우 (AI 벡터 하이브리드 검색)
    try:
        with torch.no_grad():
            inputs = state.siglip_processor(text=[search_text], padding="max_length", return_tensors="pt")
            inputs = {k: v.to(state.siglip_model.device) for k, v in inputs.items()}
            text_features = state.siglip_model.get_text_features(**inputs)
            # norm normalization
            text_features = text_features / text_features.norm(p=2, dim=-1, keepdim=True)
            text_vector = text_features[0].cpu().numpy().tolist()
        
        # [수정] Attribute Error를 발생시키던 옛날 .search()를 버리고 최신 .query_points()로 복구
        results = state.qdrant_client.query_points(
            collection_name="gumaphoto_hybrid_kr",
            query=text_vector,
            using="scene",
            query_filter=q_filter,
            limit=req.offset + req.limit,
            offset=0,
            with_payload=True,
            score_threshold=0.20
        ).points
        raw_results = results[req.offset:]
        
        # 만약 SigLIP 검색 결과가 부족하다면 Fallback Text 샷
        if not raw_results and req.offset == 0:
            print("[*] SigLIP 임달 미달. Fallback: 메타데이터 역추적 검색 가동...")
            fallback_must = []
            if must_conds: fallback_must.extend(must_conds)
            
            fallback_filter = Filter(
                must=fallback_must,
                should=[
                    FieldCondition(key="caption", match=MatchText(text=search_text)),
                    FieldCondition(key="location", match=MatchText(text=search_text)),
                    FieldCondition(key="people", match=MatchText(text=search_text)),
                    FieldCondition(key="objects", match=MatchText(text=search_text)),
                    FieldCondition(key="emotion", match=MatchText(text=search_text))
                ]
            )
            res_scroll, _ = state.qdrant_client.scroll(
                collection_name="gumaphoto_hybrid_kr",
                scroll_filter=fallback_filter,
                limit=req.offset + req.limit,
                with_payload=True
            )
            raw_results = res_scroll[req.offset:]

        formatted_results = []
        for hit in raw_results:
            payload = getattr(hit, 'payload', {}) or {}
            score = getattr(hit, 'score', 1.0)
            filepath = payload.get("filepath", "")
            if not filepath: continue
                
            photo_url = filepath.replace("/app/data/organized", "/photos")
            formatted_results.append({
                "id": hit.id,
                "url": photo_url,
                "original_path": filepath,
                "score": score,
                "date": payload.get("date", "Unknown"),
                "location": payload.get("location", "Unknown Location"),
                "people": payload.get("people", []),
                "caption": payload.get("caption", ""),
                "time_of_day": payload.get("time_of_day", "Unknown"),
                "season": payload.get("season", "Unknown"),
                "doc_id": hit.id
            })

        print(f"✅ AI 검색 로딩 완료: {len(formatted_results)}건 반환")
        return {"results": formatted_results}

    except Exception as e:
        import traceback
        print(f"❌ 검색 중 치명적 오류 발생:\n{traceback.format_exc()}")
        return {"error": str(e), "results": []}

@router.get("/api/filters")
async def get_filters():
    import os, re
    locations = []
    dates = []
    try:
        if os.path.exists("/app/data/available_tags.json"):
            import json
            with open("/app/data/available_tags.json", "r", encoding="utf-8") as f:
                tag_data = json.load(f)
                locations = sorted(tag_data.get("locations", []))
                
        organized_dir = "/app/data/organized"
        if os.path.exists(organized_dir):
            for year_folder in os.listdir(organized_dir):
                year_path = os.path.join(organized_dir, year_folder)
                if os.path.isdir(year_path):
                    for tag_folder in os.listdir(year_path):
                        match = re.search(r'^(\d{4}-\d{2})_', tag_folder)
                        if match:
                            dates.append(match.group(1))
                            
        dates = sorted(list(set(dates)), reverse=True)
    except Exception as e:
        print(f"Filter fetch error: {e}")

    return {
        "dates": ["All Dates"] + dates,
        "locations": ["All Locations"] + locations,
        "names": ["All Names", "송이", "성욱", "준우", "지우"]
    }
