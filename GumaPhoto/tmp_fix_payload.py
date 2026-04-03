import os

path = r'd:\TheGumaLab\GumaPhoto\api\services\feedback_cache.py'
code = open(path, 'r', encoding='utf-8').read()
code = code.replace('with_payload=True', 'with_payload=["location", "date", "people"]')
open(path, 'w', encoding='utf-8').write(code)

path2 = r'd:\TheGumaLab\GumaPhoto\api\routers\feedback.py'
code2 = open(path2, 'r', encoding='utf-8').read()
code2 = code2.replace('with_payload=True', 'with_payload=["location", "date", "people", "face_bbox", "filepath"]')
open(path2, 'w', encoding='utf-8').write(code2)

print("Optimized payload loading!")
