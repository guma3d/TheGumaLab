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
            payload={"people": ["No Person"]},
            points=[real_point_id]
        )
        sync_payload_to_sqlite(real_point_id)
        return {"message": "Ignored successfully as No Person."}
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
            limit=100,
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
            
            # 사용자 지시사항: "해당 얼굴과 유사한 얼굴벡터를 가진 사진들을 유사율 0.8 기준으로 보여줘야 함"
            cutoff = 0.80 if fb_type == "face" else 0.85
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
        import numpy as np
        import pickle
        import os
        from qdrant_client.http.models import Filter, FieldCondition, MatchValue
        
        check_people = True if random.random() < 0.6 else False
        
        if check_people:
            # 1. '낮은 정확도(Low Accuracy)' 얼굴 사진 탐색 로직 (사용자 MLOps 지시사항 반영)
            # Qdrant에 랜덤 노이즈 768차원 벡터를 던져서, 은하계 전역에서 진정한 무작위 100장을 가져옴
            random_vec = np.random.randn(768).tolist()
            try:
                # `search()`를 통해 무작위 샘플링 및 Face 벡터 반환 요청 (with_vectors=["face"])
                random_hits = state.qdrant_client.search(
                    collection_name="gumaphoto_hybrid_kr",
                    query_vector=("scene", random_vec),
                    limit=100,
                    with_payload=True,
                    with_vectors=["face"]
                )
                
                # [최적화] 매번 하드디스크에서 pkl을 열지 않고, 부팅 시 메모리에 적재된 사전 재사용
                known_faces = getattr(state, "known_faces", {})
                        
                if known_faces:
                    # 무작위 샘플 중 얼굴 벡터가 존재하며, 정확도가 0.55 밑으로 떨어지는 타겟 찾기
                    for hit in random_hits:
                        face_vec = hit.vector.get("face") if hit.vector else None
                        p_people = hit.payload.get("people", [])
                        
                        # 완전히 알 수 없다고 판정된 'Unknown People'은 기존 로직에서 잡을 것이므로 패스
                        if face_vec and "Unknown People" not in p_people:
                            best_sim = -1.0
                            for k_name, k_vec in known_faces.items():
                                sim = np.dot(face_vec, k_vec)
                                if sim > best_sim:
                                    best_sim = sim
                            
                            # 정확도가 현저히 낮은 사진(0.55 이하) 발견 시, 억지 채점된 사진이므로 피드백 타겟으로 즉시 반환
                            if 0.0 < best_sim <= 0.55:
                                p = hit.payload or {}
                                url_path = p.get("filepath", "").replace("/app/data/organized", "/photos")
                                return {
                                    "id": hit.id,
                                    "url": url_path,
                                    "issue": "People",
                                    "date": p.get("date", "Unknown"),
                                    "location": p.get("location", "Unknown"),
                                    "people": p.get("people", []),
                                    "face_bbox": p.get("face_bbox", None)
                                }
            except Exception as rand_err:
                print(f"      [!] 랜덤 샘플링 유사도 채점 실패: {rand_err}")

            # 2. '완전 인식 실패(Unknown People)' 사진 탐색 로직 (기존)
            res, _ = state.qdrant_client.scroll(
                collection_name="gumaphoto_hybrid_kr",
                scroll_filter=Filter(must=[FieldCondition(key="people", match=MatchValue(value="Unknown People"))]),
                limit=100,
                with_payload=True
            )
            if res:
                raw_target = random.choice(res)
                p = raw_target.payload or {}
                url_path = p.get("filepath", "").replace("/app/data/organized", "/photos")
                return {
                    "id": raw_target.id,
                    "url": url_path,
                    "issue": "People",
                    "date": p.get("date", "Unknown"),
                    "location": p.get("location", "Unknown"),
                    "people": p.get("people", []),
                    "face_bbox": p.get("face_bbox", None)
                }
                
        # [초고속 튜닝 🚀] 전체 스캔 대신 Qdrant Scroll API를 통해 Unknown 요소 50개만 캐싱하여 랜덤 추출 (SQLite 소각)
        from qdrant_client.http.models import Filter, FieldCondition, MatchText
        unknowns, _ = state.qdrant_client.scroll(
            collection_name="gumaphoto_hybrid_kr",
            scroll_filter=Filter(
                should=[
                    FieldCondition(key="date", match=MatchText(text="Unknown")),
                    FieldCondition(key="location", match=MatchText(text="Unknown")),
                    FieldCondition(key="location", match=MatchText(text="위치정보없음"))
                ]
            ),
            limit=50,
            with_payload=True,
            with_vectors=False
        )
        
        if unknowns:
            raw_target = random.choice(unknowns)
            p = raw_target.payload or {}
            loc = p.get("location", "")
            date_val = p.get("date", "")
            issues = []
            if "Unknown" in date_val or not date_val: issues.append("Date")
            if "위치정보없음" in loc or "Unknown" in loc or not loc: issues.append("Location")
                
            if issues:
                issue = random.choice(issues)
                url_path = p.get("filepath", "").replace("/app/data/organized", "/photos")
                return {
                    "id": raw_target.id,
                    "url": url_path,
                    "issue": issue,
                    "date": date_val,
                    "location": loc,
                    "people": p.get("people", []),
                    "face_bbox": p.get("face_bbox", None)
                }
                    
    except Exception as e:
        print(f"❌ 피드백 고속 혼합 탐색 중 예외 발생: {e}")

    return {"id": None, "message": "No photos require feedback at this time."}

@router.post("/api/feedback_v2/submit")
async def submit_feedback_v2(req: FeedbackV2Request):
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
            parsed_loc = response.text.strip().replace("\n", "").replace("\"", "")
            if parsed_loc and len(parsed_loc) < 50:
                final_correct_value = parsed_loc
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

    # Redis Celery 큐로 작업 던지기
    db_correct_value = f"{prefix}{final_correct_value}" if prefix else final_correct_value
    
    real_target_points = [get_uuid_from_id(tid) for tid in req.target_points] if req.target_points else []
    tp_json = json.dumps(real_target_points) if real_target_points else "[]"
    
    try:
        if fb_type == "face":
            from api.tasks import run_feedback_face_job
            run_feedback_face_job.delay(real_point_id, db_correct_value, tp_json)
        else:
            if db_correct_value.startswith("DATE|"):
                date_val = db_correct_value.split("|", 1)[1]
                from api.tasks import run_feedback_time_loc_job
                run_feedback_time_loc_job.delay(real_point_id, date_val, "Unknown-Location", tp_json)
            elif db_correct_value.startswith("LOC|"):
                loc_val = db_correct_value.split("|", 1)[1]
                from api.tasks import run_feedback_time_loc_job
                run_feedback_time_loc_job.delay(real_point_id, "Unknown Date", loc_val, tp_json)
            else:
                from api.tasks import run_feedback_time_loc_job
                run_feedback_time_loc_job.delay(real_point_id, "Unknown Date", db_correct_value, tp_json)
                
        print(f"🚀 [Feedback v2.0 -> Redis] Celery 대기열에 지시서 발송 완료! (ID: {real_point_id})")
        return {"message": "Feedback submitted successfully. Processing in background."}
        
    except Exception as e:
        print(f"❌ [Feedback v2.0 -> Redis] 큐 발송 실패: {e}")
        return {"error": "Failed to submit feedback."}

@router.get("/api/location/search_kakao")
async def search_kakao_location(q: str):
    import requests
    import os
    kakao_key = os.environ.get("KAKAO_REST_API_KEY", "").strip()
    if not kakao_key:
        return {"error": "KAKAO_REST_API_KEY is not configured in .env."}

    url = "https://dapi.kakao.com/v2/local/search/keyword.json"
    headers = {"Authorization": f"KakaoAK {kakao_key}"}
    params = {"query": q, "size": 10}

    try:
        res = requests.get(url, headers=headers, params=params, timeout=5)
        if res.status_code == 200:
            data = res.json()
            results = []
            for doc in data.get("documents", []):
                # Kakao Local API returns y as latitude and x as longitude
                lat_str = doc.get("y", "")
                lon_str = doc.get("x", "")
                
                # We format the name combining the place_name and address for clarity
                place_name = doc.get("place_name", "")
                address_name = doc.get("road_address_name") or doc.get("address_name") or ""
                
                # Combine them so the UI can show detailed info
                full_name = f"{place_name} ({address_name})" if address_name else place_name
                
                # Store the exact bracket format for direct metadata_editor parsing
                if lat_str and lon_str:
                    exact_format = f"[{lat_str[:9]}, {lon_str[:10]}] {place_name}"
                    results.append({"display": full_name, "exact": exact_format})
            return {"results": results}
        else:
            return {"error": f"Kakao API Error: {res.status_code} {res.text}"}
    except Exception as e:
        return {"error": str(e)}
