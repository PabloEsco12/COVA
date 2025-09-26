# backend/app/__init__.py
import os

import os

import os

import os

import os

import os

import os

from flask import Flask
from .config import load_config
from .extensions import db, migrate, bcrypt, jwt, limiter, socketio
from .error_handlers import register_error_handlers
from .logging_utils import configure_json_logging
from . import models  # important: charger les modèles AVANT migrations
from .routes import register_blueprints
from flask_cors import CORS


def create_app() -> Flask:
    configure_json_logging()

    app = Flask(__name__)
    load_config(app)

    configure_json_logging(app)

    os.makedirs(app.config.get("UPLOAD_FOLDER", "uploads"), exist_ok=True)

    db.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)
    jwt.init_app(app)
    limiter.init_app(app)
    socketio.init_app(app)

    CORS(app, resources={
    r"/api/*": {
        "origins": [
            "http://localhost:5173",
            "https://covamessagerie.be",
            "https://www.covamessagerie.be"
        ]
        }
    })
    

    register_error_handlers(app)
    register_blueprints(app)

    @app.after_request
    def apply_security_headers(resp):
        resp.headers.setdefault("X-Content-Type-Options", "nosniff")
        resp.headers.setdefault("X-Frame-Options", "DENY")
        resp.headers.setdefault("Referrer-Policy", "no-referrer")
        return resp

    return app

