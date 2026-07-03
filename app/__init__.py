from flask import Flask, request, redirect, Response, jsonify, render_template, url_for
import logging
from urllib.parse import unquote
import os
from .config import Config
from .extensions import db, migrate, login_manager, socketio
from .auth.routes import auth_bp
from .main.routes import main_bp

# used to inspect existing tables
from sqlalchemy import inspect as sqlalchemy_inspect


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
        try:
            # First, inspect the raw request URI from the WSGI environ if available.
            # Some platforms (or proxies) preserve the original encoded path in RAW_URI/REQUEST_URI
            raw_environ = None
            for key in ('RAW_URI', 'REQUEST_URI', 'ORIG_PATH_INFO', 'RAW_PATH_INFO'):
                raw_environ = request.environ.get(key)
                if raw_environ:
                    break
            # Fallback to request.path (may be already decoded)
            raw_path = raw_environ if raw_environ else request.path or ""

            # If we see encoded quotes in the raw path, decode and clean
            if raw_path and ('%22' in raw_path or '%27' in raw_path or '%2522' in raw_path):
                decoded = raw_path
                for _ in range(3):
                    next_decoded = unquote(decoded)
                    if next_decoded == decoded:
                        break
                    decoded = next_decoded
                cleaned = decoded.replace('%22', '').replace('%27', '').replace('\"', '').replace("'", '')
                qs = request.query_string.decode() if request.query_string else ""
                target = f"{cleaned}?{qs}" if qs else cleaned
                app.logger.info("RAW sanitize redirect: %s -> %s", raw_path, target)
                return redirect(target, code=301)

            # As a secondary check operate on the already-decoded request.path
            decoded = request.path or ""
            for _ in range(2):
                nxt = unquote(decoded)
                if nxt == decoded:
                    break
                decoded = nxt
            if ('%22' in decoded) or ('%27' in decoded) or ('\"' in decoded) or ("\'" in decoded) or ('"' in decoded) or ("'" in decoded):
                cleaned = decoded.replace('%22', '').replace('%27', '').replace('\"', '').replace("'", '')
                qs = request.query_string.decode() if request.query_string else ""
                target = f"{cleaned}?{qs}" if qs else cleaned
                app.logger.info("sanitize_path redirect: %s -> %s", request.path, target)
                return redirect(target, code=301)
        except Exception as e:
            app.logger.debug('sanitize_path error: %s', e)

    # Provide a simple SVG favicon to avoid 404s until a real favicon is added to static/
    @app.route('/favicon.ico')
    def favicon():
        svg = ("<?xml version=\"1.0\" encoding=\"UTF-8\"?>"
               "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 100 100\">"
               "<rect width=\"100\" height=\"100\" fill=\"#0d6efd\"/>"
               "<text x=\"50\" y=\"65\" font-size=\"60\" text-anchor=\"middle\" fill=\"#fff\">Z</text>"
               "</svg>")
        return Response(svg, mimetype='image/svg+xml')

    # Emergency explicit redirects for a few known malformed logout URLs
    # These are very targeted and safe — they only redirect these exact paths.
    @app.route('/%22/logout/%22')
    @app.route('/%22/logout/')
    @app.route('/%22/logout')
    @app.route('/%22logout%22')
    @app.route('/%22logout')
    def redirect_malformed_logout():
        app.logger.info("explicit redirect: malformed logout path -> /logout")
        return redirect(url_for('auth.logout'), code=301)

    @app.route('/health')
    def health():
        return jsonify({'status': 'ok'})

    @app.errorhandler(404)
    def not_found(e):
        try:
            path = request.path or ""
            # If path contains encoded or literal quotes, try to clean & redirect
            if '%22' in path or '%27' in path or '"' in path or "'" in path:
                decoded = path
                for _ in range(3):
                    nxt = unquote(decoded)
                    if nxt == decoded:
                        break
                    decoded = nxt
                cleaned = decoded.replace('%22', '').replace('%27', '').replace('"', '').replace("'", '')
                if cleaned == "":
                    cleaned = "/"
                qs = request.query_string.decode() if request.query_string else ""
                target = f"{cleaned}?{qs}" if qs else cleaned
                app.logger.info("404 fallback redirect: %s -> %s", path, target)
                return redirect(target, code=301)
        except Exception as ex:
            app.logger.debug('404 fallback error: %s', ex)

        # default behavior: render 404 page
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

# Attempt to run DB migrations automatically on startup to avoid missing-tables errors in production.
# Only run migrations if a migrations/ folder exists (avoid failing startup when no migration scripts are present).
migrations_dir = os.path.join(app.root_path, 'migrations')
if os.path.isdir(migrations_dir):
    try:
        from flask_migrate import upgrade as _upgrade
        with app.app_context():
            try:
                _upgrade()
                app.logger.info('Automatic DB migrations applied on startup')
            except SystemExit as _se:
                app.logger.warning('Automatic DB migration exited unexpectedly: %s', _se)
            except Exception as _e:
                app.logger.warning('Automatic DB migration failed: %s', _e)
    except Exception as ex:
        # Migration package might not be available in some environments; don't fail startup.
        app.logger.debug('flask_migrate.upgrade not available or failed to import: %s', ex)
else:
    # No migrations directory — attempt to create tables from current models as a safe fallback.
    try:
        with app.app_context():
            inspector = sqlalchemy_inspect(db.engine)
            existing = inspector.get_table_names()
            if not existing:
                app.logger.info('No existing tables detected — creating tables from models (db.create_all)')
                db.create_all()
                app.logger.info('db.create_all() completed')
            else:
                app.logger.info('Existing tables detected; skipping db.create_all()')
    except Exception as ex:
        app.logger.warning('Automatic db.create_all() failed: %s', ex)
