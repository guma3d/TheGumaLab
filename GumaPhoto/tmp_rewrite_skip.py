import sys

path = r'd:\TheGumaLab\GumaPhoto\api\services\feedback_service.py'
with open(path, 'r', encoding='utf-8') as f:
    code = f.read()

target = "    if face_bbox and len(face_bbox) == 4:"
replacement = """    if skip_enrolled_learning:
        learnable = False
        print("  [🛡️ 수동 보호] 사용자가 'Send But NoFeedback'을 요청했습니다. 딥러닝 enrolled 등록을 건너뜁니다.")
    elif face_bbox and len(face_bbox) == 4:"""

if target in code:
    code = code.replace(target, replacement, 1)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(code)
    print("Added skip_enrolled_learning logic.")
else:
    print("Could not find target line!")
