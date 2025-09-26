from flask import Flask
from flask_cors import CORS
from .config import load_config
from .extensions import db, migrate, bcrypt, jwt, limiter, socketio, ALLOWED_ORIGINS
from .error_handlers import register_error_handlers
from .logging_utils import configure_json_logging
from . import models
from .routes import register_blueprints

def create_app() -> Flask:
    app = Flask(__name__)
    load_config(app)

    db.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)
    jwt.init_app(app)
    limiter.init_app(app)

    # CORS REST
    CORS(app, resources={r"/api/*": {"origins": ALLOWED_ORIGINS}})
    # CORS WebSocket (Socket.IO)
    socketio.init_app(app, cors_allowed_origins=ALLOWED_ORIGINS)

    register_error_handlers(app)
    register_blueprints(app)

    @app.after_request
    def apply_security_headers(resp):
        resp.headers.setdefault("X-Content-Type-Options", "nosniff")
        resp.headers.setdefault("X-Frame-Options", "DENY")
        resp.headers.setdefault("Referrer-Policy", "no-referrer")
        return resp

    return app
