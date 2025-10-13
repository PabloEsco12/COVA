"""
backend/app/config.py
Centralise la configuration Flask + extensions (base, JWT, SQLAlchemy, upload, etc.).
"""

import os
from dataclasses import dataclass, asdict


# --- CONSTANTES DE BASE ---
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_DEFAULT_UPLOAD_DIR = os.path.join(_BASE_DIR, "static", "uploads")


# --- FONCTION D’UTILITAIRE POUR LIRE LES VARIABLES D’ENVIRONNEMENT ---
def _get_env(name: str, default: str | None = None) -> str:
    """
    Récupère une variable d’environnement et déclenche une erreur si elle est obligatoire.
    """
    val = os.getenv(name, default)
    if val is None:
        raise RuntimeError(f"Variable d'environnement manquante : {name}")
    return val


# --- CONFIGURATION PRINCIPALE ---
@dataclass(slots=True)
class Config:
    """Configuration principale de l’application Flask."""

    # --- Flask ---
    SECRET_KEY: str = _get_env("SECRET_KEY")
    FLASK_ENV: str = os.getenv("FLASK_ENV", "production")

    # --- JWT ---
    JWT_SECRET_KEY: str = _get_env("JWT_SECRET_KEY")

    # --- Base de données ---
    SQLALCHEMY_DATABASE_URI: str = _get_env("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False

    # --- Frontend (important pour les liens de confirmation par email) ---
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:5173")

    # --- Services externes (ex: visioconférence) ---
    CALL_BASE_URL: str = os.getenv("CALL_BASE_URL", "https://meet.jit.si")

    # --- Gestion des fichiers ---
    UPLOAD_FOLDER: str = os.getenv("UPLOAD_FOLDER", _DEFAULT_UPLOAD_DIR)


# --- CHARGEMENT DE LA CONFIGURATION ---
def load_config(app) -> None:
    """
    Injecte la configuration dans l’instance Flask.
    Valide les variables d’environnement à la construction.
    """
    cfg = Config()
    for key, value in asdict(cfg).items():
        app.config[key] = value
