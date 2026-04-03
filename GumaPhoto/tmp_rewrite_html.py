import sys
path = r'd:\TheGumaLab\GumaPhoto\templates\index.html'
with open(path, 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Update Scan by Similarity to Send
html = html.replace('Scan by Similarity', 'Send')

# 2. Add fb-no-learning-btn right under fb-submit-btn
old_btn = '''<button id="fb-submit-btn" style="width: 100%; padding: 11px; font-weight: 700; background: linear-gradient(135deg, #10b981, #059669); border: none; font-size: 1.15rem; border-radius: 12px; color: #ffffff; cursor: pointer; box-shadow: 0 8px 20px rgba(16, 185, 129, 0.3); transition: transform 0.2s, box-shadow 0.2s;">
                                Send
                            </button>'''

new_btn = '''<button id="fb-submit-btn" style="width: 100%; padding: 11px; font-weight: 700; background: linear-gradient(135deg, #10b981, #059669); border: none; font-size: 1.15rem; border-radius: 12px; color: #ffffff; cursor: pointer; box-shadow: 0 8px 20px rgba(16, 185, 129, 0.3); transition: transform 0.2s, box-shadow 0.2s;">
                                Send
                            </button>
                            <button id="fb-no-learning-btn" style="display: none; width: 100%; padding: 11px; font-weight: 700; background: rgba(56, 189, 248, 0.15); border: 1px solid rgba(56, 189, 248, 0.4); font-size: 1.05rem; border-radius: 12px; color: #38bdf8; cursor: pointer; transition: all 0.2s;">
                                Send But NoFeedback
                            </button>'''

html = html.replace(old_btn, new_btn)

# 3. Bump version
import re
html = re.sub(r'script_app_v2\.js\?v=\d+', 'script_app_v2.js?v=82', html)

with open(path, 'w', encoding='utf-8') as f:
    f.write(html)
print('HTML updated.')
