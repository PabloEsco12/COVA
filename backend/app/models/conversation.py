"""Conversation and membership related models."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    LargeBinary,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .enums import ConversationMemberRole, ConversationType, MembershipState

if TYPE_CHECKING:
    from .message import Message


class Conversation(Base):
    """Discussion channel (direct, group, broadcast)."""

    __tablename__ = "conversations"
    __table_args__ = (
        Index("ix_conversations_org", "organization_id"),
        Index("ix_conversations_workspace", "workspace_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    workspace_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="SET NULL")
    )
    created_by: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("user_accounts.id", ondelete="SET NULL"))
    title: Mapped[str | None] = mapped_column(String(160))
    topic: Mapped[str | None] = mapped_column(Text)
    type: Mapped[ConversationType] = mapped_column(
        Enum(ConversationType, name="conversation_type"), nullable=False, default=ConversationType.DIRECT
    )
    is_encrypted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    retention_days_override: Mapped[int | None] = mapped_column(Integer)
    slow_mode_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    allow_attachments: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    allow_replies: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    extra_metadata: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    organization = relationship("Organization", back_populates="conversations")
    workspace = relationship("Workspace", back_populates="conversations")
    members = relationship("ConversationMember", back_populates="conversation", cascade="all, delete-orphan")
    keys = relationship("ConversationEncryptionKey", back_populates="conversation", cascade="all, delete-orphan")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    calls = relationship("CallSession", back_populates="conversation", cascade="all, delete-orphan")


class ConversationMember(Base):
    """Member of a conversation with a specific role and state."""

    __tablename__ = "conversation_members"
    __table_args__ = (
        UniqueConstraint("conversation_id", "user_id", name="uix_conversation_member"),
        Index("ix_conversation_members_user", "user_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("user_accounts.id", ondelete="CASCADE"), nullable=False
    )
    role: Mapped[ConversationMemberRole] = mapped_column(
        Enum(ConversationMemberRole, name="conversation_member_role"), nullable=False, default=ConversationMemberRole.MEMBER
    )
    state: Mapped[MembershipState] = mapped_column(
        Enum(MembershipState, name="conversation_membership_state"), nullable=False, default=MembershipState.ACTIVE
    )
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    invited_by: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True))
    muted_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_read_message_id: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True))

    conversation = relationship("Conversation", back_populates="members")
    user = relationship("UserAccount", back_populates="conversation_memberships")
    key_wraps = relationship("MemberKeyWrap", back_populates="member", cascade="all, delete-orphan")


class ConversationEncryptionKey(Base):
    """Master encryption key (rotated) for a conversation."""

    __tablename__ = "conversation_encryption_keys"
    __table_args__ = (
        UniqueConstraint("conversation_id", "generation", name="uix_conversation_key_generation"),
    )

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False
    )
    generation: Mapped[int] = mapped_column(Integer, nullable=False)
    encrypted_key: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    key_algo: Mapped[str] = mapped_column(String(32), nullable=False)
    created_by: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    rotated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    conversation = relationship("Conversation", back_populates="keys")
    member_key_wraps = relationship("MemberKeyWrap", back_populates="conversation_key", cascade="all, delete-orphan")


class MemberKeyWrap(Base):
    """Encrypted key material for one member and key generation."""

    __tablename__ = "member_key_wraps"
    __table_args__ = (
        UniqueConstraint("conversation_key_id", "member_id", name="uix_member_key_wrap"),
    )

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_key_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("conversation_encryption_keys.id", ondelete="CASCADE"), nullable=False
    )
    member_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("conversation_members.id", ondelete="CASCADE"), nullable=False
    )
    encrypted_key: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    wrapped_with: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    rotated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    conversation_key = relationship("ConversationEncryptionKey", back_populates="member_key_wraps")
    member = relationship("ConversationMember", back_populates="key_wraps")


class ConversationInvite(Base):
    """Invitation token for external users to join a conversation."""

    __tablename__ = "conversation_invites"
    __table_args__ = (
        UniqueConstraint("token", name="uix_conversation_invite_token"),
    )

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False
    )
    email: Mapped[str] = mapped_column(String(320), nullable=False)
    role: Mapped[ConversationMemberRole] = mapped_column(
        Enum(ConversationMemberRole, name="invite_role"), nullable=False, default=ConversationMemberRole.MEMBER
    )
    token: Mapped[str] = mapped_column(String(160), nullable=False)
    invited_by: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    conversation = relationship("Conversation")


class CallSession(Base):
    """Real-time audio/video call associated with a conversation."""

    __tablename__ = "call_sessions"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False
    )
    initiator_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("user_accounts.id", ondelete="SET NULL"))
    call_type: Mapped[str] = mapped_column(String(16), nullable=False)
    room_name: Mapped[str] = mapped_column(String(160), nullable=False)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    call_metadata: Mapped[dict | None] = mapped_column(JSONB)

    conversation = relationship("Conversation", back_populates="calls")
    participants = relationship("CallParticipant", back_populates="call", cascade="all, delete-orphan")


class CallParticipant(Base):
    """Participation of a user/device in a call session."""

    __tablename__ = "call_participants"
    __table_args__ = (
        UniqueConstraint("call_id", "member_id", name="uix_call_participant"),
    )

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    call_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("call_sessions.id", ondelete="CASCADE"), nullable=False
    )
    member_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("conversation_members.id", ondelete="CASCADE"), nullable=False
    )
    device_id: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("devices.id", ondelete="SET NULL"))
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    left_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    metrics: Mapped[dict | None] = mapped_column(JSONB)

    call = relationship("CallSession", back_populates="participants")
    member = relationship("ConversationMember")
