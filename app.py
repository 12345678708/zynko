from flask import Flask, render_template, request, redirect, session, jsonify
import sqlite3
import random
import string
import os
import qrcode
from io import BytesIO
import base64
import secrets
import time
from datetime import datetime, timedelta
import unicodedata
import re
from collections import defaultdict, deque

app = Flask(__name__)
app.secret_key = "zynko_secret_key_super_secure_2026"

# =========================
# 🤖 IA DIORX
# =========================
NOM_IA = "DIORX"
brain = defaultdict(list)
context = deque(maxlen=50)
history = []

def clean(text):
    text = text.lower()
    text = ''.join(c for c in unicodedata.normalize('NFD', text)
                   if unicodedata.category(c) != 'Mn')
    text = re.sub(r'[^\w\s]', '', text)
    return text

def learn(sentence):
    words = sentence.split()
    if len(words) > 2:
        for i in range(len(words)-2):
            key = (words[i], words[i+1])
            brain[key].append(words[i+2])
    context.append(sentence)

def generate_response(max_words=15):
    if not brain:
        return "desoler je ne comprent pas encore"
    key = random.choice(list(brain.keys()))
    phrase = [key[0], key[1]]
    for _ in range(max_words):
        if key not in brain: break
        next_word = random.choice(brain[key])
        phrase.append(next_word)
        key = (key[1], next_word)
    return " ".join(phrase)

def emotion(msg):
    msg_clean = clean(msg)
    if any(w in msg_clean for w in ["triste", "fatigu", "marre", "deprim"]): return "sad"
    if any(w in msg_clean for w in ["super", "cool", "genial", "top", "heureux"]): return "happy"
    return "normal"

def reply(message):
    msg_clean = clean(message)
    learn(msg_clean)
    
    # Salutations
    if any(w in msg_clean for w in ["salut", "bonjour", "coucou"]):
        return "Salut ! Je suis DIORX, ton IA personnelle 😄"
    
    # Pierre-feuille-ciseaux
    if "pierre feuille ciseaux" in msg_clean or "pfc" in msg_clean:
        choix = ["pierre", "feuille", "ciseaux"]
        ia = random.choice(choix)
        return f"Je choisis {ia} ! 😎"
    
    # Heure
    if "heure" in msg_clean:
        return f"Il est {datetime.now().strftime('%H:%M')} 🕒"
    
    # Météo
    if "meteo" in msg_clean or "météo" in msg_clean:
        meteos = ["☀️ soleil", "🌧️ pluie", "⛅ nuages", "🌬️ vent"]
        return f"Aujourd'hui : {random.choice(meteos)}"
    
    # Conseils
    if "conseil" in msg_clean:
        tips = ["Respire 🙂", "Prends une pause ☕", "Reste positif 💪", "Bois de l'eau 💧"]
        return random.choice(tips)
    
    # Génération intelligente
    gen = generate_response()
    e = emotion(message)
    if e == "sad":
        return "Je comprends 😢 " + gen
    elif e == "happy":
        return "Génial 😄 " + gen
    else:
        return "Hmm 🤔 " + gen

# =========================
# 🔑 CODE AMI UNIQUE
# =========================
def generate_friend_code():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    while True:
        code = "ZYN-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        c.execute("SELECT * FROM users WHERE friend_code=?", (code,))
        if not c.fetchone():
            conn.close()
            return code

# =========================
# 📱 GENERATE QR CODE
# =========================
def generate_qr_code(friend_code):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(friend_code)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return f"data:image/png;base64,{img_str}"

# =========================
# 🧱 INIT DATABASE
# =========================
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
        email_verified INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS verification_codes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        code TEXT UNIQUE NOT NULL,
        expires_at TIMESTAMP NOT NULL,
        used INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS friends (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        friend_id INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(user_id, friend_id),
        FOREIGN KEY(user_id) REFERENCES users(id),
        FOREIGN KEY(friend_id) REFERENCES users(id)
    )
    """)

    conn.commit()
    conn.close()

init_db()

# =========================
# 🔐 HASH PASSWORD
# =========================
def hash_password(password):
    import hashlib
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password, hashed):
    return hash_password(password) == hashed

# =========================
# 📧 GENERATE VERIFICATION CODE
# =========================
def generate_verification_code(user_id):
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    
    code = ''.join(random.choices(string.digits, k=6))
    expires_at = datetime.now() + timedelta(hours=1)
    
    c.execute(
        "INSERT INTO verification_codes (user_id, code, expires_at) VALUES (?, ?, ?)",
        (user_id, code, expires_at)
    )
    conn.commit()
    conn.close()
    
    return code

# =========================
# 🏠 HOME
# =========================
@app.route("/")
def home():
    if "user_id" in session:
        return redirect("/dashboard")
    return render_template("index.html")

# =========================
# 🆕 REGISTER
# =========================
@app.route("/register", methods=["POST"])
def register():
    username = request.form.get("username", "").strip()
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")
    
    if len(username) < 3:
        return "Pseudo doit avoir au moins 3 caractères ❌"
    if len(password) < 6:
        return "Mot de passe doit avoir au moins 6 caractères ❌"
    if "@" not in email:
        return "Email invalide ❌"
    
    code = generate_friend_code()
    hashed_password = hash_password(password)

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    try:
        c.execute(
            "INSERT INTO users (username, email, password, friend_code) VALUES (?, ?, ?, ?)",
            (username, email, hashed_password, code)
        )
        conn.commit()
        user_id = c.lastrowid
        
        verification_code = generate_verification_code(user_id)
        print(f"Code de vérification pour {email}: {verification_code}")
        
    except Exception as e:
        conn.close()
        if "username" in str(e).lower():
            return "Pseudo déjà pris ❌"
        elif "email" in str(e).lower():
            return "Email déjà utilisé ❌"
        return f"Erreur: {str(e)} ❌"

    conn.close()
    return redirect(f"/verify-email/{user_id}")

# =========================
# 📧 VERIFY EMAIL PAGE
# =========================
@app.route("/verify-email/<int:user_id>")
def verify_email_page(user_id):
    return render_template("verify_email.html", user_id=user_id)

# =========================
# ✅ VERIFY CODE
# =========================
@app.route("/verify-code", methods=["POST"])
def verify_code():
    user_id = request.form.get("user_id")
    code = request.form.get("code", "").strip()
    
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
        return "Code invalide ou expiré ❌"
    
    c.execute("UPDATE verification_codes SET used=1 WHERE id=?", (verify_record[0],))
    c.execute("UPDATE users SET email_verified=1 WHERE id=?", (user_id,))
    conn.commit()
    conn.close()
    
    return redirect("/")

# =========================
# 🔐 LOGIN
# =========================
@app.route("/login", methods=["POST"])
def login():
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("SELECT id, password, email_verified FROM users WHERE username=?", (username,))
    user = c.fetchone()

    conn.close()

    if user and verify_password(password, user[1]):
        if not user[2]:
            return "Email non vérifié ❌ Vérifiez votre email!"
        session["user_id"] = user[0]
        return redirect("/dashboard")

    return "Login incorrect ❌"

# =========================
# 🤖 CHAT WITH DIORX
# =========================
@app.route("/chat")
def chat():
    return render_template("chat.html", name=NOM_IA, history=history)

@app.route("/api/chat", methods=["POST"])
def api_chat():
    message = request.json.get("message", "")
    if not message:
        return jsonify({"error": "Message vide"}), 400
    
    response = reply(message)
    emo = emotion(message)
    history.append((message, response, emo))
    
    return jsonify({
        "message": message,
        "response": response,
        "emotion": emo
    })

# =========================
# 📊 DASHBOARD
# =========================
@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect("/")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("SELECT username, friend_code, email FROM users WHERE id=?", (session["user_id"],))
    user = c.fetchone()

    if not user:
        conn.close()
        session.clear()
        return redirect("/")

    c.execute("""
    SELECT u.id, u.username
    FROM friends f
    JOIN users u ON u.id = f.friend_id
    WHERE f.user_id=?
    ORDER BY u.username ASC
    """, (session["user_id"],))

    friends = c.fetchall()
    qr_code = generate_qr_code(user[1])

    conn.close()

    return render_template("dashboard.html", user=user, friends=friends, qr_code=qr_code)

# =========================
# ➕ ADD FRIEND
# =========================
@app.route("/add_friend", methods=["POST"])
def add_friend():
    if "user_id" not in session:
        return redirect("/")

    code = request.form.get("code", "").upper().strip()
    
    if not code:
        return "Veuillez entrer un code ❌"

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("SELECT id, username FROM users WHERE friend_code=?", (code,))
    user = c.fetchone()

    if not user:
        conn.close()
        return "Code introuvable ❌"

    friend_id = user[0]
    user_id = session["user_id"]

    if user_id == friend_id:
        conn.close()
        return "Tu ne peux pas t'ajouter toi-même 🙅"

    c.execute("SELECT * FROM friends WHERE user_id=? AND friend_id=?", (user_id, friend_id))
    if c.fetchone():
        conn.close()
        return "Vous êtes déjà amis ✅"

    try:
        c.execute(
            "INSERT INTO friends (user_id, friend_id) VALUES (?, ?)",
            (user_id, friend_id)
        )
        c.execute(
            "INSERT OR IGNORE INTO friends (user_id, friend_id) VALUES (?, ?)",
            (friend_id, user_id)
        )
        conn.commit()
        conn.close()
        return redirect("/dashboard")
    except Exception as e:
        conn.close()
        return f"Erreur lors de l'ajout: {str(e)} ❌"

# =========================
# 🚪 LOGOUT
# =========================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=False)
