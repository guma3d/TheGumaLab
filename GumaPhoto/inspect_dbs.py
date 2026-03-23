import sqlite3
import os

def inspect_db(path):
    print(f"\n--- Database: {path} ---")
    if not os.path.exists(path):
        print("File does not exist.")
        return
        
    try:
        db = sqlite3.connect(path)
        cur = db.cursor()
        
        cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cur.fetchall()
        
        if not tables:
            print("No tables found.")
            return
            
        for table in tables:
            table_name = table[0]
            try:
                cur.execute(f"SELECT COUNT(1) FROM {table_name}")
                count = cur.fetchone()[0]
                print(f"Table: {table_name:20} - {count} rows")
            except Exception as e:
                print(f"Table: {table_name:20} - Error counting rows")
                
    except Exception as e:
        print("Error accessing DB:", e)

if __name__ == '__main__':
    inspect_db('/app/data/organizer_state.db')
    inspect_db('/app/data/gumaphoto_main.db')
