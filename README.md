# Zynko - Clean Flask app (prototype)

Fonctionnalités:
- Auth (register/login/logout)
- Chat temps réel (Flask-SocketIO)
- Signaling WebRTC prototype pour audio/vidéo
- PWA manifest + service worker
- Déploiement: Procfile (gunicorn + eventlet) / Dockerfile

Pour local:
1. python -m venv .venv && source .venv/bin/activate
2. pip install -r requirements.txt
3. export FLASK_APP=app.py
   export FLASK_ENV=development
   (optionnel) export DATABASE_URL=sqlite:///data.db
4. flask db init && flask db migrate && flask db upgrade
5. python app.py
Visiter http://localhost:10000

Notes:
- Pour WebRTC en production, prévoir serveur TURN (coturn).
- Configure SECRET_KEY et DATABASE_URL via variables d'environnement.
