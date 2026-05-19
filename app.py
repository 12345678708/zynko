from flask import Flask, render_template, request, redirect, session, jsonify
import sqlite3
import random
import string
import hashlib
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = "zynko_secret_key_2026"

# =====================
# DATABASE INIT
# =====================
def init_db():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    
    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        friend_code TEXT UNIQUE NOT NULL,
        email_verified INTEGER DEFAULT 0
    )
    """)
    
    c.execute("""
    CREATE TABLE IF NOT EXISTS friends (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        friend_id INTEGER NOT NULL,
        UNIQUE(user_id, friend_id),
        FOREIGN KEY(user_id) REFERENCES users(id),
        FOREIGN KEY(friend_id) REFERENCES users(id)
    )
    """)
    
    conn.commit()
    conn.close()

init_db()

# =====================
# UTILS
# =====================
def generate_code():
    while True:
        code = "ZYN-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE friend_code=?", (code,))
        if not c.fetchone():
            conn.close()
            return code
        conn.close()

def hash_pwd(pwd):
    return hashlib.sha256(pwd.encode()).hexdigest()

def verify_pwd(pwd, hashed):
    return hash_pwd(pwd) == hashed

# =====================
# HOME
# =====================
@app.route("/")
def home():
    if "user_id" in session:
        return redirect("/dashboard")
    return render_template("index.html")

# =====================
# REGISTER
# =====================
@app.route("/register", methods=["POST"])
def register():
    username = request.form.get("username", "").strip()
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")
    
    if len(username) < 3 or len(password) < 6:
        return "Erreur: Username min 3 chars, Password min 6 chars"
    
    if "@" not in email:
        return "Email invalide"
    
    code = generate_code()
    hashed = hash_pwd(password)
    
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    
    try:
        c.execute(
            "INSERT INTO users (username, email, password, friend_code, email_verified) VALUES (?, ?, ?, ?, 1)",
            (username, email, hashed, code)
        )
        conn.commit()
        conn.close()
        return redirect("/")
    except Exception as e:
        conn.close()
        return f"Erreur: {str(e)}"

# =====================
# LOGIN
# =====================
@app.route("/login", methods=["POST"])
def login():
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT id, password FROM users WHERE username=?", (username,))
    user = c.fetchone()
    conn.close()
    
    if user and verify_pwd(password, user[1]):
        session["user_id"] = user[0]
        return redirect("/dashboard")
    
    return "Login incorrect"

# =====================
# DASHBOARD
# =====================
@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect("/")
    
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    
    c.execute("SELECT username, friend_code, email FROM users WHERE id=?", (session["user_id"],))
    user = c.fetchone()
    
    if not user:
        conn.close()
        session.clear()
        return redirect("/")
    
    c.execute("""
    SELECT u.id, u.username FROM friends f
    JOIN users u ON u.id = f.friend_id
    WHERE f.user_id=?
    ORDER BY u.username ASC
    """, (session["user_id"],))
    
    friends = c.fetchall()
    conn.close()
    
    return render_template("dashboard.html", user=user, friends=friends)

# =====================
# ADD FRIEND
# =====================
@app.route("/add_friend", methods=["POST"])
def add_friend():
    if "user_id" not in session:
        return redirect("/")
    
    code = request.form.get("code", "").upper().strip()
    
    if not code:
        return "Code vide"
    
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    
    c.execute("SELECT id, username FROM users WHERE friend_code=?", (code,))
    friend = c.fetchone()
    
    if not friend:
        conn.close()
        return "Code non trouve"
    
    friend_id = friend[0]
    user_id = session["user_id"]
    
    if user_id == friend_id:
        conn.close()
        return "Tu ne peux pas t'ajouter toi-meme"
    
    c.execute("SELECT * FROM friends WHERE user_id=? AND friend_id=?", (user_id, friend_id))
    if c.fetchone():
        conn.close()
        return "Deja amis"
    
    try:
        c.execute("INSERT INTO friends (user_id, friend_id) VALUES (?, ?)", (user_id, friend_id))
        c.execute("INSERT OR IGNORE INTO friends (user_id, friend_id) VALUES (?, ?)", (friend_id, user_id))
        conn.commit()
        conn.close()
        return redirect("/dashboard")
    except Exception as e:
        conn.close()
        return f"Erreur: {str(e)}"

# =====================
# LOGOUT
# =====================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=False)
