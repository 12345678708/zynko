from flask import Flask, render_template, request, redirect, session, jsonify
from flask_socketio import SocketIO, emit
import sqlite3, os

app = Flask(__name__)
app.secret_key = "secret"
socketio = SocketIO(app, cors_allowed_origins="*")

UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ================= DB =================
def db():
    return sqlite3.connect("database.db")

def init():
    conn = db()
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT, email TEXT, password TEXT)")
    conn.commit()

init()

# ================= ROUTES =================
@app.route("/")
def home():
    if "user" not in session:
        return redirect("/login")
    return render_template("chat.html", user=session["user"])

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
        e = request.form["email"]
        p = request.form["password"]

        conn = db()
        c = conn.cursor()
        c.execute("INSERT INTO users (username,email,password) VALUES (?,?,?)",(u,e,p))
        conn.commit()

        return redirect("/login")
    return render_template("register.html")

# ================= SOCKET =================
@socketio.on("message")
def handle_message(data):
    emit("message", data, broadcast=True)

@socketio.on("typing")
def typing(data):
    emit("typing", data, broadcast=True)

# ================= IMAGE UPLOAD =================
@app.route("/upload", methods=["POST"])
def upload():
    file = request.files["file"]
    path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(path)
    return jsonify({"file": file.filename})

# ================= RUN =================
if __name__ == "__main__":
    socketio.run(app, debug=True)
