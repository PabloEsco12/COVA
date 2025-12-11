from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.models import UserAccount


@dataclass
class RegisterResult:
    """Résultat de l'inscription: utilisateur créé et jeton de confirmation éventuel."""

    user: UserAccount
    confirmation_token: str | None


@dataclass
class AuthResult:
    """Résultat d'authentification incluant tokens d'accès et de rafraîchissement."""

    user: UserAccount
    access_token: str
    refresh_token: str
    refresh_expires_at: datetime


class TotpRequiredError(Exception):
    """Déclenche un challenge TOTP obligatoire avant d'émettre de nouveaux tokens."""


__all__ = ["RegisterResult", "AuthResult", "TotpRequiredError"]
