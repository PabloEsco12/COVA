"""
Base declarative commune pour les modèles SQLAlchemy de la nouvelle génération.

Infos utiles:
- Centralise l'héritage des modèles pour partager metadata et config globale.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base commune des modèles SQLAlchemy."""

    __abstract__ = True
