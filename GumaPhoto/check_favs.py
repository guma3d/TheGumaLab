import sqlite3

try:
    db = sqlite3.connect('/app/data/gumaphoto_main.db')
    cur = db.cursor()
    cur.execute("SELECT count(1) FROM photos WHERE is_favorite = 1;")
    fav_count = cur.fetchone()[0]
    print(f"Number of favorite photos: {fav_count}")
    
    cur.execute("SELECT count(1) FROM photos WHERE original_context IS NOT NULL AND original_context != 'None';")
    context_count = cur.fetchone()[0]
    print(f"Number of photos with context: {context_count}")
        
    db.close()
except Exception as e:
    print(e)
