import re
path = 'd:/TheGumaLab/GumaPhoto/frontend/script_app_v2.js'
with open(path, 'r', encoding='utf-8') as f: lines = f.readlines()

def get_block(start_match):
    start = -1
    for i, l in enumerate(lines):
        if start_match in l: start = i; break
    if start == -1: return -1, -1
    
    braces = 0
    end = -1
    for i in range(start, len(lines)):
        braces += lines[i].count('{') - lines[i].count('}')
        if braces == 0:
            end = i
            break
    return start, end

# 1. extract renderThemes
st1, ed1 = get_block('function renderThemes(')
themes_code = ''.join(lines[st1:ed1+1])

# 2. extract renderGallery
st2, ed2 = get_block('function renderGallery(')
gallery_code = ''.join(lines[st2:ed2+1])

# write to components/gallery.js
out = 'window.GumaGallery = {};\n\n' + themes_code + '\nwindow.GumaGallery.renderThemes = renderThemes;\n\n' + gallery_code + '\nwindow.GumaGallery.renderGallery = renderGallery;\n'
with open('d:/TheGumaLab/GumaPhoto/frontend/js_modules/components/gallery.js', 'w', encoding='utf-8') as f:
    f.write(out)

# remove from script_app_v2.js
to_remove = set(range(st1, ed1+1)) | set(range(st2, ed2+1))
new_lines = [l for i, l in enumerate(lines) if i not in to_remove]
content = ''.join(new_lines)

content = re.sub(r'\brenderThemes\(', 'window.GumaGallery.renderThemes(', content)
content = re.sub(r'\brenderGallery\(', 'window.GumaGallery.renderGallery(', content)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print('Phase 3_1 restored')
