with open('d:/TheGumaLab/GumaPhoto/templates/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# I will just write the EXACT block
target_block = '''    <!-- UI Interaction Library (Zoom) -->
    <script src="https://unpkg.com/@panzoom/panzoom@4.5.1/dist/panzoom.min.js"></script>
    <script src="frontend/guma-earth_app.js?v=71"></script>
    <!-- Phase 1 ~ 3: Modular Scripts -->
    <script src="frontend/js_modules/state/store.js"></script>
    <script src="frontend/js_modules/utils.js"></script>
    <script src="frontend/js_modules/components/gallery.js"></script>
    <script src="frontend/js_modules/components/feedback.js"></script>
    <script src="frontend/js_modules/components/lightbox.js"></script>
    <script src="frontend/js_modules/components/upload.js"></script>
    <script src="frontend/js_modules/components/monitor.js"></script>
    <!-- Phase 1: API Fetch Modules -->
    <script type="module" src="frontend/js_modules/api/fetcher.js"></script>
    <script src="frontend/script_app_v2.js?v=94"></script>'''

import re
# Find the part from UI Interaction Library to <script src="frontend/script_app_v2.js
pattern = r'<!-- UI Interaction Library \(Zoom\) -->.*?<script src="frontend/script_app_v2\.js[^>]+></script>'
html = re.sub(pattern, target_block, html, flags=re.DOTALL)

with open('d:/TheGumaLab/GumaPhoto/templates/index.html', 'w', encoding='utf-8') as f:
    f.write(html)
