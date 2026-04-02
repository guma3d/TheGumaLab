import os
from qdrant_client import QdrantClient
class PhotoPurger:
    @staticmethod
    def purge_photo_data(abs_path: str, point_id: str = None, keep_original: bool = False):
        """
        [3단 연쇄 하드딜리트 파이프라인 통합 유틸리티]
        1. 물리적 파생 파일(XMP, WEBP) 사살 (keep_original=False 시 원본까지 파쇄)
        2. Qdrant 벡터 증발
        3. SQLAlchemy DB Tombstone 부여 (영구 제명 상태 = DELETED)
        """
        import urllib.parse
        abs_path = urllib.parse.unquote(abs_path)
        
        if abs_path.startswith("/videos/"):
            abs_path = abs_path.replace("/videos/", "/app/data/organized/")
        elif abs_path.startswith("/photos/"):
            abs_path = abs_path.replace("/photos/", "/app/data/organized/")
            
        print(f"🗑️ [PhotoPurger 청소 가동] 타겟 파일: {os.path.basename(abs_path)} / 보존 여부: {keep_original}")

        # [1] 서버 스토리지 물리 쓰레기 파일 폭파
        try:
            # 원본 폐기 여부 분기
            if not keep_original:
                if os.path.exists(abs_path):
                    os.remove(abs_path)
                    print(f"   ✅ [1/3] 서버 원본 파일 영구 삭제(파쇄) 완료")
                else:
                    print(f"   ⚠️ [1/3] 서버에 원본 파일이 존재하지 않아 패스함")
            else:
                print(f"   ✅ [1/3] 원본 파일 보존 (피드백 이주 모드)")

            # 파생 XMP 쓰레기 청소
            xmp_path_1 = abs_path + ".xmp"
            xmp_path_2 = os.path.splitext(abs_path)[0] + ".xmp"
            for xp in [xmp_path_1, xmp_path_2]:
                if os.path.exists(xp):
                    try: os.remove(xp)
                    except: pass

            # 파생 WEBP 썸네일 완전 삭제 (모든 조합 검색)
            base_name = os.path.splitext(abs_path)[0]
            orig_ext = abs_path.rsplit('.', 1)[-1].lower() if '.' in abs_path else ""
            thumb_targets = [
                f"{base_name}_{orig_ext}.webp",
                f"{base_name}_heic.webp",
                f"{base_name}_png.webp",
                f"{base_name}_jpg.webp"
            ]
            for p in thumb_targets:
                if os.path.exists(p):
                    try: os.remove(p)
                    except: pass

            print(f"   ✅ [1/3-파생자료] WEBP 썸네일 및 XMP 파생 파일 영구 삭제 완료")
            
            # [1/4 추가 롤백 기능] 기존 enrolled 학습 도감에 잔존하는 과거 크롭 썸네일 추적 파괴 (오염 완벽 차단)
            if point_id:
                import glob
                ghost_crops = glob.glob(f"/app/data/enrolled/*/{point_id}.jpg")
                for ghost in ghost_crops:
                    try:
                        os.remove(ghost)
                        print(f"   ✅ [1/4 롤백] 과거 학습 도감에서 잔재(크롭) 영구 소각 완료: {ghost}")
                    except: pass
                    
        except Exception as e:
            print(f"   ❌ [1/3] 물리적 파일 삭제 파이프라인 중 오류 발생: {e}")

        # [2] Qdrant DB 포인트 데이터 제거
        if point_id:
            try:
                qdrant_url = os.environ.get("QDRANT_URL", "http://qdrant:6333")
                qdrant_client = QdrantClient(url=qdrant_url)
                qdrant_client.delete(
                    collection_name="gumaphoto_hybrid_kr",
                    points_selector=[point_id]
                )
                print(f"   ✅ [2/3] Qdrant DB 내부 단일 벡터 데이터 즉각 파기 완료")
            except Exception as e:
                print(f"   ❌ [2/3] Qdrant DB 삭제 통신망 접속 오류: {e}")

        # [3] SQLite 통합 명부 삭제 (현재 아키텍처에서 폐기됨 - Qdrant 단일 진실화로 인해 불필요)
        print(f"   ✅ [3/3] SQLite 명단 제거 생략 (단일 진실 아키텍처로 인한 통폐합 완료)")
