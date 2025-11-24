"""
Schemas Pydantic pour les utilisateurs (profils, compte courant, mises a jour).

Infos utiles:
- from_attributes active pour mapper depuis SQLAlchemy.
- Couvre resume du compte, profil detaille et operations de securite basique.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    """Champs communs exposes sur un utilisateur."""
    id: uuid.UUID
    email: EmailStr
    role: str
    is_confirmed: bool


class UserProfileOut(BaseModel):
    """Profil utilisateur complet (affichage et preferences)."""
    display_name: str | None = None
    avatar_url: str | None = None
    locale: str | None = None
    timezone: str | None = None
    profile_data: dict | None = None


class UserOut(UserBase):
    """Utilisateur expose avec statut et profil associe."""
    is_active: bool
    created_at: datetime
    profile: UserProfileOut | None = None

    class Config:
        from_attributes = True


class MeSummaryOut(BaseModel):
    """Vue resume pour /me (utilisee par l'UI)."""
    id: uuid.UUID
    email: EmailStr
    pseudo: str
    avatar: str | None = None
    avatar_url: str | None = None
    date_crea: datetime | None = None


class MeProfileOut(BaseModel):
    """Profil detaille de l'utilisateur courant."""
    email: EmailStr
    display_name: str | None = None
    avatar_url: str | None = None
    locale: str | None = None
    timezone: str | None = None
    job_title: str | None = None
    department: str | None = None
    phone_number: str | None = None
    pgp_public_key: str | None = None
    status_message: str | None = None


class MeProfileUpdate(BaseModel):
    """Payload de mise a jour partielle du profil."""
    display_name: str | None = None
    locale: str | None = None
    timezone: str | None = None
    job_title: str | None = None
    department: str | None = None
    phone_number: str | None = None
    pgp_public_key: str | None = None
    status_message: str | None = None


class AvatarResponse(BaseModel):
    """URL de l'avatar apres upload/mise a jour."""
    avatar_url: str | None = None


class AccountDeleteRequest(BaseModel):
    """Confirmation de suppression de compte (mot de passe requis)."""
    password: str


class PasswordUpdateRequest(BaseModel):
    """Changement de mot de passe (ancien + nouveau)."""
    old_password: str
    new_password: str
