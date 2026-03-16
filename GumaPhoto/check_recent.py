import sqlite3

try:
    conn = sqlite3.connect('/app/data/organizer_state.db')
    cur = conn.cursor()
    
    cur.execute("SELECT filepath, status, face_count FROM vectorized_files ORDER BY ROWID DESC LIMIT 5")
    rows = cur.fetchall()
    for row in rows:
        print(f"Vectorized: {row[0]}, Status: {row[1]}, Faces: {row[2]}")
        
except Exception as e:
    print(f"Error: {e}")
