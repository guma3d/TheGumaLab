import sqlite3
db_path = "/app/data/organizer_state.db"
conn = sqlite3.connect(db_path)
c = conn.cursor()
c.execute("SELECT status, COUNT(*) FROM vectorized_files GROUP BY status")
print("Status counts:", c.fetchall())
conn.close()
