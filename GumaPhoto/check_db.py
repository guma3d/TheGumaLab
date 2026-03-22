import sqlite3

try:
    db = sqlite3.connect('/app/data/gumaphoto_main.db')
    cursor = db.cursor()
    cursor.execute("SELECT file_hash, original_context, filepath FROM photos WHERE original_context LIKE '%fbtrace%'")
    rows = cursor.fetchall()
    
    for r in rows:
        print(f"Hash: {r[0]}\nContext: {r[1]}\nFile: {r[2]}\n---")
    print(f"Total fbtraces found: {len(rows)}")
except Exception as e:
    print(f"Error: {e}")
