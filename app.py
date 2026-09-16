# Version Zynko Secure - tout en 1 fichier
import os, sqlite3, random, smtplib, re
from email.mime.text import MIMEText
from datetime import datetime, timedelta
from flask import Flask, request, session, jsonify, render_template_string, g
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-moi-en-prod-diorx")
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Lax')
DB = "zynko.db"

# anti-spam simple en mémoire
RATE = {} # ip -> [timestamps]

def check_rate(ip, limit=5, per=60):
    now=datetime.now()
    t=RATE.get(ip, [])
    t=[x for x in t if now-x < timedelta(seconds=per)]
    if len(t)>=limit: return False
    t.append(now); RATE[ip]=t; return True

def get_db():
    db=getattr(g,'_db',None)
    if db is None:
        db=g._db=sqlite3.connect(DB); db.row_factory=sqlite3.Row
    return db

def init_db():
    with sqlite3.connect(DB) as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, username TEXT UNIQUE, email TEXT UNIQUE, password TEXT, verified INTEGER DEFAULT 0, code TEXT, code_exp TEXT, created TEXT);
        CREATE TABLE IF NOT EXISTS posts(id INTEGER PRIMARY KEY, user_id INTEGER, content TEXT, created TEXT);
        CREATE TABLE IF NOT EXISTS messages(id INTEGER PRIMARY KEY, user_id INTEGER, content TEXT, created TEXT);
        CREATE TABLE IF NOT EXISTS follows(id INTEGER PRIMARY KEY, follower_id INTEGER, followed_id INTEGER, UNIQUE(follower_id,followed_id));
        """)
init_db()
@app.teardown_appcontext
def close_db(e): db=getattr(g,'_db',None);
                 if db: db.close()

def is_valid_email(e): return re.match(r"^[^@]+@[^@]+\.[^@]+$", e)
def is_valid_username(u): return re.match(r"^[a-zA-Z0-9_]{3,20}$", u)

def send_real_email(to_email, code):
    USER=os.environ.get("EMAIL_USER"); PASS=os.environ.get("EMAIL_PASS")
    if not USER or not PASS:
        print(f"[TEST MODE] Code pour {to_email} : {code}")
        return False, code
    try:
        msg=MIMEText(f"Zynko - Ton code de vérification : {code}\nExpire dans 10 minutes.\nSi ce n'est pas toi, ignore ce mail.")
        msg['Subject']=f"Zynko - Code {code}"; msg['From']=USER; msg['To']=to_email
        with smtplib.SMTP_SSL("smtp.gmail.com",465) as s:
            s.login(USER,PASS); s.send_message(msg)
        return True, None
    except Exception as e:
        print("Email fail", e); return False, code

#... [le reste du HTML/Routes identique à avant mais avec checks]...
