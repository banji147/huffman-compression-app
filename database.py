import sqlite3

# Connect to database (creates it if it doesn't exist)
conn = sqlite3.connect('users.db')
c = conn.cursor()

# Create users table
c.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
)
''')

conn.commit()
conn.close()
