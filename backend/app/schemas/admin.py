"""
############################################################
# Schemas : Administration des utilisateurs
# Auteur : Valentin Masurelle
# Date   : 2025-11-25
#
# Description:
# - Payloads et reponses pour la creation/suppression d'utilisateurs par un admin.
############################################################
"""

from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field

from app.models import UserRole
from .user import UserOut


class AdminUserCreateRequest(BaseModel):
    """Création d'utilisateur par un administrateur."""
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    display_name: str | None = Field(default=None, max_length=160)
    role: UserRole | None = None
    confirm_now: bool = True


class AdminUserCreateResponse(BaseModel):
    """Utilisateur créée et éventuel lien de confirmation."""
    user: UserOut
    confirmation_url: str | None = None


class AdminUserDeleteResponse(BaseModel):
    """Confirmation de suppression effectuee par un administrateur."""
    message: str = "Utilisateur supprime."
