"""
Helpers de securite (hash, JWT) pour le backend v2.

Infos utiles:
- Bcrypt via passlib pour le hashing des mots de passe.
- JWT signe avec secret/algorithme definis dans la configuration; expiration paramétrable.
- Toutes les dates de token sont gerees en UTC.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict

from jose import JWTError, jwt
from passlib.context import CryptContext

from ..config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Compare un mot de passe en clair avec son hash bcrypt."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Genere un hash bcrypt pour un mot de passe."""
    return pwd_context.hash(password)


def create_access_token(subject: str | Dict[str, Any], expires_minutes: int | None = None) -> str:
    """Cree un JWT signe pour un sujet (sub ou dict), avec expiration en minutes."""
    if expires_minutes is None:
        expires_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES
    expires_delta = timedelta(minutes=expires_minutes)
    to_encode: Dict[str, Any] = {}
    if isinstance(subject, dict):
        to_encode.update(subject)
    else:
        to_encode["sub"] = str(subject)
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode["exp"] = expire
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict[str, Any]:
    """Decode et valide un JWT, leve ValueError si invalide."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError as exc:
        raise ValueError("Invalid token") from exc


__all__ = ["verify_password", "get_password_hash", "create_access_token", "decode_token"]
