import sqlite3
import os

for path in ['/app/data/organizer_state.db', '/app/organizer_state.db']:
    if os.path.exists(path):
        print("DB found at:", path)
        c = sqlite3.connect(path)
        print([r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()])
