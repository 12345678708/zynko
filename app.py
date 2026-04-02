from flask import Flask, render_template, request, send_from_directory
from flask_socketio import SocketIO, emit
import os

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'

socketio = SocketIO(app, cors_allowed_origins="*")

users = {}

# =====================
# ROUTES
# =====================
@app.route('/')
def index():
    return render_template("index.html")

@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['file']
    path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(path)
    return {"url": "/uploads/" + file.filename}

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# =====================
# SOCKET
# =====================
@socketio.on('connect')
def connect():
    print("User connected")

@socketio.on('join')
def join(data):
    users[request.sid] = data['username']
    emit('user_count', len(users), broadcast=True)

@socketio.on('message')
def message(data):
    emit('message', data, broadcast=True)

@socketio.on('typing')
def typing(data):
    emit('typing', data, broadcast=True)

@socketio.on('disconnect')
def disconnect():
    users.pop(request.sid, None)
    emit('user_count', len(users), broadcast=True)

# =====================
# LANCEMENT
# =====================
if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000)
