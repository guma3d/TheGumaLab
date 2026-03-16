import os

uploads_dir = "/app/data/uploads_raw"
video_extensions = ('.mp4', '.mov', '.avi', '.mkv', '.wmv', '.flv', '.webm', '.m4v', '.3gp', '.mts', '.m2ts')

removed_count = 0
total_size_freed = 0

for root, dirs, files in os.walk(uploads_dir):
    for file in files:
        if file.lower().endswith(video_extensions):
            file_path = os.path.join(root, file)
            try:
                size = os.path.getsize(file_path)
                os.remove(file_path)
                print(f"🗑️ Removed: {file_path} ({size / (1024*1024):.2f} MB)")
                removed_count += 1
                total_size_freed += size
            except Exception as e:
                print(f"❌ Failed to remove {file_path}: {e}")

print(f"\n✅ Total videos removed: {removed_count}")
print(f"✅ Total space freed: {total_size_freed / (1024*1024*1024):.2f} GB")
