import json
import urllib.request

url = "http://localhost:6337/collections/gumaphoto_hybrid_kr/points/scroll"
headers = {"Content-Type": "application/json"}
data = {
    "filter": {
        "should": [
            {
                "key": "people",
                "match": {
                    "value": "Unknown Person"
                }
            },
            {
                "key": "people",
                "match": {
                    "value": "Unknown People"
                }
            }
        ]
    },
    "limit": 5,
    "with_payload": ["people"]
}

req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'), headers=headers)
try:
    with urllib.request.urlopen(req) as response:
        result = json.loads(response.read().decode('utf-8'))
        print("Total returned:", len(result.get('result', {}).get('points', [])))
        for p in result.get('result', {}).get('points', []):
            print(p['payload'])
except Exception as e:
    print(e)
