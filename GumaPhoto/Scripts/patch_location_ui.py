import os
import sys
import unicodedata
from qdrant_client import QdrantClient
from qdrant_client.http import models

import os
qdrant_url = os.getenv("QDRANT_URL", "http://127.0.0.1:6337") # Host/Tunnel 포트 6337 대응
print(f"[*] Qdrant DB({qdrant_url}) 빠른 교정 스크립트를 시작합니다...")
client = QdrantClient(url=qdrant_url)

def _remove_latin(t):
    if not isinstance(t, str): return t
    res = ""
    for c in t:
        if 'LATIN' in unicodedata.name(c, ''):
            res += unicodedata.normalize('NFD', c).encode('ascii', 'ignore').decode('utf-8')
        else: res += c
    return res

collection = "gumaphoto_hybrid_kr"

try:
    info = client.get_collection(collection)
except Exception as e:
    print(f"[-] 컬렉션을 찾을 수 없습니다: {e}")
    sys.exit(1)

offs = None
updated_count = 0
total_checked = 0

print("[*] 전체 사진 DB를 스캔하며 문제가 되는 장소명(외계어 및 특수 라틴문자)을 추적합니다...")

# Qdrant의 경우 한번에 1000개씩 스크롤하며 검사 가능
while True:
    records, offs = client.scroll(
        collection_name=collection,
        limit=1000,
        with_payload=True,
        with_vectors=False,
        offset=offs
    )
    
    total_checked += len(records)
    
    for r in records:
        loc = r.payload.get("location", "")
        # 특정 CP949 쓰레기 텍스트(부천시 에러) 발견 혹은 아스키로 벗겨낼 수 있는 라틴어 발견 시
        if "??ǳ" in loc or "???" in loc or loc != _remove_latin(loc):
            original = loc
            # CP949 쓰레기 문자(부천시 1053장 에러)의 경우 하드코딩 교정
            if "??ǳ" in loc or "???" in loc:
                clean_loc = "대한민국 부천시"
            else:
                clean_loc = _remove_latin(loc)
                
            print(f"  [수정] {original} ➡️ {clean_loc}")
            
            # Payload 업데이트
            client.set_payload(
                collection_name=collection,
                payload={"location": clean_loc},
                points=[r.id],
                wait=True
            )
            updated_count += 1
            
    if offs is None:
        break

print(f"\n✅ 완료되었습니다! 총 {total_checked}장의 DB를 스캔하였고, {updated_count}장의 장소명을 정상적으로 백업/클린업 했습니다.")
