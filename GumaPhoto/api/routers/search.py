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

# [Family Profile] 가족 개인화 프로필 로드
_FAMILY_PROFILE = {}
_FAMILY_ALIASES = {}  # alias → member_key 역매핑
try:
    _fp_path = "/app/data/family_profile.json"
    if os.path.exists(_fp_path):
        with open(_fp_path, "r", encoding="utf-8") as f:
            _fp_data = json.load(f)
            _FAMILY_PROFILE = _fp_data.get("members", {})
            for key, member in _FAMILY_PROFILE.items():
                for alias in member.get("aliases", []):
                    _FAMILY_ALIASES[alias] = key
                _FAMILY_ALIASES[key] = key
        print(f"[Family Profile] 가족 프로필 로드 완료: {list(_FAMILY_PROFILE.keys())}")
except Exception as e:
    print(f"[Family Profile] 로드 실패: {e}")

def _calc_age_at_year(birth_date_str: str, target_year: int) -> int:
    """생년월일 문자열로부터 특정 연도의 만 나이 계산"""
    birth_year = int(birth_date_str[:4])
    return target_year - birth_year

def _resolve_age_to_years(member_key: str, age: int) -> list:
    """특정 가족 구성원의 나이를 해당 나이였던 연도(들)로 변환"""
    member = _FAMILY_PROFILE.get(member_key)
    if not member:
        return []
    birth_year = int(member["birth_date"][:4])
    # 만 나이 기준: 해당 나이가 되는 해
    target_year = birth_year + age
    return [target_year]

def _build_family_context_for_prompt(current_year: int) -> str:
    """Gemini 프롬프트에 주입할 가족 컨텍스트 문자열 생성"""
    if not _FAMILY_PROFILE:
        return ""
    lines = ["Family Profile (for age/relationship-based queries):"]
    for key, m in _FAMILY_PROFILE.items():
        birth_year = int(m["birth_date"][:4])
        current_age = current_year - birth_year
        aliases = ", ".join(m.get("aliases", []))
        lines.append(f"  - {key} ({m['role']}): born {m['birth_date']}, currently {current_age}세 (만), aliases=[{aliases}]")
    return "\n".join(lines)

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
                
        # --- 1차: Local 파싱 (인물, 연도, 나이, 별명 분리) ---
        local_years = []
        local_people = []
        remaining_words = []
        local_age_context = {}  # {member_key: age} - 나이 기반 연도 변환용

        words = search_text.split()
        i = 0
        while i < len(words):
            word = words[i]

            # 1. 연도 추출 (정규식 기반)
            y_match = re.search(r'^(20\d{2})년?$', word)
            if y_match:
                local_years.append(int(y_match.group(1)))
                i += 1
                continue

            # 2. 나이 패턴 매칭 ("35살", "7세", "30대")
            age_match = re.search(r'^(\d{1,3})(살|세)$', word)
            decade_match = re.search(r'^(\d{1,2})0대$', word)
            life_stage_map = {
                "돌잔치": (0, 1), "돌": (0, 1), "신생아": (0, 0),
                "유치원": (4, 7), "초등학교": (7, 13), "초등": (7, 13),
                "중학교": (13, 16), "중학생": (13, 16),
                "고등학교": (16, 19), "고등": (16, 19), "고등학생": (16, 19),
                "대학교": (19, 23), "대학생": (19, 23), "대학": (19, 23),
                "군대": (19, 22), "군인": (19, 22),
                "결혼": (25, 35), "결혼식": (25, 35), "웨딩": (25, 35),
            }

            if age_match:
                age_val = int(age_match.group(1))
                # 앞 단어가 인물이면 해당 인물의 나이로 매칭
                if local_people:
                    member_key = local_people[-1]
                    years = _resolve_age_to_years(member_key, age_val)
                    local_years.extend(years)
                    print(f"[*] 나이→연도 변환: {member_key} {age_val}살 → {years}")
                i += 1
                continue

            if decade_match:
                decade_base = int(decade_match.group(1)) * 10
                if local_people:
                    member_key = local_people[-1]
                    decade_years = []
                    for age in range(decade_base, decade_base + 10):
                        decade_years.extend(_resolve_age_to_years(member_key, age))
                    local_years.extend(decade_years)
                    print(f"[*] 연대→연도 변환: {member_key} {decade_base}대 → {decade_years}")
                i += 1
                continue

            if word in life_stage_map:
                age_min, age_max = life_stage_map[word]
                if local_people:
                    member_key = local_people[-1]
                    stage_years = []
                    for age in range(age_min, age_max + 1):
                        stage_years.extend(_resolve_age_to_years(member_key, age))
                    local_years.extend(stage_years)
                    print(f"[*] 생애단계→연도 변환: {member_key} '{word}' → {stage_years}")
                else:
                    # 인물 없이 생애단계만 있으면 visual로 넘김
                    remaining_words.append(word)
                i += 1
                continue

            # 3. 인물 추출 (이름 또는 별명으로 시작하는 단어)
            matched = False
            for kn in known_names_list:
                if word.startswith(kn):
                    local_people.append(kn)
                    matched = True
                    break
            if not matched:
                # 별명/역할 매칭 (아빠, 엄마, 형 등)
                for alias, member_key in _FAMILY_ALIASES.items():
                    if word.startswith(alias) and member_key in known_names_list:
                        local_people.append(member_key)
                        matched = True
                        break
            if matched:
                i += 1
                continue

            remaining_words.append(word)
            i += 1
            
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
                    
                    # 가족 프로필 컨텍스트 생성
                    family_context = _build_family_context_for_prompt(current_year)

                    # Gemini에게 남은 문장(visual_query_key)에 대해서만 분석 지시!
                    prompt = f"""You are a Photo Search Query Parser for a FAMILY photo album.
Current Year: {current_year}
Known People in DB: [{known_names_str}]
Known Locations in DB: [{known_locs_str}]

{family_context}

User Query: "{visual_query_key}"

IMPORTANT AGE/LIFE-STAGE RULES:
- If a query mentions age (e.g., "35살", "7세"), calculate the year when that person was that age using their birth date from the Family Profile.
  Example: 성욱(born 1991) + "35살" → year 2026. Output years: [2026].
- If a query mentions a decade (e.g., "30대"), output ALL years in that age range.
  Example: 성욱 + "30대" → ages 30-39 → years [2021,2022,2023,2024,2025,2026,2027,2028,2029,2030].
- If a query mentions a life stage (e.g., "초등학교", "돌잔치", "유치원"), map it to an age range:
  돌잔치/돌=0~1세, 유치원=4~7세, 초등학교=7~13세, 중학교=13~16세, 고등학교=16~19세, 대학교=19~23세
  Then convert to years using the person's birth date.
- Role/alias references (아빠, 엄마, 형, 첫째, 둘째) should map to the matching person from Family Profile.

Parse the query into EXACTLY this JSON structure:
{{
  "years": [], // list of integers, e.g., 2025. convert "작년" to {current_year - 1}. Convert age references using Family Profile birth dates. If none, []
  "people": [], // list of names exactly matching the Known People list. Also resolve aliases (아빠→성욱, 엄마→민지, etc). Fix misspellings if obvious. If none, []
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
  "visual": "EMPTY" // Translate all visual/abstract concepts (including seasons/times) into concise English keywords. For "겨울", output "winter, snow, cold, frozen". For "밤", output "night, dark, streetlights". DO NOT include people/locations/ages. If none, "EMPTY".
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

    # [계절/시간대 하드 필터] 사용자가 명시적으로 언급한 계절/시간대는 must 조건으로 강제
    if extracted_seasons:
        if len(extracted_seasons) == 1:
            must_conds.append(FieldCondition(key="season", match=MatchValue(value=extracted_seasons[0])))
        else:
            s_shoulds = [FieldCondition(key="season", match=MatchValue(value=s)) for s in extracted_seasons]
            must_conds.append(Filter(should=s_shoulds))
        print(f"[*] 🌸 계절 하드 필터 적용: {extracted_seasons}")

    if extracted_times:
        if len(extracted_times) == 1:
            must_conds.append(FieldCondition(key="time_of_day", match=MatchValue(value=extracted_times[0])))
        else:
            t_shoulds = [FieldCondition(key="time_of_day", match=MatchValue(value=t)) for t in extracted_times]
            must_conds.append(Filter(should=t_shoulds))
        print(f"[*] 🕐 시간대 하드 필터 적용: {extracted_times}")

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
        
        # [V2] RRF는 계절/시간대가 must 하드필터로 이동했으므로 더 이상 불필요 → 항상 순수 벡터 검색
        use_rrf = False
        
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


@router.post("/api/rebuild_cache")
async def api_rebuild_cache():
    """수동으로 타임라인 캐시를 즉시 재생성합니다."""
    try:
        rebuild_timeline_cache()
        return {"status": "success", "message": "타임라인 캐시 재생성 완료"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

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


def rebuild_timeline_cache():
    """
    Qdrant에서 최신 500장을 스캔하여 timeline_cache.json 을 재생성합니다.
    업로드/인덱싱 완료 후 호출되어야 합니다.
    """
    import pickle

    # Celery 워커 프로세스는 FastAPI lifespan을 타지 않아 state.qdrant_client가 None.
    # 여기서 lazy init하여 재사용(같은 워커 프로세스 내) 및 skip 방지.
    qc = state.qdrant_client
    if qc is None:
        try:
            from qdrant_client import QdrantClient
            qc = QdrantClient(url=os.getenv("QDRANT_URL", "http://qdrant:6333"))
            state.qdrant_client = qc
            print("[Timeline Cache] Celery context: Qdrant client lazy-initialized.")
        except Exception as init_err:
            print(f"[Timeline Cache] Qdrant client 초기화 실패: {init_err}")
            return

    try:
        coll = "gumaphoto_hybrid_kr"

        # recent 500장 (최신순)
        recent_points, _ = qc.scroll(
            collection_name=coll, limit=500, with_payload=True, with_vectors=False,
            order_by=OrderBy(key="sort_date", direction=Direction.DESC)
        )

        def point_to_dict(pt):
            p = pt.payload or {}
            filepath = p.get("filepath", "")
            photo_url = filepath.replace("/app/data/organized", "/photos")
            return {
                "id": pt.id, "url": photo_url, "original_path": filepath,
                "date": p.get("date", "Unknown"), "location": p.get("location", "Unknown Location"),
                "people": p.get("people", []), "caption": p.get("caption", ""),
                "season": p.get("season", "Unknown"), "time_of_day": p.get("time_of_day", "Unknown"),
            }

        cache = {"recent": [point_to_dict(pt) for pt in recent_points]}

        # 인물별 태그 캐시
        known_names = []
        if os.path.exists("/app/data/known_faces.pkl"):
            try:
                with open("/app/data/known_faces.pkl", "rb") as f:
                    known_names = list(pickle.load(f).keys())
            except Exception:
                pass

        for name in known_names:
            try:
                person_filter = Filter(must=[FieldCondition(key="people", match=MatchValue(value=name))])
                pts, _ = qc.scroll(
                    collection_name=coll, scroll_filter=person_filter,
                    limit=500, with_payload=True, with_vectors=False,
                    order_by=OrderBy(key="sort_date", direction=Direction.DESC)
                )
                cache[name] = [point_to_dict(pt) for pt in pts]
            except Exception as e:
                print(f"[Timeline Cache] '{name}' 스캔 실패: {e}")
                cache[name] = []

        cache_path = "/app/data/caches/timeline_cache.json"
        os.makedirs(os.path.dirname(cache_path), exist_ok=True)
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False)

        print(f"✅ [Timeline Cache] 재생성 완료: recent={len(cache['recent'])}장, 인물 {len(known_names)}명")
    except Exception as e:
        import traceback
        print(f"❌ [Timeline Cache] 재생성 실패: {e}")
        traceback.print_exc()

