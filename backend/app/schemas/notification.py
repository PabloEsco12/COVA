"""Notification schemas."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.models import NotificationChannel


class NotificationPreferenceOut(BaseModel):
    channel: NotificationChannel
    is_enabled: bool
    quiet_hours: dict | None = None

    class Config:
        from_attributes = True


class NotificationPreferenceUpdate(BaseModel):
    is_enabled: bool
    quiet_hours: dict | None = None


class OutboundNotificationOut(BaseModel):
    id: UUID
    channel: NotificationChannel
    payload: dict
    status: str
    scheduled_at: datetime

    class Config:
        from_attributes = True


class NotificationTestResponse(BaseModel):
    skipped: bool
    detail: str
    notification: OutboundNotificationOut | None = None
