import urllib.request, json
req = urllib.request.Request(
    'http://localhost:8000/api/search',
    data=json.dumps({"query": "강원도 사진", "offset": 0, "limit": 50}).encode('utf-8'),
    headers={'Content-Type': 'application/json'}
)
print(urllib.request.urlopen(req).read().decode('utf-8'))
