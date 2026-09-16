import os
from flask import Flask, render_template_string

app = Flask(__name__)

HTML = """
<!DOCTYPE html><html lang="fr"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Zynko</title>
<style>
:root{--bg:#0a0a0f;--card:#15101f;--card2:#1f1730;--text:#f5f3ff;--muted:#9a8ec2;--grad:linear-gradient(135deg,#7C3AED 0%,#EC4899 50%,#EF4444 100%);--border:#2a2340}
*{box-sizing:border-box;margin:0;padding:0;font-family:system-ui}
body{background:var(--bg);color:var(--text);height:100dvh;display:grid;grid-template-columns:340px 1fr}
.side{background:var(--card);border-right:1px solid var(--border);display:flex;flex-direction:column}
.top{height:60px;border-bottom:1px solid var(--border);display:flex;align-items:center;padding:0 14px;justify-content:space-between}
.logo{font-weight:900;font-size:22px;background:var(--grad);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.list{flex:1;overflow:auto}.item{padding:12px;display:flex;gap:10px;border-bottom:1px solid #ffffff0a;cursor:pointer}
.item.on{background:linear-gradient(90deg,#7C3AED26,transparent);border-left:3px solid #7C3AED}
.av{width:38px;height:38px;border-radius:50%;background:var(--grad);display:grid;place-items:center;font-weight:800}
.main{display:flex;flex-direction:column;position:relative}
.bg{position:absolute;inset:0;background:radial-gradient(#7C3AED22,#0a0a0f)}
.msgs{flex:1;overflow:auto;padding:16px;display:flex;flex-direction:column;gap:8px;z-index:1}
.bub{max-width:70%;padding:9px 12px;border-radius:14px;font-size:14px}.me{align-self:flex-end;background:var(--grad)}.other{align-self:flex-start;background:var(--card2);border:1px solid var(--border)}
.bar{padding:10px;display:flex;gap:8px;background:var(--card);border-top:1px solid var(--border);z-index:1}
.bar input{flex:1;background:var(--card2);border:1px solid var(--border);color:#fff;padding:10px;border-radius:10px}
.bar button{background:var(--grad);border:0;color:#fff;padding:10px 14px;border-radius:10px;font-weight:700}
</style></head><body>
<div class="side"><div class="top"><div class="logo">Zynko</div><span style="font-size:11px;color:#9a8ec2">github + render</span></div>
<div class="list">
<div class="item on"><div class="av">K</div><div><b>Karen ✨</b><br><span style="font-size:11px;color:#9a8ec2">IA • Netfly</span></div></div>
<div class="item"><div class="av">G</div><div><b>General</b></div></div>
</div></div>
<div class="main"><div class="bg"></div><div class="top" style="z-index:1;background:var(--card)"><b>Karen ✨</b><span style="font-size:11px;color:#9a8ec2">en ligne</span></div>
<div class="msgs" id="m"><div class="bub other">Salut ! Dashboard mono-fichier OK. Tape /fond pour tester.</div></div>
<div class="bar"><input id="i" placeholder="Message..." onkeydown="if(event.key==='Enter')send()"><button onclick="send()">➤</button></div>
</div>
<script>
function send(){let e=document.getElementById('i');if(!e.value)return;document.getElementById('m').innerHTML+=`<div class=bub me>${e.value}</div>`;e.value='';let d=document.getElementById('m');d.scrollTop=d.scrollHeight}
</script></body></html>
"""

@app.route("/")
def home(): return render_template_string(HTML)

@app.route("/health")
def health(): return {"status":"ok"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
