import sqlite3

conn = sqlite3.connect('D:/TheGumaLab/GumaPhoto/data/organizer_state.db')
cursor = conn.cursor()
cursor.execute("PRAGMA table_info(vectorized_files)")
print("Columns in vectorized_files:")
for col in cursor.fetchall():
    print(col)
