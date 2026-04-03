import urllib.request
import json
import traceback

req = urllib.request.Request("http://localhost:8000/api/search", method="POST")
req.add_header("Content-Type", "application/json")
data = json.dumps({
    "query": "하와이",
    "offset": 0,
    "limit": 50,
    "people": [],
    "location": "",
    "objects": [],
    "scene": "",
    "is_load_more": False,
    "date": "",
    "sort": "desc"
}).encode("utf-8")

try:
    with urllib.request.urlopen(req, data=data) as response:
        res = json.loads(response.read().decode("utf-8"))
        print("Results count:", len(res.get("results", [])))
        if res.get("results"):
            print("First item:", res["results"][0])
except Exception as e:
    print("Error:", e)
    traceback.print_exc()
