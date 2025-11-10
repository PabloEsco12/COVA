"""Token schemas."""

from __future__ import annotations

from pydantic import BaseModel


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int | None = None


class TokenPayload(BaseModel):
    sub: str | None = None
    exp: int | None = None
