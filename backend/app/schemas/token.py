"""
############################################################
# Schemas : Token (JWT)
# Auteur : Valentin Masurelle
# Date   : 2025-05-04
#
# Description:
# - TokenPair pour les réponses d'auth/refresh.
# - TokenPayload pour les claims décodés du JWT.
############################################################
"""

from __future__ import annotations

from pydantic import BaseModel


class TokenPair(BaseModel):
    """Couple access/refresh tokens exposés par l'API."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int | None = None


class TokenPayload(BaseModel):
    """Claims essentiels d'un JWT (sujet, expiration)."""
    sub: str | None = None
    exp: int | None = None
