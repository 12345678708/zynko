from flask import Flask, render_template, request, redirect, session, jsonify
from flask_socketio import SocketIO, emit, join_room
import sqlite3
import uuid

app = Flask(__name__)
app.secret_key = "zynko_secret"

socketio = SocketIO(app, cors_allowed_origins="*")

# ---------------- DB ----------------

def db():
    return sqlite3.connect("zynko.db")

def init_db():
    conn = db()
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS users(
        username TEXT UNIQUE,
        email TEXT,
        password TEXT,
        friend_code TEXT,
        online INTEGER DEFAULT 0
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS groups(
        id INTEGER PRIMARY KEY,
        name TEXT
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

        conn = db()
        user = conn.execute(
            "SELECT username FROM users WHERE email=? AND password=?",
            (email,password)
        ).fetchone()
        conn.close()

        if user:
            session["user"]=user[0]
            return redirect("/chat")

    return render_template("login.html")

# ---------------- REGISTER ----------------

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":

        username=request.form.get("username")
        email=request.form.get("email")
        password=request.form.get("password")

        if not username or not email or not password:
            return "Erreur champs",400

        code=str(uuid.uuid4())[:8]

        try:
            conn=db()
            conn.execute(
                "INSERT INTO users VALUES(?,?,?,?,0)",
                (username,email,password,code)
            )
            conn.commit()
            conn.close()
        except:
            return "Utilisateur existe"

        return redirect("/")

    return render_template("register.html")

# ---------------- CHAT ----------------

@app.route("/chat")
def chat():
    if "user" not in session:
        return redirect("/")
    return render_template("chat.html", user=session["user"])

# ---------------- GROUP ----------------

@app.route("/create_group", methods=["POST"])
def create_group():
    name = request.json.get("name")

    conn=db()
    conn.execute("INSERT INTO groups(name) VALUES(?)",(name,))
    conn.commit()
    conn.close()

    return "ok"

# ---------------- SOCKET ----------------

@socketio.on("join")
def join(data):
    join_room(data["room"])

@socketio.on("send")
def send(data):
    emit("msg", data, to=data["room"])

# ---------------- RUN ----------------

if __name__ == "__main__":
    socketio.run(app)
