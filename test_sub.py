import requests
import json
payload = {
    "point_id": "735d9cee-76a3-5a9c-ab09-64f35d02d969", 
    "issue_type": "Location", 
    "correct_value": "대한민국-부천시", 
    "target_points": ["735d9cee-76a3-5a9c-ab09-64f35d02d969", "25d80482-1ddc-4cff-bee7-01a61c37b7ad", "f0f6c2c7-bdce-4ab8-a14a-10fcc39cf5c7"] 
}
r = requests.post("http://localhost:8000/api/feedback_v2/submit", json=payload)
print(r.status_code, r.text)
