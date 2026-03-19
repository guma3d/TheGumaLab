import os

uploads_dir = "/app/data/uploads_raw"
if os.path.exists(uploads_dir):
    print("Files in uploads_raw:")
    for f in os.listdir(uploads_dir):
        print(f)
