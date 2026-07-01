from flask import Flask, request, redirect, Response
from .config import Config
from .extensions import db, migrate, login_manager, socketio
from .auth.routes import auth_bp
from .main.routes import main_bp


def create_app():
    app = Flask(__name__, static_folder="static", template_folder="templates")
    app.config.from_object(Config)

    # init extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    socketio.init_app(app, cors_allowed_origins="*")  # adjust CORS in prod

    # register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)

    # Quick fix: sanitize incoming paths that contain quoted characters (e.g. %22 or ")
    @app.before_request
    def sanitize_path():
        # If the URL path contains encoded or literal quotes, remove them and redirect
        path = request.path or ""
        if "%22" in path or '"' in path:
            new_path = path.replace("%22", "").replace('"', "")
            qs = request.query_string.decode() if request.query_string else ""
            if qs:
                return redirect(f"{new_path}?{qs}", code=301)
            return redirect(new_path, code=301)

    # Provide a simple SVG favicon to avoid 404s until a real favicon is added to static/
    @app.route('/favicon.ico')
    def favicon():
        svg = ("<?xml version=\"1.0\" encoding=\"UTF-8\"?>"
               "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 100 100\">"
               "<rect width=\"100\" height=\"100\" fill=\"#0d6efd\"/>"
               "<text x=\"50\" y=\"65\" font-size=\"60\" text-anchor=\"middle\" fill=\"#fff\">Z</text>"
               "</svg>")
        return Response(svg, mimetype='image/svg+xml')

    return app

# expose app and socketio for gunicorn
app = create_app()
