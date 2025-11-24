"""
Schemas Pydantic pour preferences et notifications sortantes.

Infos utiles:
- from_attributes actif pour hydrater depuis les entites SQLAlchemy.
- Couvre la mise a jour des preferences (quiet hours) et la lecture d'envois pending/envoyes.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.models import NotificationChannel


class NotificationPreferenceOut(BaseModel):
    """Preference utilisateur pour un canal de notification."""
    channel: NotificationChannel
    is_enabled: bool
    quiet_hours: dict | None = None

    class Config:
        from_attributes = True


class NotificationPreferenceUpdate(BaseModel):
    """Payload de mise a jour des preferences (activation + plages de silence)."""
    is_enabled: bool
    quiet_hours: dict | None = None


class OutboundNotificationOut(BaseModel):
    """Notification en file d'attente ou envoyee, exposee par l'API."""
    id: UUID
    channel: NotificationChannel
    payload: dict
    status: str
    scheduled_at: datetime

    class Config:
        from_attributes = True


class NotificationTestResponse(BaseModel):
    """Retour d'un test de notification (mode simulation)."""
    skipped: bool
    detail: str
    notification: OutboundNotificationOut | None = None
