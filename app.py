from flask import Flask, render_template, request, redirect, session, jsonify
from flask_socketio import SocketIO, emit, join_room
import sqlite3, uuid, os

app = Flask(__name__)
app.secret_key = "zynko_secret"

socketio = SocketIO(app, cors_allowed_origins="*")

UPLOAD_FOLDER = "static/uploads"

if os.path.exists(UPLOAD_FOLDER) and not os.path.isdir(UPLOAD_FOLDER):
    os.remove(UPLOAD_FOLDER)

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# -------- DB --------

def db():
    return sqlite3.connect("zynko.db", check_same_thread=False)

def init_db():
    conn = db()
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS users(
        username TEXT UNIQUE,
        email TEXT,
        password TEXT,
        online INTEGER DEFAULT 0
    )
    """)

    conn.commit()
    conn.close()

init_db()

# -------- LOGIN --------

@app.route("/", methods=["GET","POST"])
def login():
    if request.method == "POST":

        email = request.form.get("email")
        password = request.form.get("password")

        if not email or not password:
            return "Erreur",400

        conn=db()
        user=conn.execute(
            "SELECT username FROM users WHERE email=? AND password=?",
            (email,password)
        ).fetchone()
        conn.close()

        if user:
            session["user"]=user[0]

            conn=db()
            conn.execute("UPDATE users SET online=1 WHERE username=?",(user[0],))
            conn.commit()
            conn.close()

            return redirect("/chat")

    return render_template("login.html")

# -------- REGISTER --------

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method=="POST":

        username=request.form.get("username")
        email=request.form.get("email")
        password=request.form.get("password")

        if not username or not email or not password:
            return "Erreur champs",400

        try:
            conn=db()
            conn.execute(
                "INSERT INTO users VALUES(?,?,?,0)",
                (username,email,password)
            )
            conn.commit()
            conn.close()
        except:
            return "Utilisateur existe"

        return redirect("/")

    return render_template("register.html")

# -------- CHAT --------

@app.route("/chat")
def chat():
    if "user" not in session:
        return redirect("/")
    return render_template("chat.html", user=session["user"])

# -------- UPLOAD IMAGE --------

@app.route("/upload", methods=["POST"])
def upload():
    file = request.files.get("file")
    if not file:
        return "No file",400

    filename = str(uuid.uuid4()) + file.filename
    path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(path)

    return jsonify({"url": "/static/uploads/"+filename})

# -------- SOCKET --------

@socketio.on("join")
def join(data):
    join_room(data["room"])

@socketio.on("send")
def send(data):
    emit("msg", data, to=data["room"])

# -------- LOGOUT --------

@app.route("/logout")
def logout():
    user=session.get("user")

    conn=db()
    conn.execute("UPDATE users SET online=0 WHERE username=?",(user,))
    conn.commit()
    conn.close()

    session.clear()
    return redirect("/")

# -------- RUN --------

if __name__=="__main__":
    socketio.run(app)
