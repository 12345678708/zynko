from flask import Flask, render_template, request, redirect, session, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room
import sqlite3, os, uuid
from datetime import datetime

app = Flask(__name__)
app.secret_key = "zynko_secret_god"
socketio = SocketIO(app, cors_allowed_origins="*")

UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ---------------- DATABASE ----------------
def db():
    return sqlite3.connect("zynko.db")

def init_db():
    conn = db()
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        email TEXT UNIQUE,
        password TEXT,
        avatar TEXT DEFAULT 'avatar.png',
        friend_code TEXT UNIQUE,
        online INTEGER DEFAULT 0
    )
    """)
    c.execute("""
    CREATE TABLE IF NOT EXISTS friends(
        user TEXT,
        friend TEXT,
        status TEXT DEFAULT 'pending'
    )
    """)
    c.execute("""
    CREATE TABLE IF NOT EXISTS messages(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender TEXT,
        receiver TEXT,
        text TEXT,
        image TEXT,
        audio TEXT,
        timestamp TEXT,
        reaction TEXT
    )
    """)
    conn.commit()
    conn.close()

init_db()

# ---------------- LOGIN ----------------
@app.route("/", methods=["GET","POST"])
def login():
    if request.method=="POST":
        email = request.form.get("email")
        password = request.form.get("password")
        if not email or not password:
            return "Email et mot de passe obligatoires",400
        conn = db()
        c = conn.cursor()
        user = c.execute(
            "SELECT username FROM users WHERE email=? AND password=?",
            (email,password)).fetchone()
        if user:
            session["user"]=user[0]
            c.execute("UPDATE users SET online=1 WHERE username=?",(user[0],))
            conn.commit()
            conn.close()
            return redirect("/chat")
        conn.close()
    return render_template("login.html")

# ---------------- REGISTER ----------------
@app.route("/register", methods=["GET","POST"])
def register():
    if request.method=="POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        if not username or not email or not password:
            return "Tous les champs sont obligatoires",400
        code = str(uuid.uuid4())[:8]
        conn = db()
        c = conn.cursor()
        try:
            c.execute("INSERT INTO users(username,email,password,friend_code) VALUES(?,?,?,?)",
                      (username,email,password,code))
            conn.commit()
        except:
            conn.close()
            return "Utilisateur déjà existant"
        conn.close()
        return redirect("/")
    return render_template("register.html")

# ---------------- CHAT ----------------
@app.route("/chat")
def chat():
    if "user" not in session:
        return redirect("/")
    username = session["user"]
    conn=db()
    c=conn.cursor()
    users = c.execute("SELECT username,online,avatar FROM users").fetchall()
    friends = c.execute("SELECT friend,status FROM friends WHERE user=?",(username,)).fetchall()
    conn.close()
    return render_template("chat.html", username=username, users=users, friends=friends)

# ---------------- FRIEND REQUEST ----------------
@app.route("/add_friend",methods=["POST"])
def add_friend():
    code = request.form.get("code")
    user = session["user"]
    conn=db()
    c=conn.cursor()
    friend = c.execute("SELECT username FROM users WHERE friend_code=?",(code,)).fetchone()
    if friend:
        try:
            c.execute("INSERT INTO friends(user,friend,status) VALUES(?,?,?)",(user,friend[0],"pending"))
            conn.commit()
        except:
            pass
    conn.close()
    return redirect("/chat")

# ---------------- UPLOAD FILE ----------------
@app.route("/upload",methods=["POST"])
def upload():
    file = request.files["file"]
    filename = str(uuid.uuid4())+"_"+file.filename
    path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(path)
    return jsonify({"file":filename})

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    user = session.get("user")
    conn = db()
    conn.execute("UPDATE users SET online=0 WHERE username=?",(user,))
    conn.commit()
    conn.close()
    session.clear()
    return redirect("/")

# ---------------- SOCKET ----------------
online_users = set()

@socketio.on("connect")
def connected():
    user = session.get("user")
    if user:
        online_users.add(user)
        emit("update_users", list(online_users), broadcast=True)

@socketio.on("disconnect")
def disconnected():
    user = session.get("user")
    if user:
        online_users.discard(user)
        emit("update_users", list(online_users), broadcast=True)

@socketio.on("send_message")
def handle_message(data):
    user = data.get("user")
    receiver = data.get("receiver","all")
    text = data.get("text")
    image = data.get("image")
    audio = data.get("audio")
    timestamp = str(datetime.now())
    conn = db()
    c=conn.cursor()
    c.execute("INSERT INTO messages(sender,receiver,text,image,audio,timestamp) VALUES(?,?,?,?,?,?)",
              (user,receiver,text,image,audio,timestamp))
    conn.commit()
    conn.close()
    emit("new_message", data, broadcast=True)

@socketio.on("typing")
def typing(data):
    emit("typing", data, broadcast=True, include_self=False)

if __name__=="__main__":
    socketio.run(app, debug=True)
