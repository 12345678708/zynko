from flask import Blueprint, render_template, request
from flask_login import login_required, current_user
from ..models import Message
from ..extensions import db, socketio
from flask_socketio import emit, join_room, leave_room

main_bp = Blueprint("main", __name__, url_prefix="")

@main_bp.route("/")
def index():
    return render_template("index.html")

@main_bp.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html", user=current_user)

# Socket.IO handlers for chat & signaling
@socketio.on("join")
def on_join(data):
    room = data.get("room")
    username = data.get("username")
    if room:
        join_room(room)
        emit("status", {"msg": f"{username} a rejoint {room}"}, room=room)

@socketio.on("leave")
def on_leave(data):
    room = data.get("room")
    username = data.get("username")
    if room:
        leave_room(room)
        emit("status", {"msg": f"{username} a quitté {room}"}, room=room)

@socketio.on("chat_message")
def handle_chat_message(data):
    room = data.get("room")
    username = data.get("username")
    body = data.get("body")
    if room and username and body:
        msg = Message(user_id=None, username=username, room=room, body=body)
        db.session.add(msg)
        db.session.commit()
        emit("chat_message", {"username": username, "body": body, "created_at": msg.created_at.isoformat()}, room=room)

@socketio.on("webrtc_signal")
def handle_webrtc_signal(data):
    room = data.get("room")
    emit("webrtc_signal", data, room=room, include_self=False)
