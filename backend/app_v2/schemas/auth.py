"""Authentication request/response models."""

from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field

from .token import TokenPair
from .user import UserOut


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    display_name: str | None = Field(default=None, max_length=160)


class RegisterResponse(BaseModel):
    message: str
    user_id: str | None = None
    confirmation_url: str | None = None


class ResendConfirmationRequest(BaseModel):
    email: EmailStr


class ResendConfirmationResponse(BaseModel):
    message: str = "Confirmation email resent."


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ForgotPasswordResponse(BaseModel):
    message: str = "If the account exists, a reset link has been sent."


class ResetPasswordRequest(BaseModel):
    token: str = Field(min_length=16, max_length=160)
    password: str = Field(min_length=8, max_length=128)


class ResetPasswordResponse(BaseModel):
    message: str = "Password updated successfully."


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    totp_code: str | None = Field(default=None, min_length=6, max_length=8)


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutResponse(BaseModel):
    message: str = "Logout successful."


class LogoutAllResponse(BaseModel):
    message: str = "All sessions revoked."
    revoked_count: int = 0


class AuthSession(BaseModel):
    tokens: TokenPair
    user: UserOut


class ConfirmEmailResponse(BaseModel):
    message: str
    user: UserOut
