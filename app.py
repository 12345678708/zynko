from flask import Flask, render_template, request, redirect, session, jsonify
import sqlite3
import random
import string

app = Flask(__name__)
app.secret_key = "zynko_secret"

DATABASE = "zynko.db"


def get_db():
    return sqlite3.connect(DATABASE)


def init_db():

    db = get_db()
    c = db.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY,
        username TEXT UNIQUE,
        password TEXT,
        friend_code TEXT UNIQUE
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS friends(
        id INTEGER PRIMARY KEY,
        user TEXT,
        friend TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS messages(
        id INTEGER PRIMARY KEY,
        sender TEXT,
        receiver TEXT,
        message TEXT
    )
    """)

    db.commit()
    db.close()


init_db()


def generate_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))


# LOGIN

@app.route("/", methods=["GET","POST"])
@app.route("/login", methods=["GET","POST"])

def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        db = get_db()
        c = db.cursor()

        user = c.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (username,password)
        ).fetchone()

        db.close()

        if user:

            session["user"] = username
            return redirect("/chat")

    return render_template("login.html")


# REGISTER

@app.route("/register", methods=["GET","POST"])

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
                (username,password,code)
            )

            db.commit()

        except:
            return "Pseudo déjà utilisé"

        db.close()

        return redirect("/login")

    return render_template("register.html")


# PAGE CHAT

@app.route("/chat")

def chat():

    if "user" not in session:
        return redirect("/login")

    username = session["user"]

    db = get_db()
    c = db.cursor()

    friends = c.execute(
        "SELECT friend FROM friends WHERE user=?",
        (username,)
    ).fetchall()

    code = c.execute(
        "SELECT friend_code FROM users WHERE username=?",
        (username,)
    ).fetchone()

    db.close()

    if code:
        code = code[0]

    return render_template(
        "chat.html",
        username=username,
        friends=friends,
        code=code
    )


# ENVOYER MESSAGE

@app.route("/send", methods=["POST"])

def send():

    sender = session["user"]
    receiver = request.form["receiver"]
    message = request.form["message"]

    db = get_db()
    c = db.cursor()

    c.execute(
        "INSERT INTO messages(sender,receiver,message) VALUES(?,?,?)",
        (sender,receiver,message)
    )

    db.commit()
    db.close()

    return "ok"


# RECEVOIR MESSAGES

@app.route("/messages/<friend>")

def messages(friend):

    user = session["user"]

    db = get_db()
    c = db.cursor()

    msgs = c.execute(
        """
        SELECT sender,message FROM messages
        WHERE (sender=? AND receiver=?)
        OR (sender=? AND receiver=?)
        """,
        (user,friend,friend,user)
    ).fetchall()

    db.close()

    return jsonify(msgs)


# AJOUT AMI

@app.route("/add_friend", methods=["POST"])

def add_friend():

    code = request.form["code"]
    user = session["user"]

    db = get_db()
    c = db.cursor()

    friend = c.execute(
        "SELECT username FROM users WHERE friend_code=?",
        (code,)
    ).fetchone()

    if friend:

        friend = friend[0]

        c.execute(
            "INSERT INTO friends(user,friend) VALUES(?,?)",
            (user,friend)
        )

        db.commit()

    db.close()

    return redirect("/chat")


# LOGOUT

@app.route("/logout")

def logout():

    session.clear()
    return redirect("/login")


if __name__ == "__main__":
    app.run()
