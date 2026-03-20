from flask import Flask, render_template, request, redirect, session, jsonify
from flask_socketio import SocketIO, emit
import sqlite3
import uuid
import cloudinary
import cloudinary.uploader

app = Flask(__name__)
app.secret_key = "zynko_secret"

socketio = SocketIO(app, cors_allowed_origins="*")

# ---------------- CLOUDINARY ----------------

cloudinary.config(
    cloud_name="TON_CLOUD_NAME",
    api_key="TON_API_KEY",
    api_secret="TON_API_SECRET"
)

# ---------------- DATABASE ----------------

def db():
    return sqlite3.connect("zynko.db")

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
    CREATE TABLE IF NOT EXISTS messages(
        id INTEGER PRIMARY KEY,
        sender TEXT,
        text TEXT,
        image TEXT
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
            return "Email obligatoire", 400

        conn = db()
        c = conn.cursor()

        user = c.execute(
            "SELECT username FROM users WHERE email=? AND password=?",
            (email, password)
        ).fetchone()

        conn.close()

        if user:
            session["user"] = user[0]
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
            return "Champs manquants", 400

        code = str(uuid.uuid4())[:8]

        conn = db()
        c = conn.cursor()

        try:
            c.execute(
                "INSERT INTO users(username,email,password,friend_code) VALUES(?,?,?,?)",
                (username,email,password,code)
            )
            conn.commit()
        except:
            return "Utilisateur existe déjà"

        conn.close()
        return redirect("/")

    return render_template("register.html")

# ---------------- CHAT ----------------

@app.route("/chat")
def chat():
    if "user" not in session:
        return redirect("/")

    return render_template("chat.html", user=session["user"])

# ---------------- UPLOAD IMAGE ----------------

@app.route("/upload", methods=["POST"])
def upload():
    file = request.files["file"]

    if not file:
        return "No file", 400

    result = cloudinary.uploader.upload(file)

    return jsonify({"url": result["secure_url"]})

# ---------------- SOCKET ----------------

@socketio.on("send_message")
def handle_message(data):

    emit("receive_message", data, broadcast=True)

# ---------------- LOGOUT ----------------

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ---------------- RUN ----------------

if __name__ == "__main__":
    socketio.run(app)
