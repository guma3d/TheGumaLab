import urllib.request
import json
import sys

try:
    req = urllib.request.Request(
        "http://localhost:5000/admin/regenerate-html",
        data=json.dumps({"password":"admin", "task_id":"all"}).encode('utf-8')
    )
    req.add_header('Content-Type', 'application/json')
    response = urllib.request.urlopen(req)
    print("Success:", response.read().decode('utf-8'))
except Exception as e:
    print("Error:", e)
    if hasattr(e, 'read'):
        print(e.read().decode('utf-8'))
