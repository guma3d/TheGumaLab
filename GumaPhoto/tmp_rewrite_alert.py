import re

path = r'd:\TheGumaLab\GumaPhoto\frontend\script_app_v2.js'
with open(path, 'r', encoding='utf-8') as f:
    js = f.read()

# Note: The original alert might have slightly different characters (like encoding issues in the output),
# so we will use regex to find the alert near reload()
js = re.sub(
    r'alert\([^)]*Feedback submitted successfully[^)]*\);',
    r'alert(`총 ${targetPointsArray.length || 1}장의 사진이 수정되었습니다. 화면을 새로고침합니다.`);',
    js
)

with open(path, 'w', encoding='utf-8') as f:
    f.write(js)

path2 = r'd:\TheGumaLab\GumaPhoto\templates\index.html'
with open(path2, 'r', encoding='utf-8') as f:
    html = f.read()

html = re.sub(r'script_app_v2\.js\?v=\d+', 'script_app_v2.js?v=85', html)

with open(path2, 'w', encoding='utf-8') as f:
    f.write(html)

print("Alert updated and version bumped to 85.")
