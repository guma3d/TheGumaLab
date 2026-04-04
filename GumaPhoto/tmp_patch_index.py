with open('d:/TheGumaLab/GumaPhoto/templates/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Add gallery and feedback (since I reverted index.html checkout)
if 'components/gallery.js' not in html:
    html = html.replace(
        '<script src="frontend/js_modules/utils.js"></script>',
        '<script src="frontend/js_modules/utils.js"></script>\n    <script src="frontend/js_modules/components/gallery.js"></script>\n    <script src="frontend/js_modules/components/feedback.js"></script>\n    <script src="frontend/js_modules/components/lightbox.js"></script>',
        1
    )
elif 'components/lightbox.js' not in html:
    html = html.replace(
        '<script src="frontend/js_modules/components/feedback.js"></script>',
        '<script src="frontend/js_modules/components/feedback.js"></script>\n    <script src="frontend/js_modules/components/lightbox.js"></script>'
    )

with open('d:/TheGumaLab/GumaPhoto/templates/index.html', 'w', encoding='utf-8') as f:
    f.write(html)
