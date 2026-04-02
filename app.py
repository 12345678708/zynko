from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
import sqlite3, os, random

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

UPLOAD = "static/uploads"
os.makedirs(UPLOAD, exist_ok=True)

# ===== DB =====
def db():
    return sqlite3.connect("database.db")

def init():
    c = db().cursor()
    c.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT, code TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS messages (user TEXT, msg TEXT)")
    db().commit()

init()

# ===== ROUTE =====
@app.route("/")
def home():
    return render_template("chat.html")

# ===== UPLOAD =====
@app.route("/upload", methods=["POST"])
def upload():
    f = request.files["file"]
    path = os.path.join(UPLOAD, f.filename)
    f.save(path)
    return jsonify({"file": f.filename})

# ===== SOCKET =====
users_online = {}
typing_users = set()

@socketio.on("connect_user")
def connect(data):
    users_online[data["user"]] = request.sid
    emit("online", list(users_online.keys()), broadcast=True)

@socketio.on("send_message")
def msg(data):
    emit("new_message", data, broadcast=True)

@socketio.on("typing")
def typing(data):
    typing_users.add(data["user"])
    emit("typing", list(typing_users), broadcast=True)

@socketio.on("stop_typing")
def stop(data):
    typing_users.discard(data["user"])
    emit("typing", list(typing_users), broadcast=True)

# ===== RUN =====
if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000)
