from flask import Flask, render_template, request, redirect, session
import sqlite3
import random
import string
import os

app = Flask(__name__)
app.secret_key = "zynko_secret_key"

# =========================
# 🔑 CODE AMI UNIQUE
# =========================
def generate_friend_code():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    while True:
        code = "ZYN-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        c.execute("SELECT * FROM users WHERE friend_code=?", (code,))
        if not c.fetchone():
            conn.close()
            return code


# =========================
# 🧱 INIT DATABASE
# =========================
def init_db():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        friend_code TEXT UNIQUE
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS friends (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        friend_id INTEGER
    )
    """)

    conn.commit()
    conn.close()

init_db()


# =========================
# 🏠 HOME
# =========================
@app.route("/")
def home():
    if "user_id" in session:
        return redirect("/dashboard")
    return render_template("index.html")


# =========================
# 🆕 REGISTER
# =========================
@app.route("/register", methods=["POST"])
def register():
    username = request.form["username"]
    password = request.form["password"]
    code = generate_friend_code()

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    try:
        c.execute(
            "INSERT INTO users (username, password, friend_code) VALUES (?, ?, ?)",
            (username, password, code)
        )
        conn.commit()
    except:
        return "Utilisateur déjà existant ❌"

    conn.close()
    return redirect("/")


# =========================
# 🔐 LOGIN
# =========================
@app.route("/login", methods=["POST"])
def login():
    username = request.form["username"]
    password = request.form["password"]

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("SELECT id FROM users WHERE username=? AND password=?", (username, password))
    user = c.fetchone()

    conn.close()

    if user:
        session["user_id"] = user[0]
        return redirect("/dashboard")

    return "Login incorrect ❌"


# =========================
# 📊 DASHBOARD
# =========================
@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect("/")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("SELECT username, friend_code FROM users WHERE id=?", (session["user_id"],))
    user = c.fetchone()

    c.execute("""
    SELECT u.username
    FROM friends f
    JOIN users u ON u.id = f.friend_id
    WHERE f.user_id=?
    """, (session["user_id"],))

    friends = c.fetchall()

    conn.close()

    return render_template("dashboard.html", user=user, friends=friends)


# =========================
# ➕ ADD FRIEND
# =========================
@app.route("/add_friend", methods=["POST"])
def add_friend():
    if "user_id" not in session:
        return redirect("/")

    code = request.form["code"]

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("SELECT id FROM users WHERE friend_code=?", (code,))
    user = c.fetchone()

    if not user:
        return "Code introuvable ❌"

    friend_id = user[0]
    user_id = session["user_id"]

    c.execute("INSERT INTO friends (user_id, friend_id) VALUES (?, ?)", (user_id, friend_id))
    conn.commit()
    conn.close()

    return redirect("/dashboard")


# =========================
# 🚪 LOGOUT
# =========================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


if __name__ == "__main__":
    # Production: gunicorn launches this, don't use app.run()
    # Local dev: python app.py works fine
    app.run(debug=False)
