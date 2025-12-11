"""
############################################################
# Schemas : Auth
# Auteur : Valentin Masurelle
# Date   : 2025-05-04
#
# Description:
# - Payloads et réponses pour inscription/login/refresh/reset password.
# - Validation email/mot de passe via Pydantic (EmailStr, Field).
############################################################
"""

from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field

from .token import TokenPair
from .user import UserOut


class RegisterRequest(BaseModel):
    """Payload d'inscription utilisateur."""
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    display_name: str | None = Field(default=None, max_length=160)


class RegisterResponse(BaseModel):
    """Réponse à l'inscription (inclut lien/jeton de confirmation si applicable)."""
    message: str
    user_id: str | None = None
    confirmation_url: str | None = None


class ResendConfirmationRequest(BaseModel):
    """Requête pour renvoyer un email de confirmation."""
    email: EmailStr


class ResendConfirmationResponse(BaseModel):
    """Réponse standardisée au renvoi de confirmation."""
    message: str = "Confirmation email resent."


class ForgotPasswordRequest(BaseModel):
    """Requête de mot de passe oublié."""
    email: EmailStr


class ForgotPasswordResponse(BaseModel):
    """Réponse neutre (évite de divulguer l'existence du compte)."""
    message: str = "If the account exists, a reset link has been sent."


class ResetPasswordRequest(BaseModel):
    """Payload pour appliquer un nouveau mot de passe à partir d'un token."""
    token: str = Field(min_length=16, max_length=160)
    password: str = Field(min_length=8, max_length=128)


class ResetPasswordResponse(BaseModel):
    """Confirmation de mise à jour de mot de passe."""
    message: str = "Password updated successfully."


class LoginRequest(BaseModel):
    """Requête de connexion avec champ optionnel pour TOTP."""
    email: EmailStr
    password: str
    totp_code: str | None = Field(default=None, min_length=6, max_length=8)
    timezone: str | None = Field(default=None, max_length=64)


class RefreshRequest(BaseModel):
    """Payload pour rafraîchir un token d'accès."""
    refresh_token: str


class LogoutResponse(BaseModel):
    """Réponse standard au logout."""
    message: str = "Logout successful."


class LogoutAllResponse(BaseModel):
    """Réponse au logout global avec compteur de jetons révoqués."""
    message: str = "All sessions revoked."
    revoked_count: int = 0


class AuthSession(BaseModel):
    """Regroupe les tokens et les informations de l'utilisateur authentifié."""
    tokens: TokenPair
    user: UserOut


class ConfirmEmailResponse(BaseModel):
    """Retour de confirmation d'email avec utilisateur authentifié."""
    message: str
    user: UserOut
