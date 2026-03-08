import urllib.request, json
try:
    print(urllib.request.urlopen(urllib.request.Request('http://localhost:5000/admin/regenerate-html', data=json.dumps({"password":"admin", "task_id":"all"}).encode(), headers={'Content-Type': 'application/json'})).read().decode())
except Exception as e:
    print(e)
