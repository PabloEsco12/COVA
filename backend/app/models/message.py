"""
############################################################
# Modèles : Message (contenu, livraisons, interactions)
# Auteur : Valentin Masurelle
# Date   : 2025-05-04
#
# Description:
# - Messages chiffrés avec positions de flux et index full-text.
# - Livraisons par membre, reactions et pins uniques par combinaison.
# - Cascade delete sur livraisons/PJ/reactions pour éviter les orphelins.
############################################################
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    LargeBinary,
    String,
    Text,
    UniqueConstraint,
    Index,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .enums import MessageDeliveryState, MessageType

if TYPE_CHECKING:
    from .conversation import Conversation


class Message(Base):
    """Encrypted message stored in the system."""

    __tablename__ = "messages"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False
    )
    author_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("user_accounts.id", ondelete="SET NULL"), nullable=True
    )
    author_device_id: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("devices.id", ondelete="SET NULL"))
    type: Mapped[MessageType] = mapped_column(Enum(MessageType, name="message_type"), nullable=False, default=MessageType.TEXT)
    stream_position: Mapped[int] = mapped_column(Integer, nullable=False)
    ciphertext: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    encryption_scheme: Mapped[str] = mapped_column(String(32), nullable=False)
    encryption_metadata: Mapped[dict | None] = mapped_column(JSONB)
    signature: Mapped[bytes | None] = mapped_column(LargeBinary)
    search_text: Mapped[str | None] = mapped_column(Text)
    is_system: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    edited_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    deletion_reason: Mapped[str | None] = mapped_column(Text)
    reply_to_message_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("messages.id", ondelete="SET NULL")
    )
    forward_from_message_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("messages.id", ondelete="SET NULL")
    )

    conversation: Mapped["Conversation"] = relationship(back_populates="messages")
    author: Mapped["UserAccount | None"] = relationship(back_populates="sent_messages")
    deliveries: Mapped[list["MessageDelivery"]] = relationship(back_populates="message", cascade="all, delete-orphan")
    attachments: Mapped[list["MessageAttachment"]] = relationship(back_populates="message", cascade="all, delete-orphan")
    reactions: Mapped[list["MessageReaction"]] = relationship(back_populates="message", cascade="all, delete-orphan")
    pins: Mapped[list["MessagePin"]] = relationship(back_populates="message", cascade="all, delete-orphan")
    reply_to: Mapped["Message | None"] = relationship(
        "Message",
        remote_side="Message.id",
        foreign_keys=[reply_to_message_id],
        backref="replies",
    )
    forwarded_from: Mapped["Message | None"] = relationship(
        "Message",
        remote_side="Message.id",
        foreign_keys=[forward_from_message_id],
        backref="forwards",
    )

    __table_args__ = (
        UniqueConstraint("conversation_id", "stream_position", name="uix_message_stream"),
        Index("ix_messages_conversation_stream", "conversation_id", "stream_position"),
        Index("ix_messages_conversation_created", "conversation_id", "created_at"),
        Index(
            "ix_messages_fulltext",
            func.to_tsvector("simple", func.coalesce(func.convert_from(ciphertext, "UTF8"), "")),
            postgresql_using="gin",
        ),
        Index(
            "ix_messages_search_text",
            func.to_tsvector("simple", func.coalesce(search_text, "")),
            postgresql_using="gin",
        ),
    )


class MessageDelivery(Base):
    """Per-recipient delivery status."""

    __tablename__ = "message_deliveries"
    __table_args__ = (
        UniqueConstraint("message_id", "member_id", name="uix_message_delivery"),
    )

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    message_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("messages.id", ondelete="CASCADE"), nullable=False
    )
    member_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("conversation_members.id", ondelete="CASCADE"), nullable=False
    )
    state: Mapped[MessageDeliveryState] = mapped_column(
        Enum(MessageDeliveryState, name="message_delivery_state"), nullable=False, default=MessageDeliveryState.QUEUED
    )
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    failed_reason: Mapped[str | None] = mapped_column(Text)

    message = relationship("Message", back_populates="deliveries")
    member = relationship("ConversationMember")


class MessageAttachment(Base):
    """Encrypted attachment metadata."""

    __tablename__ = "message_attachments"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    message_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("messages.id", ondelete="CASCADE"), nullable=False
    )
    storage_url: Mapped[str] = mapped_column(Text, nullable=False)
    file_name: Mapped[str | None] = mapped_column(String(255))
    mime_type: Mapped[str | None] = mapped_column(String(128))
    size_bytes: Mapped[int | None] = mapped_column(Integer)
    sha256: Mapped[str | None] = mapped_column(String(64))
    encryption_info: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    message = relationship("Message", back_populates="attachments")


class MessageReaction(Base):
    """Emoji reaction to a message."""

    __tablename__ = "message_reactions"
    __table_args__ = (
        UniqueConstraint("message_id", "member_id", "emoji", name="uix_message_reaction"),
    )

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    message_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("messages.id", ondelete="CASCADE"), nullable=False
    )
    member_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("conversation_members.id", ondelete="CASCADE"), nullable=False
    )
    emoji: Mapped[str] = mapped_column(String(16), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    message = relationship("Message", back_populates="reactions")
    member = relationship("ConversationMember")


class MessagePin(Base):
    """Pinned message reference per conversation."""

    __tablename__ = "message_pins"
    __table_args__ = (
        UniqueConstraint("conversation_id", "message_id", name="uix_message_pin"),
    )

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False
    )
    message_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("messages.id", ondelete="CASCADE"), nullable=False
    )
    pinned_by: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("user_accounts.id", ondelete="SET NULL"))
    pinned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    conversation = relationship("Conversation")
    message = relationship("Message", back_populates="pins")
