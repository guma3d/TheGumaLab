import os

path = r"D:\Pictures\Unknown-Year\Unknown-Year_Unknown-Location\Unknown-Year_123.jpg"

print(f"File Path: {path}")
if os.path.exists(path):
    size = os.path.getsize(path)
    print(f"Exists: YES")
    print(f"Size: {size} bytes")
    if size == 0:
        print("Warning: File is empty.")
else:
    print("Exists: NO")
