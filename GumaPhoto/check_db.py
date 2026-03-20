import sqlite3
c = sqlite3.connect('/app/data/organizer_state.db')
print(c.execute('SELECT * FROM feedback_tasks').fetchall())
