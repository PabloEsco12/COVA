# backend/app/__init__.py

from flask import Flask
from .config import load_config
from .extensions import db, migrate, bcrypt, jwt
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

    db.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)
    jwt.init_app(app)

    CORS(app, origins=["http://localhost:5173"], supports_credentials=True)

    register_error_handlers(app)
    register_blueprints(app)

    return app
