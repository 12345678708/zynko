from flask import Flask, render_template, request, redirect, session
import sqlite3
import random
import string

app = Flask(__name__)
app.secret_key = "zynko_secret"

DATABASE = "zynko.db"


# -----------------------------
# DATABASE
# -----------------------------

def get_db():
    return sqlite3.connect(DATABASE)


def init_db():

    db = get_db()
    c = db.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        friend_code TEXT UNIQUE
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS messages(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender TEXT,
        receiver TEXT,
        message TEXT
    )
    """)

    db.commit()
    db.close()


init_db()


# -----------------------------
# GENERATE FRIEND CODE
# -----------------------------

def generate_code():

    return ''.join(
        random.choices(string.ascii_uppercase + string.digits, k=8)
    )


# -----------------------------
# LOGIN
# -----------------------------

@app.route("/", methods=["GET", "POST"])
@app.route("/login", methods=["GET", "POST"])

def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        db = get_db()
        c = db.cursor()

        user = c.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (username, password)
        ).fetchone()

        db.close()

        if user:

            session["user"] = username
            return redirect("/chat")

    return render_template("login.html")


# -----------------------------
# REGISTER
# -----------------------------

@app.route("/register", methods=["GET", "POST"])

def register():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        if len(username) > 12:
            return "Pseudo max 12 caractères"

        code = generate_code()

        db = get_db()
        c = db.cursor()

        try:

            c.execute(
                "INSERT INTO users(username,password,friend_code) VALUES(?,?,?)",
                (username, password, code)
            )

            db.commit()

        except:

            db.close()
            return "Pseudo déjà utilisé"

        db.close()

        return redirect("/login")

    return render_template("register.html")


# -----------------------------
# CHAT
# -----------------------------

@app.route("/chat", methods=["GET", "POST"])

def chat():

    if "user" not in session:
        return redirect("/login")

    username = session["user"]

    db = get_db()
    c = db.cursor()

    if request.method == "POST":

        receiver = request.form["receiver"]
        message = request.form["message"]

        if message.strip() != "":

            c.execute(
                "INSERT INTO messages(sender,receiver,message) VALUES(?,?,?)",
                (username, receiver, message)
            )

            db.commit()

    messages = c.execute(
        "SELECT * FROM messages WHERE sender=? OR receiver=?",
        (username, username)
    ).fetchall()

    code = c.execute(
        "SELECT friend_code FROM users WHERE username=?",
        (username,)
    ).fetchone()

    db.close()

    if code:
        code = code[0]
    else:
        code = "NONE"

    return render_template(
        "chat.html",
        username=username,
        messages=messages,
        code=code
    )


# -----------------------------
# LOGOUT
# -----------------------------

@app.route("/logout")

def logout():

    session.clear()

    return redirect("/login")


# -----------------------------
# START
# -----------------------------

if __name__ == "__main__":

    app.run(debug=True)
