import re

path = r'd:\TheGumaLab\GumaPhoto\api\routers\feedback.py'
with open(path, 'r', encoding='utf-8') as f:
    code = f.read()

# 1. 스크롤 범위를 넓혀 다양한 클러스터를 확보 (500 -> 3000)
code = re.sub(r'limit=500,  # 500개를 캐싱하여 넓은 랜덤풀 생성', r'limit=3000,  # 3000개 캐싱하여 더 방대한 후보군 도출', code)

# 2. 후보군 검사 횟수를 증가 (30 -> 100)
code = re.sub(r'if len\(candidates\) >= 30: # 30개 후보 수집', r'if len(candidates) >= 100: # 100개 후보 수집하여 최강의 덩어리 탐색', code)

with open(path, 'w', encoding='utf-8') as f:
    f.write(code)

print("Priority pool widened.")
