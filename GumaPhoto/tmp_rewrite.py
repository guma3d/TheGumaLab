import sys
path = r'd:\TheGumaLab\GumaPhoto\api\services\feedback_service.py'
with open(path, 'r', encoding='utf-8') as f: lines = f.readlines()

new_lines = []
in_block = False
for i, line in enumerate(lines):
    if line.startswith('    if len(candidates) >= 1:'):
        in_block = True
        new_lines.append("    face_bbox = main_target.get('face_bbox')\n")
        new_lines.append("    learnable = True\n")
        new_lines.append("    if face_bbox and len(face_bbox) == 4:\n")
        new_lines.append("        bw = face_bbox[2] - face_bbox[0]\n")
        new_lines.append("        bh = face_bbox[3] - face_bbox[1]\n")
        new_lines.append("        if bw < 300 or bh < 300:\n")
        new_lines.append("            learnable = False\n")
        new_lines.append("            print(f\"  [🛡️ 딥러닝 보호] BBox 크기({int(bw)}x{int(bh)})가 300px 미만이므로, 품질 보호를 위해 enrolled 등록 및 실시간 벡터 주입을 스킵합니다.\")\n")
        new_lines.append("    else:\n")
        new_lines.append("        learnable = False\n")
        new_lines.append("        \n")
        new_lines.append("    if learnable:\n")
        new_lines.append('    ' + line)
        continue
        
    if in_block:
        if line.startswith('    # 2. 빠른 DB 즉시 덮어쓰기'):
            in_block = False
            new_lines.append(line)
        else:
            if line == '\n':
                new_lines.append(line)
            else:
                new_lines.append('    ' + line)
    else:
        new_lines.append(line)

with open(path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
print('Done editing.')
