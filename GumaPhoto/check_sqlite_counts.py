import sqlite3

def check_db():
    try:
        db = sqlite3.connect('/app/data/organizer_state.db')
        cur = db.cursor()
        
        cur.execute("SELECT count(1) FROM vectorized_files")
        sql_total = cur.fetchone()[0]
        
        cur.execute("SELECT count(1) FROM vectorized_files WHERE status='DONE'")
        sql_done = cur.fetchone()[0]
        
        cur.execute("SELECT count(1) FROM vectorized_files WHERE status='ERROR'")
        sql_err = cur.fetchone()[0]
        
        print("SQLite Total:", sql_total)
        print("SQLite DONE:", sql_done)
        print("SQLite ERROR:", sql_err)
    except Exception as e:
        print("SQLite Error:", e)

if __name__ == '__main__':
    check_db()
