"""User ORM model."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Index, SmallInteger, String, Text, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Enum as SAEnum

from ..db.base import Base
from .enums import UserRole

if TYPE_CHECKING:
    from .auth import EmailConfirmationToken, PasswordResetToken, RefreshToken, TotpSecret, UserKeyPair
    from .contact import Contact
    from .conversation import ArchivedConversation, ConversationMember, Message, MessageAttachment, MessageReaction, MessageRead
    from .device import Device
    from .invitation import Invitation
    from .audit import AuditLog


class User(Base):
    __tablename__ = "users"
    __table_args__ = (Index("ix_users_email", "email", unique=True),)

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    hashed_password: Mapped[str] = mapped_column(Text, nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    role: Mapped[UserRole] = mapped_column(
        SAEnum(
            UserRole,
            name="user_role",
            values_callable=lambda enum_cls: [item.value for item in enum_cls],
            validate_strings=True,
        ),
        nullable=False,
        default=UserRole.MEMBER,
    )
    avatar_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    public_key: Mapped[str | None] = mapped_column(Text, nullable=True)
    notification_login: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_confirmed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    failed_totp_attempts: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)
    totp_locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Relationships
    conversation_members: Mapped[list["ConversationMember"]] = relationship(
        "ConversationMember",
        back_populates="user",
        foreign_keys="ConversationMember.user_id",
    )
    messages: Mapped[list["Message"]] = relationship("Message", back_populates="author")
    message_reads: Mapped[list["MessageRead"]] = relationship("MessageRead", back_populates="user")
    message_reactions: Mapped[list["MessageReaction"]] = relationship("MessageReaction", back_populates="user")
    message_attachments: Mapped[list["MessageAttachment"]] = relationship("MessageAttachment", back_populates="uploaded_by")
    archived_conversations: Mapped[list["ArchivedConversation"]] = relationship("ArchivedConversation", back_populates="user")
    devices: Mapped[list["Device"]] = relationship("Device", back_populates="user", cascade="all, delete-orphan")
    contacts: Mapped[list["Contact"]] = relationship(
        "Contact",
        back_populates="owner",
        cascade="all, delete-orphan",
        foreign_keys="Contact.owner_id",
    )
    contact_links: Mapped[list["Contact"]] = relationship(
        "Contact",
        foreign_keys="Contact.contact_id",
    )
    invitations_sent: Mapped[list["Invitation"]] = relationship("Invitation", back_populates="inviter")
    email_confirmation_tokens: Mapped[list["EmailConfirmationToken"]] = relationship(
        "EmailConfirmationToken",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(
        "RefreshToken",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    password_reset_tokens: Mapped[list["PasswordResetToken"]] = relationship(
        "PasswordResetToken",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    totp_secret: Mapped["TotpSecret | None"] = relationship(
        "TotpSecret",
        back_populates="user",
        cascade="all, delete-orphan",
        uselist=False,
    )
    key_pair: Mapped["UserKeyPair | None"] = relationship(
        "UserKeyPair",
        back_populates="user",
        cascade="all, delete-orphan",
        uselist=False,
    )
    audit_logs: Mapped[list["AuditLog"]] = relationship("AuditLog", back_populates="user")
