from flask import Flask, render_template, request, redirect, session, jsonify
from flask_socketio import SocketIO, emit
import sqlite3, os, uuid, time
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "zynko_secret"
socketio = SocketIO(app, cors_allowed_origins="*")

UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def db():
    return sqlite3.connect("zynko.db", check_same_thread=False)

def init_db():
    conn=db()
    c=conn.cursor()

    c.execute("""CREATE TABLE IF NOT EXISTS users(
        username TEXT PRIMARY KEY,
        email TEXT,
        password TEXT,
        friend_code TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS messages(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender TEXT,
        receiver TEXT,
        text TEXT,
        image TEXT,
        audio TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS reactions(
        msg_id INTEGER,
        user TEXT,
        emoji TEXT
    )""")

    conn.commit()
    conn.close()

init_db()

# LOGIN
@app.route("/", methods=["GET","POST"])
def login():
    if request.method=="POST":
        email=request.form["email"]
        password=request.form["password"]

        conn=db()
        c=conn.cursor()
        user=c.execute("SELECT username,password FROM users WHERE email=?",(email,)).fetchone()
        conn.close()

        if user and check_password_hash(user[1], password):
            session["user"]=user[0]
            return redirect("/chat")

    return render_template("login.html")

# REGISTER
@app.route("/register", methods=["GET","POST"])
def register():
    if request.method=="POST":
        username=request.form["username"]
        email=request.form["email"]
        password=generate_password_hash(request.form["password"])
        code=str(uuid.uuid4())[:8]

        conn=db()
        try:
            conn.execute("INSERT INTO users VALUES(?,?,?,?)",(username,email,password,code))
            conn.commit()
        except:
            return "Erreur utilisateur"
        conn.close()

        return redirect("/")

    return render_template("register.html")

# CHAT
@app.route("/chat")
def chat():
    if "user" not in session:
        return redirect("/")
    return render_template("chat.html", username=session["user"])

# SOCKET CHAT PRIVÉ
@socketio.on("send_message")
def msg(data):
    emit("new_message", data, room=data["receiver"])
    emit("new_message", data, room=data["sender"])

# REACTIONS ❤️
@socketio.on("react")
def react(data):
    emit("reaction", data, broadcast=True)

# WEBRTC SIGNAL
@socketio.on("call")
def call(data):
    emit("incoming_call", data, broadcast=True)

if __name__=="__main__":
    socketio.run(app, debug=True)
