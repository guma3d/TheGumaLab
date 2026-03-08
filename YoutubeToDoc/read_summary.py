import os
with open('/app/output/zsdmj-bF5kM/zsdmj-bF5kM-summary.html', 'r', encoding='utf-8') as f:
    text = f.read()
    idx = text.find('<div class="caption markdown-body">')
    if idx != -1:
        print(text[idx:idx+300])
