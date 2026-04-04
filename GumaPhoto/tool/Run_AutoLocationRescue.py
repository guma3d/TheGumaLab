import os
import sys
import time
import json
import subprocess
from collections import Counter

# Qdrant 라이브러리 (사용자 로컬 환경에 없으면 자동 설치)
try:
    from qdrant_client import QdrantClient
    from qdrant_client.http.models import Filter, FieldCondition, MatchText, MatchValue
except ImportError:
    print("⏳ 필요 패키지(qdrant-client) 자동 설치 중...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "qdrant-client"])
    from qdrant_client import QdrantClient
    from qdrant_client.http.models import Filter, FieldCondition, MatchText, MatchValue

# 기준 폴더 강제 맞춤 (tool 폴더 내부로 고정)
try:
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
except Exception:
    pass

LOCAL_EXIFTOOL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "exiftool_engine", "exiftool.exe")
if not os.path.exists(LOCAL_EXIFTOOL):
    # 환경변수 패스에 있는지 확인
    LOCAL_EXIFTOOL = "exiftool"

# 부모 경로 (GumaPhoto 최상단)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def convert_to_host_path(container_path):
    """
    Qdrant DB에는 '/app/data/organized/...' 형식의 도커 내부 경로로 저장되어 있음.
    docker-compose 매핑에 따라 D:\\Pictures 와 맞물리도록 처리.
    """
    if container_path.startswith("/app/data/organized/"):
        return container_path.replace("/app/data/organized/", "D:\\Pictures\\").replace("/", os.sep)
    elif container_path.startswith("/app/data/uploads_raw/"):
        return container_path.replace("/app/data/uploads_raw/", "D:\\Pictures\\uploads_raw\\").replace("/", os.sep)
    elif "/app/data/" in container_path:
        rel_path = container_path.split("/app/data/")[-1]
        return os.path.join(BASE_DIR, "data", rel_path.replace("/", os.sep))
    return container_path

def write_gps_exif(filepath, lat, lon):
    """
    사용자 요청: XMP 없이 순수 GPS 메타데이터만 EXIF에 물리적 주입.
    """
    if not lat or not lon:
        return False, "GPS 데이터 없음"
        
    lat_ref = "N" if lat >= 0 else "S"
    lon_ref = "E" if lon >= 0 else "W"
    
    args = [
        "-m", "-overwrite_original",
        "-charset", "FileName=utf8",
        "-charset", "utf8",
        # XMP 사용 안 함 (사용자 요청)
        f"-GPSLatitude={abs(lat)}",
        f"-GPSLatitudeRef={lat_ref}",
        f"-GPSLongitude={abs(lon)}",
        f"-GPSLongitudeRef={lon_ref}",
        filepath
    ]
    args_str = "\n".join(args)
    
    try:
        res = subprocess.run([LOCAL_EXIFTOOL, "-@", "-"], input=args_str.encode('utf-8'), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out_str = res.stdout.decode('cp949', errors='ignore')
        
        is_success = False
        for line in out_str.split('\n'):
            line = line.strip()
            if "image files updated" in line and not line.startswith("0 image files"):
                is_success = True
                break
                
        if is_success:
            return True, ""
        else:
            err_msg = res.stderr.decode('cp949', errors='ignore').strip()
            return False, f"ExifTool Error: {err_msg} | Stdout: {out_str}"
    except Exception as e:
        return False, f"Process Error: {str(e)}"

def rollback_exif_gps(filepath):
    """
    ExifTool을 사용해 주입된 GPS 정보 전체(-gps:all=)를 삭제하여 원상복구.
    """
    args = [
        "-m", "-overwrite_original",
        "-charset", "FileName=utf8",
        "-charset", "utf8",
        "-gps:all=",
        filepath
    ]
    args_str = "\n".join(args)
    
    try:
        res = subprocess.run([LOCAL_EXIFTOOL, "-@", "-"], input=args_str.encode('utf-8'), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True, ""
    except Exception as e:
        return False, str(e)

def perform_rollback(client, col_name, rollback_file):
    print("\n" + "=" * 80)
    print("⏪ [ROLLBACK MODE] 자동 주입 복구(Rollback) 프로세스 시작")
    print("=" * 80)
    
    if not os.path.exists(rollback_file):
        print(f"❌ 롤백 데이터 파일이 없습니다. ({rollback_file})")
        return
        
    with open(rollback_file, "r", encoding="utf-8") as f:
        history = json.load(f)
        
    if not history:
        print("❌ 롤백할 기록이 없습니다.")
        return
        
    print(f"총 {len(history)}건의 복구 대상 기록을 발견했습니다.")
    confirm = input("❗ 이 사진들의 GPS 값을 날리고 'Unknown Location'으로 되돌리시겠습니까? (Y/N): ")
    if confirm.strip().upper() not in ["Y", "YES"]:
        print("롤백 작업을 취소합니다.")
        return
        
    success = 0
    fail = 0
    for idx, item in enumerate(history, 1):
        t_id = item["id"]
        filepath = item["filepath"]
        print(f"[{idx}/{len(history)}] ⏪ {os.path.basename(filepath)} ➡️ 원상복구 중...")
        
        # 1. 파일 GPS 삭제
        if os.path.exists(filepath):
            ok, err = rollback_exif_gps(filepath)
            if not ok:
                print(f"   └ ❌ 파일 GPS 삭제 실패: {err}")
                
        # 2. DB 페이로드 초기화 (Unknown Location 설정 및 geo_point 파기)
        try:
            client.delete_payload(
                collection_name=col_name,
                keys=["geo_point"],
                points=[t_id]
            )
            client.set_payload(
                collection_name=col_name,
                payload={"location": "Unknown Location"},
                points=[t_id]
            )
            success += 1
        except Exception as e:
            print(f"   └ ❌ DB 파기 에러: {e}")
            fail += 1
            
    print(f"\n✅ 롤백 완료: 성공 {success}장 / 실패 {fail}장")
    print("⚠️ 롤백 기록 파일을 안전을 위해 삭제합니다.")
    os.remove(rollback_file)

def main():
    print("================================================================================")
    print("🛰️ [GumaPhoto] Unknown Location 자동 구조 시스템 (AI Semantic Consensus)")
    print("================================================================================")
    print(" - XMP 제외, 순수 DB Payload & 물리 파일 GPS(EXIF) 완전 삽입 모드")
    print(" - 대상: 위치가 없는 전체 Unknown 사진")
    print(" - 방식: 0.83 이상 유사도를 가진 정답 사진 중 Top-5 다수결/합의 도출")
    print("================================================================================\n")
    
    # 1. Qdrant 연결 (호스트에서 도커 컨테이너로 매핑된 기본 포트 6337 혹은 6333 접속)
    client = None
    for port in [6337, 6333]:
        try:
            print(f"🔄 Qdrant 포트 {port} 접속 시도 중...")
            test_client = QdrantClient(f"http://localhost:{port}")
            cols = test_client.get_collections()
            client = test_client
            print(f"✅ Qdrant 접속 완료 (포트 {port})")
            break
        except Exception:
            continue
            
    if not client:
        print("❌ Qdrant 접속 실패. 도커 컨테이너가 실행 중인지, 포트 매핑을 확인하세요.")
        return

    col_name = "gumaphoto_hybrid_kr"
    rollback_file = os.path.join(BASE_DIR, "data", "rescue_rollback_snapshot.json")
    
    if len(sys.argv) > 1 and sys.argv[1] == "--rollback":
        perform_rollback(client, col_name, rollback_file)
        return
        
    # 기존 기록(히스토리) 로드
    history = []
    if os.path.exists(rollback_file):
        with open(rollback_file, "r", encoding="utf-8") as f:
            try: history = json.load(f)
            except: pass
    
    # 2. 타겟 (Unknown Location) 확보
    print("\n🔍 1단계: 'Unknown Location' 타겟 리스트를 수집합니다...")
    target_photos = []
    offset = None
    limit = 5000
    
    unknown_filter = Filter(
        should=[
            FieldCondition(key="location", match=MatchText(text="Unknown")),
            FieldCondition(key="location", match=MatchText(text="위치정보없음")),
            FieldCondition(key="location", match=MatchValue(value=""))
        ]
    )
    
    while True:
        batch, offset = client.scroll(
            collection_name=col_name,
            scroll_filter=unknown_filter,
            limit=limit,
            offset=offset,
            with_payload=["location", "filepath"],
            with_vectors=False
        )
        for b in batch:
            p_loc = b.payload.get("location", "")
            if "Unknown" in p_loc or "위치정보없음" in p_loc or not p_loc.strip():
                target_photos.append(b)
                
        if offset is None:
            break
            
    print(f"🎯 구출 대상 사진 총 {len(target_photos)} 장 수집 완료.\n")
    
    # 사용자 확인
    user_input = input(f"🚀 총 {len(target_photos)}장에 대해 AI 위치 유추 복원(DB + 물리파일(EXIF) 덮어쓰기)을 시작하시겠습니까? (Y/N): ")
    if user_input.strip().upper() not in ["Y", "YES"]:
        print("작업을 취소합니다.")
        return
        
    print("\n" + "-" * 80)
    print("🔥 2단계: AI 멀티 병렬 탐색 및 Consensus 복원 가동!")
    print("-" * 80)

    # 3. 사진별 복원 로직
    success_count = 0
    fail_count = 0
    start_t = time.time()
    
    # Qdrant에서 제외할 필터(이미 위치 정보가 없는 애들은 Top 5에서 무조건 제외해야 빠르고 정확함)
    known_location_filter = Filter(
        must_not=[
            FieldCondition(key="location", match=MatchText(text="Unknown")),
            FieldCondition(key="location", match=MatchText(text="위치정보없음"))
        ]
    )

    for idx, target in enumerate(target_photos, 1):
        t_id = target.id
        t_filepath = target.payload.get("filepath", "Unknown")
        host_filepath = convert_to_host_path(t_filepath)
        filename = os.path.basename(t_filepath)
        
        try:
            # AI 시각적 배경(Scene) 유사도 기반 쿼리 수행
            # 사용자 요청: Target은 이미 정답이 있는(Known) 사진들 안에서만 Top 5를 탐색
            search_result = client.query_points(
                collection_name=col_name,
                query=t_id,
                using="scene",
                query_filter=known_location_filter, 
                limit=5,
                score_threshold=0.80,
                with_payload=["location", "geo_point"]
            ).points
            
            # 본인과 동일한 사진이 리턴된 경우 무조건 배제 
            valid_candidates = [hit for hit in search_result if str(hit.id) != str(t_id)]
            
            if not valid_candidates:
                print(f"[{idx}/{len(target_photos)}] ❌ {filename} ➡️ 유사한 정답 사진 결과 없음 (0.83 이상 패스)")
                fail_count += 1
                continue
                
            # 합의(Consensus) 알고리즘
            loc_list = [hit.payload.get("location") for hit in valid_candidates if hit.payload.get("location")]
            
            if not loc_list:
                print(f"[{idx}/{len(target_photos)}] ❌ {filename} ➡️ Top-5 안에 위치 값이 든 사진이 전무함")
                fail_count += 1
                continue

            counter = Counter(loc_list)
            most_common, count = counter.most_common(1)[0]
            
            best_match = None
            is_consensus = False
            
            # 다수결 (2명 이상 합의된 위치인가?)
            if count >= 2:
                is_consensus = True
                # 합의된 주소를 가진 가장 점수가 높은 사진을 베스트 매치로 채택
                for hit in valid_candidates:
                    if hit.payload.get("location") == most_common:
                        best_match = hit
                        break
            else:
                print(f"[{idx:04d}/{len(target_photos)}] ⏭️ {filename[:20]:20} ➡️ 합의 없음 (분산됨) -> 건너뜀")
                fail_count += 1
                continue
                
            final_loc_str = best_match.payload.get("location")
            final_geo = best_match.payload.get("geo_point") or {}
            target_lat = final_geo.get("lat")
            target_lon = final_geo.get("lon")
            best_score = best_match.score
            
            print(f"[{idx:04d}/{len(target_photos)}] 🎯 {filename[:20]:20} ➡️ {final_loc_str} (최고유사도 {best_score:.2f}, 합의 {count}표)")
            
            # 1. 원본 파일 메타데이터(EXIF) 덮어쓰기 (XMP 제외, GPS 위경도만)
            if target_lat and target_lon:
                if os.path.exists(host_filepath):
                    exif_ok, exif_err = write_gps_exif(host_filepath, target_lat, target_lon)
                    if not exif_ok:
                        print(f"     └ ❗ 물리 EXIF 주입에 실패했습니다: {exif_err}")
                else:
                    print(f"     └ ❗ 디스크에 원본 사진이 존재하지 않습니다: {host_filepath}")
            
            # 2. Qdrant DB 직접 수정 (벡터 인덱서 불필요)
            new_payload = {"location": final_loc_str}
            if target_lat and target_lon:
                new_payload["geo_point"] = {"lat": target_lat, "lon": target_lon}
                
            client.set_payload(
                collection_name=col_name,
                payload=new_payload,
                points=[t_id]
            )
            
            # 3. 롤백을 대비한 성공 스냅샷 저장
            history.append({
                "id": t_id,
                "filepath": host_filepath
            })
            with open(rollback_file, "w", encoding="utf-8") as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
                
            success_count += 1
            
        except Exception as e:
            print(f"[{idx}/{len(target_photos)}] ❌ {filename} ➡️ 심각한 처리 에러: {str(e)}")
            fail_count += 1

    print("\n" + "=" * 80)
    print("🏆 [최종 통계 리포트]")
    print("=" * 80)
    print(f" - 총 투입 대상: {len(target_photos)} 장")
    print(f" - 🎯 성공적으로 복원 연동됨: {success_count} 장")
    print(f" - ❌ 유사 검색 실패 및 오류: {fail_count} 장")
    print(f" - 총 소요 시간: {time.time() - start_t:.1f}초")
    print("================================================================================")
    print("✅ 작업이 완료되었습니다! (GumaPhoto의 시스템 탭과 지도 탭에서 새로고침 하시면 복원된 사진들이 즉시 나타납니다.)")

if __name__ == "__main__":
    main()
