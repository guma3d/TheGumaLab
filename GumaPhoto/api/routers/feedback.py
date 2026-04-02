from fastapi import APIRouter
from pydantic import BaseModel
import typing
import os
import json
from sqlalchemy import func
import uuid
from core.state import state
from qdrant_client.http.models import Filter, FieldCondition, MatchValue
import random

def get_uuid_from_id(id_val: typing.Union[int, str]) -> typing.Union[int, str]:
    if isinstance(id_val, int):
        return id_val
    val_str = str(id_val)
    if val_str.isdigit():
        return int(val_str)
    return val_str

router = APIRouter()

class FeedbackV2Request(BaseModel):
    point_id: typing.Union[int, str]
    issue_type: str
    correct_value: typing.Optional[str] = ""
    target_points: typing.Optional[typing.List[typing.Union[int, str]]] = []

def sync_payload_to_sqlite(point_id: str):
    """Qdrant 단일 진실화 아키텍처로 인해 SQLite 동기화 과정 삭제됨"""
    pass

@router.post("/api/feedback_v2/ignore_face")
async def ignore_face_feedback(req: FeedbackV2Request):
    if not state.qdrant_client: return {"error": "Qdrant not loaded"}
    real_point_id = get_uuid_from_id(req.point_id)
    try:
        # 뒤통수(오탐지) 랜드마크 제거 로직: Qdrant에서 'face_bbox'를 찢어버리고 'Unidentifiable Person' 명찰을 섬세하게 붙임
        state.qdrant_client.delete_payload(
            collection_name="gumaphoto_hybrid_kr",
            keys=["face_bbox"],
            points=[real_point_id]
        )
        state.qdrant_client.set_payload(
            collection_name="gumaphoto_hybrid_kr",
            payload={"people": ["Unidentifiable Person"]},
            points=[real_point_id]
        )
        
        try:
            pt = state.qdrant_client.retrieve(collection_name="gumaphoto_hybrid_kr", ids=[real_point_id], with_payload=True)
            fpath = pt[0].payload.get("filepath", "unknown") if pt else "unknown"
            old_people = pt[0].payload.get("people", ["Unknown Person"]) if pt else ["Unknown Person"]
            with open("/app/data/audit_trace.json", "a", encoding="utf-8") as tf:
                tf.write(json.dumps({"type": "BEFORE", "trace_id": real_point_id, "filepath": fpath, "people": old_people}, ensure_ascii=False) + "\n")
                tf.write(json.dumps({"type": "AFTER", "trace_id": real_point_id, "filepath": fpath, "people": ["Unidentifiable Person"]}, ensure_ascii=False) + "\n")
        except: pass
        
        sync_payload_to_sqlite(real_point_id)
        return {"message": "Ignored successfully."}
    except Exception as e:
        return {"error": str(e)}

@router.post("/api/feedback_v2/no_person")
async def no_person_feedback(req: FeedbackV2Request):
    if not state.qdrant_client: return {"error": "Qdrant not loaded"}
    real_point_id = get_uuid_from_id(req.point_id)
    try:
        # 인형/포스터 등 '진짜 사람이 아님(No Person)' 케이스
        state.qdrant_client.delete_payload(
            collection_name="gumaphoto_hybrid_kr",
            keys=["face_bbox"],
            points=[real_point_id]
        )
        state.qdrant_client.set_payload(
            collection_name="gumaphoto_hybrid_kr",
            payload={"people": ["No People"]},
            points=[real_point_id]
        )
        
        try:
            pt = state.qdrant_client.retrieve(collection_name="gumaphoto_hybrid_kr", ids=[real_point_id], with_payload=True)
            fpath = pt[0].payload.get("filepath", "unknown") if pt else "unknown"
            old_people = pt[0].payload.get("people", ["Unknown Person"]) if pt else ["Unknown Person"]
            with open("/app/data/audit_trace.json", "a", encoding="utf-8") as tf:
                tf.write(json.dumps({"type": "BEFORE", "trace_id": real_point_id, "filepath": fpath, "people": old_people}, ensure_ascii=False) + "\n")
                tf.write(json.dumps({"type": "AFTER", "trace_id": real_point_id, "filepath": fpath, "people": ["No People"]}, ensure_ascii=False) + "\n")
        except: pass
        
        sync_payload_to_sqlite(real_point_id)
        return {"message": "Ignored successfully as No People."}
    except Exception as e:
        return {"error": str(e)}

@router.post("/api/feedback_v2/temptest")
async def temptest_feedback(req: FeedbackV2Request):
    if not state.qdrant_client: return {"error": "Qdrant not loaded"}
    
    real_point_id = get_uuid_from_id(req.point_id)
    
    # "People"이면 face 벡터 참조, 그 외는 scene 벡터
    fb_type = "face" if "People" in req.issue_type else "scene"
    
    try:
        recommend_res = state.qdrant_client.query_points(
            collection_name="gumaphoto_hybrid_kr",
            query=real_point_id,
            using=fb_type,
            limit=300,  # 더 많은 유사 사진 목록을 확보하기 위해 리소스 한도 증가 (기존 100 -> 300)
            with_payload=True
        ).points
        
        # 사용자가 명시적으로 선택한 '메인 원본 피드백 타겟'을 강제로 최우선 순위로 끌어옵니다.
        target_point = state.qdrant_client.retrieve(
            collection_name="gumaphoto_hybrid_kr",
            ids=[real_point_id],
            with_payload=True
        )
        
        similars = []
        if target_point:
            p = target_point[0].payload or {}
            similars.append({
                "id": target_point[0].id,
                "url": p.get("filepath", "").replace("/app/data/organized", "/photos"),
                "score": 1.0,
                "date": p.get("date", "Unknown"),
                "location": p.get("location", "Unknown Location"),
                "people": p.get("people", []),
                "face_bbox": p.get("face_bbox", None)
            })
            
        for hit in recommend_res:
            if str(hit.id) == real_point_id: continue
            
            # 사용자 지시사항 반영: 장소(scene) 피드백 시 검색 풀은 넓게 유지하되, 지나친 오탐을 방지하기 위해 83%로 상향
            cutoff = 0.80 if fb_type == "face" else 0.83
            if hit.score < cutoff: continue
            
            payload = hit.payload or {}
            filepath = payload.get("filepath", "")
            if not filepath: continue
            
            # 사용자 요청: 장소/날짜 피드백 시에는 해당 값이 "Unknown"이거나 비어있는 유사 사진만 노출. (이미 멀쩡한 피드백 제외 방지)
            if fb_type != "face":
                if "Location" in req.issue_type:
                    p_loc = payload.get("location", "")
                    if "Unknown" not in p_loc and "위치정보없음" not in p_loc and p_loc.strip() != "":
                        continue
                elif "Date" in req.issue_type or "날짜" in req.issue_type:
                    p_date = payload.get("date", "")
                    if "Unknown" not in p_date and p_date.strip() != "":
                        continue
            
            url_path = filepath.replace("/app/data/organized", "/photos")
            similars.append({
                "id": hit.id,
                "url": url_path,
                "score": round(hit.score, 3),
                "date": payload.get("date", "Unknown"),
                "location": payload.get("location", "Unknown Location"),
                "people": payload.get("people", []),
                "face_bbox": payload.get("face_bbox", None)
            })
            
        return {"results": similars}
    except Exception as e:
        print(f"❌ TempTest (Simulation) 에러: {e}")
        return {"error": str(e), "results": []}

@router.get("/api/feedback_v2/unknown")
async def get_unknown_photo():
    if not state.qdrant_client: return {"error": "Qdrant not loaded"}
    try:
        import random
        from qdrant_client.http.models import Filter, FieldCondition, MatchText, MatchValue
        
        # 한 번의 쿼리로 모든 종류의 Unknown(Date, Location, People)을 무작위 추출
        unknowns, _ = state.qdrant_client.scroll(
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
            limit=500,  # 500개를 캐싱하여 넓은 랜덤풀 생성
            with_payload=True,
            with_vectors=False
        )
        
        if unknowns:
            random.shuffle(unknowns)
            
            for raw_target in unknowns:
                p = raw_target.payload or {}
                loc = p.get("location", "")
                date_val = p.get("date", "")
                people_val = p.get("people", [])
                
                issues = []
                if "Unknown" in date_val or not date_val: 
                    issues.append("Date")
                if "위치정보없음" in loc or "Unknown" in loc or not loc: 
                    issues.append("Location")
                    
                # 사람 판별: Unidentifiable Person / No People 은 확실하게 정해진 상태이므로 Unknown 취급 안함.
                has_unknown_person = False
                for person in people_val:
                    if person in ["Unknown Person", "Unknown People"]:
                        has_unknown_person = True
                        break
                if has_unknown_person and p.get("face_bbox"):
                    issues.append("People")
                    
                if issues:
                    issue = random.choice(issues)
                    url_path = p.get("filepath", "").replace("/app/data/organized", "/photos")
                    return {
                        "id": raw_target.id,
                        "url": url_path,
                        "issue": issue,
                        "date": date_val,
                        "location": loc,
                        "people": people_val,
                        "face_bbox": p.get("face_bbox", None)
                    }
                    
    except Exception as e:
        print(f"❌ 피드백 고속 혼합 탐색 중 예외 발생: {e}")

    return {"id": None, "message": "No photos require feedback at this time."}

from fastapi import BackgroundTasks

@router.post("/api/feedback_v2/submit")
async def submit_feedback_v2(req: FeedbackV2Request, background_tasks: BackgroundTasks):
    print(f"===========================================================")
    print(f"[🔍 DEBUG] SUBMIT API POST RECEIVED!")
    print(f"  - point_id: {req.point_id}")
    print(f"  - issue: {req.issue_type}, correct: {req.correct_value}")
    if req.target_points:
        print(f"  - target_points length: {len(req.target_points)}")
        print(f"  - sample: {req.target_points[:3]}")
    else:
        print(f"  - req.target_points IS EMPTY OR NONE!")
    print(f"===========================================================")
    
    fb_type = "face" if "People" in req.issue_type else "time_loc"
    
    real_point_id = get_uuid_from_id(req.point_id)
    
    final_correct_value = req.correct_value
    prefix = ""
    
    # 1. Location 피드백인 경우
    if fb_type == "time_loc" and "Location" in req.issue_type and state.gemini_client:
        prefix = "LOC|"
        if req.correct_value.startswith("["):
            # 카카오 자동완성 등 위경도 기반 정확한 페이로드가 들어온 경우, AI 교정을 생략하고 원형 보존
            final_correct_value = req.correct_value
        else:
            try:
                existing_locations = []
                if os.path.exists("/app/data/available_tags.json"):
                    with open("/app/data/available_tags.json", "r", encoding="utf-8") as f:
                        tag_data = json.load(f)
                        existing_locations = tag_data.get("locations", [])
                        
                prompt = (
                    f"사용자 입력 장소: '{req.correct_value}'\n"
                    "당신은 스마트 갤러리의 위치 정보 표준화 매니저입니다.\n"
                    "사용자가 구어체나 부분 약어로 장소를 입력하더라도, 다음의 <보유 장소 목록> 중에서 가장 정확히 일치하는 '국가명-지역명' 형태로 교정(Parsing)해주세요.\n"
                    f"<보유 장소 목록>: {existing_locations}\n"
                    "규칙 1: 목록에 정규화된 이름이 존재한다면, 목록의 텍스트와 100% 동일한 문자열을 반환하세요.\n"
                    "규칙 2: 목록에 아예 없는 완전한 신규 국가/도시라면, '국가명-지역명' 포맷을 유지하여 새로 창조하세요.\n"
                    "규칙 3: 불필요한 부연 설명이나 마크다운 없이 오직 교정된 '문자열 1줄'만 반환하세요."
                )
                response = state.gemini_client.models.generate_content(
                    model='gemini-3.1-flash-lite-preview',
                    contents=prompt,
                )
                final_correct_value = response.text.strip().replace("\n", "").replace("\"", "")
                print(f"[Gemini 장소 교정] 원본: '{req.correct_value}' -> 결과: '{final_correct_value}'")
            except Exception as e:
                print(f"[Gemini 위치 파싱 오류] {e}")

    # 2. Date 피드백인 경우
    elif fb_type == "time_loc" and ("Date" in req.issue_type or "날짜" in req.issue_type) and state.gemini_client:
        prefix = "DATE|"
        try:
            prompt_date = (
                f"사용자 입력 날짜: '{req.correct_value}'\n"
                "당신은 스마트 갤러리 날짜 교정기입니다.\n"
                "사용자의 한글 구어체 입력을 'YYYY-MM' 포맷(숫자와 하이픈만)으로 변환하세요.\n"
                "예: '25년 3월' -> '2025-03', '작년 겨울' -> '2025년 기준 작년 12월이므로 2024-12'\n"
                "절대로 다른 부연 설명을 섞지 말고 오직 'YYYY-MM' 1줄만 반환하세요."
            )
            response_date = state.gemini_client.models.generate_content(
                model='gemini-3.1-flash-lite-preview',
                contents=prompt_date,
            )
            parsed_date = response_date.text.strip().replace("\n", "").replace("\"", "")
            if parsed_date and "-" in parsed_date:
                final_correct_value = parsed_date
                print(f"[Gemini 날짜 교정] 원본: '{req.correct_value}' -> 결과: '{final_correct_value}'")
        except Exception as e:
            print(f"[Gemini 날짜 파싱 오류] {e}")

    db_correct_value = f"{prefix}{final_correct_value}" if prefix else final_correct_value
    
    real_target_points = [get_uuid_from_id(tid) for tid in req.target_points] if req.target_points else []
    tp_json = json.dumps(real_target_points) if real_target_points else "[]"
    
    try:
        all_pts = [real_point_id] + real_target_points if real_target_points else [real_point_id]
        
        if fb_type == "face":
            # 인물의 경우 feedback_service에 크롭만 하고 바로 DB 처리
            from api.services.feedback_service import process_face_enrollment
            process_face_enrollment(real_point_id, final_correct_value, tp_json)
        else:
            # 1. UI 즉각 반영을 위한 Qdrant 상태 초고속 병행 업데이트 (processing_status 불필요)
            target_date = "Unknown Date"
            target_loc = "Unknown Location"
            
            if db_correct_value.startswith("DATE|"):
                target_date = db_correct_value.split("|", 1)[1]
                state.qdrant_client.set_payload(collection_name="gumaphoto_hybrid_kr", payload={"date": target_date}, points=all_pts)
            else:
                target_loc = db_correct_value.split("|", 1)[1] if db_correct_value.startswith("LOC|") else db_correct_value
                
                payload_obj = {"location": target_loc}
                try:
                    import re
                    match = re.search(r'^\[([-\d\.]+),\s*([-\d\.]+)\]\s*(.*)$', target_loc)
                    if match:
                        lat_val = float(match.group(1))
                        lon_val = float(match.group(2))
                        clean_loc = str(match.group(3)).strip()
                        payload_obj["location"] = clean_loc
                        payload_obj["geo_point"] = {"lat": lat_val, "lon": lon_val}
                except:
                    pass
                state.qdrant_client.set_payload(collection_name="gumaphoto_hybrid_kr", payload=payload_obj, points=all_pts)
            
            # 2. 물리 파일(EXIF) 덮어쓰기는 연산은 빠르나 디스크 I/O가 1초가량 딜레이를 주므로 백그라운드 위임
            from api.services.feedback_service import process_time_location_feedback
            background_tasks.add_task(process_time_location_feedback, real_point_id, target_date, target_loc, tp_json)
                
        print(f"✅ [Instant Feedback] Qdrant 즉시 반영 및 EXIF 처리 프로세스 인계 완료 (ID: {real_point_id})")
        return {"message": "Feedback submitted successfully."}
        
    except Exception as e:
        print(f"❌ [Feedback v3.0 -> SQLite] 큐 발송 실패: {e}")
        return {"error": "Failed to submit feedback."}

import asyncio
import requests
import os

@router.get("/api/location/search_global")
async def search_global_location(q: str):
    kakao_key = os.environ.get("KAKAO_REST_API_KEY", "").strip()
    
    def fetch_kakao_sync():
        if not kakao_key: return []
        url = "https://dapi.kakao.com/v2/local/search/keyword.json"
        headers = {"Authorization": f"KakaoAK {kakao_key}"}
        params = {"query": q, "size": 10}
        try:
            res = requests.get(url, headers=headers, params=params, timeout=5.0)
            if res.status_code == 200:
                data = res.json()
                results = []
                for doc in data.get("documents", []):
                    lat_str = doc.get("y", "")
                    lon_str = doc.get("x", "")
                    place_name = doc.get("place_name", "")
                    address_name = doc.get("road_address_name") or doc.get("address_name") or ""
                    full_name = f"{place_name} ({address_name})" if address_name else place_name
                    if lat_str and lon_str:
                        exact_format = f"[{lat_str[:9]}, {lon_str[:10]}] {place_name}"
                        results.append({"display": full_name, "exact": exact_format, "short_name": place_name})
                return results
        except Exception: pass
        return []

    def fetch_osm_sync():
        url = "https://nominatim.openstreetmap.org/search"
        params = {"q": q, "format": "jsonv2", "limit": 10, "accept-language": "ko"}
        headers = {"User-Agent": "GumaPhoto-SearchApp/1.0"}
        try:
            res = requests.get(url, headers=headers, params=params, timeout=5.0)
            if res.status_code == 200:
                data = res.json()
                results = []
                for doc in data:
                    lat_str = doc.get("lat", "")
                    lon_str = doc.get("lon", "")
                    display_name = doc.get("display_name", "")
                    short_name = display_name.split(',')[0].strip()
                    if lat_str and lon_str:
                        exact_format = f"[{lat_str[:9]}, {lon_str[:10]}] {short_name}"
                        results.append({"display": display_name, "exact": exact_format, "short_name": short_name})
                return results
        except Exception: pass
        return []

    kakao_results, osm_results = await asyncio.gather(
        asyncio.to_thread(fetch_kakao_sync),
        asyncio.to_thread(fetch_osm_sync)
    )
    
    return {
        "kakao": kakao_results,
        "osm": osm_results
    }
