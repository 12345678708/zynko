import os
import sqlite3
import uuid
from flask import Flask, render_template, request, redirect, session

app = Flask(__name__)
app.secret_key = "zynko_secret"

UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

DB = "zynko.db"


def db():
    return sqlite3.connect(DB)


def init_db():
    conn = db()
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY,
        username TEXT UNIQUE,
        email TEXT,
        password TEXT,
        avatar TEXT,
        friend_code TEXT UNIQUE
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS friends(
        user TEXT,
        friend TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS messages(
        sender TEXT,
        receiver TEXT,
        text TEXT,
        read INTEGER DEFAULT 0
    )
    """)

    conn.commit()
    conn.close()


init_db()


# ---------------- LOGIN ----------------

@app.route("/", methods=["GET","POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        conn = db()
        c = conn.cursor()

        user = c.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (username,password)
        ).fetchone()

        conn.close()

        if user:
            session["user"] = username
            return redirect("/chat")

    return render_template("login.html")


# ---------------- REGISTER ----------------

@app.route("/register", methods=["GET","POST"])
def register():

    if request.method == "POST":

        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]

        if len(username) > 20:
            return "Pseudo trop long"

        friend_code = str(uuid.uuid4())[:8]

        conn = db()
        c = conn.cursor()

        try:

            c.execute("""
            INSERT INTO users(username,email,password,avatar,friend_code)
            VALUES(?,?,?,?,?)
            """,(username,email,password,"avatar.png",friend_code))

            conn.commit()

        except:
            conn.close()
            return "Pseudo déjà utilisé"

        conn.close()

        return redirect("/")

    return render_template("register.html")


# ---------------- CHAT ----------------

@app.route("/chat")
def chat():

    if "user" not in session:
        return redirect("/")

    username = session["user"]

    conn = db()
    c = conn.cursor()

    friends = c.execute("""
    SELECT friend FROM friends WHERE user=?
    """,(username,)).fetchall()

    unread = c.execute("""
    SELECT sender,COUNT(*) FROM messages
    WHERE receiver=? AND read=0
    GROUP BY sender
    """,(username,)).fetchall()

    conn.close()

    return render_template(
        "chat.html",
        username=username,
        friends=friends,
        unread=dict(unread)
    )


# ---------------- ADD FRIEND ----------------

@app.route("/add_friend", methods=["POST"])
def add_friend():

    if "user" not in session:
        return redirect("/")

    code = request.form["code"]
    username = session["user"]

    conn = db()
    c = conn.cursor()

    friend = c.execute(
        "SELECT username FROM users WHERE friend_code=?",
        (code,)
    ).fetchone()

    if friend:

        c.execute(
            "INSERT INTO friends(user,friend) VALUES(?,?)",
            (username,friend[0])
        )

        conn.commit()

    conn.close()

    return redirect("/chat")


# ---------------- UPLOAD AVATAR ----------------

@app.route("/avatar", methods=["POST"])
def avatar():

    if "user" not in session:
        return redirect("/")

    file = request.files["avatar"]

    filename = file.filename

    path = os.path.join(UPLOAD_FOLDER, filename)

    file.save(path)

    conn = db()
    c = conn.cursor()

    c.execute(
        "UPDATE users SET avatar=? WHERE username=?",
        (filename,session["user"])
    )

    conn.commit()
    conn.close()

    return redirect("/chat")


# ---------------- LOGOUT ----------------

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")
    

if __name__ == "__main__":
    app.run()
