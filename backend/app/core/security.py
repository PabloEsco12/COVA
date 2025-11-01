"""Security helpers for hashing and JWT management."""

from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Annotated, Literal, Tuple
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from .config import settings

TokenType = Literal["access", "refresh"]

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/token")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def generate_token(length: int = 48) -> str:
    """Return a URL-safe random token."""
    return secrets.token_urlsafe(length)


def hash_token(token: str) -> str:
    """Produce a deterministic SHA-256 digest of a token (for safe storage)."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def generate_jti() -> str:
    """Generate a unique identifier for refresh tokens."""
    return secrets.token_hex(16)


def create_access_token(subject: UUID | str, expires_delta: timedelta | None = None) -> str:
    expiry = expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return _create_jwt(subject, "access", expiry)


def create_refresh_token(subject: UUID | str, *, jti: str, expires_delta: timedelta | None = None) -> str:
    expiry = expires_delta or timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES)
    return _create_jwt(subject, "refresh", expiry, extra_claims={"jti": jti})


def _create_jwt(
    subject: UUID | str,
    token_type: TokenType,
    expires_delta: timedelta,
    *,
    extra_claims: dict | None = None,
) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(subject),
        "type": token_type,
        "iat": now,
        "exp": now + expires_delta,
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> UUID:
    payload = _decode_token(token, expected_type="access")
    return _extract_subject(payload)


def decode_refresh_token(token: str) -> Tuple[UUID, str]:
    payload = _decode_token(token, expected_type="refresh")
    jti = payload.get("jti")
    if not isinstance(jti, str):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token invalid",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return _extract_subject(payload), jti


def _decode_token(token: str, *, expected_type: TokenType) -> dict:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except JWTError as exc:  # pragma: no cover - library path
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    token_type = payload.get("type")
    if token_type != expected_type:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload


def _extract_subject(payload: dict) -> UUID:
    sub = payload.get("sub")
    if sub is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        return UUID(str(sub))
    except ValueError as exc:  # pragma: no cover
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token subject",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


async def get_current_user_id(token: Annotated[str, Depends(oauth2_scheme)]) -> UUID:
    return decode_access_token(token)
