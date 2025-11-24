"""
############################################################
# Modèles : Device & Sessions
# Auteur : Valentin Masurelle
# Date   : 2025-05-04
#
# Description:
# - Appareils identifies par fingerprint (unique par user).
# - Sessions stockant JTI tokens et metadonnees d'activité.
# - Abonnements push uniques par device/endpoint.
############################################################
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .enums import NotificationChannel


class Device(Base):
    """Registered device for a user."""

    __tablename__ = "devices"
    __table_args__ = (
        UniqueConstraint("user_id", "fingerprint", name="uix_devices_fingerprint"),
    )

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("user_accounts.id", ondelete="CASCADE"), nullable=False
    )
    display_name: Mapped[str | None] = mapped_column(String(120))
    platform: Mapped[str | None] = mapped_column(String(32))
    fingerprint: Mapped[str | None] = mapped_column(String(128))
    public_key: Mapped[str | None] = mapped_column(Text)
    trust_level: Mapped[int] = mapped_column(default=0)
    registered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_seen_ip: Mapped[str | None] = mapped_column(String(45))
    device_metadata: Mapped[dict | None] = mapped_column(JSONB)

    user = relationship("UserAccount", back_populates="devices")
    sessions = relationship("SessionToken", back_populates="device", cascade="all, delete-orphan")


class SessionToken(Base):
    """Active login session, linked to a device when available."""

    __tablename__ = "session_tokens"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("user_accounts.id", ondelete="CASCADE"), nullable=False
    )
    device_id: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("devices.id", ondelete="SET NULL"))
    access_token_jti: Mapped[str | None] = mapped_column(String(36))
    refresh_token_jti: Mapped[str | None] = mapped_column(String(36))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_activity_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ip_address: Mapped[str | None] = mapped_column(String(45))
    user_agent: Mapped[str | None] = mapped_column(Text)

    user = relationship("UserAccount", back_populates="sessions")
    device = relationship("Device", back_populates="sessions")


class PushSubscription(Base):
    """Web push subscription per device."""

    __tablename__ = "push_subscriptions"
    __table_args__ = (
        UniqueConstraint("device_id", "endpoint", name="uix_push_subscription"),
    )

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    device_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("devices.id", ondelete="CASCADE"), nullable=False
    )
    channel: Mapped[NotificationChannel] = mapped_column(Enum(NotificationChannel, name="notification_channel"))
    endpoint: Mapped[str] = mapped_column(Text, nullable=False)
    p256dh: Mapped[str | None] = mapped_column(Text)
    auth_secret: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    last_error_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    device = relationship("Device")
