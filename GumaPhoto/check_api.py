import requests
import json
import sys

try:
    url = "http://localhost:8085/api/search"
    payload = {
        "query": "",
        "offset": 0,
        "limit": 20,
        "is_load_more": False,
        "people": [],
        "location": "",
        "scene": ""
    }
    headers = {"Content-Type": "application/json"}
    
    response = requests.post(url, json=payload, headers=headers)
    print(f"Status: {response.status_code}")
    data = response.json()
    print("KEYS:", data.keys())
    if "themes" in data:
        print("THEMES:", len(data["themes"]))
        for t in data["themes"]:
            print(f"  - {t['title']} (Photos: {len(t['photos'])})")
    if "results" in data:
        print("RESULTS:", len(data["results"]))
    if "error" in data:
        print("ERROR:", data["error"])
        
except Exception as e:
    print("Error:", e)
