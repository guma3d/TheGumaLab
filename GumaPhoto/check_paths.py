import sqlite3
conn = sqlite3.connect("/app/data/organizer_state.db")
c = conn.cursor()
c.execute("SELECT filepath FROM vectorized_files LIMIT 5")
print(c.fetchall())
conn.close()
