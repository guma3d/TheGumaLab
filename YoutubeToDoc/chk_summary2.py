import json
with open('/app/data/task_status.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
t1 = data.get('97888841-bb67-4443-86e1-bae35bc93bda')
if t1:
    print(t1.get('result', {}).get('summary', '')[:200])
else:
    print("Not found")
