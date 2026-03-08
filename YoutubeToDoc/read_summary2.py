import os
with open('/app/output/vmaxhbu4YJQ/vmaxhbu4YJQ-summary.html', 'r', encoding='utf-8') as f:
    text = f.read()
    idx = text.find('<div class="caption markdown-body">')
    if idx != -1:
        print(text[idx:idx+300])
