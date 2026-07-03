from flask import Blueprint, render_template, request, jsonify, current_app, abort
from flask_login import login_required, current_user
from ..models import Message, DirectMessage, User, Friendship, Group, GroupMembership, GroupMessage
from ..extensions import db, socketio
from flask_socketio import emit, join_room, leave_room

main_bp = Blueprint("main", __name__, url_prefix="")

# in-memory mapping username -> room (personal room)
connected_user_rooms = {}

@main_bp.route("/")
def index():
    return render_template("index.html")

@main_bp.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html", user=current_user)

@main_bp.route('/messages')
@login_required
def messages():
    # minimal messages page; template handles socket connections
    return render_template('messages.html', user=current_user)

@main_bp.route('/friends')
@login_required
def friends_page():
    # list friend requests and friends
    requests = Friendship.query.filter_by(addressee_id=current_user.id, status='pending').all()
    friends = Friendship.query.filter(((Friendship.requester_id==current_user.id)|(Friendship.addressee_id==current_user.id)), Friendship.status=='accepted').all()
    return render_template('friends.html', requests=requests, friends=friends)

@main_bp.route('/friends/request', methods=['POST'])
@login_required
def send_friend_request():
    data = request.form or request.json or {}
    username = data.get('username')
    if not username:
        return jsonify({'error':'username required'}), 400
    target = User.query.filter_by(username=username).first()
    if not target:
        return jsonify({'error':'user not found'}), 404
    # avoid duplicates
    if Friendship.query.filter_by(requester_id=current_user.id, addressee_id=target.id).first() or Friendship.query.filter_by(requester_id=target.id, addressee_id=current_user.id).first():
        return jsonify({'status':'exists'}), 200
    fr = Friendship(requester_id=current_user.id, addressee_id=target.id, status='pending')
    db.session.add(fr)
    db.session.commit()
    # notify addressee if online
    room = f'user:{target.username}'
    try:
        emit('friend_request', {'from':current_user.username, 'id': fr.id}, room=room)
    except Exception:
        current_app.logger.debug('Could not emit friend_request to %s', room)
    return jsonify({'status':'sent'})

@main_bp.route('/friends/accept/<int:fr_id>', methods=['POST'])
@login_required
def accept_friend(fr_id):
    fr = Friendship.query.get_or_404(fr_id)
    if fr.addressee_id != current_user.id:
        abort(403)
    fr.status = 'accepted'
    db.session.commit()
    # notify requester
    requester = User.query.get(fr.requester_id)
    room = f'user:{requester.username}'
    try:
        emit('friend_accepted', {'by': current_user.username}, room=room)
    except Exception:
        current_app.logger.debug('Could not emit friend_accepted to %s', room)
    return jsonify({'status':'accepted'})

# Socket handlers
@socketio.on('join')
def on_join(data):
    room = data.get('room')
    username = data.get('username')
    if username:
        personal_room = f'user:{username}'
        join_room(personal_room)
        connected_user_rooms[username] = personal_room
        emit('status', {'msg': f'{username} connecté'}, room=personal_room)
    if room:
        join_room(room)
        emit('status', {'msg': f"{username} a rejoint {room}"}, room=room)

@socketio.on('leave')
def on_leave(data):
    room = data.get('room')
    username = data.get('username')
    if room:
        leave_room(room)
        emit('status', {'msg': f"{username} a quitté {room}"}, room=room)

@socketio.on('chat_message')
def handle_chat_message(data):
    room = data.get('room')
    username = data.get('username')
    body = data.get('body')
    if room and username and body:
        msg = Message(user_id=None, username=username, room=room, body=body)
        db.session.add(msg)
        db.session.commit()
        emit('chat_message', { 'username': username, 'body': body, 'created_at': msg.created_at.isoformat() }, room=room)

@socketio.on('private_message')
def handle_private_message(data):
    to = data.get('to')  # username of recipient
    from_user = data.get('from')
    body = data.get('body')
    if not to or not from_user or not body:
        return
    recipient = User.query.filter_by(username=to).first()
    sender = User.query.filter_by(username=from_user).first()
    if not recipient or not sender:
        return
    dm = DirectMessage(sender_id=sender.id, recipient_id=recipient.id, body=body)
    db.session.add(dm)
    db.session.commit()
    # emit to recipient personal room and sender
    try:
        emit('private_message', {'from': from_user, 'body': body, 'created_at': dm.created_at.isoformat()}, room=f'user:{to}')
        emit('private_message', {'to': to, 'body': body, 'created_at': dm.created_at.isoformat()}, room=f'user:{from_user}')
    except Exception:
        current_app.logger.debug('Could not emit private_message to rooms user:%s or user:%s', to, from_user)

@socketio.on('join_group')
def handle_join_group(data):
    group_id = data.get('group_id')
    username = data.get('username')
    if not group_id or not username:
        return
    room = f'group:{group_id}'
    join_room(room)
    emit('status', {'msg': f'{username} a rejoint le groupe {group_id}'}, room=room)

@socketio.on('group_message')
def handle_group_message(data):
    group_id = data.get('group_id')
    username = data.get('username')
    body = data.get('body')
    if not group_id or not username or not body:
        return
    try:
        user = User.query.filter_by(username=username).first()
        user_id = user.id if user else None
        gm = GroupMessage(group_id=group_id, user_id=user_id, body=body)
        db.session.add(gm)
        db.session.commit()
        emit('group_message', {'group_id': group_id, 'username': username, 'body': body, 'created_at': gm.created_at.isoformat()}, room=f'group:{group_id}')
    except Exception:
        current_app.logger.exception('Failed to store/emit group message')
