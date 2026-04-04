import os
from celery import Celery
from celery.signals import worker_process_init
from core.log_broadcaster import setup_unified_logging

@worker_process_init.connect
def init_celery_stdout_wrapper(**kwargs):
    setup_unified_logging("⚙️[CeleryBot]")

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

app = Celery("gumaphoto_tasks", broker=REDIS_URL, backend=REDIS_URL)

app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Seoul",
    enable_utc=False,
    task_acks_late=True,
    worker_prefetch_multiplier=1
)

# Automatically discover tasks in our modules
app.autodiscover_tasks(["api"])

from celery.schedules import crontab

# Celery Beat 정기 스케줄러 설정
app.conf.beat_schedule = {
    'daily-feedback-cache-rebuild-at-3am': {
        'task': 'tasks.feedback_cache_builder',
        'schedule': crontab(hour=3, minute=0),
    },
    'daily-theme-cache-baking-at-3am': {
        'task': 'tasks.theme_builder',
        'schedule': crontab(hour=3, minute=0), # 매일 새벽 3시 00분
    },
}
