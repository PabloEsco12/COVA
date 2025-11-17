"""Schemas describing organisations and their members."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr

from app.models import OrganizationRole


class OrganizationMembershipInfo(BaseModel):
    id: uuid.UUID
    role: OrganizationRole
    joined_at: datetime
    is_admin: bool = False
    can_manage_admins: bool = False


class OrganizationSummary(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    created_at: datetime
    member_count: int
    admin_count: int
    membership: OrganizationMembershipInfo


class OrganizationMemberOut(BaseModel):
    membership_id: uuid.UUID
    user_id: uuid.UUID
    email: EmailStr
    display_name: str | None = None
    role: OrganizationRole
    is_admin: bool = False
    joined_at: datetime


class OrganizationMemberList(BaseModel):
    organization: OrganizationSummary
    members: list[OrganizationMemberOut]


class OrganizationRoleUpdate(BaseModel):
    role: OrganizationRole

