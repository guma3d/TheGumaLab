from fastapi import APIRouter
from pydantic import BaseModel
import typing
import os
import json
import sqlite3
from core.state import state
from qdrant_client.http.models import Filter, FieldCondition, MatchValue
import random

router = APIRouter()

class FeedbackV2Request(BaseModel):
    point_id: typing.Union[int, str]
    issue_type: str
    correct_value: str
    target_points: typing.Optional[typing.List[typing.Union[int, str]]] = []

@router.get("/api/feedback_v2/unknown")
async def get_unknown_photo():
    if not state.qdrant_client: return {"error": "Qdrant not loaded"}
    
    try:
        search_res = state.qdrant_client.scroll(
            collection_name="gumaphoto_hybrid_kr",
            scroll_filter=Filter(
                should=[
                    FieldCondition(key="date", match=MatchValue(value="Unknown-Year")),
                    FieldCondition(key="location", match=MatchValue(value="위치정보없음")),
                    FieldCondition(key="location", match=MatchValue(value="Unknown-Location"))
                ]
            ),
            limit=500,
            with_payload=True
        )[0]
        
        if search_res:
            raw_target = random.choice(search_res)
            loc = raw_target.payload.get("location", "")
            people = raw_target.payload.get("people", [])
            date_val = raw_target.payload.get("date", "")
            filepath = raw_target.payload.get("filepath", "")
            
            issues = []
            if "Unknown" in date_val or not date_val:
                issues.append("Date")
            if "위치정보없음" in loc or "Unknown" in loc or not loc:
                issues.append("Location")
                
            if issues:
                issue = random.choice(issues)
                url_path = filepath.replace("/app/data/organized", "/photos")
                return {
                    "id": raw_target.id,
                    "url": url_path,
                    "issue": issue,
                    "date": date_val,
                    "location": loc,
                    "people": people
                }
    except Exception as e:
        print(f"Qdrant Scroll 예외 발생: {e}")

    return {"id": None, "message": "현재 피드백이 필요한 사진을 찾지 못했습니다."}

@router.post("/api/feedback_v2/submit")
async def submit_feedback_v2(req: FeedbackV2Request):
    fb_type = "face" if "People" in req.issue_type else "time_loc"
    
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
    tp_json = json.dumps(req.target_points) if req.target_points else "[]"
    
    try:
        if fb_type == "face":
            from api.tasks import run_feedback_face_job
            run_feedback_face_job.delay(str(req.point_id), db_correct_value, tp_json)
        else:
            if db_correct_value.startswith("DATE|"):
                date_val = db_correct_value.split("|", 1)[1]
                from api.tasks import run_feedback_time_loc_job
                run_feedback_time_loc_job.delay(str(req.point_id), date_val, "Unknown", tp_json)
            elif db_correct_value.startswith("LOC|"):
                loc_val = db_correct_value.split("|", 1)[1]
                from api.tasks import run_feedback_time_loc_job
                run_feedback_time_loc_job.delay(str(req.point_id), "Unknown", loc_val, tp_json)
            else:
                from api.tasks import run_feedback_time_loc_job
                run_feedback_time_loc_job.delay(str(req.point_id), "Unknown", db_correct_value, tp_json)
                
        print(f"🚀 [Feedback v2.0 -> Redis] Celery 대기열에 지시서 발송 완료! (ID: {req.point_id})")
        return {"message": "정답이 Redis 대기열 큐로 즉각 발송되었습니다! 순차 처리 봇이 안전하게 스캔합니다."}
        
    except Exception as e:
        print(f"❌ [Feedback v2.0 -> Redis] 큐 발송 실패: {e}")
        return {"error": str(e)}
