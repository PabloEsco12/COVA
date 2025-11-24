"""
Schemas Pydantic pour l'API de gestion des contacts.

Infos utiles:
- Incluent creation, mise a jour du statut/alias et representation publique d'un contact.
- Config from_attributes pour hydrater depuis les models SQLAlchemy.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from app.models import ContactStatus


class ContactCreateRequest(BaseModel):
    """Payload de creation de contact."""
    email: EmailStr
    alias: str | None = Field(default=None, max_length=160)


class ContactStatusUpdate(BaseModel):
    """Mise a jour du statut (accepté/bloqué/etc.)."""
    status: ContactStatus


class ContactAliasUpdate(BaseModel):
    """Mise a jour de l'alias du contact."""
    alias: str | None = Field(default=None, max_length=160)


class ContactOut(BaseModel):
    """Representation API d'un contact avec profil et statut."""
    id: uuid.UUID
    contact_user_id: uuid.UUID
    email: EmailStr
    display_name: str | None
    avatar_url: str | None = None
    job_title: str | None = None
    department: str | None = None
    phone_number: str | None = None
    status_message: str | None = None
    status: ContactStatus
    alias: str | None
    created_at: datetime
    updated_at: datetime
    awaiting_my_response: bool = False

    class Config:
        from_attributes = True
