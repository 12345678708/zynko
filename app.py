from flask import Flask, render_template, request, redirect, session
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "zynko_secret_key"

DATABASE = "zynko.db"
UPLOAD_FOLDER = "static/uploads"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def db():
    return sqlite3.connect(DATABASE)


def init_db():
    conn = db()
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        email TEXT UNIQUE,
        password TEXT,
        online INTEGER DEFAULT 0
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS friends(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user TEXT,
        friend TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS messages(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender TEXT,
        receiver TEXT,
        message TEXT,
        image TEXT,
        audio TEXT
    )
    """)

    conn.commit()
    conn.close()


init_db()

# ---------------- LOGIN ----------------

@app.route("/", methods=["GET","POST"])
@app.route("/login", methods=["GET","POST"])

def login():

    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")

        conn = db()
        c = conn.cursor()

        user = c.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (username,password)
        ).fetchone()

        if user:

            session["user"] = username

            c.execute(
                "UPDATE users SET online=1 WHERE username=?",
                (username,)
            )

            conn.commit()
            conn.close()

            return redirect("/friends")

        conn.close()

    return render_template("login.html")


# ---------------- REGISTER ----------------

@app.route("/register", methods=["GET","POST"])

def register():

    if request.method == "POST":

        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")

        if len(username) > 20:
            return "Pseudo trop long (20 max)"

        conn = db()
        c = conn.cursor()

        try:

            c.execute(
                "INSERT INTO users(username,email,password) VALUES(?,?,?)",
                (username,email,password)
            )

            conn.commit()

        except:
            conn.close()
            return "Pseudo ou email déjà utilisé"

        conn.close()

        return redirect("/login")

    return render_template("register.html")


# ---------------- FRIENDS ----------------

@app.route("/friends", methods=["GET","POST"])

def friends():

    if "user" not in session:
        return redirect("/login")

    username = session["user"]

    conn = db()
    c = conn.cursor()

    if request.method == "POST":

        friend = request.form.get("friend")

        if friend:

            c.execute(
                "INSERT INTO friends(user,friend) VALUES(?,?)",
                (username,friend)
            )

            conn.commit()

    friends = c.execute("""
        SELECT users.username, users.online
        FROM friends
        JOIN users ON users.username=friends.friend
        WHERE friends.user=?
    """,(username,)).fetchall()

    conn.close()

    return render_template("friends.html",
                           friends=friends,
                           username=username)


# ---------------- CHAT ----------------

@app.route("/chat", methods=["GET","POST"])

def chat():

    if "user" not in session:
        return redirect("/login")

    username = session["user"]
    receiver = request.args.get("user")

    conn = db()
    c = conn.cursor()

    if request.method == "POST":

        message = request.form.get("message")
        image = request.files.get("image")
        audio = request.files.get("audio")

        image_name = None
        audio_name = None

        if image and image.filename != "":
            image_name = image.filename
            image.save(os.path.join(UPLOAD_FOLDER,image_name))

        if audio and audio.filename != "":
            audio_name = audio.filename
            audio.save(os.path.join(UPLOAD_FOLDER,audio_name))

        c.execute("""
        INSERT INTO messages(sender,receiver,message,image,audio)
        VALUES(?,?,?,?,?)
        """,(username,receiver,message,image_name,audio_name))

        conn.commit()

    messages = c.execute("""
    SELECT sender,message,image,audio
    FROM messages
    WHERE (sender=? AND receiver=?)
    OR (sender=? AND receiver=?)
    """,(username,receiver,receiver,username)).fetchall()

    conn.close()

    return render_template("chat.html",
                           messages=messages,
                           receiver=receiver,
                           username=username)


# ---------------- LOGOUT ----------------

@app.route("/logout")

def logout():

    if "user" in session:

        conn = db()
        c = conn.cursor()

        c.execute(
            "UPDATE users SET online=0 WHERE username=?",
            (session["user"],)
        )

        conn.commit()
        conn.close()

    session.clear()

    return redirect("/login")


# ---------------- RUN ----------------

if __name__ == "__main__":
    app.run()
