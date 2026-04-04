import re
path = 'd:/TheGumaLab/GumaPhoto/frontend/script_app_v2.js'
with open(path, 'r', encoding='utf-8') as f: lines = f.readlines()

start = -1
end = -1
for i, l in enumerate(lines):
    if 'const feedbackHubBtn = document.getElementById' in l: start = i
    if 'function switchView(' in l: end = i

if start != -1 and end != -1:
    content_to_extract = ''.join(lines[start:end])
    
    header = 'window.GumaFeedback = {};\nwindow.feedbackQueue = [];\n\n'
    footer = '\nwindow.GumaFeedback.preloadFeedbackQueue = preloadFeedbackQueue;\nwindow.preloadFeedbackQueue = preloadFeedbackQueue;\n'
    
    with open('d:/TheGumaLab/GumaPhoto/frontend/js_modules/components/feedback.js', 'w', encoding='utf-8') as f:
        f.write(header + content_to_extract + footer)

    new_lines = lines[:start] + lines[end:]
    with open(path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    print(f'Extracted {end - start} lines to feedback.js')
else:
    print('Could not find start/end markers.')
