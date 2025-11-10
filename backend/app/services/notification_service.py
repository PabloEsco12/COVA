"""Notification service."""

from __future__ import annotations

from datetime import datetime, timezone
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import NotificationChannel, NotificationPreference, OutboundNotification, UserAccount


class NotificationService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_preferences(self, user: UserAccount) -> list[NotificationPreference]:
        stmt = select(NotificationPreference).where(NotificationPreference.user_id == user.id)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def upsert_preference(
        self,
        user: UserAccount,
        channel: NotificationChannel,
        *,
        is_enabled: bool,
        quiet_hours: dict | None,
    ) -> NotificationPreference:
        stmt = select(NotificationPreference).where(
            NotificationPreference.user_id == user.id,
            NotificationPreference.channel == channel,
        )
        result = await self.session.execute(stmt)
        preference = result.scalar_one_or_none()
        if preference is None:
            preference = NotificationPreference(user_id=user.id, channel=channel)
            self.session.add(preference)
        preference.is_enabled = is_enabled
        preference.quiet_hours = quiet_hours
        await self.session.flush()
        return preference

    async def enqueue_notification(
        self,
        *,
        organization_id: str | None,
        user_id: str | None,
        channel: NotificationChannel,
        payload: dict,
        schedule_at: datetime | None = None,
    ) -> OutboundNotification:
        notification = OutboundNotification(
            organization_id=uuid.UUID(organization_id) if organization_id else None,
            user_id=uuid.UUID(user_id) if user_id else None,
            channel=channel,
            payload=payload,
            scheduled_at=schedule_at or datetime.now(timezone.utc),
            status="pending",
        )
        self.session.add(notification)
        await self.session.flush()
        return notification
