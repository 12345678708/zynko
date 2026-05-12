from flask import Flask, render_template, request, redirect, session, jsonify
import sqlite3
import random
import string
import os
import qrcode
from io import BytesIO
import base64

app = Flask(__name__)
app.secret_key = "zynko_secret_key"

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
    """Génère un code QR pour le code ami"""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(friend_code)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convertir en base64
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
        username TEXT UNIQUE,
        password TEXT,
        friend_code TEXT UNIQUE
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS friends (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        friend_id INTEGER
    )
    """)

    conn.commit()
    conn.close()

init_db()


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
    username = request.form["username"]
    password = request.form["password"]
    code = generate_friend_code()

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    try:
        c.execute(
            "INSERT INTO users (username, password, friend_code) VALUES (?, ?, ?)",
            (username, password, code)
        )
        conn.commit()
    except:
        return "Utilisateur déjà existant ❌"

    conn.close()
    return redirect("/")


# =========================
# 🔐 LOGIN
# =========================
@app.route("/login", methods=["POST"])
def login():
    username = request.form["username"]
    password = request.form["password"]

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("SELECT id FROM users WHERE username=? AND password=?", (username, password))
    user = c.fetchone()

    conn.close()

    if user:
        session["user_id"] = user[0]
        return redirect("/dashboard")

    return "Login incorrect ❌"


# =========================
# 📊 DASHBOARD
# =========================
@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect("/")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("SELECT username, friend_code FROM users WHERE id=?", (session["user_id"],))
    user = c.fetchone()

    c.execute("""
    SELECT u.username
    FROM friends f
    JOIN users u ON u.id = f.friend_id
    WHERE f.user_id=?
    """, (session["user_id"],))

    friends = c.fetchall()

    # Générer le QR code
    qr_code = generate_qr_code(user[1])

    conn.close()

    return render_template("dashboard.html", user=user, friends=friends, qr_code=qr_code)


# =========================
# 📱 API QR CODE
# =========================
@app.route("/api/qr/<friend_code>")
def get_qr_code(friend_code):
    """Endpoint pour obtenir le QR code en JSON"""
    try:
        qr_code = generate_qr_code(friend_code)
        return jsonify({"success": True, "qr_code": qr_code})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


# =========================
# ➕ ADD FRIEND
# =========================
@app.route("/add_friend", methods=["POST"])
def add_friend():
    if "user_id" not in session:
        return redirect("/")

    code = request.form["code"].upper().strip()

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("SELECT id FROM users WHERE friend_code=?", (code,))
    user = c.fetchone()

    if not user:
        conn.close()
        return "Code introuvable ❌"

    friend_id = user[0]
    user_id = session["user_id"]

    # Vérifier que l'utilisateur n'ajoute pas lui-même
    if user_id == friend_id:
        conn.close()
        return "Tu ne peux pas t'ajouter toi-même 🙅"

    # Vérifier si déjà amis
    c.execute("SELECT * FROM friends WHERE user_id=? AND friend_id=?", (user_id, friend_id))
    if c.fetchone():
        conn.close()
        return "Vous êtes déjà amis ✅"

    c.execute("INSERT INTO friends (user_id, friend_id) VALUES (?, ?)", (user_id, friend_id))
    conn.commit()
    conn.close()

    return redirect("/dashboard")


# =========================
# 🚪 LOGOUT
# =========================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


if __name__ == "__main__":
    # Production: gunicorn launches this, don't use app.run()
    # Local dev: python app.py works fine
    app.run(debug=False)
