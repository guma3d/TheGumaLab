import os

path1 = r'd:\TheGumaLab\GumaPhoto\api\tasks.py'
c1 = open(path1, 'r', encoding='utf-8').read()
if 'tasks.feedback_cache_builder' not in c1:
    c1 = c1 + '''\n\n@app.task(name="tasks.feedback_cache_builder")
def run_feedback_builder_job():
    try:
        import urllib.request
        print("🚀 [Celery] 새벽 3시 피드백 캐시 갱신 시작...")
        urllib.request.urlopen("http://gumaphoto_app:8000/api/feedback_v2/rebuild_cache_now", data=b"", timeout=10)
    except Exception as e:
        pass\n'''
    open(path1, 'w', encoding='utf-8').write(c1)

path2 = r'd:\TheGumaLab\GumaPhoto\core\celery_app.py'
c2 = open(path2, 'r', encoding='utf-8').read()
target = "'daily-theme-cache-baking-at-3am': {"
if 'daily-feedback-cache-rebuild-at-3am' not in c2:
    new_beat = """'daily-feedback-cache-rebuild-at-3am': {
        'task': 'tasks.feedback_cache_builder',
        'schedule': crontab(hour=3, minute=0),
    },
    'daily-theme-cache-baking-at-3am': {"""
    c2 = c2.replace(target, new_beat)
    open(path2, 'w', encoding='utf-8').write(c2)

print("Patch applied successfully.")
