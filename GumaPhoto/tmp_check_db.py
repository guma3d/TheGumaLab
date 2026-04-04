import sqlite3
import pprint

def get_schema(db_path, tables):
    print(f"=== {db_path} ===")
    conn = sqlite3.connect(db_path)
    for table in tables:
        cursor = conn.execute(f"PRAGMA table_info({table})")
        print(f"Table: {table}")
        for col in cursor.fetchall():
            print(col)
        
        count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"Row count: {count}")
    print()

get_schema('d:/TheGumaLab/GumaPhoto/data/organizer_state.db', ['vectorized_files'])
get_schema('d:/TheGumaLab/GumaPhoto/data/gumaphoto_main.db', ['photos'])
