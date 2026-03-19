import sqlite3

try:
    conn = sqlite3.connect('D:/TheGumaLab/GumaPhoto/data/organizer_state.db')
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM vectorized_files WHERE status='DELETED'")
    count = cursor.fetchone()[0]
    print(f"Number of DELETED rows in vectorized_files: {count}")
    
    cursor.execute("SELECT COUNT(*) FROM processed_files WHERE status='DELETED'")
    count2 = cursor.fetchone()[0]
    print(f"Number of DELETED rows in processed_files: {count2}")
except Exception as e:
    print(f"Error accessing DB: {e}")
