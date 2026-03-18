from flask import Flask, render_template, request, redirect, session, jsonify
from flask_socketio import SocketIO, emit, join_room
import sqlite3, os, uuid, time
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "secret"
socketio = SocketIO(app, cors_allowed_origins="*")

UPLOAD_FOLDER="static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def db():
    return sqlite3.connect("db.db", check_same_thread=False)

# INIT DB
def init():
    conn=db()
    c=conn.cursor()

    c.execute("""CREATE TABLE IF NOT EXISTS users(
        username TEXT PRIMARY KEY,
        email TEXT UNIQUE,
        password TEXT,
        friend_code TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS friends(
        id INTEGER PRIMARY KEY,
        sender TEXT,
        receiver TEXT,
        status TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS messages(
        id INTEGER PRIMARY KEY,
        sender TEXT,
        receiver TEXT,
        text TEXT,
        image TEXT,
        audio TEXT,
        time INTEGER
    )""")

    conn.commit()
    conn.close()

init()

# LOGIN
@app.route("/", methods=["GET","POST"])
def login():
    if request.method=="POST":
        email=request.form.get("email")
        password=request.form.get("password")

        conn=db()
        user=conn.execute("SELECT username,password FROM users WHERE email=?",(email,)).fetchone()
        conn.close()

        if user and check_password_hash(user[1], password):
            session["user"]=user[0]
            return redirect("/chat")

    return render_template("login.html")

# REGISTER
@app.route("/register", methods=["GET","POST"])
def register():
    if request.method=="POST":
        username=request.form.get("username")
        email=request.form.get("email")
        password=generate_password_hash(request.form.get("password"))
        code=str(uuid.uuid4())[:8]

        conn=db()
        try:
            conn.execute("INSERT INTO users VALUES(?,?,?,?)",(username,email,password,code))
            conn.commit()
        except:
            return "Utilisateur existe déjà"
        conn.close()

        return redirect("/")

    return render_template("register.html")

# CHAT
@app.route("/chat")
def chat():
    if "user" not in session:
        return redirect("/")
    return render_template("chat.html", username=session["user"])

# ADD FRIEND
@app.route("/add_friend", methods=["POST"])
def add_friend():
    code=request.form.get("code")
    user=session["user"]

    conn=db()
    target=conn.execute("SELECT username FROM users WHERE friend_code=?",(code,)).fetchone()

    if target:
        conn.execute("INSERT INTO friends(sender,receiver,status) VALUES(?,?,?)",
                     (user,target[0],"pending"))
        conn.commit()

    conn.close()
    return redirect("/chat")

# ACCEPT FRIEND
@app.route("/accept/<user>")
def accept(user):
    me=session["user"]
    conn=db()
    conn.execute("UPDATE friends SET status='accepted' WHERE sender=? AND receiver=?",(user,me))
    conn.commit()
    conn.close()
    return redirect("/chat")

# SOCKET
@socketio.on("join")
def join(data):
    join_room(data)

@socketio.on("send_message")
def msg(data):
    room=data["receiver"]
    emit("new_message", data, room=room)
    emit("new_message", data, room=data["sender"])

if __name__=="__main__":
    socketio.run(app, debug=True)
