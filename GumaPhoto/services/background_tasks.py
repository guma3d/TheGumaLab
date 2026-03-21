import os
import asyncio
from core.state import state

# [Event-Driven Architecture] Event-Bus에 이벤트를 던지는 마이크로서비스용 퍼블리셔
from core.events import publish_event

def trigger_upload_pipeline():
    """백그라운드에서 실행되던 복잡한 3순환 파이프라인 (완전 이벤트 드리븐으로 결합 끊음)"""
    
    with state.upload_lock:
        if state.pipeline_running:
            state.needs_rerun = True
            print("⏳ [Scheduler] 파이프라인 가동 기록 확인 (신규 파일 접수를 계속 마킹해둠)")
            return
        state.pipeline_running = True
        state.needs_rerun = False
        
    try:
        print("🚀 [Publisher 📡] 새 사진 업로드 또는 재검열 발견! Event Bus에 방송(FileUploaded)을 날립니다!")
        # 🔗 더 이상 Organizer를 직접 호명하지 않습니다. 
        # 단순히 'FileUploaded' 사건이 터졌다고 전 세계 인터넷(Redis)으로 송출할 뿐입니다.
        publish_event("FileUploaded", {"source": "direct_trigger"})
        
        with state.upload_lock:
            state.pipeline_running = False
            state.needs_rerun = False
            print("✅ [Publisher] 파이프라인 이벤트 송출이 완료되어 로컬 폰툰 락을 해제합니다.")
            
    except Exception as e:
        print(f"❌ [Publisher Error] 이벤트 송출 중 오류 발생: {e}")
        with state.upload_lock:
            state.pipeline_running = False
            state.needs_rerun = False

async def scheduled_scan(interval_seconds: int = 3600):
    """지정된 시간(기본 1시간)마다 주기적으로 uploads_raw 폴더를 스캔하여 파이프라인 무인 가동"""
    print(f"⏱️ [Autonomous Scanner 🛰️] 무인 정찰기가 백그라운드 궤도에 진입했습니다. ({interval_seconds // 60}분 단위)")
    while True:
        await asyncio.sleep(interval_seconds)
        try:
            if not os.path.exists(state.upload_dir):
                continue
            files_exist = any(os.path.isfile(os.path.join(state.upload_dir, f)) for f in os.listdir(state.upload_dir) if not f.startswith('.'))
            if files_exist:
                print(f"⏱️ [Scanner 알람 🔔] 정기 레이더 정찰 중 미분류 파일 조각 발견! 즉각 방송(FileUploaded)을 때립니다!")
                publish_event("FileUploaded", {"source": "autonomous_scheduler"})
        except asyncio.CancelledError:
            break
        except Exception as e:
            pass
