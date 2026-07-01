# WSGI entrypoint expected by Procfile/gunicorn: "app:app"
from app import app, socketio

if __name__ == "__main__":
    # local dev: run with socketio.run to enable Socket.IO
    # In production Gunicorn with an async worker (eventlet/gevent) should be used.
    socketio.run(app, host="0.0.0.0", port=10000, debug=True)
