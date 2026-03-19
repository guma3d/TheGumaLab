import requests
import json

url = "http://localhost:8085/api/search"
payload = {
    "query": "dummy",
    "offset": 0,
    "limit": 10,
    "is_load_more": True,
    "people": [],
    "location": "",
    "scene": "winter"
}
res = requests.post(url, json=payload)
print(res.status_code)
d = res.json()
print("RESULTS:", len(d.get("results", [])))
