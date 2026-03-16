import xml.etree.ElementTree as ET
import sys

files = [
    '/app/data/organized/2026/2026-01_Unknown-Location/2026-01_01.xmp',
    '/app/data/organized/2026/2026-01_Hanam-Si-South-Korea/2026-01_01.xmp'
]

for f in files:
    try:
        print(f"\n======== [ {f.split('/')[-1]} ] ========")
        tree = ET.parse(f)
        root = tree.getroot()
        
        # 간단하게 전체 텍스트 출력
        for elem in root.iter():
            if elem.text and elem.text.strip():
                # 태그 이름에서 네임스페이스 제거하고 출력
                tag_name = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
                print(f"{tag_name}: {elem.text.strip()}")
    except Exception as e:
        print(f"Error reading {f}: {e}")
