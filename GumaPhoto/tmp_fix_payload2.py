import os

path = r'd:\TheGumaLab\GumaPhoto\api\services\feedback_cache.py'
code = open(path, 'r', encoding='utf-8').read()
code = code.replace('with_payload=["location", "date", "people"]', 'with_payload=["location", "date", "people", "filepath"]')
open(path, 'w', encoding='utf-8').write(code)

print("Updated fallback properly.")
