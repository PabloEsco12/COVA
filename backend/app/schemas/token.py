"""
Schemas Pydantic pour les tokens d'acces et leurs payloads.

Infos utiles:
- TokenPair correspond aux reponses d'authentification/refresh.
- TokenPayload represente les claims decodes d'un JWT.
"""

from __future__ import annotations

from pydantic import BaseModel


class TokenPair(BaseModel):
    """Couple access/refresh tokens expose par l'API."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int | None = None


class TokenPayload(BaseModel):
    """Claims essentiels d'un JWT (sujet, expiration)."""
    sub: str | None = None
    exp: int | None = None
