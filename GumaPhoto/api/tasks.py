from core.celery_app import app

@app.task(name="tasks.theme_builder")
def run_theme_builder_job():
    try:
        from api.services.theme_service import build_theme_cache
        build_theme_cache()
    except Exception as e:
        print(f"❌ [Celery] Theme Builder 오류: {e}")
        raise

@app.task(name="tasks.organizer")
def run_organizer_job():
    try:
        from api.routers.organizer import run_organizer_task
        print("🚀 [Celery] Organizer 파이프라인 가동 시작...")
        run_organizer_task()
        print("✅ [Celery] Organizer 작업 완료!")
    except Exception as e:
        print(f"❌ [Celery] Organizer 오류: {e}")
        raise

@app.task(name="tasks.indexer")
def run_indexer_job():
    try:
        import sys
        sys.path.append("/app")
        from vector_indexer import VectorIndexer
        print("🚀 [Celery] 최신 메인 Vector Indexer (딥러닝 VRAM 가동) 시작...")
        idx_bot = VectorIndexer()
        idx_bot.run()
        print("✅ [Celery] 최신 Vector Indexer 작업 완료! VRAM 100% 반환 대기 중...")
    except Exception as e:
        print(f"❌ [Celery] Vector Indexer 오류: {e}")
        raise

@app.task(name="tasks.dispatch_event")
def dispatch_event(event_type: str, payload: dict):
    """
    [Event-Driven Architecture: Event Hub / Router]
    이벤트 광장(Redis Pub/Sub)에서 들려오는 방송을 수신하여 
    전 세계의 구독자(Subscriber 봇들)를 적재적소에 출동시키는 관제탑 역할
    """
    print(f"👂 [Event Subscriber 📡] '{event_type}' 방송을 무전 수신했습니다. 관제탑에서 해당 워커들을 출동시킵니다.")
    
    if event_type == "FileUploaded":
        # 🔔 사건 접수: 새 원본 사진들이 쏟아짐!
        # 🤖 출동 부서: 정리정돈 봇
        run_organizer_job.delay()
        
    elif event_type == "FileOrganized":
        # 🔔 사건 접수: 하드디스크에 사진들이 년도별로 너무 예쁘게 정리되었음!
        # 🤖 출동 부서: AI 딥러닝 봇 (VRAM 투입)
        run_indexer_job.delay()
