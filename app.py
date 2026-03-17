from flask import Flask, render_template, request, redirect, session, jsonify
from flask_socketio import SocketIO, emit
import sqlite3, os, uuid

app = Flask(__name__)
app.secret_key = "zynko_secret"
socketio = SocketIO(app, cors_allowed_origins="*")

UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def db():
    return sqlite3.connect("zynko.db", check_same_thread=False)

def init_db():
    conn = db()
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY,
        username TEXT UNIQUE,
        email TEXT UNIQUE,
        password TEXT,
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

    conn.commit()
    conn.close()

init_db()

# LOGIN
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
            session["user"] = user[0]
            return redirect("/chat")

    return render_template("login.html")

# REGISTER
@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")

        if not username or not email or not password:
            return redirect("/register")

        code = str(uuid.uuid4())[:8]

        try:
            conn = db()
            conn.execute(
                "INSERT INTO users(username,email,password,friend_code) VALUES(?,?,?,?)",
                (username,email,password,code)
            )
            conn.commit()
            conn.close()
        except:
            return "Erreur utilisateur"

        return redirect("/")

    return render_template("register.html")

# CHAT
@app.route("/chat")
def chat():
    if "user" not in session:
        return redirect("/")

    conn = db()
    users = conn.execute("SELECT username FROM users").fetchall()
    conn.close()

    return render_template("chat.html", username=session["user"], users=users)

# ADD FRIEND
@app.route("/add_friend", methods=["POST"])
def add_friend():
    code = request.form.get("code")
    user = session["user"]

    conn = db()
    friend = conn.execute(
        "SELECT username FROM users WHERE friend_code=?",
        (code,)
    ).fetchone()

    if friend:
        conn.execute("INSERT INTO friends VALUES(?,?)", (user,friend[0]))
        conn.commit()

    conn.close()
    return redirect("/chat")

# UPLOAD
@app.route("/upload", methods=["POST"])
def upload():
    file = request.files.get("file")
    if not file:
        return jsonify({"error":"no file"})

    name = str(uuid.uuid4()) + "_" + file.filename
    file.save(os.path.join(UPLOAD_FOLDER,name))

    return jsonify({"file":name})

# SOCKET
@socketio.on("send_message")
def handle(data):
    emit("new_message", data, broadcast=True)

# LOGOUT
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=10000)
