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
    """Reponse a l'inscription (inclut lien/jeton de confirmation si applicable)."""
    message: str
    user_id: str | None = None
    confirmation_url: str | None = None


class ResendConfirmationRequest(BaseModel):
    """Requete pour renvoyer un email de confirmation."""
    email: EmailStr


class ResendConfirmationResponse(BaseModel):
    """Reponse standardisee au renvoi de confirmation."""
    message: str = "Confirmation email resent."


class ForgotPasswordRequest(BaseModel):
    """Requete de mot de passe oublie."""
    email: EmailStr


class ForgotPasswordResponse(BaseModel):
    """Reponse neutre (evite de divulguer l'existence du compte)."""
    message: str = "If the account exists, a reset link has been sent."


class ResetPasswordRequest(BaseModel):
    """Payload pour appliquer un nouveau mot de passe a partir d'un token."""
    token: str = Field(min_length=16, max_length=160)
    password: str = Field(min_length=8, max_length=128)


class ResetPasswordResponse(BaseModel):
    """Confirmation de mise a jour de mot de passe."""
    message: str = "Password updated successfully."


class LoginRequest(BaseModel):
    """Requete de connexion avec champ optionnel pour TOTP."""
    email: EmailStr
    password: str
    totp_code: str | None = Field(default=None, min_length=6, max_length=8)


class RefreshRequest(BaseModel):
    """Payload pour rafraichir un token d'acces."""
    refresh_token: str


class LogoutResponse(BaseModel):
    """Reponse standard au logout."""
    message: str = "Logout successful."


class LogoutAllResponse(BaseModel):
    """Reponse au logout global avec compteur de jetons revoques."""
    message: str = "All sessions revoked."
    revoked_count: int = 0


class AuthSession(BaseModel):
    """Regroupe les tokens et les informations de l'utilisateur authentifie."""
    tokens: TokenPair
    user: UserOut


class ConfirmEmailResponse(BaseModel):
    """Retour de confirmation d'email avec utilisateur hydrate."""
    message: str
    user: UserOut
