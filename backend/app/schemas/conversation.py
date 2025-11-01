"""Pydantic schemas for conversation domain."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ConversationBase(BaseModel):
    title: str | None = None
    topic: str | None = None


class ConversationCreate(ConversationBase):
    participant_ids: list[UUID] = Field(default_factory=list)
    settings: dict | None = None


class ConversationMemberUser(BaseModel):
    id: UUID
    email: str
    display_name: str | None = None

    model_config = ConfigDict(from_attributes=True)


class ConversationMemberRead(BaseModel):
    conversation_id: UUID
    user_id: UUID
    role: str
    joined_at: datetime
    invited_by_id: UUID | None = None
    user: ConversationMemberUser | None = None

    model_config = ConfigDict(from_attributes=True)


class ConversationRead(ConversationBase):
    id: UUID
    owner_id: UUID | None = None
    is_group: bool
    created_at: datetime
    updated_at: datetime
    settings: dict | None = None
    members: list[ConversationMemberRead] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class ConversationSettingsUpdate(BaseModel):
    settings: dict


class ConversationArchiveRequest(BaseModel):
    archived: bool = True


ConversationRead.model_rebuild()
