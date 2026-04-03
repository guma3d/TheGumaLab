from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, List
from core.state import state
import json
import os
import re
import torch
from qdrant_client.http.models import Filter, FieldCondition, MatchText, MatchAny, MatchValue, OrderBy, Direction, GeoRadius, GeoPoint, Range

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
        
    try:
        if not state.qdrant_client.collection_exists("gumaphoto_hybrid_kr"):
            return {"results": [], "error": "잠시만요! 딥러닝 벡터 DB의 기초 뼈대를 구축 중입니다. 조금 뒤에 툴을 새로고침 해주세요!"}
    except Exception as e:
        return {"results": [], "error": "잠시만요! 딥러닝 벡터 DB의 기초 뼈대를 구축 중입니다. 조금 뒤에 툴을 새로고침 해주세요!"}
        
    search_text = req.query.strip()
    
    # [수정] 프론트엔드 UI의 기본 진입점 쿼리 정규화
    # 테마용 쿼리(theme_dummy)는 req.scene에 영문 검색어가 들어있으므로 이를 채택합니다.
    if search_text == "theme_dummy" and req.scene:
        search_text = req.scene.strip()
    elif search_text in ["timeline_dummy", "tag_dummy", "theme_dummy"]:
        search_text = ""
        
    # 테마와 완전히 동일한 파이프라인 구조(Static JSON Cache)로 타임라인 500장 검색
    is_timeline = (not req.query.strip() and not req.scene and not req.location and not req.date) or (req.query in ["timeline_dummy", "tag_dummy"])
    if is_timeline and req.offset < 500:
        try:
            cache_path = "/app/data/caches/timeline_cache.json"
            if os.path.exists(cache_path):
                import json
                with open(cache_path, "r", encoding="utf-8") as f:
                    t_cache = json.load(f)
                
                target_key = "recent"
                if req.people and len(req.people) > 0:
                    target_key = req.people[0]
                    
                if target_key in t_cache:
                    cached_list = t_cache[target_key]
                    if cached_list and len(cached_list) > req.offset:
                        end_idx = min(req.offset + req.limit, 500)
                        sliced = cached_list[req.offset : end_idx]
                        if sliced:
                            print(f"🚀 [Baking Cache Hit] Guma Family 통합 아키텍처 JSON 반환: {target_key} ({req.offset}~{end_idx}장)")
                            return {"results": sliced}
        except Exception as e:
            print(f"[-] File Cache Load Error: {e}")
    
    # 0. One-Shot Smart NLP Extraction (Gemini)
    extracted_years = []
    extracted_names = []
    extracted_locations = []
    
    if search_text and state.gemini_client:
        try:
            import datetime, re, json, pickle
            current_year = datetime.datetime.now().year
            
            known_names_str = ""
            if os.path.exists('/app/data/known_faces.pkl'):
                with open('/app/data/known_faces.pkl', 'rb') as f:
                    known_names_str = ", ".join(list(pickle.load(f).keys()))
            
            prompt = f"""You are a Photo Search Query Parser.
Current Year: {current_year}
Known People in DB: [{known_names_str}]

User Query: "{search_text}"

Parse the query into EXACTLY this JSON structure:
{{
  "years": [], // list of integers, e.g., 2025. convert "작년" to {current_year - 1}. If none, []
  "people": [], // list of names exactly matching the Known People list. Fix misspellings if obvious. If none, []
  "locations": [], // list of strings for ANY specific geographic place. Extract EXACT TEXT for full-text search. e.g., "하와이", "제주도". If none, []
  "visual": "EMPTY" // Translate all remaining visual/abstract concepts to a concise English phrase. DO NOT include the extracted years, people, or locations. e.g. "수영하는" -> "swimming". If no visual meaning remains, output "EMPTY".
}}
Output ONLY valid JSON without markup.
"""
            t_resp = state.gemini_client.models.generate_content(model='gemini-3.1-flash-lite-preview', contents=prompt)
            resp_text = t_resp.text.strip()
            if resp_text.startswith("```json"): resp_text = resp_text[7:-3].strip()
            elif resp_text.startswith("```"): resp_text = resp_text[3:-3].strip()
            
            parsed = json.loads(resp_text)
            extracted_years = parsed.get("years", [])
            extracted_names = parsed.get("people", [])
            extracted_locations = parsed.get("locations", [])
            visual_remainder = parsed.get("visual", "EMPTY")
            
            if visual_remainder.upper() != "EMPTY":
                search_text = visual_remainder.strip()
            else:
                search_text = ""
                
            print(f"[*] 🧠 Smart NLP Extraction: Years={extracted_years}, People={extracted_names}, Locs={extracted_locations}, Visual='{search_text}'")
        except Exception as ge:
            print(f"[-] Smart NLP matching error: {ge}")

    # UI 선택 이름 병합
    final_people = list(set(req.people + extracted_names))
    
    # UI 선택 장소 병합
    final_locations = list(set([loc for loc in extracted_locations if loc.strip()]))
    if req.location and req.location != "All Locations":
        final_locations.append(req.location)
    
    # 1. 쿼리가 없을 경우 (Home 화면 진입 시) -> 단순 필터 + 스크롤 검색
    direct = Direction.ASC if req.sort == "asc" else Direction.DESC
    must_conds = []
    
    # 필터 구성 (UI에서 날아온 location, date 및 동적 people)
    if final_people:
        for p_name in final_people:
            must_conds.append(FieldCondition(key="people", match=MatchValue(value=p_name)))
            
    if final_locations:
        if len(final_locations) == 1:
            must_conds.append(FieldCondition(key="location", match=MatchText(text=final_locations[0])))
        else:
            loc_shoulds = [FieldCondition(key="location", match=MatchText(text=loc)) for loc in final_locations]
            must_conds.append(Filter(should=loc_shoulds))
            
    if extracted_years:
        if len(extracted_years) == 1:
            must_conds.append(FieldCondition(key="sort_date", range=Range(gte=int(extracted_years[0])*10000, lte=int(extracted_years[0])*10000 + 1231)))
        else:
            y_shoulds = [FieldCondition(key="sort_date", range=Range(gte=int(y)*10000, lte=int(y)*10000 + 1231)) for y in extracted_years]
            must_conds.append(Filter(should=y_shoulds))
            
    if req.date and req.date != "All Dates":
        must_conds.append(FieldCondition(key="date", match=MatchValue(value=req.date)))
        
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
                payload = getattr(hit, 'payload', {}) or {}
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
            if len(formatted_results) > 0 or not req.search.strip():
                print(f"✅ 일반 스크롤 로딩 완료: {len(formatted_results)}건 반환 (쿼리 없음)")
                return {"results": formatted_results}
            else:
                print(f"[*] 하드 필터 검색 결과 없음(0건). 제약을 모두 풀고 원본 검색어로 순수 AI 검색으로 롤백합니다.")
                search_text = req.search.strip()
                q_filter = None
                must_conds = []
        except Exception as e:
            print(f"❌ 스크롤 데이터 로딩 에러: {e}")
            return {"results": [], "error": str(e)}


    try:
        with torch.no_grad():
            inputs = state.siglip_processor(text=[search_text], padding="max_length", return_tensors="pt")
            inputs = {k: v.to(state.siglip_model.device) for k, v in inputs.items()}
            text_features = state.siglip_model.get_text_features(**inputs)
            # norm normalization
            text_features = text_features / text_features.norm(p=2, dim=-1, keepdim=True)
            text_vector = text_features[0].cpu().numpy().tolist()
        
        results = state.qdrant_client.query_points(
            collection_name="gumaphoto_hybrid_kr",
            query=text_vector,
            using="scene",
            query_filter=q_filter,
            limit=req.offset + req.limit,
            offset=0,
            with_payload=True
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
            
        # 3. 모든 필터 조건 검색이 실패한 경우 최후의 보루 (순수 벡터 검색으로 롤백)
        if not raw_results and req.offset == 0 and must_conds:
            print("[*] ⚠️ 1/2차 필터 매칭 결과 완전 0건. 페이로드 필터를 강제 해제하고 순수 벡터 매칭만으로 컨텍스트 검색을 개시합니다.")
            
            # 원래 사용자가 적은 원본 문장 전체를 가져와서 완전 순수 벡터로 재가공
            pure_query = req.search.strip()
            if state.gemini_client and re.search(r'[가-힣]', pure_query):
                try:
                    p = f"Translate the core meaning of this Korean photo search query to brief English keywords: {pure_query}"
                    t_resp = state.gemini_client.models.generate_content(model='gemini-3.1-flash-lite-preview', contents=p)
                    pure_query = t_resp.text.strip().replace('\n', '')
                except:
                    pass
            
            try:
                with torch.no_grad():
                    inputs = state.siglip_processor(text=[pure_query], padding="max_length", return_tensors="pt")
                    inputs = {k: v.to(state.siglip_model.device) for k, v in inputs.items()}
                    t_feat = state.siglip_model.get_text_features(**inputs)
                    t_feat = t_feat / t_feat.norm(p=2, dim=-1, keepdim=True)
                    pure_vector = t_feat[0].cpu().numpy().tolist()
                    
                unres = state.qdrant_client.query_points(
                    collection_name="gumaphoto_hybrid_kr",
                    query=pure_vector,
                    using="scene",
                    query_filter=None,  # 필터 전면 개방
                    limit=req.offset + req.limit,
                    offset=0,
                    with_payload=True
                ).points
                raw_results = unres[req.offset:]
            except Exception as e:
                print(f"[-] 3차 순수 벡터 롤백 실패: {e}")

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

        # --------------------------------------------------------------------------
        # [신규 아키텍처] Qdrant 단일화로 인해 SQLite를 거치지 않고, 
        # 디스크의 원본 이미지(PIL) 헤더를 직접 읽어 해상도(width/height)를 주입합니다.
        # --------------------------------------------------------------------------
        for res in formatted_results:
            try:
                from PIL import Image
                with Image.open(res["original_path"]) as img:
                    w, h = img.size
            except Exception:
                w, h = 800, 800
            
            res["width"] = w
            res["height"] = h
            # 원본 파일 크기 주입 (SQLite bytes 테이블 대체)
            try:
                res["file_size_bytes"] = os.path.getsize(res["original_path"])
            except Exception:
                res["file_size_bytes"] = 0
                
        print(f"✅ 원본 파일 헤더 직접 파싱 성공! (총 결과 {len(formatted_results)}건 반환)")
        return {"results": formatted_results}

    except Exception as e:
        import traceback
        print(f"❌ 검색 중 치명적 오류 발생:\n{traceback.format_exc()}")
        return {"error": str(e), "results": []}

@router.get("/api/filters")
async def get_filters():
    import os
    locations = []
    dates = []
    try:
        if os.path.exists("/app/data/available_tags.json"):
            import json
            with open("/app/data/available_tags.json", "r", encoding="utf-8") as f:
                tag_data = json.load(f)
                locations = sorted(tag_data.get("locations", []))
                
                # [아키텍처 혁신 변경] 폴더/파일 구조 의존도를 100% 끊어냈으므로 
                # 날짜 버튼들도 오직 Qdrant에서 추출되어 캐시된 JSON(available_tags)에만 의존합니다!
                raw_dates = tag_data.get("dates", [])
                dates = sorted(raw_dates, reverse=True)
                
        # 동적 인물 명단 바인딩
        names = ["All Names"]
        if os.path.exists("/app/data/known_faces.pkl"):
            import pickle
            with open("/app/data/known_faces.pkl", "rb") as f:
                learned_faces = list(pickle.load(f).keys())
                names.extend(sorted(learned_faces))
        else:
            names.extend(["송이", "성욱", "준우", "지우"])
    except Exception as e:
        print(f"Filter fetch error: {e}")

    return {
        "dates": ["All Dates"] + dates,
        "locations": ["All Locations"] + locations,
        "names": names
    }

@router.get("/api/map/geojson")
def get_map_geojson():
    if not state.qdrant_client:
        return {"type": "FeatureCollection", "features": []}
        
    try:
        features = []
        offset = None
        
        while True:
            records, offset = state.qdrant_client.scroll(
                collection_name="gumaphoto_hybrid_kr",
                with_payload=["filepath", "geo_point", "date", "location", "people", "season", "time_of_day"],
                limit=5000,
                offset=offset
            )
            for hit in records:
                payload = getattr(hit, 'payload', {}) or {}
                geo = payload.get("geo_point")
                if geo and isinstance(geo, dict) and "lat" in geo and "lon" in geo:
                    filepath = payload.get("filepath", "")
                    photo_url = filepath.replace("/app/data/organized", "/photos")
                    features.append({
                        "type": "Feature",
                        "geometry": {
                            "type": "Point",
                            "coordinates": [float(geo["lon"]), float(geo["lat"])]
                        },
                        "properties": {
                            "id": hit.id,
                            "url": photo_url,
                            "date": payload.get("date", "1970:01:01 00:00:00"),
                            "location": payload.get("location", "Unknown Location"),
                            "people": payload.get("people", []),
                            "season": payload.get("season", "Unknown"),
                            "time_of_day": payload.get("time_of_day", "Unknown")
                        }
                    })
            if offset is None:
                break
                
        return {
            "type": "FeatureCollection",
            "features": features
        }
    except Exception as e:
        print(f"❌ GeoJSON 동적 생성 오류: {e}")
        return {"type": "FeatureCollection", "features": []}

import random
import os
import json

@router.get("/api/themes")
async def get_random_themes(limit: int = 9):
    cache_path = "/app/data/caches/themes_cache.json"
    
    # 1. 캐시 파일이 존재하면 초고속 베이킹된 테마 서빙
    if os.path.exists(cache_path):
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                all_cached_themes = json.load(f)
            
            if all_cached_themes and len(all_cached_themes) > 0:
                import re; import random
                # 50% 지역/로케이션 테마 추출 알고리즘 (기존 캐시 호환)
                def check_loc(t):
                    if t.get("is_location") is True: return True
                    # 한국어 타이틀이 포함되어 있으면 한국 지역 테마로 동적 판단
                    return bool(re.search(r'[가-힣]', t.get("title", "")))
                
                loc_pool = [t for t in all_cached_themes if check_loc(t)]
                oth_pool = [t for t in all_cached_themes if not check_loc(t)]
                
                # 목표 슬롯 계산 (정확히 50%) -> 9개 요청 시 5개(올림) 지역 할당
                loc_limit = min(len(loc_pool), (limit + 1) // 2)
                oth_limit = min(len(oth_pool), limit - loc_limit)
                
                # 나머지 테마 풀이 부족하다면 지역 테마로 남은 슬롯을 메꿈
                if loc_limit + oth_limit < limit:
                    loc_limit = min(len(loc_pool), limit - oth_limit)
                    
                selected = random.sample(loc_pool, loc_limit) + random.sample(oth_pool, oth_limit)
                random.shuffle(selected) # 교차로 잘 섞이도록 셔플
                
                return {"themes": selected}
        except Exception as e:
            print(f"[-] Theme cache load error: {e}")
            
    # 2. 캐시 파일이 만들어지기 전(최초 구동)에는 빈 배열 반환하여 UI 오류 방지
    # (실제 캐시는 새벽 3시나 인덱싱 완료 후 백그라운드 워커가 생성함)
    return {"themes": []}

import os
@router.get("/api/system/indexer-log")
def get_indexer_log():
    try:
        log_path = "/app/data/indexer_geo_log.txt"
        if os.path.exists(log_path):
            with open(log_path, "r", encoding="utf-8") as f:
                lines = f.read().splitlines()
                return {"log": "\\n".join(lines[-25:])}
        return {"log": "Log file not found."}
    except Exception as e:
        return {"log": f"Error reading log: {str(e)}"}
