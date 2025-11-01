"""Authentication schemas."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from .user import UserPrivate


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)
    display_name: str | None = Field(default=None, max_length=255)
    notification_login: bool | None = Field(default=False)


class RegisterResponse(BaseModel):
    message: str = "Inscription reussie. Consultez votre e-mail pour confirmer votre compte."
    user_id: UUID | None = None
    confirmation_url: str | None = None


class ConfirmEmailResponse(BaseModel):
    message: str
    confirmed_at: datetime | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    totp_code: str | None = Field(default=None, min_length=6, max_length=8)
    device_name: str | None = Field(default=None, max_length=255)
    device_platform: str | None = Field(default=None, max_length=16)
    user_agent: str | None = None


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 3600


class RefreshRequest(BaseModel):
    refresh_token: str


class RefreshResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LogoutResponse(BaseModel):
    message: str = "Deconnexion effectuee."


class LogoutAllResponse(BaseModel):
    message: str = "Tous les appareils ont ete deconnectes."
    revoked_count: int = 0


class AuthSession(BaseModel):
    tokens: TokenPair
    user: UserPrivate
