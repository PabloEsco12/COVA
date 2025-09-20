"""
backend/app/config.py
Centralise la configuration Flask + extensions.
"""
from dataclasses import dataclass, asdict
import os


_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_DEFAULT_UPLOAD_DIR = os.path.join(_BASE_DIR, "static", "uploads")


def _get_env(name: str, default: str | None = None) -> str:
    val = os.getenv(name, default)
    if val is None:
        raise RuntimeError(f"Variable d'environnement manquante : {name}")
    return val


@dataclass(slots=True)
class Config:
    # Flask
    SECRET_KEY: str = _get_env("SECRET_KEY")
    FLASK_ENV: str = os.getenv("FLASK_ENV", "production")

    # JWT
    JWT_SECRET_KEY: str = _get_env("JWT_SECRET_KEY")

    # SQLAlchemy
    SQLALCHEMY_DATABASE_URI: str = _get_env("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False
    
    # Frontend
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:5173")

    # Fichiers
    UPLOAD_FOLDER: str = os.getenv("UPLOAD_FOLDER", _DEFAULT_UPLOAD_DIR)


def load_config(app) -> None:
    """Injecte la configuration dans l’instance Flask."""
    cfg = Config()                   # construit => vérifie les variables d’env
    for key, value in asdict(cfg).items():   # ← asdict() fonctionne avec slots
        app.config[key] = value
