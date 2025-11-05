import sqlite3

conn = sqlite3.connect('users.db')
c = conn.cursor()

c.execute('''
    CREATE TABLE IF NOT EXISTS compressions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        filename TEXT,
        original_size INTEGER,
        compressed_size INTEGER,
        compression_ratio REAL,
        compressed_filename TEXT
    )
''')

conn.commit()
conn.close()

print("Compression table created successfully.")
