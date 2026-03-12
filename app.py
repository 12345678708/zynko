from flask import Flask, render_template, request, redirect, session
import sqlite3

app = Flask(__name__)
app.secret_key = "zynko_secret"

DATABASE="zynko.db"


def get_db():
    return sqlite3.connect(DATABASE)


def init_db():

    db=get_db()
    c=db.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS users(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    email TEXT UNIQUE,
    password TEXT
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
    message TEXT
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

        db.close()

        if user:

            session["user"]=username
            return redirect("/chat")

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
            return "Utilisateur ou email déjà utilisé"

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

    friends=c.execute(
    "SELECT friend FROM friends WHERE user=?",
    (username,)
    ).fetchall()

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

        message=request.form["message"]

        c.execute(
        "INSERT INTO messages(sender,receiver,message) VALUES(?,?,?)",
        (username,receiver,message)
        )

        db.commit()

    messages=c.execute(
    """SELECT sender,message FROM messages
    WHERE (sender=? AND receiver=?)
    OR (sender=? AND receiver=?)
    """,
    (username,receiver,receiver,username)
    ).fetchall()

    db.close()

    return render_template(
    "chat.html",
    username=username,
    receiver=receiver,
    messages=messages
    )


@app.route("/logout")

def logout():

    session.clear()
    return redirect("/login")


if __name__=="__main__":
    app.run()
