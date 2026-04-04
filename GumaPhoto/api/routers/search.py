from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, List
from core.state import state
import json
import os
import re
import torch
from qdrant_client.http.models import Filter, FieldCondition, MatchText, MatchAny, MatchValue, OrderBy, Direction, GeoRadius, GeoPoint, Range, ValuesCount

router = APIRouter()

import json
import hashlib
import os

_IMAGE_META_CACHE_FILE = "/app/data/image_meta_cache.json"
try:
    if os.path.exists(_IMAGE_META_CACHE_FILE):
        with open(_IMAGE_META_CACHE_FILE, "r") as f:
            _IMAGE_META_CACHE = json.load(f)
    else:
        _IMAGE_META_CACHE = {}
except Exception:
    _IMAGE_META_CACHE = {}

def _get_auto_cache_version():
    try:
        # 이 파일(search.py)의 내용이 한 글자라도 바뀌면 해시값이 자동으로 바뀝니다.
        with open(__file__, 'rb') as f:
            return "v_" + hashlib.md5(f.read()).hexdigest()[:8]
    except Exception:
        return "v_auto"

_NLP_CACHE = {}
_NLP_CACHE_VERSION = _get_auto_cache_version() # 사람이 까먹어도 파일이 수정되면 즉시 캐시 무효화

@router.post("/clear_nlp_cache")
def clear_nlp_cache():
    _NLP_CACHE.clear()
    return {"status": "success", "message": "NLP 쿼리 캐시가 초기화되었습니다."}

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
                            # [FIX] 캐시 반환 시에도 인메모리 해상도 사이즈 정보 강제 병합
                            cache_updated = False
                            for res in sliced:
                                if "width" in res and "height" in res and res["width"] > 0:
                                    continue
                                
                                orig_path = res.get("original_path", "")
                                if orig_path in _IMAGE_META_CACHE:
                                    w, h, sz = _IMAGE_META_CACHE[orig_path]
                                else:
                                    try:
                                        from PIL import Image
                                        from pillow_heif import register_heif_opener
                                        register_heif_opener()
                                        with Image.open(orig_path) as img:
                                            w, h = img.size
                                        sz = os.path.getsize(orig_path)
                                        _IMAGE_META_CACHE[orig_path] = [w, h, sz]
                                        cache_updated = True
                                    except Exception:
                                        w, h, sz = 800, 800, 0
                                res["width"] = w
                                res["height"] = h
                                res["file_size_bytes"] = sz
                            
                            if cache_updated:
                                try:
                                    with open(_IMAGE_META_CACHE_FILE, "w") as f:
                                        json.dump(_IMAGE_META_CACHE, f)
                                except Exception as e:
                                    print(f"[-] Image Meta Cache 영구 저장 실패: {e}")
                                    
                            return {"results": sliced}
        except Exception as e:
            print(f"[-] File Cache Load Error: {e}")
    
    # 0. One-Shot Smart NLP Extraction (Hybrid Local Stripping + Gemini)
    extracted_years = []
    extracted_names = []
    extracted_locations = []
    extracted_seasons = []
    extracted_times = []
    known_locs_str = ""
    
    if search_text and state.gemini_client:
        import pickle, datetime
        
        known_names_list = []
        if os.path.exists('/app/data/known_faces.pkl'):
            try:
                with open('/app/data/known_faces.pkl', 'rb') as f:
                    known_names_list = list(pickle.load(f).keys())
            except Exception:
                pass
                
        # --- 1차: Local 파싱 (인물, 연도 분리) ---
        local_years = []
        local_people = []
        remaining_words = []
        
        for word in search_text.split():
            # 1. 연도 추출 (정규식 기반)
            y_match = re.search(r'^(20\d{2})년?$', word)
            if y_match:
                local_years.append(int(y_match.group(1)))
                continue
                
            # 2. 인물 추출 (이름으로 시작하는 단어 - 예: '준우가', '송이랑')
            matched = False
            for kn in known_names_list:
                if word.startswith(kn):
                    local_people.append(kn)
                    matched = True
                    break
            if matched:
                continue
                
            remaining_words.append(word)
            
        # 사람과 연도가 싹 떨어져 나간 순수 나머지 문장 (이것을 캐시 키로 씁니다!)
        visual_query_key = " ".join(remaining_words).strip()
        
        if not visual_query_key:
            # 남은 검색어가 없으면 (예: "준우 2023년") 즉시 반환! API를 호출할 필요가 없음.
            extracted_years = local_years
            extracted_names = local_people
            search_text = ""
            print(f"[*] ⚡ NLP 0-ms Direct Hit: Years={extracted_years}, People={extracted_names}, Visual='EMPTY'")
        else:
            # 캐시 확인
            cache_key = f"{_NLP_CACHE_VERSION}_{visual_query_key}"
            if cache_key in _NLP_CACHE:
                parsed = _NLP_CACHE[cache_key]
                
                # 병합: 로컬에서 찾은 것 + 캐시에서 꺼낸 것
                extracted_years = list(set(local_years + parsed.get("years", [])))
                extracted_names = list(set(local_people + parsed.get("people", [])))
                extracted_locations = parsed.get("locations", [])
                visual_remainder = parsed.get("visual", "EMPTY")
                
                if visual_remainder.upper() != "EMPTY":
                    search_text = visual_remainder.strip()
                else:
                    search_text = ""
                    
                print(f"[*] ⚡ NLP Component Cache Hit: '{visual_query_key}' -> Years={extracted_years}, People={extracted_names}, Locs={extracted_locations}, Visual='{search_text}'")
            else:
                try:
                    current_year = datetime.datetime.now().year
                    known_names_str = ", ".join(known_names_list)
                    
                    if os.path.exists("/app/data/available_tags.json"):
                        with open("/app/data/available_tags.json", "r", encoding="utf-8") as fm:
                            tag_data = json.load(fm)
                            locs = tag_data.get("locations", [])
                            known_locs_str = ", ".join(locs)
                    
                    # Gemini에게 남은 문장(visual_query_key)에 대해서만 분석 지시!
                    prompt = f"""You are a Photo Search Query Parser.
Current Year: {current_year}
Known People in DB: [{known_names_str}]
Known Locations in DB: [{known_locs_str}]

User Query: "{visual_query_key}"

Parse the query into EXACTLY this JSON structure:
{{
  "years": [], // list of integers, e.g., 2025. convert "작년" to {current_year - 1}. If none, []
  "people": [], // list of names exactly matching the Known People list. Fix misspellings if obvious. If none, []
  "locations": [ // If a broad region ("전라도", "강원도", "제주도", "유럽") is queried, DO NOT output a massive single location. Instead, output MULTIPLE specific locations corresponding to actual cities/districts strictly derived from 'Known Locations in DB'. (e.g. for "강원도", select ["대한민국-강릉시", "대한민국-속초시", "대한민국-춘천시", "대한민국-삼척시"] if they exist in the DB list)
    {{
      "lat": 37.7518,
      "lon": 128.876,
      "radius": 20000,    // Provide small 20km radius. NEVER exceed 30000 (30km).
      "matched_word": "강릉", // The strict substring from the user query
      "official_name": "강릉시", // Official administrative name
      "db_exact_locations": ["대한민국-강릉시"] // MANDATORY: Select all matching locations STRICTLY from 'Known Locations in DB'. Do not make up regions like '대한민국-강원도' if they are not in the list.
    }}
  ], // If none, []
  "seasons": [], // Extract mentioned seasons exactly matching ["봄", "여름", "가을", "겨울"]. If none, []
  "time_of_days": [], // Extract mentioned times exactly matching ["아침", "낮", "오후", "저녁", "밤", "심야"]. If none, []
  "visual": "EMPTY" // Translate all visual/abstract concepts (including seasons/times) into concise English keywords. For "겨울", output "winter, snow, cold, frozen". For "밤", output "night, dark, streetlights". DO NOT include people/locations. If none, "EMPTY".
}}
Output ONLY valid JSON without markup.
"""
                    t_resp = state.gemini_client.models.generate_content(model='gemini-3.1-flash-lite-preview', contents=prompt)
                    resp_text = t_resp.text.strip()
                    if resp_text.startswith("```json"): resp_text = resp_text[7:-3].strip()
                    elif resp_text.startswith("```"): resp_text = resp_text[3:-3].strip()
                    
                    parsed = json.loads(resp_text)
                    
                    # 혹시 모를 AI 환각 방지 레이어
                    raw_extracted_names = parsed.get("people", [])
                    clean_names = []
                    for name in raw_extracted_names:
                        base_name = name.split('_')[0] if '_' in name else name
                        if base_name in known_names_list and base_name not in clean_names:
                            clean_names.append(base_name)
                    parsed["people"] = clean_names 
                    
                    # '나머지 문장' 자체를 캐시 (다른 인물이 같은 행동을 검색할 때 100% 재활용)
                    _NLP_CACHE[cache_key] = parsed
                    
                    # 최종 병합
                    extracted_years = list(set(local_years + parsed.get("years", [])))
                    extracted_names = list(set(local_people + parsed.get("people", [])))
                    extracted_locations = parsed.get("locations", [])
                    extracted_seasons = parsed.get("seasons", [])
                    extracted_times = parsed.get("time_of_days", [])
                    visual_remainder = parsed.get("visual", "EMPTY")
                    
                    if visual_remainder.upper() != "EMPTY":
                        search_text = visual_remainder.strip()
                    else:
                        search_text = ""
                        
                    print(f"[*] 🧠 Smart NLP Extraction (Partial): '{visual_query_key}' -> Years={extracted_years}, People={extracted_names}, Locs={extracted_locations}, Visual='{search_text}'")
                except Exception as ge:
                    print(f"[-] Smart NLP matching error: {ge}")

    # UI 선택 이름 병합
    final_people = list(set(req.people + extracted_names))
    
    # 1. 쿼리가 없을 경우 (Home 화면 진입 시) -> 단순 필터 + 스크롤 검색
    direct = Direction.ASC if req.sort == "asc" else Direction.DESC
    must_conds = []
    
    # 필터 구성 (UI에서 날아온 location, date 및 동적 people)
    if final_people:
        for p_name in final_people:
            must_conds.append(FieldCondition(key="people", match=MatchValue(value=p_name)))
            
    # [V2] 다중 중심점(Multi-Centroid) GPS 및 정확한 텍스트 매칭 OR(Should) 융합
    if extracted_locations:
        loc_shoulds = []
        for loc_obj in extracted_locations:
            try:
                if isinstance(loc_obj, dict):
                    db_exact_locations = loc_obj.get("db_exact_locations", [])
                    has_exact = False
                    
                    if isinstance(db_exact_locations, list) and len(db_exact_locations) > 0:
                        has_exact = True
                        for db_loc in db_exact_locations:
                            loc_shoulds.append(FieldCondition(key="location", match=MatchText(text=db_loc)))
                    
                    # DB 정답 장소가 파악됐다면, 20km 반경(GeoRadius)이나 모호한 이름 매칭을 전면 배제하여 칼같은 정확도 보장
                    if not has_exact:
                        if "lat" in loc_obj and "lon" in loc_obj:
                            loc_shoulds.append(
                                FieldCondition(
                                    key="geo_point",
                                    geo_radius=GeoRadius(
                                        center=GeoPoint(lat=float(loc_obj["lat"]), lon=float(loc_obj["lon"])),
                                        radius=min(float(loc_obj.get("radius", 20000)), 35000)
                                    )
                                )
                            )
                        
                        matched_word = loc_obj.get("matched_word", "")
                        official_name = loc_obj.get("official_name", "")
                        
                        if matched_word:
                            loc_shoulds.append(FieldCondition(key="location", match=MatchText(text=matched_word)))
                        if official_name:
                            loc_shoulds.append(FieldCondition(key="location", match=MatchText(text=official_name)))
            except Exception as e:
                print(f"[-] GeoRadius 파싱 에러: {e}")
                
        if loc_shoulds:
            must_conds.append(Filter(should=loc_shoulds))
            
    # UI 명시적 텍스트 Location 필터 병합
    if req.location and req.location != "All Locations":
        must_conds.append(FieldCondition(key="location", match=MatchText(text=req.location)))
            
    if extracted_years:
        if len(extracted_years) == 1:
            must_conds.append(FieldCondition(key="sort_date", range=Range(gte=int(extracted_years[0])*10000, lte=int(extracted_years[0])*10000 + 1231)))
        else:
            y_shoulds = [FieldCondition(key="sort_date", range=Range(gte=int(y)*10000, lte=int(y)*10000 + 1231)) for y in extracted_years]
            must_conds.append(Filter(should=y_shoulds))
            
    if req.date and req.date != "All Dates":
        must_conds.append(FieldCondition(key="date", match=MatchValue(value=req.date)))
        
    # === 단독 인물 우선 배치 (Pagination 보존) 로직 ===
    exact_filter = None
    group_filter = None
    if final_people:
        # DB에 저장된 people 배열의 길이를 측정하여 초고속 O(1) 단독/합사 분기 수행
        val_count_cond = FieldCondition(key="people", values_count=ValuesCount(gt=len(final_people)))
        
        # 단독 사진: final_people이 모두 포함되어 있고, 그 외 인물은 없음 (배열 길이 <= len(final_people))
        exact_filter = Filter(must=list(must_conds), must_not=[val_count_cond])
        
        # 합사 사진: final_people이 모두 포함되어 있고, 최소 1명 이상의 다른 인물이 더 있음 (배열 길이 > len(final_people))
        g_musts = list(must_conds)
        g_musts.append(val_count_cond)
        group_filter = Filter(must=g_musts)
    else:
        exact_filter = Filter(must=must_conds) if must_conds else None
        
    print(f"[*] EXACT_FILTER DUMP: {exact_filter}")
        
    q_filter = Filter(must=must_conds) if must_conds else None

    total_hits_count = 0
    try:
        if group_filter is not None:
            c1 = state.qdrant_client.count(collection_name="gumaphoto_hybrid_kr", count_filter=exact_filter, exact=True).count
            c2 = state.qdrant_client.count(collection_name="gumaphoto_hybrid_kr", count_filter=group_filter, exact=True).count
            total_hits_count = c1 + c2
        else:
            total_hits_count = state.qdrant_client.count(collection_name="gumaphoto_hybrid_kr", count_filter=exact_filter, exact=True).count
    except Exception as e:
        print("[-] Count error:", e)

    if not search_text:
        try:
            if group_filter is not None:
                res_exact, _ = state.qdrant_client.scroll(
                    collection_name="gumaphoto_hybrid_kr", scroll_filter=exact_filter, limit=req.offset + req.limit, with_payload=True, order_by=OrderBy(key="sort_date", direction=direct)
                )
                res_group, _ = state.qdrant_client.scroll(
                    collection_name="gumaphoto_hybrid_kr", scroll_filter=group_filter, limit=req.offset + req.limit, with_payload=True, order_by=OrderBy(key="sort_date", direction=direct)
                )
                res_scroll = res_exact + res_group
            else:
                res_scroll, _ = state.qdrant_client.scroll(
                    collection_name="gumaphoto_hybrid_kr", scroll_filter=exact_filter, limit=req.offset + req.limit, with_payload=True, order_by=OrderBy(key="sort_date", direction=direct)
                )
            
            raw_results = res_scroll[req.offset:req.offset+req.limit]
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
            # 사용자가 강제한 필터 내역(장소, 인물 등)이 있음에도 0건일 시 억지로 제약을 푸는 현상을 방지합니다.
            # _IMAGE_META_CACHE 를 통해 프론트엔드 Masonry UI에서 박스가 깨지지 않도록 메타데이터를 직접 주입해 리턴.
            cache_updated = False
            for res in formatted_results:
                orig_path = res.get("original_path", "")
                if orig_path in _IMAGE_META_CACHE:
                    w, h, sz = _IMAGE_META_CACHE[orig_path]
                else:
                    try:
                        from PIL import Image
                        with Image.open(orig_path) as img:
                            w, h = img.size
                        sz = os.path.getsize(orig_path)
                        _IMAGE_META_CACHE[orig_path] = [w, h, sz]
                        cache_updated = True
                    except Exception:
                        w, h, sz = 800, 800, 0
                res["width"] = w
                res["height"] = h
                res["file_size_bytes"] = sz
                
            if cache_updated:
                try:
                    with open(_IMAGE_META_CACHE_FILE, "w") as f:
                        json.dump(_IMAGE_META_CACHE, f)
                except Exception as e:
                    print(f"[-] Image Meta Cache 영구 저장 실패: {e}")
            
            print(f"✅ 엄격한 하드 필터 검색 완료: {len(formatted_results)}건 반환 / 총 {total_hits_count}건")
            return {"results": formatted_results, "total_hits": total_hits_count}
        except Exception as e:
            print(f"❌ 스크롤 데이터 로딩 에러: {e}")
            return {"results": [], "error": str(e)}


    try:
        from qdrant_client.http.models import Prefetch, FusionQuery, Fusion
        
        with torch.no_grad():
            inputs = state.siglip_processor(text=[search_text], padding="max_length", return_tensors="pt")
            inputs = {k: v.to(state.siglip_model.device) for k, v in inputs.items()}
            text_features = state.siglip_model.get_text_features(**inputs)
            # norm normalization
            text_features = text_features / text_features.norm(p=2, dim=-1, keepdim=True)
            text_vector = text_features[0].cpu().numpy().tolist()
        
        # [V2] RRF 기반 듀얼 라우팅 세팅 (계절/시간대 메타데이터 병합)
        use_rrf = bool(extracted_seasons or extracted_times)
        
        def execute_qdrant_query(q_filter):
            if use_rrf:
                metadata_shoulds = []
                if extracted_seasons:
                    metadata_shoulds.extend([FieldCondition(key="season", match=MatchValue(value=s)) for s in extracted_seasons])
                if extracted_times:
                    metadata_shoulds.extend([FieldCondition(key="time_of_day", match=MatchValue(value=t)) for t in extracted_times])
                    
                meta_must = []
                if q_filter and q_filter.must:
                    meta_must.extend(q_filter.must)
                
                metadata_filter = Filter(must=meta_must, should=metadata_shoulds, must_not=q_filter.must_not if q_filter else None)
                
                # Prefetch 2개를 묶어 RRF Fusion
                return state.qdrant_client.query_points(
                    collection_name="gumaphoto_hybrid_kr",
                    prefetch=[
                        Prefetch(query=text_vector, using="scene", filter=q_filter, limit=req.offset + req.limit),
                        Prefetch(query=metadata_filter, limit=req.offset + req.limit)
                    ],
                    query=FusionQuery(fusion=Fusion.RRF),
                    limit=req.offset + req.limit,
                    offset=0,
                    with_payload=True
                ).points
            else:
                return state.qdrant_client.query_points(
                    collection_name="gumaphoto_hybrid_kr", 
                    query=text_vector, 
                    using="scene", 
                    query_filter=q_filter, 
                    limit=req.offset + req.limit, 
                    offset=0, 
                    with_payload=True
                ).points
                
        if group_filter is not None:
            results_exact = execute_qdrant_query(exact_filter)
            results_group = execute_qdrant_query(group_filter)
            results = results_exact + results_group
        else:
            results = execute_qdrant_query(exact_filter)
            
        raw_results = results[req.offset:req.offset+req.limit]
        
        # 만약 SigLIP 검색 결과가 부족하다면 Fallback Text 샷
        if not raw_results and req.offset == 0:
            print("[*] SigLIP 임달 미달. Fallback: 메타데이터 역추적 검색 가동...")
            fallback_must = []
            if must_conds: fallback_must.extend(must_conds)
            
            fallback_shoulds = [
                FieldCondition(key="caption", match=MatchText(text=search_text)),
                FieldCondition(key="location", match=MatchText(text=search_text)),
                FieldCondition(key="people", match=MatchText(text=search_text)),
                FieldCondition(key="objects", match=MatchText(text=search_text)),
                FieldCondition(key="emotion", match=MatchText(text=search_text))
            ]
            
            if group_filter is not None:
                exact_fallback = Filter(must=exact_filter.must, must_not=exact_filter.must_not, should=fallback_shoulds)
                group_fallback = Filter(must=group_filter.must, must_not=group_filter.must_not, should=fallback_shoulds)
                
                res_exact, _ = state.qdrant_client.scroll(collection_name="gumaphoto_hybrid_kr", scroll_filter=exact_fallback, limit=req.offset + req.limit, with_payload=True)
                res_group, _ = state.qdrant_client.scroll(collection_name="gumaphoto_hybrid_kr", scroll_filter=group_fallback, limit=req.offset + req.limit, with_payload=True)
                res_scroll = res_exact + res_group
            else:
                exact_fallback = Filter(must=exact_filter.must, must_not=exact_filter.must_not, should=fallback_shoulds) if exact_filter else Filter(should=fallback_shoulds)
                res_scroll, _ = state.qdrant_client.scroll(collection_name="gumaphoto_hybrid_kr", scroll_filter=exact_fallback, limit=req.offset + req.limit, with_payload=True)
                
            raw_results = res_scroll[req.offset:req.offset+req.limit]
            
        # 3. 모든 필터 조건 검색이 실패한 경우 최후의 보루 (순수 벡터 검색으로 롤백)
        # -> 사용자 의도(지역/인물)를 훼손하면서 엉뚱한 결과를 뱉는 강제 해제 롤백 기능을 제거했습니다.
        if not raw_results and req.offset == 0 and must_conds:
            print("[*] ⚠️ 1/2차 필터 매칭 결과 완전 0건. 사용자 지정 필터를 존중하여 순수 AI 롤백을 생략합니다.")

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
                "face_bbox": payload.get("face_bbox", None),
                "doc_id": hit.id
            })

        # --------------------------------------------------------------------------
        # [신규 아키텍처] Qdrant 단일화로 인해 SQLite를 거치지 않고, 
        # 디스크의 원본 이미지(PIL) 헤더를 직접 읽되, In-Memory Cache를 적용하여
        # 파일별로 1회만 디스크를 읽고, 이후에는 0ms 단위의 초고속 반환을 달성합니다.
        # --------------------------------------------------------------------------
        for res in formatted_results:
            orig_path = res.get("original_path", "")
            if orig_path in _IMAGE_META_CACHE:
                w, h, sz = _IMAGE_META_CACHE[orig_path]
            else:
                try:
                    from PIL import Image
                    with Image.open(orig_path) as img:
                        w, h = img.size
                    sz = os.path.getsize(orig_path)
                    _IMAGE_META_CACHE[orig_path] = (w, h, sz)
                except Exception:
                    w, h, sz = 800, 800, 0
            res["width"] = w
            res["height"] = h
            res["file_size_bytes"] = sz
                
        print(f"✅ AI 복합 검색 완료: {len(formatted_results)}건 반환 / 총 {total_hits_count}건 타겟팅")
        return {
            "results": formatted_results,
            "total_hits": total_hits_count,
            "people_detected": extracted_names,
            "location_detected": known_locs_str if final_people else (extracted_locations[0].get("matched_word", "") if extracted_locations else ""),
            "enhanced_query": search_text,
            "fallback_triggered": fallback_must is not None if 'fallback_must' in locals() else False
        }

    except Exception as e:
        import traceback
        print(f"❌ 검색 중 치명적 오류 발생:\n{traceback.format_exc()}")
        return {"error": str(e), "results": []}

@router.get("/api/filters")
async def get_filters():
    locations = []
    dates = []
    try:
        if os.path.exists("/app/data/available_tags.json"):
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

@router.get("/api/family_tags")
async def get_family_tags():
    """
    사용자의 'Guma Family' 모든 태그에 대한 캐시를 1번의 가벼운 요청(태그 당 20장)으로 
    프론트엔드에 한방에 쏴주는 궁극의 최적화 라우트입니다.
    """
    cache_path = "/app/data/caches/timeline_cache.json"
    result = {}
    try:
        if os.path.exists(cache_path):
            with open(cache_path, "r", encoding="utf-8") as f:
                t_cache = json.load(f)
            # 프론트엔드가 요구하는 5개의 메인 태그
            tags = ["recent", "성욱", "준우", "지우", "송이"]
            for tag in tags:
                if tag in t_cache:
                    cached_list = t_cache[tag]
                    result[tag] = {
                        "results": cached_list[:20], # UI 부하 방지를 위해 초기 로딩은 20장만
                        "offset": 20,
                        "totalHits": len(cached_list),
                        "hasMore": len(cached_list) > 20
                    }
    except Exception as e:
        print(f"[-] Family tags cache load error: {e}")
    return result

@router.get("/api/system/indexer-log")
def get_indexer_log():
    try:
        import redis
        import os
        r = redis.Redis.from_url(os.getenv("REDIS_URL", "redis://redis:6379/0"), decode_responses=True)
        logs = r.lrange("gumaphoto_logs_history", 0, -1)
        if not logs:
            return {"log": "System Active. Waiting for background logs..."}
        return {"log": "\\n".join(logs[-25:])}
    except Exception as e:
        return {"log": f"Error reading Redis unified logs: {str(e)}"}
