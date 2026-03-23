import sqlite3

try:
    db = sqlite3.connect('/app/data/gumaphoto_main.db')
    cur = db.cursor()
    cur.execute("PRAGMA table_info(photos);")
    print("Columns in photos table:")
    for row in cur.fetchall():
        print(f"Name: {row[1]:20} Type: {row[2]}")
        
    db.close()
except Exception as e:
    print(e)
