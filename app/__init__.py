from flask import Flask, request, redirect, Response, jsonify, render_template
import logging
from .config import Config
from .extensions import db, migrate, login_manager, socketio
from .auth.routes import auth_bp
from .main.routes import main_bp


def create_app():
    app = Flask(__name__, static_folder="static", template_folder="templates")
    app.config.from_object(Config)

    # configure basic logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s: %(message)s')
    app.logger = logging.getLogger('zynko')

    # init extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    # prefer eventlet async mode in production (ensure eventlet is installed)
    socketio.init_app(app, cors_allowed_origins="*", async_mode="eventlet")

    # register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)

    # Quick fix: sanitize incoming paths that contain quoted characters (e.g. %22 or ")
    @app.before_request
    def sanitize_path():
        path = request.path or ""
        if "%22" in path or '"' in path:
            new_path = path.replace("%22", "").replace('"', "")
            qs = request.query_string.decode() if request.query_string else ""
            target = f"{new_path}?{qs}" if qs else new_path
            app.logger.info("Sanitizing bad path %s -> %s", path, target)
            return redirect(target, code=301)

    # Provide a simple SVG favicon to avoid 404s until a real favicon is added to static/
    @app.route('/favicon.ico')
    def favicon():
        svg = ("<?xml version=\"1.0\" encoding=\"UTF-8\"?>"
               "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 100 100\">"
               "<rect width=\"100\" height=\"100\" fill=\"#0d6efd\"/>"
               "<text x=\"50\" y=\"65\" font-size=\"60\" text-anchor=\"middle\" fill=\"#fff\">Z</text>"
               "</svg>")
        return Response(svg, mimetype='image/svg+xml')

    @app.route('/health')
    def health():
        return jsonify({'status': 'ok'})

    @app.errorhandler(404)
    def not_found(e):
        # simple HTML page for 404
        try:
            return render_template('404.html'), 404
        except Exception:
            return ("<h1>404 Not Found</h1>", 404)

    @app.errorhandler(500)
    def server_error(e):
        app.logger.exception('Server error: %s', e)
        try:
            return render_template('500.html'), 500
        except Exception:
            return ("<h1>500 Internal Server Error</h1>", 500)

    return app

# expose app and socketio for gunicorn
app = create_app()
