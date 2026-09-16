import os, sqlite3, random, smtplib, hashlib
from email.mime.text import MIMEText
from datetime import datetime
from flask import Flask, request, session, jsonify, render_template_string, g
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "zynko-secret-2026")
DB = "zynko.db"

# --- DB ---
def get_db():
    db = getattr(g, '_db', None)
    if db is None:
        db = g._db = sqlite3.connect(DB)
        db.row_factory = sqlite3.Row
    return db

def init_db():
    with sqlite3.connect(DB) as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, username TEXT UNIQUE, email TEXT UNIQUE, password TEXT, verified INTEGER DEFAULT 0, code TEXT, created TEXT);
        CREATE TABLE IF NOT EXISTS posts(id INTEGER PRIMARY KEY, user_id INTEGER, content TEXT, image TEXT, created TEXT);
        CREATE TABLE IF NOT EXISTS follows(id INTEGER PRIMARY KEY, follower_id INTEGER, followed_id INTEGER, UNIQUE(follower_id,followed_id));
        CREATE TABLE IF NOT EXISTS messages(id INTEGER PRIMARY KEY, user_id INTEGER, content TEXT, created TEXT);
        """)
init_db()

@app.teardown_appcontext
def close_db(e):
    db=getattr(g,'_db',None)
    if db: db.close()

# --- EMAIL REEL ---
def send_real_email(to_email, code):
    EMAIL_USER = os.environ.get("EMAIL_USER") # ton gmail
    EMAIL_PASS = os.environ.get("EMAIL_PASS") # mot de passe d'application gmail
    if not EMAIL_USER or not EMAIL_PASS:
        print(f"[ZYNKO] CODE POUR {to_email} : {code} -> Mets EMAIL_USER/EMAIL_PASS sur Render pour un vrai email")
        return False, code # on renvoie le code pour que tu puisses tester
    try:
        msg = MIMEText(f"Ton code Zynko est : {code}\nIl expire dans 10 minutes.\n\nC'est Karen ✨")
        msg['Subject'] = f"Zynko - Ton code : {code}"
        msg['From'] = EMAIL_USER
        msg['To'] = to_email
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
            s.login(EMAIL_USER, EMAIL_PASS)
            s.send_message(msg)
        return True, None
    except Exception as e:
        print("Email error", e)
        return False, code

# --- PAGES ---
AUTH_HTML = """
<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Zynko - Connexion</title>
<style>
:root{--bg:#07050e;--card:#151122;--line:#241f3a;--grad:linear-gradient(135deg,#7C3AED,#EC4899,#EF4444)}
*{box-sizing:border-box;margin:0;padding:0;font-family:Inter,system-ui}
body{background:radial-gradient(800px at 30% -10%,#7C3AED33,transparent),radial-gradient(800px at 90% 10%,#EC489933,transparent),var(--bg);color:#fff;min-height:100dvh;display:grid;place-items:center}
.box{width:100%;max-width:400px;background:var(--card);border:1px solid var(--line);border-radius:20px;padding:24px}
.logo{font-weight:900;font-size:32px;background:var(--grad);-webkit-background-clip:text;-webkit-text-fill-color:transparent;text-align:center;margin-bottom:8px}
.tabs{display:flex;background:#0e0b18;border-radius:12px;padding:4px;margin:16px 0}
.tab{flex:1;padding:10px;text-align:center;border-radius:8px;cursor:pointer;color:#8f85b0;font-weight:700}
.tab.on{background:#fff;color:#000}
input{width:100%;background:#1d1930;border:1px solid var(--line);color:#fff;padding:12px 14px;border-radius:12px;margin:6px 0}
button{width:100%;background:var(--grad);border:0;color:#fff;padding:12px;border-radius:12px;font-weight:800;margin-top:10px;cursor:pointer}
small{color:#8f85b0;display:block;text-align:center;margin-top:12px}
#msg{padding:10px;border-radius:10px;margin:8px 0;display:none;font-size:13px}
</style></head><body>
<div class="box">
<div class="logo">Zynko</div><small>WhatsApp x Discord x Instagram — mais vrai.</small>
<div class="tabs"><div id="t1" class="tab on" onclick="sw(1)">Connexion</div><div id="t2" class="tab" onclick="sw(2)">Créer compte</div></div>
<div id="msg"></div>
<div id="login">
<input id="l_email" placeholder="Email"><input id="l_pass" type="password" placeholder="Mot de passe">
<button onclick="login()">Se connecter</button>
</div>
<div id="register" style="display:none">
<input id="r_user" placeholder="Pseudo"><input id="r_email" placeholder="Email"><input id="r_pass" type="password" placeholder="Mot de passe">
<button onclick="reg()">Créer + envoyer code</button>
</div>
<div id="verify" style="display:none">
<p style="font-size:14px;margin:10px 0">Code reçu par email (6 chiffres)</p>
<input id="v_code" placeholder="123456"><input id="v_email" type="hidden">
<button onclick="verify()">Vérifier</button>
<div id="code_debug" style="font-size:11px;color:#8f85b0;margin-top:8px"></div>
</div>
</div>
<script>
function sw(n){
document.getElementById('t1').classList.toggle('on',n==1);
document.getElementById('t2').classList.toggle('on',n==2);
document.getElementById('login').style.display=n==1?'block':'none';
document.getElementById('register').style.display=n==2?'block':'none';
}
function show(m,ok){let e=document.getElementById('msg');e.style.display='block';e.textContent=m;e.style.background=ok?'#1a3d2a':'#3d1a1a'}
async function reg(){
let r=await fetch('/api/register',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({username:r_user.value,email:r_email.value,password:r_pass.value})});
let j=await r.json(); show(j.msg, j.ok);
if(j.ok){ document.getElementById('register').style.display='none'; document.getElementById('login').style.display='none'; document.getElementById('verify').style.display='block'; document.getElementById('v_email').value=r_email.value;
if(j.debug_code) document.getElementById('code_debug').innerText='TEST (car email non configuré) -> code: '+j.debug_code; }
}
async function verify(){
let r=await fetch('/api/verify',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email:document.getElementById('v_email').value,code:v_code.value})});
let j=await r.json(); show(j.msg, j.ok); if(j.ok) location.href='/';
}
async function login(){
let r=await fetch('/api/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email:l_email.value,password:l_pass.value})});
let j=await r.json(); show(j.msg, j.ok); if(j.ok) location.href='/';
}
</script></body></html>
"""

SOCIAL_HTML = """
<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Zynko</title>
<style>
:root{--bg:#08060e;--card:#13101c;--card2:#1c1730;--line:#221e36;--text:#f1efff;--muted:#8f85b0;--grad:linear-gradient(135deg,#7C3AED,#EC4899,#EF4444)}
*{box-sizing:border-box;margin:0;padding:0;font-family:Inter,system-ui}body{background:var(--bg);color:var(--text);display:grid;grid-template-columns:300px 1fr 320px;height:100dvh;overflow:hidden}
nav{border-right:1px solid var(--line);background:#0e0b18;display:flex;flex-direction:column}
.logo{font-weight:900;font-size:28px;background:var(--grad);-webkit-background-clip:text;-webkit-text-fill-color:transparent;padding:16px}
.ch{padding:12px 14px;border-bottom:1px solid #ffffff0a;cursor:pointer;display:flex;gap:10px;align-items:center;color:var(--muted)}.ch.on{background:#7C3AED22;color:#fff;border-left:3px solid #7C3AED}
.av{width:36px;height:36px;border-radius:50%;background:var(--grad);display:grid;place-items:center;font-weight:800;flex-shrink:0}
main{display:flex;flex-direction:column;background:radial-gradient(600px at 50% 0%,#7C3AED18,transparent)}
.msgs{flex:1;overflow:auto;padding:16px;display:flex;flex-direction:column;gap:10px}
.bub{max-width:72%;padding:10px 14px;border-radius:16px;font-size:14px;line-height:1.4}.me{align-self:flex-end;background:var(--grad)}.other{align-self:flex-start;background:var(--card2);border:1px solid var(--line)}
.bar{display:flex;gap:8px;padding:12px;background:var(--card);border-top:1px solid var(--line)}.bar input{flex:1;background:var(--card2);border:1px solid var(--line);color:#fff;padding:12px;border-radius:999px}.bar button{background:var(--grad);border:0;color:#fff;padding:10px 18px;border-radius:999px;font-weight:800}
.post{background:var(--card);border:1px solid var(--line);border-radius:16px;margin:12px 16px;overflow:hidden}.ph{display:flex;gap:10px;padding:10px 14px}
.right{border-left:1px solid var(--line);background:#0e0b18;padding:14px;overflow:auto}.card{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:12px;margin-bottom:12px}
.sug{display:flex;justify-content:space-between;align-items:center;padding:8px 0}.sug button{padding:6px 12px;border-radius:999px;border:0;font-weight:700;cursor:pointer}.follow{background:#fff;color:#000}.unfollow{background:var(--card2);color:#fff;border:1px solid var(--line)!important}
.top{height:56px;border-bottom:1px solid var(--line);display:flex;align-items:center;justify-content:space-between;padding:0 14px;background:#0e0b18bb;backdrop-filter:blur(10px)}
</style></head><body>
<nav><div class="logo">Zynko</div>
<div style="padding:8px 14px;color:var(--muted);font-size:11px;letter-spacing:1px">DISCORD • SALONS</div>
<div class="ch on" onclick="switchMode('chat')">💬 <b>general</b></div>
<div class="ch" onclick="switchMode('feed')">📸 <b>feed</b> — insta</div>
<div style="margin-top:auto;padding:12px;border-top:1px solid var(--line);display:flex;justify-content:space-between;align-items:center">
<div style="display:flex;gap:8px;align-items:center"><div class="av">{{USER[0]|upper}}</div><div><b style="font-size:13px">{{USER}}</b><br><span style="font-size:11px;color:var(--muted)">{{EMAIL}}</span></div></div>
<button onclick="fetch('/api/logout',{method:'POST'}).then(()=>location.href='/')" style="background:transparent;border:1px solid var(--line);color:#fff;padding:6px 10px;border-radius:8px">Sortir</button>
</div>
</nav>

<main>
<div class="top"><b id="title"># general</b><span style="font-size:12px;color:var(--muted)">vrais users • vraie DB</span></div>
<div id="chatView" class="msgs"></div>
<div id="feedView" style="display:none;flex:1;overflow:auto">
<div style="display:flex;gap:8px;padding:12px"><div class="av">{{USER[0]|upper}}</div><input id="postInput" placeholder="Quoi de neuf? (vrai post)" style="flex:1;background:var(--card2);border:1px solid var(--line);color:#fff;padding:12px;border-radius:999px"><button onclick="createPost()" class="bar button" style="background:var(--grad);border:0;color:#fff;padding:10px 16px;border-radius:999px;font-weight:800">Poster</button></div>
<div id="feedList"></div>
</div>
<div class="bar"><input id="msgInput" placeholder="Message à general..."><button onclick="sendMsg()">➤</button></div>
</main>

<div class="right">
<div class="card"><h4 style="margin-bottom:8px">Vrais membres ({{COUNT}})</h4><div id="users"></div></div>
<div class="card"><h4>Comment ça marche?</h4><p style="font-size:12px;color:var(--muted);line-height:1.5">Pour recevoir le vrai email :<br>1. Render > Settings > Environment<br>2. Ajoute EMAIL_USER = ton gmail<br>3. EMAIL_PASS = mot de passe d'application Gmail (pas ton mot de passe normal)<br>Sinon le code s'affiche à l'écran en mode test.</p></div>
</div>

<script>
let mode='chat';
function switchMode(m){
mode=m;
document.querySelectorAll('.ch').forEach(c=>c.classList.remove('on'));
event.currentTarget.classList.add('on');
document.getElementById('chatView').style.display=m=='chat'?'flex':'none';
document.getElementById('feedView').style.display=m=='feed'?'flex':'none';
document.querySelector('.bar').style.display=m=='chat'?'flex':'none';
document.getElementById('title').innerText=m=='chat'?'# general':'📸 feed';
if(m=='chat') loadMsgs(); else loadFeed();
}
async function loadMsgs(){
let r=await fetch('/api/messages'); let j=await r.json();
document.getElementById('chatView').innerHTML=j.map(m=>`<div class="bub ${m.mine?'me':'other'}"><b style="font-size:11px;opacity:.7">${m.username}</b><br>${m.content}</div>`).join('');
let d=document.getElementById('chatView'); d.scrollTop=d.scrollHeight;
}
async function sendMsg(){
let i=document.getElementById('msgInput'); if(!i.value) return;
await fetch('/api/messages',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({content:i.value})});
i.value=''; loadMsgs();
}
async function loadFeed(){
let r=await fetch('/api/posts'); let j=await r.json();
document.getElementById('feedList').innerHTML=j.map(p=>`<div class="post"><div class="ph"><div class="av">${p.username[0].toUpperCase()}</div><div><b>${p.username}</b><br><span style="font-size:11px;color:#8f85b0">${p.created}</span></div></div><div style="padding:12px 14px">${p.content}</div></div>`).join('') || '<p style="padding:20px;color:#8f85b0">Aucun post encore. Sois le premier.</p>';
}
async function createPost(){
let i=document.getElementById('postInput'); if(!i.value) return;
await fetch('/api/posts',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({content:i.value})});
i.value=''; loadFeed();
}
async function loadUsers(){
let r=await fetch('/api/users'); let j=await r.json();
document.getElementById('users').innerHTML=j.map(u=>`<div class="sug"><div style="display:flex;gap:8px;align-items:center"><div class="av" style="width:28px;height:28px">${u.username[0].toUpperCase()}</div><b style="font-size:13px">${u.username}</b></div><button class="${u.is_following?'unfollow':'follow'}" onclick="toggleFollow(${u.id},this)">${u.is_following?'Suivi':'Suivre'}</button></div>`).join('');
}
async function toggleFollow(id,btn){
let r=await fetch('/api/follow',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({user_id:id})});
let j=await r.json(); btn.textContent=j.following?'Suivi':'Suivre'; btn.className=j.following?'unfollow':'follow';
}
setInterval(()=>{ if(mode=='chat') loadMsgs(); },2000);
loadMsgs(); loadUsers();
</script></body></html>
"""

# --- ROUTES AUTH ---
@app.route("/")
def index():
    if "user_id" not in session:
        return render_template_string(AUTH_HTML)
    db=get_db()
    u=db.execute("SELECT * FROM users WHERE id=?", (session["user_id"],)).fetchone()
    count=db.execute("SELECT COUNT(*) FROM users WHERE verified=1").fetchone()[0]
    return render_template_string(SOCIAL_HTML, USER=u["username"], EMAIL=u["email"], COUNT=count)

@app.route("/api/register", methods=["POST"])
def api_register():
    d=request.json
    if not d.get("username") or not d.get("email") or not d.get("password"):
        return jsonify(ok=False, msg="Remplis tout")
    code = str(random.randint(100000, 999999))
    try:
        db=get_db()
        db.execute("INSERT INTO users(username,email,password,code,verified,created) VALUES(?,?,?,?,0,?)",
                   (d["username"], d["email"].lower(), generate_password_hash(d["password"]), code, datetime.now().isoformat()))
        db.commit()
    except sqlite3.IntegrityError:
        return jsonify(ok=False, msg="Pseudo ou email déjà pris")
    sent, debug = send_real_email(d["email"].lower(), code)
    if sent:
        return jsonify(ok=True, msg=f"Code envoyé à {d['email']}! Vérifie tes spams.")
    else:
        return jsonify(ok=True, msg="Compte créé. Email non configuré sur Render, code en mode test ci-dessous.", debug_code=debug)

@app.route("/api/verify", methods=["POST"])
def api_verify():
    d=request.json
    db=get_db()
    u=db.execute("SELECT * FROM users WHERE email=?", (d["email"].lower(),)).fetchone()
    if not u: return jsonify(ok=False, msg="Utilisateur introuvable")
    if u["code"]==d["code"]:
        db.execute("UPDATE users SET verified=1, code='' WHERE id=?", (u["id"],))
        db.commit()
        session["user_id"]=u["id"]
        return jsonify(ok=True, msg="Vérifié!")
    return jsonify(ok=False, msg="Mauvais code")

@app.route("/api/login", methods=["POST"])
def api_login():
    d=request.json
    db=get_db()
    u=db.execute("SELECT * FROM users WHERE email=?", (d["email"].lower(),)).fetchone()
    if not u or not check_password_hash(u["password"], d["password"]):
        return jsonify(ok=False, msg="Email ou mot de passe faux")
    if not u["verified"]:
        return jsonify(ok=False, msg="Vérifie ton email d'abord")
    session["user_id"]=u["id"]
    return jsonify(ok=True, msg="Connecté")

@app.route("/api/logout", methods=["POST"])
def api_logout():
    session.clear()
    return jsonify(ok=True)

# --- REAL DATA APIS ---
@app.route("/api/users")
def api_users():
    if "user_id" not in session: return jsonify([])
    db=get_db()
    users=db.execute("SELECT id,username FROM users WHERE verified=1 AND id!=? ORDER BY id DESC", (session["user_id"],)).fetchall()
    follows=set(r[0] for r in db.execute("SELECT followed_id FROM follows WHERE follower_id=?", (session["user_id"],)).fetchall())
    return jsonify([{"id":u["id"],"username":u["username"],"is_following":u["id"] in follows} for u in users])

@app.route("/api/follow", methods=["POST"])
def api_follow():
    if "user_id" not in session: return jsonify(ok=False)
    uid=request.json.get("user_id")
    db=get_db()
    exists=db.execute("SELECT 1 FROM follows WHERE follower_id=? AND followed_id=?", (session["user_id"], uid)).fetchone()
    if exists:
        db.execute("DELETE FROM follows WHERE follower_id=? AND followed_id=?", (session["user_id"], uid))
        db.commit()
        return jsonify(following=False)
    else:
        db.execute("INSERT INTO follows(follower_id,followed_id) VALUES(?,?)", (session["user_id"], uid))
        db.commit()
        return jsonify(following=True)

@app.route("/api/messages", methods=["GET","POST"])
def api_messages():
    if "user_id" not in session: return jsonify([])
    db=get_db()
    if request.method=="POST":
        c=request.json.get("content","")[:500]
        if c: db.execute("INSERT INTO messages(user_id,content,created) VALUES(?,?,?)",(session["user_id"],c,datetime.now().isoformat())); db.commit()
        return jsonify(ok=True)
    msgs=db.execute("SELECT m.content,m.created,u.username, m.user_id FROM messages m JOIN users u ON u.id=m.user_id ORDER BY m.id DESC LIMIT 50").fetchall()
    msgs=msgs[::-1]
    return jsonify([{"content":m["content"],"username":m["username"],"created":m["created"][:16],"mine":m["user_id"]==session["user_id"]} for m in msgs])

@app.route("/api/posts", methods=["GET","POST"])
def api_posts():
    if "user_id" not in session: return jsonify([])
    db=get_db()
    if request.method=="POST":
        c=request.json.get("content","")[:1000]
        if c: db.execute("INSERT INTO posts(user_id,content,created) VALUES(?,?,?)",(session["user_id"],c,datetime.now().isoformat())); db.commit()
        return jsonify(ok=True)
    posts=db.execute("SELECT p.content,p.created,u.username FROM posts p JOIN users u ON u.id=p.user_id ORDER BY p.id DESC LIMIT 30").fetchall()
    return jsonify([{"content":p["content"],"username":p["username"],"created":p["created"][:16]} for p in posts])

@app.route("/health")
def health(): return {"ok":True}

if __name__=="__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",10000)))
