from flask import Flask, render_template, request, redirect, session, send_from_directory
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "zynko_secret"

DATABASE="zynko.db"
UPLOAD_FOLDER="static/uploads"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def get_db():
    return sqlite3.connect(DATABASE)


def init_db():

    db=get_db()
    c=db.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS users(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    email TEXT,
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

    db.commit()
    db.close()

init_db()


# LOGIN

@app.route("/",methods=["GET","POST"])
@app.route("/login",methods=["GET","POST"])

def login():

    if request.method=="POST":

        username=request.form["username"]
        password=request.form["password"]

        db=get_db()
        c=db.cursor()

        user=c.execute(
        "SELECT * FROM users WHERE username=? AND password=?",
        (username,password)
        ).fetchone()

        if user:

            session["user"]=username

            c.execute("UPDATE users SET online=1 WHERE username=?", (username,))
            db.commit()

            return redirect("/friends")

        db.close()

    return render_template("login.html")


# REGISTER

@app.route("/register",methods=["GET","POST"])

def register():

    if request.method=="POST":

        username=request.form["username"]
        email=request.form["email"]
        password=request.form["password"]

        db=get_db()
        c=db.cursor()

        try:

            c.execute(
            "INSERT INTO users(username,email,password) VALUES(?,?,?)",
            (username,email,password)
            )

            db.commit()

        except:
            return "Utilisateur déjà utilisé"

        db.close()

        return redirect("/login")

    return render_template("register.html")


# FRIENDS

@app.route("/friends",methods=["GET","POST"])

def friends():

    if "user" not in session:
        return redirect("/login")

    username=session["user"]

    db=get_db()
    c=db.cursor()

    if request.method=="POST":

        friend=request.form["friend"]

        c.execute(
        "INSERT INTO friends(user,friend) VALUES(?,?)",
        (username,friend)
        )

        db.commit()

    friends=c.execute("""
    SELECT users.username, users.online
    FROM friends
    JOIN users ON users.username=friends.friend
    WHERE friends.user=?
    """,(username,)).fetchall()

    db.close()

    return render_template("friends.html",friends=friends)


# CHAT

@app.route("/chat",methods=["GET","POST"])

def chat():

    if "user" not in session:
        return redirect("/login")

    username=session["user"]
    receiver=request.args.get("user")

    db=get_db()
    c=db.cursor()

    if request.method=="POST":

        message=request.form.get("message")
        image=request.files.get("image")
        audio=request.files.get("audio")

        image_name=None
        audio_name=None

        if image and image.filename!="":
            image_name=image.filename
            image.save(os.path.join(UPLOAD_FOLDER,image_name))

        if audio and audio.filename!="":
            audio_name=audio.filename
            audio.save(os.path.join(UPLOAD_FOLDER,audio_name))

        c.execute("""
        INSERT INTO messages(sender,receiver,message,image,audio)
        VALUES(?,?,?,?,?)
        """,(username,receiver,message,image_name,audio_name))

        db.commit()

    messages=c.execute("""
    SELECT sender,message,image,audio FROM messages
    WHERE (sender=? AND receiver=?)
    OR (sender=? AND receiver=?)
    """,(username,receiver,receiver,username)).fetchall()

    db.close()

    return render_template("chat.html",
                           receiver=receiver,
                           username=username,
                           messages=messages)


@app.route("/logout")

def logout():

    if "user" in session:

        db=get_db()
        c=db.cursor()

        c.execute("UPDATE users SET online=0 WHERE username=?", (session["user"],))
        db.commit()
        db.close()

    session.clear()

    return redirect("/login")


if __name__=="__main__":
    app.run()
