import sqlite3
import json
from collections import Counter
import os

conn = sqlite3.connect('d:/TheGumaLab/GumaPhoto/data/organizer_state.db')
cursor = conn.cursor()

cursor.execute("SELECT filepath, metadata FROM vectorized_files")

folder_counts = Counter()

for filepath, meta_str in cursor.fetchall():
    try:
        meta = json.loads(meta_str)
        if meta.get('location') == 'Unknown Location':
            # Extract folder. Windows or Linux path
            # The user asked about D:\Pictures, so let's handle the path string carefully.
            # Convert backslashes to forward slashes for unified processing
            norm_path = filepath.replace('\\', '/')
            # Extract the parent folder name
            folder = os.path.basename(os.path.dirname(norm_path))
            
            # The prompt requested "연도-월 폴더단위로" (Year-Month folder unit).
            # From the sample, folder names look like: 2021-05_xxx, 2017-03_xxx, 2024-04_xxx
            
            folder_counts[folder] += 1
            
    except Exception as e:
        pass

# Print the top 20
print("Top folders with most Unknown Locations:")
for folder, count in folder_counts.most_common(50):
    # Print the folder. Avoid unicode encode error by using safe print
    try:
        print(f"{folder}: {count}")
    except UnicodeEncodeError:
        print(f"{folder.encode('utf-8', 'replace').decode('utf-8')}: {count}")
