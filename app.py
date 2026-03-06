from flask import Flask, render_template, request, redirect, session
import sqlite3
import random
import string

app = Flask(__name__)
app.secret_key = "zynko_secret"

# -----------------------------
# Base de données
# -----------------------------
def get_db():
    conn = sqlite3.connect("zynko.db")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        friend_code TEXT
    )
    """)
    conn.commit()
    conn.close()

init_db()

# -----------------------------
# Générer code ami
# -----------------------------
def generate_code():
    return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(6))

# -----------------------------
# Page accueil
# -----------------------------
@app.route("/")
def home():
    if "username" in session:
        return redirect("/chat")
    return redirect("/login")

# -----------------------------
# Login
# -----------------------------
@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db()
        user = conn.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (username,password)
        ).fetchone()
        conn.close()

        if user:
            session["username"] = username
            return redirect("/chat")

    return render_template("login.html")

# -----------------------------
# Register
# -----------------------------
@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        code = generate_code()

        conn = get_db()
        try:
            conn.execute(
                "INSERT INTO users(username,password,friend_code) VALUES(?,?,?)",
                (username,password,code)
            )
            conn.commit()
        except:
            pass
        conn.close()

        return redirect("/login")

    return render_template("register.html")

# -----------------------------
# Chat
# -----------------------------
@app.route("/chat")
def chat():
    if "username" not in session:
        return redirect("/login")

    conn = get_db()
    code = conn.execute(
        "SELECT friend_code FROM users WHERE username=?",
        (session["username"],)
    ).fetchone()

    conn.close()

    return render_template("chat.html", code=code["friend_code"])

# -----------------------------
# Logout
# -----------------------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# -----------------------------
# Lancer serveur
# -----------------------------
if __name__ == "__main__":
    app.run(debug=True)
