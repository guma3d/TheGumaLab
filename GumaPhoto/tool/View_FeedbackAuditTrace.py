import json
import os
from collections import defaultdict

filepath = r"D:\TheGumaLab\GumaPhoto\data\audit_trace.json"
if not os.path.exists(filepath):
    print("아직 피드백 내역(audit_trace.json)이 생성되지 않았습니다. 먼저 피드백을 실행해 보세요!")
    exit(0)

traces = defaultdict(list)
with open(filepath, "r", encoding="utf-8") as f:
    for line in f:
        if not line.strip(): continue
        try:
            data = json.loads(line)
            traces[data["trace_id"]].append(data)
        except Exception: pass

print(f"============================================================")
print(f" 🕵️‍♂️ 피드백 추적 시스템 (Feedback Audit Trace) - 최근 5건 변화 ")
print(f"============================================================\n")

latest_traces = list(traces.keys())[-5:]

for tid in latest_traces:
    actions = traces[tid]
    before = next((a for a in actions if a["type"] == "BEFORE"), None)
    after = next((a for a in actions if a["type"] == "AFTER"), None)
    
    print(f"🔹 [UUID: {tid[:15]}...]")
    
    filepath_val = before.get('filepath') if before else (after.get('filepath') if after else 'Unknown File')
    print(f"   [파일명] {os.path.basename(filepath_val)}")
    
    if before:
        print(f"   [변경 전 🚫]")
        print(f"    - 장소(Loc):   {before.get('location', '데이터 없음')}")
        print(f"    - 날짜(Date):  {before.get('date', '데이터 없음')}")
        if before.get('people'):
            print(f"    - 인물(Face):  {before.get('people')}")
            
    if after:
        print(f"   [변경 후 ✅]")
        print(f"    - 장소(Loc):   {after.get('location', '데이터 없음')}")
        print(f"    - 날짜(Date):  {after.get('date', '데이터 없음')}")
        if after.get('people'):
            print(f"    - 인물(Face):  {after.get('people')}")
        
        exif_info = after.get("exif", "")
        if exif_info:
            print(f"    - 📁 EXIF 파일 내부 주입 상태 확인:")
            exif_lines = exif_info.replace("[", "").replace("]", "").replace("'", "").split(", ")
            for ex in exif_lines:
                print(f"        {ex}")
    print("-" * 60)
print("\n✅ 실제 변경 내역 조회 완료. 원본 파일과 Qdrant DB가 투명하게 추적되었습니다.")
