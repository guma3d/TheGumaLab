import re
path = 'd:/TheGumaLab/GumaPhoto/frontend/script_app_v2.js'
with open(path, 'r', encoding='utf-8') as f: content = f.read()

# Phase 1: Utils
content = re.sub(
    r'const createBadge = \([^)]*\) => \{[^}]+\};',
    'const createBadge = window.GumaUtils.createBadge;',
    content
)
content = re.sub(
    r"const getFilename = \(path\) => path \? path\.split\([^)]+\)\.pop\(\) : 'Unknown';",
    'const getFilename = window.GumaUtils.getFilename;',
    content
)

# Fix for building cache from previous chat
content = content.replace("throw new Error('All photos are perfectly categorized!');", "throw new Error('백그라운드에서 피드백 데이터를 추출 중입니다. 잠시 후 다시 시도해주세요.');")
content = content.replace("throw new Error('All regions are perfectly categorized!');", "throw new Error('백그라운드에서 피드백 데이터를 추출 중입니다. 잠시 후 다시 시도해주세요.');")

with open(path, 'w', encoding='utf-8') as f: f.write(content)
print('Phase 1 restored')
