from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
import os, sqlite3, random

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

UPLOAD = "static/uploads"
os.makedirs(UPLOAD, exist_ok=True)

# ===== DATABASE =====
def db():
    return sqlite3.connect("database.db")

def init():
    c = db().cursor()
    c.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT, code TEXT)")
    db().commit()

init()

# ===== ROUTE =====
@app.route("/")
def home():
    return render_template("chat.html")

# ===== UPLOAD IMAGE =====
@app.route("/upload", methods=["POST"])
def upload():
    f = request.files["file"]
    path = os.path.join(UPLOAD, f.filename)
    f.save(path)
    return jsonify({"file": f.filename})

# ===== UPLOAD AUDIO =====
@app.route("/upload_audio", methods=["POST"])
def upload_audio():
    audio = request.files["audio"]
    path = os.path.join(UPLOAD, audio.filename)
    audio.save(path)
    return jsonify({"audio": audio.filename})

# ===== USERS =====
@app.route("/create_user", methods=["POST"])
def create_user():
    name = request.json["name"]
    code = str(random.randint(100000,999999))

    conn = db()
    c = conn.cursor()
    c.execute("INSERT INTO users (name,code) VALUES (?,?)",(name,code))
    conn.commit()

    return jsonify({"code":code})

# ===== SOCKET =====
users_online = {}
typing_users = set()

@socketio.on("connect_user")
def connect(data):
    users_online[data["user"]] = request.sid
    emit("online", list(users_online.keys()), broadcast=True)

@socketio.on("send_message")
def message(data):
    emit("new_message", data, broadcast=True)

@socketio.on("typing")
def typing(data):
    typing_users.add(data["user"])
    emit("typing", list(typing_users), broadcast=True)

@socketio.on("stop_typing")
def stop(data):
    typing_users.discard(data["user"])
    emit("typing", list(typing_users), broadcast=True)

# ===== GROUPES =====
@socketio.on("join_group")
def join(data):
    emit("group_joined", data, broadcast=True)

@socketio.on("group_message")
def group_msg(data):
    emit("new_message", data, broadcast=True)

# ===== REACTIONS =====
@socketio.on("react")
def react(data):
    emit("reaction", data, broadcast=True)

# ===== CALL =====
@socketio.on("call")
def call(data):
    emit("call", data, broadcast=True)

@socketio.on("answer")
def answer(data):
    emit("answer", data, broadcast=True)

# ===== RUN =====
if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000)
