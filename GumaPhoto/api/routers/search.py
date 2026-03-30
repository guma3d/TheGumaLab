from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, List
from core.state import state
import json
import os
import re
import torch
from qdrant_client.http.models import Filter, FieldCondition, MatchText, MatchAny, MatchValue, OrderBy, Direction

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
    
    # 0. 자연어 텍스트 문맥 내에서 시간(연도) 식별자 강제 추출 (NLP Year Filtering)
    extracted_years = []
    if search_text:
        try:
            import datetime, re
            current_year = datetime.datetime.now().year
            
            # 1. "N년 전"
            ago_match = re.search(r'(\d+)\s*년\s*전', search_text)
            if ago_match:
                extracted_years.append(str(current_year - int(ago_match.group(1))))
                search_text = re.sub(r'\d+\s*년\s*전', '', search_text)
                
            # 2. "2021년"
            yyyy_match = re.search(r'(20\d{2})\s*년', search_text)
            if yyyy_match:
                extracted_years.append(yyyy_match.group(1))
                search_text = re.sub(r'20\d{2}\s*년', '', search_text)
                
            # 3. "21년", "22년"
            yy_match = re.search(r'(?<!\d)(\d{2})\s*년', search_text)
            if yy_match:
                extracted_years.append("20" + yy_match.group(1))
                search_text = re.sub(r'(?<!\d)\d{2}\s*년', '', search_text)
                
            # 4. 특수 명사
            for kw, offset in [("올해", 0), ("이번년도", 0), ("작년", 1), ("재작년", 2)]:
                if kw in search_text:
                    extracted_years.append(str(current_year - offset))
                    search_text = search_text.replace(kw, "")
                    
            extracted_years = list(set(extracted_years))
            if extracted_years:
                print(f"[*] 연도 강제 식별 필터 작동 (AND 조합): {extracted_years}")
        except Exception as e:
            print(f"[-] Year extraction error: {e}")

    # 0.1. 자연어 텍스트 문맥 내에서 인물 식별자 강제 추출 (NLP Metadata Hard Filtering)
    extracted_names = []
    if search_text:
        try:
            import pickle
            if os.path.exists('/app/data/known_faces.pkl'):
                with open('/app/data/known_faces.pkl', 'rb') as f:
                    known_names = list(pickle.load(f).keys())
                for name in known_names:
                    if name in search_text:
                        extracted_names.append(name)
                        print(f"[*] 인물 강제 식별 필터 작동 (AND 조합): '{name}'")
        except Exception as e:
            print(f"[-] Known faces extraction error: {e}")

    # 0.5. 자연어 텍스트 문맥 내에서 장소 식별자 강제 추출 (NLP Metadata Hard Filtering)
    extracted_locations = []
    if search_text:
        try:
            if os.path.exists('/app/data/available_tags.json'):
                import json
                with open('/app/data/available_tags.json', 'r', encoding='utf-8') as f:
                    known_locs = json.load(f).get("locations", [])
                
                valid_locs = [loc for loc in known_locs if loc not in ["Unknown Location", "Unknown-Location", "위치정보없음", "All Locations", "None"]]
                
                if valid_locs and state.gemini_client:
                    loc_list_str = "\n".join(valid_locs)
                    prompt = f"""You are an intelligent Geolocation Entity Matcher.
Here is the list of valid locations currently available in our database:
{loc_list_str}

The user's search query is: "{search_text}"

Does the user's query imply searching for a specific location(s) from the list above?
Consider English-Korean translations (e.g. "하와이" == "Hawaii", "일본" == "Japan") and administrative variations (e.g. "강남" == "강남구").
If the location exists in the list above, return the EXACT string(s) from the list.
Output MUST be a valid JSON array of strings, and nothing else. If no location matches, output []."""
                    
                    try:
                        resp = state.gemini_client.models.generate_content(
                            model='gemini-3.1-flash-lite-preview', 
                            contents=prompt
                        )
                        # JSON parsing (Markdown fallback parsing included)
                        resp_text = resp.text.strip()
                        if resp_text.startswith("```json"):
                            resp_text = resp_text[7:-3].strip()
                        elif resp_text.startswith("```"):
                            resp_text = resp_text[3:-3].strip()
                            
                        matched_locs = json.loads(resp_text)
                        
                        if isinstance(matched_locs, list):
                            for loc in matched_locs:
                                if loc in valid_locs and loc not in extracted_locations:
                                    extracted_locations.append(loc)
                                    print(f"[*] 🧠 Gemini 지능형 장소 식별 성공: '{loc}'")
                    except Exception as ge:
                        print(f"[-] Gemini location matching error: {ge}")
                                
        except Exception as e:
            print(f"[-] Known locations extraction error: {e}")

    # UI 선택 이름과 텍스트 서치에서 추출된 이름을 모두 병합
    final_people = list(set(req.people + extracted_names))
    
    # UI 선택 장소와 텍스트 서치 추출 장소를 모두 병합
    final_locations = []
    if req.location and req.location != "All Locations":
        final_locations.append(req.location)
    else:
        final_locations.extend(extracted_locations)
    
    # 1. 쿼리가 없을 경우 (Home 화면 진입 시) -> 단순 필터 + 스크롤 검색
    direct = Direction.ASC if req.sort == "asc" else Direction.DESC
    must_conds = []
    
    # 필터 구성 (UI에서 날아온 location, date 및 동적 people)
    if final_people:
        # 벡터 매칭이 아닌 절대 Metadata 매칭으로 강제 규정 (AND 교집합)
        for p_name in final_people:
            must_conds.append(FieldCondition(key="people", match=MatchValue(value=p_name)))
            
    if final_locations:
        if len(final_locations) == 1:
            must_conds.append(FieldCondition(key="location", match=MatchValue(value=final_locations[0])))
        else:
            # Qdrant의 PayloadSchemaType.TEXT 인덱스에는 MatchAny가 정상 작동하지 않으므로, 다중 OR(should) Filter로 중첩 처리해야 합니다.
            loc_shoulds = [FieldCondition(key="location", match=MatchValue(value=loc)) for loc in final_locations]
            must_conds.append(Filter(should=loc_shoulds))
            
    if extracted_years:
        if len(extracted_years) == 1:
            must_conds.append(FieldCondition(key="date", match=MatchValue(value=extracted_years[0])))
        else:
            must_conds.append(FieldCondition(key="date", match=MatchAny(any=extracted_years)))
            
    if req.date and req.date != "All Dates":
        must_conds.append(FieldCondition(key="date", match=MatchValue(value=req.date)))
        
    q_filter = Filter(must=must_conds) if must_conds else None

    # [중요] AI 검색 품질 보호: 고유명사 강제 태그(AND/OR)가 걸렸으므로, SigLIP 영어 번역에 들어갈 문장에선 고유명사를 도려내야 합니다!
    vision_search_text = search_text
    for n in extracted_names:
        vision_search_text = vision_search_text.replace(n, "")
    for lc in extracted_locations:
        lc_parts = lc.replace("특별시", "").replace("광역시", "").replace("특별자치도", "").replace("시", "").split("-")
        for lcp in lc_parts:
            vision_search_text = vision_search_text.replace(lcp, "")
            
    # 만약 이름/장소를 다 빼고 났더니 문자열이 텅 비었다면 굳이 AI 벡터 검색을 돌릴 필요가 없음!
    if not str(vision_search_text).strip():
        search_text = ""
    else:
        search_text = vision_search_text.strip()

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
    # [신규 추가] 한국어 쿼리를 SigLIP(영어 전용 모델)가 이해할 수 있도록 초고속 Gemini 번역 투입
    if state.gemini_client and re.search(r'[가-힣]', search_text):
        try:
            print(f"[*] 한국어 쿼리 번역 시도: '{search_text}'")
            prompt = (
                f"You are an AI assistant for an image search engine.\n"
                f"Extract ONLY the visually meaningful keywords from the user's Korean query, and translate them into a concise English phrase (max 5 words).\n"
                f"User Query: {search_text}\n"
                f"Ignore all conversational phrases, greetings, or filler words regardless of what the user types.\n"
                f"If the query contains NO visually meaningful keywords after ignoring fillers, output EXACTLY the word: EMPTY\n"
                f"Do not include any extra text. Output Example: 'blue sky ocean', 'dog running', 'EMPTY'."
            )
            t_resp = state.gemini_client.models.generate_content(model='gemini-3.1-flash-lite-preview', contents=prompt)
            translated = t_resp.text.strip().replace('\n', '')
            if translated:
                print(f"  [+] 영문 매핑 완료: '{translated}'")
                if translated.upper() == "EMPTY":
                    search_text = ""
                else:
                    search_text = translated
        except Exception as e:
            print(f"  [-] Gemini 번역 에러: {e}")

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
