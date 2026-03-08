import json
with open('/app/data/task_status.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
t1 = data.get('207f7c1f-34bd-4a74-80f7-0e11e8d8f7e2')
if t1:
    print(t1.get('result', {}).get('summary', '')[:200])
else:
    print("Not found")
