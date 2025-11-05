from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory
import os, zipfile, sqlite3, time
from werkzeug.utils import secure_filename
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'

UPLOAD_FOLDER = 'uploads'
COMPRESSED_FOLDER = 'compressed'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(COMPRESSED_FOLDER, exist_ok=True)

def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS compressions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        filename TEXT NOT NULL,
        original_size INTEGER,
        compressed_size INTEGER,
        compression_ratio REAL,
        compressed_filename TEXT,
        timestamp TEXT,
        compression_time REAL
    )''')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        try:
            c.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
            conn.commit()
        except sqlite3.IntegrityError:
            return render_template('register.html', error="Username already exists.")
        finally:
            conn.close()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password))
        user = c.fetchone()
        conn.close()
        if user:
            session['username'] = username
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error="Invalid credentials.")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        uploaded_file = request.files['file']
        algorithm = request.form.get('algorithm', 'zip')

        if uploaded_file.filename:
            filename = secure_filename(uploaded_file.filename)
            original_path = os.path.join(UPLOAD_FOLDER, filename)
            uploaded_file.save(original_path)

            start_time = time.time()

            if algorithm == 'zip':
                compressed_name = filename.rsplit('.', 1)[0] + '_compressed.zip'
                compressed_path = os.path.join(COMPRESSED_FOLDER, compressed_name)
                with zipfile.ZipFile(compressed_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    zipf.write(original_path, arcname=filename)

            elif algorithm == 'huffman':
                compressed_name = filename.rsplit('.', 1)[0] + '_compressed.huff'
                compressed_path = os.path.join(COMPRESSED_FOLDER, compressed_name)
                with open(original_path, 'rb') as fin, open(compressed_path, 'wb') as fout:
                    fout.write(fin.read())  # Placeholder for actual Huffman logic

            else:
                return render_template('dashboard.html', error="Unsupported algorithm.", history=[], username=session['username'])

            compression_time = round(time.time() - start_time, 4)

            original_size = os.path.getsize(original_path)
            compressed_size = os.path.getsize(compressed_path)
            compression_ratio = round(compressed_size / original_size, 2)
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            conn = sqlite3.connect('users.db')
            c = conn.cursor()
            c.execute('''INSERT INTO compressions (username, filename, original_size, compressed_size, compression_ratio, compressed_filename, timestamp, compression_time)
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                      (session['username'], filename, original_size, compressed_size, compression_ratio, compressed_name, timestamp, compression_time))
            conn.commit()
            conn.close()

    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''SELECT id, filename, original_size, compressed_size, compression_ratio, compressed_filename, timestamp, compression_time 
                 FROM compressions WHERE username = ? ORDER BY timestamp DESC''', (session['username'],))
    history = c.fetchall()
    conn.close()
    return render_template('dashboard.html', history=history, username=session['username'])

@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(COMPRESSED_FOLDER, filename, as_attachment=True)

@app.route('/delete/<int:file_id>', methods=['POST'])
def delete_file(file_id):
    if 'username' not in session:
        return redirect(url_for('login'))

    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT compressed_filename FROM compressions WHERE id = ? AND username = ?", (file_id, session['username']))
    row = c.fetchone()

    if row:
        file_path = os.path.join(COMPRESSED_FOLDER, row[0])
        if os.path.exists(file_path):
            os.remove(file_path)
        c.execute("DELETE FROM compressions WHERE id = ? AND username = ?", (file_id, session['username']))
        conn.commit()

    conn.close()
    return redirect(url_for('dashboard'))

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'username' not in session:
        return redirect(url_for('login'))

    username = session['username']
    if request.method == 'POST':
        current_password = request.form['current_password']
        new_password = request.form['new_password']

        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute('SELECT password FROM users WHERE username = ?', (username,))
        user = c.fetchone()

        if user and user[0] == current_password:
            c.execute('UPDATE users SET password = ? WHERE username = ?', (new_password, username))
            conn.commit()
            conn.close()
            return render_template('profile.html', username=username, message='Password updated successfully.')
        else:
            conn.close()
            return render_template('profile.html', username=username, error='Incorrect current password.')

    return render_template('profile.html', username=username)

if __name__ == '__main__':
    app.run(debug=True)
