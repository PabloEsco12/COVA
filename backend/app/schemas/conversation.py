"""Conversation and message schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import List, Literal

from pydantic import BaseModel, EmailStr, Field, constr

from app.models import (
    ConversationMemberRole,
    ConversationType,
    MembershipState,
    MessageDeliveryState,
    MessageType,
)


class ConversationMemberOut(BaseModel):
    user_id: uuid.UUID
    role: ConversationMemberRole
    state: MembershipState
    joined_at: datetime
    muted_until: datetime | None = None
    display_name: str | None = None
    email: EmailStr | None = None
    avatar_url: str | None = None
    status_message: str | None = None

    class Config:
        from_attributes = True


class ConversationCreateRequest(BaseModel):
    title: str | None = Field(default=None, max_length=160)
    participant_ids: List[uuid.UUID] = Field(default_factory=list)
    type: ConversationType = ConversationType.GROUP


class ConversationOut(BaseModel):
    id: uuid.UUID
    title: str | None
    topic: str | None = None
    type: ConversationType
    created_at: datetime
    archived: bool = False
    members: List[ConversationMemberOut]
    blocked_by_viewer: bool = False
    blocked_by_other: bool = False

    class Config:
        from_attributes = True


class ConversationUpdateRequest(BaseModel):
    title: str | None = Field(default=None, max_length=160)
    topic: str | None = Field(default=None, max_length=2000)
    archived: bool | None = None


class ConversationMemberUpdateRequest(BaseModel):
    role: ConversationMemberRole | None = None
    state: MembershipState | None = None
    muted_until: datetime | None = None


class ConversationInviteCreateRequest(BaseModel):
    email: EmailStr
    role: ConversationMemberRole = ConversationMemberRole.MEMBER
    expires_in_hours: int = Field(default=72, ge=1, le=24 * 14)


class ConversationInviteOut(BaseModel):
    id: uuid.UUID
    conversation_id: uuid.UUID
    email: EmailStr
    role: ConversationMemberRole
    token: str
    expires_at: datetime
    accepted_at: datetime | None = None

    class Config:
        from_attributes = True


class MessageCreateRequest(BaseModel):
    content: str
    message_type: MessageType = MessageType.TEXT
    attachments: List[AttachmentReference] = Field(default_factory=list)
    reply_to_message_id: uuid.UUID | None = Field(default=None)
    forward_message_id: uuid.UUID | None = Field(default=None)


class MessageUpdateRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=2000)


class MessageOut(BaseModel):
    id: uuid.UUID
    conversation_id: uuid.UUID
    stream_position: int
    author_id: uuid.UUID | None
    author_display_name: str | None = None
    author_avatar_url: str | None = None
    type: MessageType
    content: str
    created_at: datetime
    is_system: bool = False
    delivery_state: MessageDeliveryState | None = None
    delivered_at: datetime | None = None
    read_at: datetime | None = None
    encryption_scheme: str | None = None
    encryption_metadata: dict | None = None
    reactions: List[MessageReactionSummary] = Field(default_factory=list)
    pinned: bool = False
    pinned_at: datetime | None = None
    pinned_by: uuid.UUID | None = None
    attachments: List[MessageAttachmentOut] = Field(default_factory=list)
    edited_at: datetime | None = None
    deleted_at: datetime | None = None
    deleted: bool = False
    reply_to: MessageReference | None = None
    forward_from: MessageReference | None = None

    class Config:
        from_attributes = True


class MessageReadRequest(BaseModel):
    message_ids: List[uuid.UUID] | None = None


class MessageReactionSummary(BaseModel):
    emoji: str
    count: int
    reacted: bool = False


class MessageReactionRequest(BaseModel):
    emoji: constr(min_length=1, max_length=16)
    action: Literal["toggle", "add", "remove"] = "toggle"


class AttachmentReference(BaseModel):
    upload_token: constr(min_length=32)


class MessageAttachmentOut(BaseModel):
    id: uuid.UUID
    file_name: str | None = None
    mime_type: str | None = None
    size_bytes: int | None = None
    sha256: str | None = None
    download_url: str | None = None
    encryption: dict | None = None


class AttachmentUploadResponse(BaseModel):
    upload_token: str
    file_name: str
    mime_type: str | None = None
    size_bytes: int
    sha256: str
    download_url: str | None = None
    encryption: dict | None = None


class MessageReference(BaseModel):
    id: uuid.UUID
    author_display_name: str | None = None
    excerpt: str | None = None
    created_at: datetime | None = None
    deleted: bool = False
    attachments: int | None = None
    stream_position: int | None = None
