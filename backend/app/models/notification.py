"""
############################################################
# Modèles : Notifications (preferences & outbox)
# Auteur : Valentin Masurelle
# Date   : 2025-05-04
#
# Description:
# - Preferences par canal avec quiet hours (JSONB).
# - OutboundNotification pour file d'attente/traitement des envois.
############################################################
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .enums import NotificationChannel


class NotificationPreference(Base):
    """Preferences de notification au niveau utilisateur."""

    __tablename__ = "notification_preferences"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("user_accounts.id", ondelete="CASCADE"), nullable=False
    )
    channel: Mapped[NotificationChannel] = mapped_column(Enum(NotificationChannel, name="notification_channel"), nullable=False)
    is_enabled: Mapped[bool] = mapped_column(default=True)
    quiet_hours: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    user = relationship("UserAccount", back_populates="notification_preferences")


class OutboundNotification(Base):
    """Notification en file d'attente pour envoi."""

    __tablename__ = "outbound_notifications"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("organizations.id", ondelete="SET NULL"))
    user_id: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("user_accounts.id", ondelete="SET NULL"))
    channel: Mapped[NotificationChannel] = mapped_column(Enum(NotificationChannel, name="notification_channel"), nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_error: Mapped[str | None] = mapped_column(Text)
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")

    organization = relationship("Organization")
    user = relationship("UserAccount")
