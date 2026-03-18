import sqlite3
import pprint

try:
    conn = sqlite3.connect('D:/TheGumaLab/GumaPhoto/data/photos.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, filename, status, error_message FROM photos WHERE status != 'indexed'")
    rows = cursor.fetchall()
    print(f"Pending/Failed rows: {len(rows)}")
    pprint.pprint(rows)
except Exception as e:
    print(f"Error accessing DB: {e}")
