import datetime
from api.tasks import dispatch_event

def publish_event(event_type: str, payload: dict = None):
    """
    [Event-Driven Architecture 핵심 중계기]
    어떤 모듈이 작업(Upload, Organize, Delete)을 마친 뒤, 다음 타자를 "직접" 호출하지 않고
    이 함수를 통해 허공에 "나 일 끝났어!" 라고 외치는(Publish) 광장 역할을 합니다.
    각 봇(Subscriber)들은 이 외침을 듣고 알아서 움직이므로 강제 결합(Coupling)이 사라집니다.
    """
    event_data = payload or {}
    event_data["timestamp"] = datetime.datetime.now().isoformat()
    
    print(f"📢 [Event Bus 📡] '{event_type}' 이벤트가 전역(Global)으로 방송되었습니다. (Payload: {event_data})")
    
    # Celery 큐의 Event Bus Router(허브)로 이벤트를 위임합니다.
    dispatch_event.delay(event_type, event_data)
