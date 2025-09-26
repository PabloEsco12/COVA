# backend/app/__init__.py

import os
from flask import Flask
from flask_cors import CORS

from .config import load_config
from .extensions import (
    db, migrate, bcrypt, jwt, limiter, socketio, ALLOWED_ORIGINS
)
from .error_handlers import register_error_handlers
from .logging_utils import configure_json_logging
from . import models  # important: charger les modèles AVANT migrations
from .routes import register_blueprints


def create_app() -> Flask:
    # Configuration de l'application
    app = Flask(__name__)
    load_config(app)

    # Initialisation des extensions
    db.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)
    jwt.init_app(app)
    limiter.init_app(app)
    socketio.init_app(app)

    # CORS : autoriser frontend local (dev) + domaine prod
    CORS(app, resources={r"/api/*": {"origins": ALLOWED_ORIGINS}})

    # Enregistreurs
    register_error_handlers(app)
    register_blueprints(app)

    # Headers de sécurité après chaque réponse
    @app.after_request
    def apply_security_headers(resp):
        resp.headers.setdefault("X-Content-Type-Options", "nosniff")
        resp.headers.setdefault("X-Frame-Options", "DENY")
        resp.headers.setdefault("Referrer-Policy", "no-referrer")
        return resp

    return app
