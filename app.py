from flask import Flask, render_template, request, redirect, session
import sqlite3
import random
import string
import os

app = Flask(__name__)
app.secret_key = "zynko_secret"

# ======================
# CREATION BASE DE DONNEES
# ======================

def init_db():
    conn = sqlite3.connect('zynko.db')

    conn.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        friend_code TEXT UNIQUE
    )
    ''')

    conn.execute('''
    CREATE TABLE IF NOT EXISTS friends (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user TEXT,
        friend TEXT
    )
    ''')

    conn.execute('''
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender TEXT,
        receiver TEXT,
        message TEXT
    )
    ''')

    conn.commit()
    conn.close()

init_db()

# ======================
# GENERER CODE AMI
# ======================

def generate_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

# ======================
# ACCUEIL
# ======================

@app.route('/')
def home():
    return redirect('/login')

# ======================
# INSCRIPTION
# ======================

@app.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == 'POST':

        username = request.form['username']
        password = request.form['password']
        code = generate_code()

        conn = sqlite3.connect('zynko.db')

        try:
            conn.execute(
                "INSERT INTO users (username,password,friend_code) VALUES (?,?,?)",
                (username, password, code)
            )
            conn.commit()
        except:
            conn.close()
            return "Utilisateur déjà existant"

        conn.close()

        return redirect('/login')

    return render_template("register.html")

# ======================
# LOGIN
# ======================

@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect('zynko.db')

        user = conn.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (username, password)
        ).fetchone()

        conn.close()

        if user:
            session['username'] = username
            return redirect('/chat')
        else:
            return "Mauvais identifiant"

    return render_template("login.html")

# ======================
# CHAT
# ======================

@app.route('/chat')
def chat():

    if 'username' not in session:
        return redirect('/login')

    conn = sqlite3.connect('zynko.db')

    code = conn.execute(
        "SELECT friend_code FROM users WHERE username=?",
        (session['username'],)
    ).fetchone()[0]

    friends = conn.execute(
        "SELECT friend FROM friends WHERE user=?",
        (session['username'],)
    ).fetchall()

    conn.close()

    return render_template(
        "chat.html",
        username=session['username'],
        code=code,
        friends=friends
    )

# ======================
# AJOUT AMI
# ======================

@app.route('/add_friend', methods=['POST'])
def add_friend():

    if 'username' not in session:
        return redirect('/login')

    code = request.form['code']

    conn = sqlite3.connect('zynko.db')

    friend = conn.execute(
        "SELECT username FROM users WHERE friend_code=?",
        (code,)
    ).fetchone()

    if friend:

        conn.execute(
            "INSERT INTO friends (user,friend) VALUES (?,?)",
            (session['username'], friend[0])
        )

        conn.commit()

    conn.close()

    return redirect('/chat')

# ======================
# CONVERSATION
# ======================

@app.route('/conversation/<friend>', methods=['GET', 'POST'])
def conversation(friend):

    if 'username' not in session:
        return redirect('/login')

    conn = sqlite3.connect('zynko.db')

    if request.method == 'POST':

        msg = request.form['msg']

        conn.execute(
            "INSERT INTO messages (sender,receiver,message) VALUES (?,?,?)",
            (session['username'], friend, msg)
        )

        conn.commit()

    messages = conn.execute("""
        SELECT sender,message FROM messages
        WHERE (sender=? AND receiver=?)
        OR (sender=? AND receiver=?)
    """, (session['username'], friend, friend, session['username'])).fetchall()

    conn.close()

    return render_template(
        "conversation.html",
        friend=friend,
        messages=messages
    )

# ======================
# LOGOUT
# ======================

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

# ======================
# DEMARRAGE SERVEUR
# ======================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)