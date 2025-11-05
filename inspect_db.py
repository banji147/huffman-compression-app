import sqlite3

# Connect to your database
conn = sqlite3.connect('users.db')
c = conn.cursor()

# Get all rows from compressions table
c.execute("SELECT * FROM compressions")
rows = c.fetchall()

# Print out the results
if rows:
    print("ID | Username | Filename | Original Size | Compressed Size | Ratio | Compressed File | Timestamp")
    for row in rows:
        print(row)
else:
    print("No data found in compressions table.")

conn.close()
