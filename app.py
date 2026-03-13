from flask import Flask, render_template, request, redirect, session, jsonify
from flask_socketio import SocketIO, emit
import sqlite3
import os
import uuid

app = Flask(__name__)
app.secret_key = "zynko_secret"

socketio = SocketIO(app, cors_allowed_origins="*")

# ---------------- UPLOAD FOLDER ----------------

UPLOAD_FOLDER = "static/uploads"

if not os.path.exists("static"):
    os.makedirs("static")

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# ---------------- DATABASE ----------------

def db():
    return sqlite3.connect("zynko.db", check_same_thread=False)


def init_db():

    conn = db()
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        email TEXT UNIQUE,
        password TEXT,
        avatar TEXT,
        friend_code TEXT UNIQUE,
        online INTEGER DEFAULT 0
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS friends(
        user TEXT,
        friend TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS messages(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender TEXT,
        receiver TEXT,
        text TEXT,
        image TEXT,
        audio TEXT
    )
    """)

    conn.commit()
    conn.close()

init_db()

# ---------------- LOGIN ----------------

@app.route("/", methods=["GET","POST"])
def login():

    if request.method == "POST":

        email = request.form.get("email")
        password = request.form.get("password")

        if not email or not password:
            return redirect("/")

        conn = db()
        c = conn.cursor()

        user = c.execute(
        "SELECT username FROM users WHERE email=? AND password=?",
        (email,password)).fetchone()

        conn.close()

        if user:

            session["user"] = user[0]

            conn = db()
            conn.execute(
            "UPDATE users SET online=1 WHERE username=?",
            (user[0],))
            conn.commit()
            conn.close()

            return redirect("/chat")

    return render_template("login.html")

# ---------------- REGISTER ----------------

@app.route("/register", methods=["GET","POST"])
def register():

    if request.method == "POST":

        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")

        if not username or not email or not password:
            return redirect("/register")

        code = str(uuid.uuid4())[:8]

        conn = db()
        c = conn.cursor()

        try:

            c.execute("""
            INSERT INTO users(username,email,password,avatar,friend_code)
            VALUES(?,?,?,?,?)
            """,(username,email,password,"avatar.png",code))

            conn.commit()

        except:
            conn.close()
            return "Utilisateur déjà existant"

        conn.close()

        return redirect("/")

    return render_template("register.html")

# ---------------- CHAT PAGE ----------------

@app.route("/chat")
def chat():

    if "user" not in session:
        return redirect("/")

    username = session["user"]

    conn = db()
    c = conn.cursor()

    users = c.execute(
    "SELECT username,online FROM users").fetchall()

    friends = c.execute(
    "SELECT friend FROM friends WHERE user=?",
    (username,)).fetchall()

    conn.close()

    return render_template(
        "chat.html",
        username=username,
        users=users,
        friends=friends
    )

# ---------------- ADD FRIEND ----------------

@app.route("/add_friend",methods=["POST"])
def add_friend():

    if "user" not in session:
        return redirect("/")

    code = request.form.get("code")
    user = session["user"]

    conn = db()
    c = conn.cursor()

    friend = c.execute(
    "SELECT username FROM users WHERE friend_code=?",
    (code,)).fetchone()

    if friend:

        c.execute(
        "INSERT INTO friends(user,friend) VALUES(?,?)",
        (user,friend[0]))

        conn.commit()

    conn.close()

    return redirect("/chat")

# ---------------- UPLOAD IMAGE ----------------

@app.route("/upload",methods=["POST"])
def upload():

    if "file" not in request.files:
        return jsonify({"error":"no file"})

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"error":"empty file"})

    filename = str(uuid.uuid4()) + "_" + file.filename

    path = os.path.join(UPLOAD_FOLDER, filename)

    file.save(path)

    return jsonify({"file": filename})

# ---------------- SOCKET CHAT ----------------

@socketio.on("send_message")
def message(data):

    emit("new_message", data, broadcast=True)

# ---------------- LOGOUT ----------------

@app.route("/logout")
def logout():

    user = session.get("user")

    if user:

        conn = db()
        conn.execute(
        "UPDATE users SET online=0 WHERE username=?",
        (user,))
        conn.commit()
        conn.close()

    session.clear()

    return redirect("/")

# ---------------- RUN ----------------

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=10000)
