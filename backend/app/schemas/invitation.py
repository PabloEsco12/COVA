"""Schemas for conversation invitations."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class InvitationCreate(BaseModel):
    email: EmailStr
    role: str | None = Field(default="member")
    expires_in_hours: int | None = Field(default=None, ge=1, le=720)


class InvitationRead(BaseModel):
    id: UUID
    conversation_id: UUID
    inviter_id: UUID | None
    email: EmailStr
    role: str
    expires_at: datetime
    accepted_at: datetime | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InvitationCreateResponse(BaseModel):
    invitation: InvitationRead
    token: str

