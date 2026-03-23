from qdrant_client import QdrantClient
from qdrant_client.http.models import Filter, FieldCondition, MatchText
import json, sqlite3

def run_unification():
    qc = QdrantClient('http://qdrant:6333')
    coll = "gumaphoto_hybrid_kr"

    print("[*] 기존 'Unknown' 및 '위치정보없음' 파편화 데이터 통합 작업을 시작합니다...")
    
    bad_locs = ["Unknown", "위치정보없음"]
    target_loc = "Unknown Location"
    total_loc_fixed = 0

    for bad in bad_locs:
        # MatchText matches exact token. Since location index is TEXT, we might get partial matches,
        # so we fetch and check string exactly.
        from qdrant_client.http.models import MatchValue
        import traceback
        
        offset = None
        while True:
            try:
                res, next_offset = qc.scroll(
                    collection_name=coll, 
                    limit=500, 
                    with_payload=True,
                    offset=offset
                )
                print(f"  - 스크롤 배치(500개) 로드 완료. 현재까지 위치 교정된 횟수: {total_loc_fixed}")
                
                for p in res:
                    loc = p.payload.get("location")
                    if loc in bad_locs:
                        # 1. Qdrant Payload 수정
                        qc.set_payload(collection_name=coll, payload={"location": target_loc}, points=[p.id])
                        total_loc_fixed += 1
                        
                        # 2. SQLite 동기화
                        fpath = p.payload.get("filepath")
                        if fpath:
                            try:
                                conn = sqlite3.connect("/app/data/organizer_state.db")
                                cur = conn.cursor()
                                cur.execute("SELECT metadata FROM vectorized_files WHERE filepath=?", (fpath,))
                                row = cur.fetchone()
                                if row and row[0]:
                                    meta = json.loads(row[0])
                                    meta["location"] = target_loc
                                    cur.execute("UPDATE vectorized_files SET metadata=? WHERE filepath=?", (json.dumps(meta, ensure_ascii=False), fpath))
                                    conn.commit()
                                conn.close()
                            except Exception as e:
                                print(f"DB Error: {e}")
                                
                if next_offset is None:
                    break
                offset = next_offset
            except Exception as qc_err:
                print(f"Scroll Error: {qc_err}")
                break
                
    # 날짜 파편화 통일
    bad_dates = ["Unknown"]
    target_date = "Unknown Date"
    total_date_fixed = 0
    
    offset = None
    while True:
        try:
            res, next_offset = qc.scroll(
                collection_name=coll, 
                limit=500, 
                with_payload=True,
                offset=offset
            )
            print(f"  - 스크롤 배치(500개) 로드 완료. 현재까지 날짜 교정된 횟수: {total_date_fixed}")
            
            for p in res:
                date_val = p.payload.get("date")
                if date_val in bad_dates:
                    qc.set_payload(collection_name=coll, payload={"date": target_date}, points=[p.id])
                    total_date_fixed += 1
                    
                    fpath = p.payload.get("filepath")
                    if fpath:
                        try:
                            conn = sqlite3.connect("/app/data/organizer_state.db")
                            cur = conn.cursor()
                            cur.execute("SELECT metadata FROM vectorized_files WHERE filepath=?", (fpath,))
                            row = cur.fetchone()
                            if row and row[0]:
                                meta = json.loads(row[0])
                                meta["date"] = target_date
                                cur.execute("UPDATE vectorized_files SET metadata=? WHERE filepath=?", (json.dumps(meta, ensure_ascii=False), fpath))
                                conn.commit()
                            conn.close()
                        except Exception as e:
                            pass
                            
            if next_offset is None:
                break
            offset = next_offset
        except Exception as qc_err:
            print(f"Scroll Error: {qc_err}")
            break

    print(f"[*] 통일 작업 완료! (위치 교정: {total_loc_fixed}장 / 날짜 교정: {total_date_fixed}장)")

if __name__ == '__main__':
    run_unification()
