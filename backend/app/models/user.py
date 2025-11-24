"""
Modèles SQLAlchemy pour comptes utilisateurs, organisations et workspaces.

Infos utiles:
- UserAccount centralise authentification/role et relations (profil, sécurité, sessions).
- Organisations et workspaces possèdent des memberships avec contraintes d'unicité.
- Cascade delete configurée pour éviter les enregistrements orphelins sur de nombreuses relations.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .enums import OrganizationRole, UserRole

if TYPE_CHECKING:
    from .auth import EmailConfirmationToken, PasswordResetToken, RefreshToken, TotpSecret
    from .device import Device, SessionToken
    from .organization import Organization, OrganizationMembership
    from .conversation import ConversationMember
    from .message import Message
    from .notification import NotificationPreference
    from .privacy import PrivacyRequest
    from .audit import AuditLog


class UserAccount(Base):
    """Authentication and account level data."""

    __tablename__ = "user_accounts"
    __table_args__ = (
        Index("ix_user_accounts_email", "email", unique=True),
    )

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(320), nullable=False, unique=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole, name="user_role"), nullable=False, default=UserRole.MEMBER)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_confirmed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_login_ip: Mapped[str | None] = mapped_column(String(45))
    failed_login_attempts: Mapped[int] = mapped_column(default=0)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    profile: Mapped["UserProfile"] = relationship(back_populates="user", cascade="all, delete-orphan", uselist=False)
    security_state: Mapped["UserSecurityState"] = relationship(
        back_populates="user", cascade="all, delete-orphan", uselist=False
    )
    organizations: Mapped[list["OrganizationMembership"]] = relationship(back_populates="user")
    devices: Mapped[list["Device"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    sessions: Mapped[list["SessionToken"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    email_tokens: Mapped[list["EmailConfirmationToken"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    password_reset_tokens: Mapped[list["PasswordResetToken"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    totp_secret: Mapped["TotpSecret | None"] = relationship(
        back_populates="user", cascade="all, delete-orphan", uselist=False
    )
    conversation_memberships: Mapped[list["ConversationMember"]] = relationship(back_populates="user")
    sent_messages: Mapped[list["Message"]] = relationship(back_populates="author")
    notification_preferences: Mapped[list["NotificationPreference"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    privacy_requests: Mapped[list["PrivacyRequest"]] = relationship(back_populates="user")
    audit_logs: Mapped[list["AuditLog"]] = relationship(back_populates="user")


class UserProfile(Base):
    """Profile information separated from credentials."""

    __tablename__ = "user_profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("user_accounts.id", ondelete="CASCADE"), primary_key=True
    )
    display_name: Mapped[str | None] = mapped_column(String(120))
    avatar_url: Mapped[str | None] = mapped_column(Text)
    locale: Mapped[str | None] = mapped_column(String(16))
    timezone: Mapped[str | None] = mapped_column(String(64))
    profile_data: Mapped[dict | None] = mapped_column(JSONB)

    user: Mapped["UserAccount"] = relationship(back_populates="profile")


class UserSecurityState(Base):
    """Security posture per account (TOTP, recovery, anomalies)."""

    __tablename__ = "user_security_states"

    user_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("user_accounts.id", ondelete="CASCADE"), primary_key=True
    )
    totp_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    recovery_codes: Mapped[list[str] | None] = mapped_column(JSONB)
    last_totp_failure_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    failed_totp_attempts: Mapped[int] = mapped_column(default=0)
    totp_locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    user: Mapped["UserAccount"] = relationship(back_populates="security_state")


class Organization(Base):
    """Tenant organisation."""

    __tablename__ = "organizations"
    __table_args__ = (
        Index("ix_organizations_slug", "slug", unique=True),
    )

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    slug: Mapped[str] = mapped_column(String(96), nullable=False, unique=True)
    settings: Mapped[dict | None] = mapped_column(JSONB)
    retention_days: Mapped[int | None] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    members: Mapped[list["OrganizationMembership"]] = relationship(
        back_populates="organization", cascade="all, delete-orphan"
    )
    workspaces: Mapped[list["Workspace"]] = relationship(back_populates="organization", cascade="all, delete-orphan")
    conversations: Mapped[list["Conversation"]] = relationship(back_populates="organization")
    audit_logs: Mapped[list["AuditLog"]] = relationship(back_populates="organization")


class OrganizationMembership(Base):
    """Link between a user and an organisation."""

    __tablename__ = "organization_memberships"
    __table_args__ = (
        UniqueConstraint("organization_id", "user_id", name="uix_org_memberships_member"),
        Index("ix_org_memberships_user", "user_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("user_accounts.id", ondelete="CASCADE"), nullable=False
    )
    role: Mapped[OrganizationRole] = mapped_column(
        Enum(OrganizationRole, name="organization_role"), nullable=False, default=OrganizationRole.MEMBER
    )
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    invited_by: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True))

    organization: Mapped["Organization"] = relationship(back_populates="members")
    user: Mapped["UserAccount"] = relationship(back_populates="organizations")
    workspaces: Mapped[list["WorkspaceMembership"]] = relationship(back_populates="membership", cascade="all, delete-orphan")


class Workspace(Base):
    """Logical grouping of conversations inside an organisation."""

    __tablename__ = "workspaces"
    __table_args__ = (
        UniqueConstraint("organization_id", "slug", name="uix_workspaces_slug"),
    )

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    slug: Mapped[str] = mapped_column(String(96), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    organization: Mapped["Organization"] = relationship(back_populates="workspaces")
    memberships: Mapped[list["WorkspaceMembership"]] = relationship(
        back_populates="workspace", cascade="all, delete-orphan"
    )
    conversations: Mapped[list["Conversation"]] = relationship(back_populates="workspace")


class WorkspaceMembership(Base):
    """Membership by organisation member in a workspace."""

    __tablename__ = "workspace_memberships"
    __table_args__ = (
        UniqueConstraint("workspace_id", "membership_id", name="uix_workspace_member"),
    )

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False
    )
    membership_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("organization_memberships.id", ondelete="CASCADE"), nullable=False
    )
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    workspace: Mapped["Workspace"] = relationship(back_populates="memberships")
    membership: Mapped["OrganizationMembership"] = relationship(back_populates="workspaces")
