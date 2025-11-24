"""
Schemas Pydantic decritant organisations et membres.

Infos utiles:
- Exposent resume d'organisation, membres et droits (admin/gestion).
- Utilises par l'API pour lister, afficher et mettre a jour les roles.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr

from app.models import OrganizationRole


class OrganizationMembershipInfo(BaseModel):
    """Informations sur l'appartenance d'un utilisateur a une organisation."""
    id: uuid.UUID
    role: OrganizationRole
    joined_at: datetime
    is_admin: bool = False
    can_manage_admins: bool = False


class OrganizationSummary(BaseModel):
    """Resume d'une organisation incluant le membership courant."""
    id: uuid.UUID
    name: str
    slug: str
    created_at: datetime
    member_count: int
    admin_count: int
    membership: OrganizationMembershipInfo


class OrganizationMemberOut(BaseModel):
    """Representation exposee d'un membre d'organisation."""
    membership_id: uuid.UUID
    user_id: uuid.UUID
    email: EmailStr
    display_name: str | None = None
    role: OrganizationRole
    is_admin: bool = False
    joined_at: datetime


class OrganizationMemberList(BaseModel):
    """Liste des membres avec le resume de l'organisation."""
    organization: OrganizationSummary
    members: list[OrganizationMemberOut]


class OrganizationRoleUpdate(BaseModel):
    """Payload de mise a jour d'un role de membre."""
    role: OrganizationRole

