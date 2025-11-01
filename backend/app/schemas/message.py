"""Pydantic schemas for messages."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class MessageCreate(BaseModel):
    content_json: dict


class MessageAuthor(BaseModel):
    id: UUID
    email: str
    display_name: str | None = None

    model_config = ConfigDict(from_attributes=True)


class MessageReactionRead(BaseModel):
    id: UUID
    user_id: UUID
    emoji: str
    created_at: datetime
    user: MessageAuthor | None = None

    model_config = ConfigDict(from_attributes=True)


class MessageAttachmentRead(BaseModel):
    id: UUID
    storage_path: str
    filename: str | None = None
    mime_type: str | None = None
    size_bytes: int | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MessageRead(BaseModel):
    id: UUID
    conversation_id: UUID
    author_id: UUID
    author: MessageAuthor | None = None
    content_json: dict
    encryption_header: dict | None = None
    created_at: datetime
    updated_at: datetime
    edited_at: datetime | None = None
    deleted_at: datetime | None = None
    state: str
    reads: list["MessageReadReceipt"] = Field(default_factory=list)
    reactions: list[MessageReactionRead] = Field(default_factory=list)
    attachments: list[MessageAttachmentRead] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class MessageReadReceipt(BaseModel):
    message_id: UUID
    user_id: UUID
    read_at: datetime
    user: MessageAuthor | None = None

    model_config = ConfigDict(from_attributes=True)


class MessageReactionCreate(BaseModel):
    emoji: str = Field(min_length=1, max_length=16)


class MessageAttachmentCreate(BaseModel):
    storage_path: str
    filename: str | None = None
    mime_type: str | None = None
    size_bytes: int | None = Field(default=None, ge=0)


MessageRead.model_rebuild()
