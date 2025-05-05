from flask import Flask, render_template, request, redirect, url_for, session, g
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'
DATABASE = 'todo.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    db = get_db()
    cur = db.execute('SELECT * FROM tasks WHERE user_id = ?', (session['user_id'],))
    tasks = cur.fetchall()
    return render_template('index.html', tasks=tasks, user=session['username'])

@app.route('/add', methods=['POST'])
def add_task():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    title = request.form['title']
    desc = request.form['description']
    start = request.form['start']
    end = request.form['end']
    db = get_db()
    db.execute('INSERT INTO tasks (title, description, start, end, status, user_id) VALUES (?, ?, ?, ?, ?, ?)',
               (title, desc, start, end, 'pending', session['user_id']))
    db.commit()
    return redirect(url_for('index'))

@app.route('/complete/<int:task_id>')
def complete_task(task_id):
    db = get_db()
    db.execute('UPDATE tasks SET status = ? WHERE id = ? AND user_id = ?', ('completed', task_id, session['user_id']))
    db.commit()
    return redirect(url_for('index'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        cur = db.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password))
        user = cur.fetchone()
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        db.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
        db.commit()
        return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    with app.app_context():
        db = get_db()
        db.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, password TEXT)')
        db.execute('''CREATE TABLE IF NOT EXISTS tasks (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        title TEXT, description TEXT,
                        start TEXT, end TEXT, status TEXT,
                        user_id INTEGER, FOREIGN KEY(user_id) REFERENCES users(id))''')
        db.commit()
    app.run(debug=True)