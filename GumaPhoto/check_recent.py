import sqlite3

try:
    conn = sqlite3.connect('/app/data/organizer_state.db')
    cur = conn.cursor()
    
    cur.execute("SELECT filepath, processed_at FROM processed_files ORDER BY processed_at DESC LIMIT 5")
    rows = cur.fetchall()
    for row in rows:
        print(f"Processed: {row[0]} at {row[1]}")
        
except Exception as e:
    print(f"Error: {e}")
