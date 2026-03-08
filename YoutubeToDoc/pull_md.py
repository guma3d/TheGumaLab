import json
with open('/app/data/task_status.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
    print(list(data.values())[0]["result"]["summary"][:500])
