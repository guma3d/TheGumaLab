import sqlite3
import os
import xml.etree.ElementTree as ET

DB_PATH = "/app/data/organizer_state.db"
UPLOADS_DIR = "/app/data/uploads_raw"

def check_progress():
    print("========================================")
    print("          📊 진행률 상세 리포트          ")
    print("========================================")
    
    # 남은 대기열 파일 수 확인
    remaining = 0
    if os.path.exists(UPLOADS_DIR):
        for root, dirs, files in os.walk(UPLOADS_DIR):
            remaining += len(files)
    print(f"⏳ 대기열 (uploads_raw) 남은 사진: {remaining} 장")

    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        c.execute("SELECT COUNT(*) FROM processed_files")
        processed_count = c.fetchone()[0]
        
        c.execute("SELECT COUNT(*) FROM vectorized_files WHERE status='DONE'")
        vectorized_count = c.fetchone()[0]
        
        c.execute("SELECT COUNT(*) FROM vectorized_files WHERE status='ERROR'")
        error_count = c.fetchone()[0]

        print(f"✅ 사진 분류 완료 (폴더 이사): {processed_count} 장")
        print(f"🤖 AI 분석 완료 (벡터화 및 태그): {vectorized_count} 장")
        print(f"❌ 오류 발생 항목: {error_count} 장")
        print("========================================\n")
        
    except Exception as e:
        print(f"DB 접근 오류: {e}\n")

def get_latest_results():
    print("========================================")
    print("     📸 최근 분석된 사진 2장 결과물     ")
    print("========================================")
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT filepath FROM vectorized_files WHERE status='DONE' ORDER BY rowid DESC LIMIT 50")
        rows = c.fetchall()
        
        found_xmp_count = 0
        for row in rows:
            if found_xmp_count >= 2:
                break
                
            filepath = row[0]
            xmp_path = filepath + ".xmp"
            if os.path.exists(xmp_path):
                found_xmp_count += 1
                print(f"\n📂 파일 경로: {filepath}")
                print(f"✅ 메타데이터(XMP) 생성 확인: 성공")
                try:
                    tree = ET.parse(xmp_path)
                    root = tree.getroot()
                    
                    ns = {
                        'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
                        'dc': 'http://purl.org/dc/elements/1.1/',
                        'guma': 'http://ns.guma3d.com/ai/1.0/'
                    }
                    
                    description = root.find('.//rdf:Description', ns)
                    if description is not None:
                        caption = description.get('{http://ns.guma3d.com/ai/1.0/}ModelCaption', '없음')
                        print(f"  📝 Florence 상황 묘사: {caption}")
                        
                        siglip_tags = description.get('{http://ns.guma3d.com/ai/1.0/}SigLIP_Tags', '없음')
                        if siglip_tags:
                            print(f"  🏷️ SigLIP 자동 태그: {siglip_tags}")
                        
                        objects_str = description.get('{http://ns.guma3d.com/ai/1.0/}Florence_Objects')
                        if objects_str:
                            print(f"  🔍 Florence 사물 인식: {objects_str}")
                            
                        faces_str = description.get('{http://ns.guma3d.com/ai/1.0/}DetectedFaces')
                        if faces_str:
                            print(f"  👤 식별된 얼굴(가족): {faces_str}")
                            
                except Exception as e:
                    print(f"  ❌ XMP 파싱 에러: {e}")
                
        if found_xmp_count == 0:
            print("아직 XMP가 생성된 10개 이내 최근 사진이 없습니다.")
            
    except Exception as e:
        print(f"DB 접근 오류: {e}")
    print("\n")

if __name__ == '__main__':
    check_progress()
    get_latest_results()
