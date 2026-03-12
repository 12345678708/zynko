from flask import Flask, render_template, request, redirect, session
from flask_socketio import SocketIO, emit
import sqlite3
import random
import string

app = Flask(__name__)
app.secret_key = "zynko_secret"

socketio = SocketIO(app)

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


# CHAT PAGE

@app.route("/chat")

def chat():

    if "user" not in session:
        return redirect("/login")

    username = session["user"]

    return render_template(
        "chat.html",
        username=username
    )


# SOCKET MESSAGE

@socketio.on("send_message")

def handle_message(data):

    sender = session["user"]
    receiver = data["receiver"]
    message = data["message"]

    db = get_db()
    c = db.cursor()

    c.execute(
        "INSERT INTO messages(sender,receiver,message) VALUES(?,?,?)",
        (sender,receiver,message)
    )

    db.commit()
    db.close()

    emit("receive_message", {
        "sender": sender,
        "message": message
    }, broadcast=True)


# LOGOUT

@app.route("/logout")

def logout():

    session.clear()
    return redirect("/login")


if __name__ == "__main__":
    socketio.run(app)
