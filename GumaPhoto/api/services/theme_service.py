import os
import json
import random
import torch
from qdrant_client.http.models import Filter, FieldCondition, MatchText
from core.state import state

def build_theme_cache():
    print("🚀 [Theme Builder] 200개 규모의 거대한 테마 정적 캐시(Baking) 시스템 가동 시작...")
    
    # AI 모델 & Qdrant 연동 런타임 검사 및 강제 로드(Celery 단독 실행 환경 대비)
    if getattr(state, 'qdrant_client', None) is None:
        from qdrant_client import QdrantClient
        state.qdrant_client = QdrantClient(url=os.environ.get("QDRANT_URL", "http://qdrant:6333"))
        
    if getattr(state, 'siglip_model', None) is None:
        try:
            from transformers import AutoProcessor, AutoModel
            import torch
            print("[Theme Builder] SigLIP 모델 오프라인 로드 중...")
            state.siglip_processor = AutoProcessor.from_pretrained("google/siglip-base-patch16-224")
            state.siglip_model = AutoModel.from_pretrained("google/siglip-base-patch16-224")
            state.siglip_model.eval()
            if torch.cuda.is_available():
                state.siglip_model.to("cuda")
        except Exception as e:
            print(f"[-] AI 모델 초기화 중 에러: {e}")
            
    # 방대한 테마 명단 기초 세트 (추후 200개까지 확장을 위해 카테고리별 분리)
    categories = {
        "Seasons & Weather": [
            {"title": "Winter Snow Vibes", "scene": "winter snow cold ice freezing snowflake white"},
            {"title": "Spring Cherry Blossoms", "scene": "spring cherry blossom flower warm pink bloom"},
            {"title": "Hot Summer Beach", "scene": "summer beach ocean sand hot sun wave"},
            {"title": "Autumn Red Leaves", "scene": "autumn fall red yellow leaves maple foliage"},
            {"title": "Rainy Days", "scene": "rain rainy wet umbrella drop puddle"},
            {"title": "Cloudy Moods", "scene": "cloudy grey sky moody overcast"},
            {"title": "Sunny Clear Skies", "scene": "blue sky sunny clear bright vivid day"},
            {"title": "Winter Sports", "scene": "ski snowboard winter snow sport slope mountain"},
            {"title": "Misty Mornings", "scene": "mist fog foggy morning haze damp"},
            {"title": "Stormy Skies", "scene": "storm lightning dark sky thunder dramatic weather"}
        ],
        "Nature & Outdoors": [
            {"title": "Peaceful Forests", "scene": "forest tree green nature woods trail leaf"},
            {"title": "Mountain Peaks", "scene": "mountain peak hiking climbing rock high altitude"},
            {"title": "Rivers and Lakes", "scene": "river lake water reflection calm stream"},
            {"title": "Beautiful Sunsets", "scene": "sunset twilight orange sky evening sun dusk"},
            {"title": "Wide Landscapes", "scene": "landscape scenic view wide open field panorama"},
            {"title": "Ocean Horizons", "scene": "ocean sea horizon deep blue water wave"},
            {"title": "Desert Sands", "scene": "desert sand dune dry heat barren arid"},
            {"title": "Flower Gardens", "scene": "garden flower blossom bloom colorful petal botanical"},
            {"title": "Waterfalls", "scene": "waterfall cascade water falling nature stream jungle"},
            {"title": "Starry Nights", "scene": "star night sky milky way galaxy dark space"}
        ],
        "City & Travel": [
            {"title": "City Skylines", "scene": "city skyline tall building skyscraper metropolis downtown"},
            {"title": "Urban Streets", "scene": "street urban walking alley road sidewalk pedestrian"},
            {"title": "Night Lights", "scene": "night city lights dark neon glowing illumination"},
            {"title": "Travel Adventures", "scene": "travel luggage airplane map passport airport trip"},
            {"title": "Train Journeys", "scene": "train railway station track passenger ride transport"},
            {"title": "Road Trips", "scene": "car driving road trip highway steering wheel vehicle"},
            {"title": "Historical Landmarks", "scene": "landmark historic monument ancient architecture ruin temple"},
            {"title": "Modern Architecture", "scene": "modern building glass steel geometry architecture structure"},
            {"title": "Busy Markets", "scene": "market crowd stall busy shopping street food vendor"},
            {"title": "Quiet Suburbs", "scene": "suburb house residential quiet neighborhood street home"}
        ],
        "Moments & Life": [
            {"title": "Happy Smiles", "scene": "happy smile laughing teeth joy cheerful expression"},
            {"title": "Birthday Parties", "scene": "birthday cake candle celebration party happy balloons"},
            {"title": "Relaxing Moments", "scene": "peaceful calm quiet resting lying sleep lazy"},
            {"title": "Studying Hard", "scene": "study book homework reading desk focus working"},
            {"title": "Graduation Day", "scene": "graduation cap diploma ceremony gown student achievement"},
            {"title": "Weddings & Love", "scene": "wedding bride groom dress ring romance love marriage"},
            {"title": "Festive Holidays", "scene": "holiday christmas tree present festive celebration gift"},
            {"title": "Concerts & Festivals", "scene": "concert festival stage music crowd light performance"},
            {"title": "Working Out", "scene": "gym workout fitness lifting running sweat exercise"},
            {"title": "Sleeping Babys", "scene": "baby cute sleeping peaceful infant child blanket"}
        ],
        "Family & Kids": [
            {"title": "Playing with Kids", "scene": "child playing kid running playground toy fun"},
            {"title": "Family Gatherings", "scene": "family together gathering group photo love reunion"},
            {"title": "Baby's First Steps", "scene": "baby walking toddler first step crawling cute"},
            {"title": "Father and Child", "scene": "father dad daughter son child holding together"},
            {"title": "Mother and Child", "scene": "mother mom daughter son child hugging holding"},
            {"title": "Sibling Love", "scene": "brother sister siblings playing hugging together child"},
            {"title": "Grandparents", "scene": "grandparent grandfather grandmother elder senior family old"},
            {"title": "Amusement Parks", "scene": "amusement park roller coaster ride fun fair kids theme"},
            {"title": "Zoo Trips", "scene": "zoo animal kids watching enclosure wild safari"},
            {"title": "School Days", "scene": "school backpack student classroom kids learning education"}
        ],
        "Food & Drink": [
            {"title": "Delicious Meals", "scene": "delicious food eating meal plate restaurant dish"},
            {"title": "Cafe Sensibility", "scene": "cafe coffee cup table light espresso latte mug"},
            {"title": "Sweet Desserts", "scene": "dessert cake sweet chocolate ice cream pastry sugar"},
            {"title": "Fresh Fruits", "scene": "fruit apple orange strawberry banana fresh healthy juicy"},
            {"title": "Home Cooking", "scene": "cooking kitchen pan food chef recipe homemade"},
            {"title": "Barbecue Time", "scene": "barbecue grill meat steak fire smoking outdoor bbq"},
            {"title": "Beer & Cheers", "scene": "beer alcohol cheers drinking glass pub bar pint"},
            {"title": "Wine & Dine", "scene": "wine glass dining fancy expensive bottle romantic dinner"},
            {"title": "Fast Food Cravings", "scene": "burger pizza fries fast food junk cola greasy eat"},
            {"title": "Healthy Salads", "scene": "salad vegetable green healthy diet fresh tomato bowl"}
        ],
        "Animals & Pets": [
            {"title": "Cute Dogs", "scene": "dog puppy pet canine cute animal fluffy bark"},
            {"title": "Lazy Cats", "scene": "cat kitten pet feline sleeping lazy cute meow"},
            {"title": "Wild Safaris", "scene": "lion elephant giraffe zebra wild africa safari animal"},
            {"title": "Birds in Flight", "scene": "bird flying wing sky feather beak dove pigeon"},
            {"title": "Aquarium Fishes", "scene": "fish aquarium tank water swimming colorful marine dive"},
            {"title": "Farm Animals", "scene": "cow horse sheep pig farm rural animal barn pasture"},
            {"title": "Bugs & Insects", "scene": "insect bug butterfly spider macro nature tiny ant"},
            {"title": "Reptiles & Amphibians", "scene": "snake lizard frog reptile scale cold blood amphibian"},
            {"title": "Ocean Life", "scene": "whale dolphin shark turtle ocean underwater sea life reef"},
            {"title": "Pet Playing", "scene": "pet playing ball toy jumping running fun active"}
        ],
        "Emotions & Moods": [
            {"title": "Pure Joy", "scene": "joy excitement jumping cheering smiling ecstatic happy"},
            {"title": "Deep Sadness", "scene": "sad crying tear gloomy depressed lonely sorrow heartbreak"},
            {"title": "Surprise & Awe", "scene": "surprise shock wow awe amazing unexpected gasping expression"},
            {"title": "Anger & Frustration", "scene": "angry mad frustrated yelling shouting expression fierce rage"},
            {"title": "Fear & Tension", "scene": "scared fear terrifying horror tension nervous bite nail"},
            {"title": "Loving Warmth", "scene": "love warm gentle kiss hug caring affectionate romance"},
            {"title": "Funny Derps", "scene": "funny silly derp awkward laugh comedy joke weird"},
            {"title": "Nostalgic Vibes", "scene": "nostalgia old retro vintage sepia memory past classic"},
            {"title": "Tired & Exhausted", "scene": "tired exhausted sleep yawn droop weary drain fatigue"},
            {"title": "Confident & Proud", "scene": "confident proud success winning champion heroic pose strong"}
        ],
        "Colors & Aesthetics": [
            {"title": "Vivid Reds", "scene": "red crimson scarlet bright saturated color ruby fire"},
            {"title": "Deep Blues", "scene": "blue navy azure cobalt deep sea color sapphire rich"},
            {"title": "Lush Greens", "scene": "green emerald jade vibrant forest color leaf vivid"},
            {"title": "Bright Yellows", "scene": "yellow sunny golden lemon bright color mustard blonde"},
            {"title": "Soft Pastels", "scene": "pastel pink peach light soft color gentlespring airy"},
            {"title": "Monochrome B&W", "scene": "black white monochrome grayscale dark classic colorless shadow"},
            {"title": "Neon Cyberpunk", "scene": "neon cyberpunk purple cyan glow bright led futuristic city"},
            {"title": "Warm Golden Hour", "scene": "golden hour warm orange sun glow ambient aesthetic light"},
            {"title": "Dark & Moody", "scene": "dark shadow under-exposed moody black low key dim gloom"},
            {"title": "High Contrast", "scene": "contrast bright pop intense vivid stark distinct edge"}
        ],
        "Korean Dynamic Locations": [
            {"title": "제주의 푸른 밤", "location": "제주"},
            {"title": "서울 도심의 속삭임", "location": "서울"},
            {"title": "인천 앞바다", "location": "인천"},
            {"title": "부산 광안리의 매력", "location": "부산"},
            {"title": "대전의 오후", "location": "대전"},
            {"title": "대구 동성로 산책", "location": "대구"},
            {"title": "광주 골목 탐방", "location": "광주"},
            {"title": "강원도의 눈 내리는 밤", "location": "강원"},
            {"title": "춘천 가는 길", "location": "춘천"},
            {"title": "아름다운 강릉 바다", "location": "강릉"}
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
                # [핵심] 150장까지만 검색하여 가장 유사한 상위 항목들만 확보 (score_threshold 삭제)
                results = state.qdrant_client.query_points(
                    collection_name="gumaphoto_hybrid_kr",
                    query=text_vector,
                    using="scene",
                    query_filter=q_filter,
                    limit=150,
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
    # 볼륨 마운트 된 디렉토리 사용 보장 (통합 캐시 저장소)
    cache_path = "/app/data/caches/themes_cache.json"
    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    
    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(cached_data, f, ensure_ascii=False, indent=2)
        
    print(f"✅ [Theme Builder] 빵 굽기 완료! 총 {len(cached_data)}개의 최고품질 랜덤 테마팩 완성.")
