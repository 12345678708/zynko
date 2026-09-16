import os
from flask import Flask, render_template_string

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html lang="fr"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Zynko • Social</title>
<style>
:root{--bg:#08060e;--card:#13101c;--card2:#1c1730;--line:#221e36;--text:#f1efff;--muted:#8f85b0;--grad:linear-gradient(135deg,#7C3AED,#EC4899,#EF4444);--pink:#EC4899}
*{box-sizing:border-box;margin:0;padding:0;font-family:Inter,system-ui}
body{background:var(--bg);color:var(--text);display:grid;grid-template-columns:280px 1fr 320px;min-height:100dvh}
nav{border-right:1px solid var(--line);background:#0e0b18;position:sticky;top:0;height:100dvh;padding:18px;display:flex;flex-direction:column;gap:18px}
.logo{font-weight:900;font-size:28px;background:var(--grad);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.navitem{display:flex;gap:12px;padding:11px 12px;border-radius:12px;cursor:pointer;font-weight:600;color:var(--muted)}
.navitem.active,.navitem:hover{background:var(--card2);color:var(--text)}
main{border-right:1px solid var(--line);max-width:680px;margin:0 auto;width:100%}
.top{height:58px;display:flex;align-items:center;justify-content:space-between;padding:0 18px;border-bottom:1px solid var(--line);background:#0e0b18cc;backdrop-filter:blur(12px);position:sticky;top:0;z-index:5}
.stories{display:flex;gap:12px;padding:14px 16px;overflow:auto;border-bottom:1px solid var(--line)}
.sto{text-align:center;min-width:62px}
.ring{width:62px;height:62px;border-radius:50%;padding:2px;background:var(--grad)}
.ring div{width:100%;height:100%;background:var(--card);border-radius:50%;display:grid;place-items:center;font-weight:800;border:2px solid var(--bg)}
.sto span{font-size:11px;color:var(--muted)}
.post{background:var(--card);border:1px solid var(--line);border-radius:18px;margin:16px;overflow:hidden}
.ph{display:flex;gap:10px;padding:12px 14px;align-items:center}
.av{width:36px;height:36px;border-radius:50%;background:var(--grad);display:grid;place-items:center;font-weight:800}
.ph b{font-size:14px}.ph i{font-size:11px;color:var(--muted);font-style:normal}
.post img{width:100%;height:380px;object-fit:cover;background:#1a1530}
.actions{display:flex;gap:14px;padding:10px 14px;font-size:20px}
.actions b.liked{color:var(--pink)}
.caption{padding:0 14px 12px;font-size:14px;line-height:1.4}
.caption span{color:var(--muted)}
.compose{display:flex;gap:10px;padding:14px 16px;border-bottom:1px solid var(--line);background:var(--card)}
.compose input{flex:1;background:var(--card2);border:1px solid var(--line);border-radius:999px;padding:12px 16px;color:#fff}
.compose button{background:var(--grad);border:0;color:#fff;padding:10px 18px;border-radius:999px;font-weight:800;cursor:pointer}
.right{padding:18px;position:sticky;top:0;height:100dvh}
.card{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:14px;margin-bottom:14px}
.card h4{margin-bottom:10px}
.sug{display:flex;justify-content:space-between;align-items:center;padding:8px 0}
.sug button{background:#fff;color:#000;border:0;padding:6px 12px;border-radius:999px;font-weight:700;font-size:12px;cursor:pointer}
@media(max-width:1100px){body{grid-template-columns:80px 1fr} .right{display:none} .logo{font-size:20px} .navitem span{display:none}}
@media(max-width:700px){body{grid-template-columns:1fr} nav{display:none}}
</style></head><body>
<nav>
<div class="logo">Zynko</div>
<div class="navitem active">🏠 <span>Feed</span></div>
<div class="navitem">🔍 <span>Explorer</span></div>
<div class="navitem">💬 <span>Messages</span></div>
<div class="navitem">❤️ <span>Notifications</span></div>
<div class="navitem">👤 <span>Profil</span></div>
<div style="margin-top:auto" class="card">En ligne • github + render<br><span style="color:var(--muted);font-size:12px">Mono-fichier OK</span></div>
</nav>

<main>
<div class="top"><b>Accueil</b><span style="font-size:12px;color:var(--muted)">zynko.onrender.com • en direct</span></div>

<div class="stories">
<div class="sto"><div class="ring"><div>K</div></div><span>Karen</span></div>
<div class="sto"><div class="ring"><div>Z</div></div><span>Zynko</span></div>
<div class="sto"><div class="ring"><div>🧠</div></div><span>Netfly</span></div>
<div class="sto"><div class="ring"><div>✨</div></div><span>IA</span></div>
<div class="sto"><div class="ring"><div>+</div></div><span>Toi</span></div>
</div>

<div class="compose"><div class="av">T</div><input id="txt" placeholder="Quoi de neuf ?"><button onclick="post()">Publier</button></div>

<div id="feed">
<div class="post">
<div class="ph"><div class="av">K</div><div><b>Karen ✨</b><br><i>IA • il y a 2 min • Netfly</i></div></div>
<img src="https://images.unsplash.com/photo-1519608487953-e999c86e7455?w=800">
<div class="actions"><b onclick="this.classList.toggle('liked')" style="cursor:pointer">❤️ 234</b><span>💬 18</span><span>↗️</span></div>
<div class="caption"><b>Karen ✨</b> Premier post sur le vrai Zynko social. Maintenant ça ressemble à un réseau ! <span>#zynko #social</span></div>
</div>

<div class="post">
<div class="ph"><div class="av" style="background:linear-gradient(135deg,#06ffa5,#3a86ff)">Z</div><div><b>Zynko Team</b><br><i>il y a 1h</i></div></div>
<img src="https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=800">
<div class="actions"><b onclick="this.classList.toggle('liked')" style="cursor:pointer">❤️ 1.2k</b><span>💬 94</span><span>↗️</span></div>
<div class="caption"><b>Zynko Team</b> Design feed, stories, likes, tout est dans un seul fichier app.py 🚀</div>
</div>
</div>
</main>

<div class="right">
<div class="card"><h4>Suggestions pour toi</h4>
<div class="sug"><div style="display:flex;gap:8px;align-items:center"><div class="av" style="width:32px;height:32px">A</div><b style="font-size:13px">alex.dev</b></div><button>Suivre</button></div>
<div class="sug"><div style="display:flex;gap:8px;align-items:center"><div class="av" style="width:32px;height:32px">M</div><b style="font-size:13px">mia_ui</b></div><button>Suivre</button></div>
<div class="sug"><div style="display:flex;gap:8px;align-items:center"><div class="av" style="width:32px;height:32px">J</div><b style="font-size:13px">john.codes</b></div><button>Suivre</button></div>
</div>
<div class="card"><h4>Tendances</h4><div style="font-size:13px;color:var(--muted);line-height:1.8">#zynko • 12k posts<br>#render • 4k<br>#flask • 2.1k</div></div>
</div>

<script>
function post(){
let t=document.getElementById('txt');if(!t.value)return;
let f=document.getElementById('feed');
f.insertAdjacentHTML('afterbegin',`<div class="post"><div class="ph"><div class="av">T</div><div><b>Toi</b><br><i>à l'instant</i></div></div><div style="padding:14px">${t.value}</div><div class="actions"><b onclick="this.classList.toggle('liked')" style="cursor:pointer">❤️ 0</b><span>💬 0</span><span>↗️</span></div></div>`);
t.value='';
}
</script>
</body></html>
"""

@app.route("/")
def home(): return render_template_string(HTML)
@app.route("/health")
def health(): return {"ok": True}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
