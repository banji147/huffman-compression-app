import sqlite3

conn = sqlite3.connect('users.db')
c = conn.cursor()

# Add the new column if it doesn't exist
try:
    c.execute('ALTER TABLE compressions ADD COLUMN compression_time REAL')
    print("Column 'compression_time' added successfully.")
except sqlite3.OperationalError as e:
    print("Migration skipped or already applied:", e)

conn.commit()
conn.close()
