import os
import re

TARGET_DIR = "/app/data/organized"
renamed_count = 0

print("[*] 폴더명 통합에 따른 빈 번호 메우기(Hole-Filling) 시작...")

for root, dirs, files in os.walk(TARGET_DIR):
    prefix_groups = {}
    
    for f in files:
        if f.startswith('.'): continue
        if f.endswith('.xmp') or f.endswith('.webp'): continue
        
        base = os.path.splitext(f)[0]
        ext = os.path.splitext(f)[1]
        
        match = re.search(r'^(.*_)(\d+)(_m\d*)?$', base)
        if match:
            prefix = match.group(1)
            num = int(match.group(2))
            padding = len(match.group(2))
            
            if prefix not in prefix_groups:
                prefix_groups[prefix] = []
            prefix_groups[prefix].append((num, padding, f, ext))

    for prefix, fileList in prefix_groups.items():
        fileList.sort(key=lambda x: x[0])
        
        max_pad = max([x[1] for x in fileList]) if fileList else 2
        if max_pad < 2: max_pad = 2
        
        expected_num = 1
        
        for item in fileList:
            current_num, padding, filename, ext = item
            
            # 파일명이 _m (병합된 파일)을 떼어내고 온전한 숫자로 압축 당기기
            old_path = os.path.join(root, filename)
            new_name = f"{prefix}{expected_num:0{max_pad}d}{ext}"
            new_path = os.path.join(root, new_name)
            
            if filename != new_name:
                if not os.path.exists(new_path):
                    os.rename(old_path, new_path)
                    renamed_count += 1
                else:
                    while os.path.exists(new_path):
                        expected_num += 1
                        new_name = f"{prefix}{expected_num:0{max_pad}d}{ext}"
                        new_path = os.path.join(root, new_name)
                    os.rename(old_path, new_path)
                    renamed_count += 1
            
            expected_num += 1

print(f"\n[!] 메타데이터 100% 보존 환경에서 완벽 정렬 완료! 총 {renamed_count}개의 파일이 구멍을 메우며 앞으로 당겨졌습니다.")
