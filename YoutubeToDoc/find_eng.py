import re

with open('YoutubeToDoc/t_jyTILDYo8.html', 'r', encoding='utf-8') as f:
    content = f.read()

captions = re.findall(r'<div class="caption markdown-body">(.*?)</div>', content, re.DOTALL)
count = 0
for c in captions:
    korean = len(re.findall(r'[가-힣]', c))
    if korean < 5:
        count += 1
        print("Mostly English segment:", c.strip()[:100])

print(f"Total empty/english segments: {count}")
