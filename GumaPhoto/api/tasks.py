from core.celery_app import app

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
        from Scripts.vector_indexer import VectorIndexer
        print("🚀 [Celery] Vector Indexer (딥러닝 VRAM 가동) 시작...")
        idx_bot = VectorIndexer()
        idx_bot.run()
        print("✅ [Celery] Vector Indexer 작업 완료!")

        # 인덱싱 완료 후 타임라인 캐시 자동 갱신
        try:
            from api.routers.search import rebuild_timeline_cache
            rebuild_timeline_cache()
        except Exception as ce:
            print(f"⚠️ [Celery] Timeline Cache 갱신 실패 (검색은 정상 작동): {ce}")
    except Exception as e:
        print(f"❌ [Celery] Vector Indexer 오류: {e}")
        raise

@app.task(name="tasks.dispatch_event")
def dispatch_event(event_type: str, payload: dict):
    print(f"👂 [Event Subscriber] '{event_type}' 수신. 워커 출동.")

    if event_type == "FileUploaded":
        run_organizer_job.delay()
    elif event_type == "FileOrganized":
        run_indexer_job.delay()
