from flask import Flask, render_template, request, redirect, session, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room
import sqlite3
import random
import string
import hashlib
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import threading
import time

load_dotenv()

app = Flask(__name__)
app.secret_key = "zynko_secret_key_2026_ultra_secure_v2"
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# =====================
# DATABASE INIT
# =====================
def init_db():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    
    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        friend_code TEXT UNIQUE NOT NULL,
        avatar_color TEXT DEFAULT '#667eea',
        bio TEXT DEFAULT '',
        email_verified INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    c.execute("""
    CREATE TABLE IF NOT EXISTS friends (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        friend_id INTEGER NOT NULL,
        status TEXT DEFAULT 'friend',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(user_id, friend_id),
        FOREIGN KEY(user_id) REFERENCES users(id),
        FOREIGN KEY(friend_id) REFERENCES users(id)
    )
    """)
    
    c.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender_id INTEGER NOT NULL,
        receiver_id INTEGER NOT NULL,
        message TEXT NOT NULL,
        read_status INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(sender_id) REFERENCES users(id),
        FOREIGN KEY(receiver_id) REFERENCES users(id)
    )
    """)
    
    c.execute("""
    CREATE TABLE IF NOT EXISTS verification_codes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        code TEXT UNIQUE NOT NULL,
        expires_at TIMESTAMP NOT NULL,
        used INTEGER DEFAULT 0,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    """)
    
    conn.commit()
    conn.close()

init_db()

# =====================
# UTILS
# =====================
def generate_code():
    while True:
        code = "ZYN-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE friend_code=?", (code,))
        if not c.fetchone():
            conn.close()
            return code
        conn.close()

def generate_verification_code(user_id):
    code = ''.join(random.choices(string.digits, k=6))
    expires_at = datetime.now() + timedelta(hours=1)
    
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute(
        "INSERT INTO verification_codes (user_id, code, expires_at) VALUES (?, ?, ?)",
        (user_id, code, expires_at)
    )
    conn.commit()
    conn.close()
    return code

def hash_pwd(pwd):
    return hashlib.sha256(pwd.encode()).hexdigest()

def verify_pwd(pwd, hashed):
    return hash_pwd(pwd) == hashed

def get_random_color():
    colors = ['#667eea', '#764ba2', '#f093fb', '#4facfe', '#43e97b', '#fa709a', '#feca57', '#00d4ff']
    return random.choice(colors)

# Keep-Alive pour Render
def keep_alive():
    while True:
        try:
            time.sleep(840)  # 14 minutes
            print("[KEEP-ALIVE] System alive")
        except Exception as e:
            print(f"Keep-alive error: {e}")

threading.Thread(target=keep_alive, daemon=True).start()

# =====================
# HOME
# =====================
@app.route("/")
def home():
    if "user_id" in session:
        return redirect("/dashboard")
    return render_template("index.html")

# =====================
# REGISTER
# =====================
@app.route("/register", methods=["POST"])
def register():
    username = request.form.get("username", "").strip()
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")
    
    if len(username) < 3:
        return "Erreur: Username min 3 chars", 400
    if len(password) < 6:
        return "Erreur: Password min 6 chars", 400
    if "@" not in email:
        return "Email invalide", 400
    
    code = generate_code()
    hashed = hash_pwd(password)
    avatar_color = get_random_color()
    
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    
    try:
        c.execute(
            "INSERT INTO users (username, email, password, friend_code, avatar_color) VALUES (?, ?, ?, ?, ?)",
            (username, email, hashed, code, avatar_color)
        )
        conn.commit()
        user_id = c.lastrowid
        conn.close()
        
        verification_code = generate_verification_code(user_id)
        print(f"[VERIFY] Code pour {email}: {verification_code}")
        
        return redirect(f"/verify-email?user_id={user_id}")
    except Exception as e:
        conn.close()
        if "username" in str(e).lower():
            return "Username déjà pris", 400
        elif "email" in str(e).lower():
            return "Email déjà utilisé", 400
        return f"Erreur: {str(e)}", 500

# =====================
# VERIFY EMAIL
# =====================
@app.route("/verify-email")
def verify_email_page():
    user_id = request.args.get('user_id')
    
    # Récupérer le code pour l'afficher
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute(
        "SELECT code FROM verification_codes WHERE user_id=? AND used=0 ORDER BY expires_at DESC LIMIT 1",
        (user_id,)
    )
    result = c.fetchone()
    conn.close()
    
    verification_code = result[0] if result else "000000"
    
    return render_template("verify_email.html", user_id=user_id, verification_code=verification_code)

@app.route("/verify-code", methods=["POST"])
def verify_code():
    user_id = request.form.get("user_id")
    code = request.form.get("code", "").strip()
    
    if not user_id or not code:
        return "Données manquantes", 400
    
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    
    c.execute(
        """SELECT id FROM verification_codes 
           WHERE user_id=? AND code=? AND used=0 AND expires_at > datetime('now')""",
        (user_id, code)
    )
    verify_record = c.fetchone()
    
    if not verify_record:
        conn.close()
        return "Code invalide ou expiré", 400
    
    c.execute("UPDATE verification_codes SET used=1 WHERE id=?", (verify_record[0],))
    c.execute("UPDATE users SET email_verified=1 WHERE id=?", (user_id,))
    conn.commit()
    conn.close()
    
    return redirect("/?verified=success")

# =====================
# LOGIN
# =====================
@app.route("/login", methods=["POST"])
def login():
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    
    if not username or not password:
        return "Remplissez tous les champs", 400
    
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT id, password, email_verified FROM users WHERE username=?", (username,))
    user = c.fetchone()
    conn.close()
    
    if user and verify_pwd(password, user[1]):
        if not user[2]:
            return "Email non vérifié. Vérifiez votre email!", 403
        session["user_id"] = user[0]
        return redirect("/dashboard")
    
    return "Login incorrect", 401

# =====================
# DASHBOARD
# =====================
@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect("/")
    
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    
    c.execute("SELECT username, friend_code, email, avatar_color, bio FROM users WHERE id=?", (session["user_id"],))
    user = c.fetchone()
    
    if not user:
        conn.close()
        session.clear()
        return redirect("/")
    
    c.execute("""
    SELECT u.id, u.username, u.avatar_color FROM friends f
    JOIN users u ON u.id = f.friend_id
    WHERE f.user_id=?
    ORDER BY u.username ASC
    """, (session["user_id"],))
    
    friends = c.fetchall()
    conn.close()
    
    return render_template("dashboard.html", user=user, friends=friends, user_id=session["user_id"])

# =====================
# ADD FRIEND
# =====================
@app.route("/add_friend", methods=["POST"])
def add_friend():
    if "user_id" not in session:
        return redirect("/")
    
    code = request.form.get("code", "").upper().strip()
    
    if not code:
        return "Code vide", 400
    
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    
    c.execute("SELECT id, username FROM users WHERE friend_code=?", (code,))
    friend = c.fetchone()
    
    if not friend:
        conn.close()
        return "Code non trouvé", 404
    
    friend_id = friend[0]
    user_id = session["user_id"]
    
    c.execute("SELECT * FROM friends WHERE user_id=? AND friend_id=?", (user_id, friend_id))
    if c.fetchone():
        conn.close()
        return "Déjà dans vos amis", 400
    
    try:
        c.execute("INSERT INTO friends (user_id, friend_id) VALUES (?, ?)", (user_id, friend_id))
        if user_id != friend_id:
            c.execute("INSERT OR IGNORE INTO friends (user_id, friend_id) VALUES (?, ?)", (friend_id, user_id))
        conn.commit()
        conn.close()
        return redirect("/dashboard")
    except Exception as e:
        conn.close()
        return f"Erreur: {str(e)}", 500

# =====================
# PROFILE
# =====================
@app.route("/api/profile/<int:user_id>")
def get_profile(user_id):
    if "user_id" not in session:
        return jsonify({"error": "Non authentifié"}), 401
    
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT username, bio, avatar_color, created_at FROM users WHERE id=?", (user_id,))
    user = c.fetchone()
    conn.close()
    
    if not user:
        return jsonify({"error": "Utilisateur non trouvé"}), 404
    
    return jsonify({"username": user[0], "bio": user[1], "avatar_color": user[2], "created_at": user[3]})

@app.route("/api/update-bio", methods=["POST"])
def update_bio():
    if "user_id" not in session:
        return jsonify({"error": "Non authentifié"}), 401
    
    bio = request.json.get("bio", "")[:200]
    
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("UPDATE users SET bio=? WHERE id=?", (bio, session["user_id"]))
    conn.commit()
    conn.close()
    
    return jsonify({"success": True})

# =====================
# MESSAGES
# =====================
@app.route("/api/messages/<int:friend_id>")
def get_messages(friend_id):
    if "user_id" not in session:
        return jsonify({"error": "Non authentifié"}), 401
    
    user_id = session["user_id"]
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    
    c.execute("""
    SELECT id, sender_id, message, created_at FROM messages
    WHERE (sender_id=? AND receiver_id=?) OR (sender_id=? AND receiver_id=?)
    ORDER BY created_at ASC
    LIMIT 100
    """, (user_id, friend_id, friend_id, user_id))
    
    messages = c.fetchall()
    conn.close()
    
    return jsonify({"messages": [{"id": m[0], "sender_id": m[1], "message": m[2], "created_at": m[3], "is_mine": m[1] == user_id} for m in messages]})

@app.route("/api/send-message", methods=["POST"])
def send_message():
    if "user_id" not in session:
        return jsonify({"error": "Non authentifié"}), 401
    
    user_id = session["user_id"]
    receiver_id = request.json.get("receiver_id")
    message = request.json.get("message", "").strip()
    
    if not message or not receiver_id:
        return jsonify({"error": "Données manquantes"}), 400
    if len(message) > 1000:
        return jsonify({"error": "Message trop long"}), 400
    
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("INSERT INTO messages (sender_id, receiver_id, message) VALUES (?, ?, ?)", (user_id, receiver_id, message))
    conn.commit()
    msg_id = c.lastrowid
    conn.close()
    
    socketio.emit('new_message', {'sender_id': user_id, 'receiver_id': receiver_id, 'message': message, 'id': msg_id}, room=f"user_{receiver_id}")
    
    return jsonify({"success": True, "id": msg_id})

# =====================
# SOCKETIO
# =====================
@socketio.on('connect')
def handle_connect():
    if 'user_id' in session:
        join_room(f"user_{session['user_id']}")
        emit('connected', {'data': 'Connecté'})

@socketio.on('call_user')
def handle_call(data):
    caller_id = session.get('user_id')
    receiver_id = data.get('receiver_id')
    call_type = data.get('call_type')
    
    if not caller_id or not receiver_id:
        return
    
    room_id = f"call_{min(caller_id, receiver_id)}_{max(caller_id, receiver_id)}_{int(time.time())}"
    socketio.emit('incoming_call', {'caller_id': caller_id, 'call_type': call_type, 'room_id': room_id}, room=f"user_{receiver_id}")

# =====================
# LOGOUT
# =====================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    socketio.run(app, host='0.0.0.0', port=10000, debug=False, allow_unsafe_werkzeug=True)
