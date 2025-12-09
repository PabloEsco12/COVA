"""
############################################################
# Schemas : Organization
# Auteur : Valentin Masurelle
# Date   : 2025-05-04
#
# Description:
# - Résumé d'organisation, membres et droits (admin/gestion).
# - Utilise pour lister, afficher et mettre à jour les roles.
############################################################
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr

from app.models import OrganizationRole


class OrganizationMembershipInfo(BaseModel):
    """Informations sur l'appartenance d'un utilisateur à une organisation."""
    id: uuid.UUID
    role: OrganizationRole
    joined_at: datetime
    is_admin: bool = False
    can_manage_admins: bool = False


class OrganizationSummary(BaseModel):
    """Résumé d'une organisation incluant le membership courant."""
    id: uuid.UUID
    name: str
    slug: str
    created_at: datetime
    member_count: int
    admin_count: int
    membership: OrganizationMembershipInfo


class OrganizationMemberOut(BaseModel):
    """Représentation exposée d'un membre d'organisation."""
    membership_id: uuid.UUID
    user_id: uuid.UUID
    email: EmailStr
    display_name: str | None = None
    role: OrganizationRole
    is_admin: bool = False
    joined_at: datetime


class OrganizationMemberList(BaseModel):
    """Liste des membres avec le résumé de l'organisation."""
    organization: OrganizationSummary
    members: list[OrganizationMemberOut]


class OrganizationRoleUpdate(BaseModel):
    """Payload de mise à jour d'un rôle de membre."""
    role: OrganizationRole

