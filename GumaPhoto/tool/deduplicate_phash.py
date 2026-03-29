import os
import sys
import subprocess

# 필수 패키지 자동 설치기 (로컬 환경 대응)
try:
    from PIL import Image
    import imagehash
except ImportError:
    print("⏳ 로컬(PC) 환경에 필요한 파이썬 패키지가 없어 자동으로 다운로드(설치)를 시도합니다...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "Pillow", "imagehash", "pillow_heif"])
        from PIL import Image
        import imagehash
        print("✅ 설치가 무사히 완료되었습니다!\n")
    except Exception as e:
        print(f"\n❌ 자동 설치 실패. 명령 프롬프트에서 수동으로 실행해주세요:\n   pip install Pillow imagehash pillow_heif\n\n(에러 사유: {e})")
        input("\n종료하려면 엔터를 누르세요...")
        sys.exit(1)

def main():
    print("=" * 60)
    print("📸 연사 및 유사 사진 자동 제거 툴 (pHash 연산기)")
    print("=" * 60)
    
    # .bat 파일에 폴더를 바로 끌어다 놓았을 경우(sys.argv)와 안에서 드래그했을 경우 지원
    if len(sys.argv) > 1:
        folder_path = sys.argv[1]
    else:
        folder_path = input("\n검사할 폴더를 터미널로 드래그 앤 드롭 하세요:\n> ").strip()
    
    # 윈도우 드래그 앤 드롭 시 추가되는 따옴표 완전 제거
    if folder_path.startswith('"') and folder_path.endswith('"'):
        folder_path = folder_path[1:-1]
    elif folder_path.startswith("'") and folder_path.endswith("'"):
        folder_path = folder_path[1:-1]
        
    if not os.path.isdir(folder_path):
        print(f"\n[오류] 경로를 찾을 수 없거나 올바른 폴더가 아닙니다: {folder_path}")
        input("\n종료하려면 엔터를 누르세요...")
        return

    print("\n[1/3] 파일 목록 수집 및 시간순 정렬 중...")
    valid_exts = {'.jpg', '.jpeg', '.png', '.bmp', '.webp', '.heic'}
    
    # HEIC 지원을 위한 패치 (설치되어 있을 경우에만 활성화)
    try:
        from pillow_heif import register_heif_opener
        register_heif_opener()
    except ImportError:
        pass
        
    all_files = []
    for root, _, files in os.walk(folder_path):
        for f in files:
            ext = os.path.splitext(f)[1].lower()
            if ext in valid_exts:
                full_path = os.path.join(root, f)
                all_files.append(full_path)
                
    if not all_files:
        print("\n[!] 해당 폴더에 처리할 이미지 파일이 없습니다.")
        input("\n종료하려면 아무 키나 누르세요...")
        return
        
    # 파일 생성/수정 시간 기준으로 오름차순 정렬
    all_files.sort(key=lambda x: os.path.getmtime(x))
    
    print(f"[2/3] 총 {len(all_files)}장의 사진에 대해 pHash(지문)를 추출하고 비교합니다...")
    
    phash_dict = {}
    to_delete = []
    
    threshold = 6  
    
    for idx, filepath in enumerate(all_files):
        if (idx + 1) % 50 == 0:
            print(f"      ... {idx + 1}장 처리 중")
            
        try:
            with Image.open(filepath) as img:
                current_hash = imagehash.phash(img)
                
            is_duplicate = False
            for kept_hash, kept_path in phash_dict.items():
                distance = current_hash - kept_hash
                if distance <= threshold:
                    is_duplicate = True
                    break
                    
            if is_duplicate:
                to_delete.append(filepath)
            else:
                phash_dict[current_hash] = filepath
                
        except Exception as e:
            pass # 너무 긴 경고창 방지를 위해 패스
            
    print("\n[3/3] 구조 분석 완료!")
    if not to_delete:
        print("🎉 폴더 내에 유사하거나 중복된 연사 사진이 없습니다. 모두 고유한 사진입니다.")
        input("\n종료하려면 엔터를 누르세요...")
        return
        
    print(f"\n⚠️ 총 {len(to_delete)}개의 연사(유사) 사진 파생물이 발견되었습니다.")
    for d in to_delete[:5]:
        print(f"   🗑️ 삭제 예정: {os.path.basename(d)}")
    if len(to_delete) > 5:
        print(f"   ... (외 {len(to_delete) - 5}장)")
        
    ans = input("\n위 스팸/유사 사진들을 영구적으로 삭제하시겠습니까? (Y / N): ").strip().upper()
    if ans == 'Y' or ans == 'YES':
        deleted_count = 0
        for p in to_delete:
            try:
                os.remove(p)
                deleted_count += 1
            except Exception as e:
                print(f"   [오류] 삭제 실패: {p} ({e})")
        print(f"\n✅ 성공적으로 {deleted_count}장의 사진이 완전히 삭제되었습니다!")
    else:
        print("\n❌ 삭제가 취소되었습니다. 사진이 보존됩니다.")
        
    input("\n프로그램을 종료하려면 엔터를 누르세요...")

if __name__ == "__main__":
    main()
