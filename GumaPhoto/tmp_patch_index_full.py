with open('d:/TheGumaLab/GumaPhoto/templates/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

target = '<!-- Phase 1: API Fetch Modules -->'
replacement = '''<!-- Phase 1 ~ 3: Modular Scripts -->
    <script src="frontend/js_modules/state/store.js"></script>
    <script src="frontend/js_modules/utils.js"></script>
    <script src="frontend/js_modules/components/gallery.js"></script>
    <script src="frontend/js_modules/components/feedback.js"></script>
    <script src="frontend/js_modules/components/lightbox.js"></script>
    <script src="frontend/js_modules/components/upload.js"></script>
    <!-- Phase 1: API Fetch Modules -->'''

if target in html and 'components/gallery.js' not in html:
    html = html.replace(target, replacement)
    
    # Also fix the duplicate utils.js load above it
    bad_part = '''    <!-- Phase 1: Modular Scripts -->
    <script src="frontend/js_modules/state/store.js"></script>
    <script src="frontend/js_modules/utils.js"></script>
    <script src="frontend/js_modules/utils.js"></script>\n'''
    html = html.replace(bad_part, '')
    
    with open('d:/TheGumaLab/GumaPhoto/templates/index.html', 'w', encoding='utf-8') as f:
        f.write(html)
