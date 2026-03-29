from flask import Flask, render_template, request, session, redirect
from flask_socketio import SocketIO, emit, join_room
import sqlite3, uuid

app = Flask(__name__)
app.secret_key = "secret"
socketio = SocketIO(app, cors_allowed_origins="*")

def db():
    return sqlite3.connect("database.db")

def init():
    conn = db()
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, username TEXT, password TEXT, code TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS friends(user TEXT, friend TEXT)")
    conn.commit()
init()

users_online = {}

# ================= ROUTES
@app.route("/")
def home():
    if "user" not in session:
        return redirect("/login")
    return render_template("chat.html", user=session["user"])

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        u = request.form["u"]
        p = request.form["p"]
        c = db().cursor()
        c.execute("SELECT * FROM users WHERE username=? AND password=?", (u,p))
        if c.fetchone():
            session["user"] = u
            return redirect("/")
    return render_template("login.html")

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        u = request.form["u"]
        p = request.form["p"]
        code = str(uuid.uuid4())[:6]
        conn = db()
        conn.execute("INSERT INTO users(username,password,code) VALUES(?,?,?)",(u,p,code))
        conn.commit()
        return redirect("/login")
    return render_template("register.html")

# ================= SOCKET

@socketio.on("join")
def join(data):
    user = data["user"]
    users_online[user] = True
    emit("online", list(users_online.keys()), broadcast=True)

@socketio.on("message")
def msg(data):
    emit("message", data, broadcast=True)

@socketio.on("typing")
def typing(data):
    emit("typing", data, broadcast=True)

@socketio.on("image")
def image(data):
    emit("image", data, broadcast=True)

@socketio.on("voice")
def voice(data):
    emit("voice", data, broadcast=True)

# ================= CALL SIGNALING (WebRTC)

@socketio.on("call")
def call(data):
    emit("call", data, broadcast=True)

@socketio.on("signal")
def signal(data):
    emit("signal", data, broadcast=True)

@socketio.on("disconnect")
def leave():
    pass

if __name__ == "__main__":
    socketio.run(app)
