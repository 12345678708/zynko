from flask import Flask, render_template, request, session, redirect
from flask_socketio import SocketIO, emit, join_room
import sqlite3

app = Flask(__name__)
app.secret_key = "secret"
socketio = SocketIO(app, cors_allowed_origins="*")

# ======================
# DATABASE
# ======================
def db():
    return sqlite3.connect("database.db")

def init_db():
    conn = db()
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT, password TEXT)")
    conn.commit()
init_db()

# ======================
# ROUTES
# ======================
@app.route("/")
def index():
    if "user" in session:
        return render_template("chat.html", user=session["user"])
    return redirect("/login")

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        u = request.form["username"]
        p = request.form["password"]
        conn = db()
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=? AND password=?", (u,p))
        if c.fetchone():
            session["user"] = u
            return redirect("/")
    return render_template("login.html")

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        u = request.form["username"]
        p = request.form["password"]
        conn = db()
        c = conn.cursor()
        c.execute("INSERT INTO users (username,password) VALUES (?,?)",(u,p))
        conn.commit()
        return redirect("/login")
    return render_template("register.html")

# ======================
# SOCKET (TEMPS RÉEL)
# ======================
users_online = {}

@socketio.on("connect")
def connect():
    print("connecté")

@socketio.on("join")
def join(data):
    user = data["user"]
    users_online[user] = True
    emit("online_users", list(users_online.keys()), broadcast=True)

@socketio.on("message")
def message(data):
    emit("message", data, broadcast=True)

@socketio.on("typing")
def typing(data):
    emit("typing", data, broadcast=True)

@socketio.on("disconnect")
def disconnect():
    print("déconnecté")

# ======================
if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000)
