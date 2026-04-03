import sys

with open("search.py", "r", encoding="utf-8") as f:
    orig = f.read()

lines = orig.split('\n')

start_line = -1
end_line = -1
for i, line in enumerate(lines):
    if "# 0. One-Shot Smart NLP Extraction (Gemini)" in line:
        start_line = i
    if "if not search_text:" in line and "res_scroll" in lines[min(i+2, len(lines)-1)]:
        end_line = i - 1
        break

if start_line == -1 or end_line == -1:
    print("Could not find start/end lines.")
    sys.exit(1)

new_code = """    # 0. One-Shot Smart NLP Extraction (Gemini)
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
            
            prompt = f\"\"\"You are a Photo Search Query Parser.
Current Year: {current_year}
Known People in DB: [{known_names_str}]

User Query: "{search_text}"

Parse the query into EXACTLY this JSON structure:
{{
  "years": [], // list of integers, e.g., 2025. convert "작년" to {current_year - 1}. If none, []
  "people": [], // list of names exactly matching the Known People list. Fix misspellings if obvious. If none, []
  "locations": [ // If any specific place, landmark, city, or province is mentioned (e.g. "하와이", "전라도", "오사카", "집근처"), convert it into GPS coordinates (WGS84).
    {{
      "lat": 35.6329,
      "lon": 139.8804,
      "radius": 50000,    // City/Province/Country: 50000. Specific landmark/district: 2000.
      "matched_word": "오사카" // The exact substring of the location from the user's query
    }}
  ], // If none, []
  "visual": "EMPTY" // Translate all remaining visual/abstract concepts to a concise English phrase. DO NOT include the extracted years, people, or locations. e.g. "수영하는" -> "swimming". If no visual meaning remains, output "EMPTY".
}}
Output ONLY valid JSON without markup.
\"\"\"
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
    
    # 1. 쿼리가 없을 경우 (Home 화면 진입 시) -> 단순 필터 + 스크롤 검색
    direct = Direction.ASC if req.sort == "asc" else Direction.DESC
    must_conds = []
    
    # 필터 구성 (UI에서 날아온 location, date 및 동적 people)
    if final_people:
        for p_name in final_people:
            must_conds.append(FieldCondition(key="people", match=MatchValue(value=p_name)))
            
    # [복구] 자연어 GPS GeoRadius 병합
    for loc_obj in extracted_locations:
        try:
            if isinstance(loc_obj, dict) and "lat" in loc_obj and "lon" in loc_obj:
                must_conds.append(
                    FieldCondition(
                        key="geo_point",
                        geo_radius=GeoRadius(
                            center=GeoPoint(lat=float(loc_obj["lat"]), lon=float(loc_obj["lon"])),
                            radius=float(loc_obj.get("radius", 50000))
                        )
                    )
                )
        except Exception as e:
            print(f"[-] GeoRadius 파싱 에러: {e}")
            
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
        
    q_filter = Filter(must=must_conds) if must_conds else None
"""

lines = lines[:start_line] + new_code.split('\n') + lines[end_line+1:]
with open("search.py", "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("Successfully generated search.py")
