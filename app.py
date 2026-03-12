from flask import Flask, render_template, request, redirect, session, url_for, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
app.secret_key = "zynko_secret_key"
socketio = SocketIO(app)

UPLOAD_FOLDER = "static/uploads"
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Stockage temporaire (remplace par DB pour prod)
users = {}        # username -> dict {email, avatar, online, room}
messages = {}     # room -> list of messages

# --- ROUTES ---

@app.route("/")
def home():
    if "username" in session:
        return redirect("/chat")
    return redirect("/login")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        if not username or not email:
            return "Email et pseudo obligatoires", 400
        session["username"] = username
        session["email"] = email
        if username not in users:
            users[username] = {"email": email, "avatar": "/static/avatar.png", "online": True, "room": username}
            messages[username] = []
        else:
            users[username]["online"] = True
        return redirect("/chat")
    return render_template("login.html")

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        if not username or not email:
            return "Email et pseudo obligatoires", 400
        session["username"] = username
        session["email"] = email
        if username not in users:
            users[username] = {"email": email, "avatar": "/static/avatar.png", "online": True, "room": username}
            messages[username] = []
        else:
            return "Pseudo déjà utilisé", 400
        return redirect("/chat")
    return render_template("register.html")

@app.route("/logout")
def logout():
    username = session.get("username")
    if username in users:
        users[username]["online"] = False
    session.clear()
    return redirect("/login")

@app.route("/chat")
def chat():
    if "username" not in session:
        return redirect("/login")
    return render_template("chat.html", username=session["username"], users=users, messages=messages)

# --- UPLOADS ---
@app.route("/upload", methods=["POST"])
def upload():
    username = session.get("username")
    if not username:
        return "Non autorisé", 403
    file = request.files.get("file")
    if file:
        filename = secure_filename(file.filename)
        path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(path)
        return jsonify({"filename": filename})
    return "Pas de fichier", 400

# --- SOCKETIO ---
@socketio.on("connect")
def handle_connect():
    username = session.get("username")
    if username:
        users[username]["online"] = True
        emit("user_list", users, broadcast=True)

@socketio.on("disconnect")
def handle_disconnect():
    username = session.get("username")
    if username in users:
        users[username]["online"] = False
        emit("user_list", users, broadcast=True)

@socketio.on("send_message")
def handle_message(data):
    sender = session.get("username")
    target = data.get("target")
    text = data.get("text")
    img = data.get("image")
    audio = data.get("audio")
    if target in messages:
        messages[target].append([sender, text, img, audio])
        emit("new_message", {"sender": sender, "text": text, "image": img, "audio": audio}, room=target)
        emit("notification", {"from": sender}, room=target)

@socketio.on("join_room")
def on_join(data):
    room = data.get("room")
    join_room(room)

@socketio.on("leave_room")
def on_leave(data):
    room = data.get("room")
    leave_room(room)

if __name__ == "__main__":
    socketio.run(app, debug=True)
