"""
############################################################
# Module : models.base (Declarative Base)
# Auteur : Valentin Masurelle
# Date   : 2025-05-04
#
# Description:
# - Base declarative commune pour tous les modèles SQLAlchemy.
# - Partage la metadata et la configuration globale.
############################################################
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base commune des modèles SQLAlchemy."""

    __abstract__ = True
