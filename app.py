from flask import Flask, render_template, request, redirect, session, jsonify
from flask_socketio import SocketIO, emit
import sqlite3, os

app = Flask(__name__)
app.secret_key = "secret"
socketio = SocketIO(app, cors_allowed_origins="*")

UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ===== DATABASE =====
def db():
    return sqlite3.connect("database.db")

def init():
    conn = db()
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT, password TEXT)")
    conn.commit()

init()

# ===== ROUTES =====
@app.route("/upload", methods=["POST"])
def upload():
    if "file" not in request.files:
        return "no file", 400

    file = request.files["file"]

    if file.filename == "":
        return "empty", 400

    path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(path)

    return jsonify({"file": file.filename})

# ===== IMAGE =====
@app.route("/upload", methods=["POST"])
def upload():
    file = request.files["file"]
    path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(path)
    return jsonify({"file": file.filename})

# ===== SOCKET =====
online_users = set()

@socketio.on("join")
def join(data):
    online_users.add(data["user"])
    emit("online", list(online_users), broadcast=True)

@socketio.on("message")
def message(data):
    emit("message", data, broadcast=True)

# ===== RUN =====
if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000)
