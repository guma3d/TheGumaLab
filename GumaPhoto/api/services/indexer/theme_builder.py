import os
import json
import random
import torch
from qdrant_client.http.models import Filter, FieldCondition, MatchText
from core.state import state

def build_theme_cache():
    print("🚀 [Theme Builder] 200개 규모의 거대한 테마 정적 캐시(Baking) 시스템 가동 시작...")
    
    # AI 모델 & Qdrant 연동 런타임 검사 및 강제 로드(Celery 단독 실행 환경 대비)
    if state.qdrant_client is None or getattr(state, 'siglip_model', None) is None:
        try:
            from core.startup import init_ai_models, init_qdrant
            init_qdrant()
            init_ai_models()
        except Exception as e:
            print(f"[-] AI 모델 초기화 중 에러: {e}")
            
    # 방대한 테마 명단 기초 세트 (추후 200개까지 확장을 위해 카테고리별 분리)
    categories = {
        "Seasons & Weather": [
            {"title": "Winter Snow Vibes", "scene": "winter snow cold ice"},
            {"title": "Spring Cherry Blossoms", "scene": "spring cherry blossom flower warm"},
            {"title": "Hot Summer Beach", "scene": "summer beach ocean sand hot"},
            {"title": "Autumn Red Leaves", "scene": "autumn fall red yellow leaves"},
            {"title": "Rainy Days", "scene": "rain rainy wet umbrella"},
            {"title": "Cloudy Moods", "scene": "cloudy grey sky moody"}
        ],
        "Nature & Outdoors": [
            {"title": "Peaceful Forests", "scene": "forest tree green nature woods"},
            {"title": "Mountain Peaks", "scene": "mountain peak hiking climbing"},
            {"title": "Rivers and Lakes", "scene": "river lake water reflection"},
            {"title": "Beautiful Sunsets", "scene": "sunset twilight orange sky evening"},
            {"title": "Sunny Skies", "scene": "blue sky sunny clear vivid"},
            {"title": "Wide Landscapes", "scene": "landscape scenic view wide"}
        ],
        "City & Travel": [
            {"title": "City Skylines", "scene": "city skyline tall building skyscraper"},
            {"title": "Urban Streets", "scene": "street urban walking alley"},
            {"title": "Night Lights", "scene": "night city lights dark neon"},
            {"title": "Cafe Sensibility", "scene": "cafe coffee cup table light"},
            {"title": "Restaurant Dining", "scene": "restaurant food eating dinner"},
            {"title": "Travel Adventures", "scene": "travel luggage airplane map passport"}
        ],
        "Moments & Life": [
            {"title": "Happy Smiles", "scene": "happy smile laughing teeth joy"},
            {"title": "Delicious Meals", "scene": "delicious food eating meal plate"},
            {"title": "Animal & Pets", "scene": "dog cat pet furry animal"},
            {"title": "Reading Time", "scene": "book reading library desk quiet"},
            {"title": "Sports & Action", "scene": "sports running playing active sweat"},
            {"title": "Art & Museums", "scene": "museum art gallery painting exhibition statue"},
            {"title": "Birthday Parties", "scene": "birthday cake candle celebration party"},
            {"title": "Relaxing Moments", "scene": "peaceful calm quiet resting lying"}
        ],
        "Dynamic Locations": [
            {"title": "Jeju Island Getaways", "location": "제주"},
            {"title": "Seoul City Vibes", "location": "서울"},
            {"title": "Incheon Stops", "location": "인천"},
            {"title": "San Francisco Memories", "location": "San Francisco"},
            {"title": "Las Vegas Nights", "location": "Las Vegas"}
        ]
    }
    
    # 카테고리 평탄화
    all_themes = []
    for cat_name, themes in categories.items():
        all_themes.extend(themes)
        
    print(f"[*] 총 {len(all_themes)}개 테마 검수를 시작합니다. 조건: 유사율 80% 이상, 최대 100장 무작위 픽업")
    
    cached_data = []
    
    for theme in all_themes:
        must_conds = []
        scene_query = theme.get("scene", "")
        loc_query = theme.get("location", "")
        
        if loc_query:
            must_conds.append(FieldCondition(key="location", match=MatchText(text=loc_query)))
            
        q_filter = Filter(must=must_conds) if must_conds else None
        text_vector = None
        
        # 1. 텍스트 영문 쿼리를 SigLIP 벡터로 변환
        if scene_query and getattr(state, 'siglip_model', None):
            with torch.no_grad():
                inputs = state.siglip_processor(text=[scene_query], padding="max_length", return_tensors="pt")
                inputs = {k: v.to(state.siglip_model.device) for k, v in inputs.items()}
                text_features = state.siglip_model.get_text_features(**inputs)
                text_features = text_features / text_features.norm(p=2, dim=-1, keepdim=True)
                text_vector = text_features[0].cpu().numpy().tolist()
                
        # 2. Qdrant 질의
        try:
            if text_vector:
                # [핵심] 500장까지 넓게 검색하되 score_threshold=0.8 로 정밀 타격
                results = state.qdrant_client.query_points(
                    collection_name="gumaphoto_hybrid_kr",
                    query=text_vector,
                    using="scene",
                    query_filter=q_filter,
                    limit=500,
                    score_threshold=0.80,
                    with_payload=True
                ).points
            else:
                # 벡터 검색이 없는 키워드일 경우 (location 등)
                res_scroll, _ = state.qdrant_client.scroll(
                    collection_name="gumaphoto_hybrid_kr",
                    scroll_filter=q_filter,
                    limit=500,
                    with_payload=True
                )
                results = res_scroll
                
            # 3. Random Sampling: 1장이라도 있다면, 풀(Pool) 안에서 최대 100장만 무작위(Random) 선택
            if len(results) > 0:
                actual_sample_size = min(len(results), 100)
                selected_hits = random.sample(results, actual_sample_size)
                
                photos = []
                for hit in selected_hits:
                    payload = getattr(hit, 'payload', {}) or {}
                    filepath = payload.get("filepath", "")
                    if not filepath: continue
                    photo_url = filepath.replace("/app/data/organized", "/photos")
                    photos.append({
                        "id": hit.id,
                        "url": photo_url,
                        "original_path": filepath,
                        "date": payload.get("date", "Unknown"),
                        "location": payload.get("location", "Unknown Location"),
                        "people": payload.get("people", [])
                    })
                    
                cached_data.append({
                    "title": theme["title"],
                    "photos": photos
                })
                print(f"  [+] 통과 '{theme['title']}': 총 {len(results)}장 중 {actual_sample_size}장 랜덤 픽업 완료")
            else:
                print(f"  [-] 탈락 '{theme['title']}': 유사도 80% 이상의 적합한 사진 없음")
                
        except Exception as e:
            print(f"  [!] 테마 처리 에러 '{theme['title']}': {e}")
            
    # 4. JSON 파일 저장(Baking)
    # 볼륨 마운트 된 디렉토리 사용 보장
    cache_path = "/app/data/frontend/themes_cache.json"
    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    
    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(cached_data, f, ensure_ascii=False, indent=2)
        
    print(f"✅ [Theme Builder] 빵 굽기 완료! 총 {len(cached_data)}개의 최고품질 랜덤 테마팩 완성.")
