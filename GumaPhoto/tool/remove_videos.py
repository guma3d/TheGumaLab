import os
import sys

def main():
    print("=" * 60)
    print("🎬 동영상 파일 일괄 영구 삭제 툴")
    print("=" * 60)
    
    # Drag and Drop on icon (sys.argv) OR interactive prompt
    if len(sys.argv) > 1:
        folder_path = sys.argv[1]
    else:
        folder_path = input("\n동영상을 색출하여 제거할 폴더를 이 터미널 안으로 드래그 앤 드롭 하세요:\n> ").strip()
    
    # Remove surrounding quotes from windows drag and drop
    if folder_path.startswith('"') and folder_path.endswith('"'):
        folder_path = folder_path[1:-1]
    elif folder_path.startswith("'") and folder_path.endswith("'"):
        folder_path = folder_path[1:-1]
        
    if not os.path.pathsep in folder_path and folder_path.strip() == "":
        return
        
    if not os.path.isdir(folder_path):
        print(f"\n[오류] 경로를 찾을 수 없거나 올바른 폴더가 아닙니다: {folder_path}")
        input("\n종료하려면 아무 키나 누르세요...")
        return

    print(f"\n[1/2] '{os.path.basename(folder_path)}' 최상위 폴더부터 구석구석 동영상을 탐색합니다...")
    video_exts = {'.mp4', '.mov', '.avi', '.mkv', '.webm', '.flv', '.wmv', '.mts', '.m4v', '.3gp'}
    
    to_delete = []
    for root, _, files in os.walk(folder_path):
        for f in files:
            ext = os.path.splitext(f)[1].lower()
            if ext in video_exts:
                to_delete.append(os.path.join(root, f))
                
    if not to_delete:
        print("\n🎉 해당 폴더에는 삭제할 동영상 파일이 단 하나도 없습니다! (사진만 존재함)")
        input("\n종료하려면 엔터를 누르세요...")
        return
        
    print(f"\n⚠️ 총 {len(to_delete)}개의 동영상 파일이 발견되었습니다.")
    for d in to_delete[:5]:
        print(f"   🗑️ 삭제 대기 표적: {os.path.basename(d)}")
    if len(to_delete) > 5:
        print(f"   ... (외에 {len(to_delete) - 5}개의 영상 추가 발견됨)")
        
    ans = input("\n위 영상들은 용량이 매우 큽니다. 영구적으로 즉각 소각하시겠습니까? (Y / N): ").strip().upper()
    if ans == 'Y' or ans == 'YES':
        deleted_count = 0
        freed_bytes = 0
        for p in to_delete:
            try:
                size = os.path.getsize(p)
                os.remove(p)
                freed_bytes += size
                deleted_count += 1
            except Exception as e:
                print(f"   [오류] 삭제 실패: {p} ({e})")
        
        freed_gb = freed_bytes / (1024 * 1024 * 1024)
        print(f"\n✅ 철저하게 {deleted_count}개의 동영상이 완전히 삭제되었습니다!")
        print(f"📀 화끈하게 확보된 하드디스크 여유 용량: 약 {freed_gb:.2f} GB")
    else:
        print("\n❌ 사용자에 의해 삭제가 취소되었습니다. 동영상들이 그대로 보존됩니다.")
        
    input("\n프로그램을 종료하려면 엔터를 누르세요...")

if __name__ == "__main__":
    main()
