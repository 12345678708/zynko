from flask import Flask
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

    return app

# expose app and socketio for gunicorn
app = create_app()
