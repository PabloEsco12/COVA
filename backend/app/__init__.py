# backend/app/__init__.py

from flask import Flask
from .config import load_config
from .extensions import db, migrate, bcrypt, jwt
from .error_handlers import register_error_handlers
from . import models  # important : charger les modèles AVANT migrations
from .routes import register_blueprints

def create_app() -> Flask:
    app = Flask(__name__)
    load_config(app)

    db.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)
    jwt.init_app(app)

    register_error_handlers(app)
    register_blueprints(app)

    return app
