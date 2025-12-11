from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models import NotificationChannel, NotificationPreference, UserAccount
from ..auth_service import quiet_hours_active
from .conversation_base import ConversationBase


class ConversationNotificationMixin(ConversationBase):
    """Notifications temps réel et push."""

    async def _broadcast_message_update(self, message) -> None:
        """Diffuse une mise a jour de message sur le canal temps reel."""
        if not self.realtime:
            return
        payload = await self.serialize_message(message)
        await self.realtime.publish_conversation(
            str(message.conversation_id),
            {
                "event": "message.updated",
                **payload,
            },
        )

    async def _filter_notification_targets(self, user_ids: list, *, now: datetime) -> list[str]:
        """Filtre les cibles push selon leurs preferences et plages de silence."""
        if not user_ids:
            return []
        normalized_ids = [uid for uid in dict.fromkeys(user_ids) if uid]
        if not normalized_ids:
            return []

        stmt_prefs = (
            select(NotificationPreference)
            .where(NotificationPreference.user_id.in_(normalized_ids))
            .where(NotificationPreference.channel == NotificationChannel.PUSH)
        )
        result_prefs = await self.session.execute(stmt_prefs)
        prefs = {pref.user_id: pref for pref in result_prefs.scalars().all()}

        stmt_profiles = (
            select(UserAccount)
            .options(selectinload(UserAccount.profile))
            .where(UserAccount.id.in_(normalized_ids))
        )
        result_profiles = await self.session.execute(stmt_profiles)
        profiles = {user.id: user.profile for user in result_profiles.scalars().all()}

        eligible: list[str] = []
        for uid in normalized_ids:
            pref = prefs.get(uid)
            profile = profiles.get(uid)
            if pref:
                if not pref.is_enabled:
                    continue
                if pref.quiet_hours and quiet_hours_active(pref.quiet_hours, now, profile):
                    continue
            eligible.append(str(uid))
        return eligible

    async def _push_message_notifications(
        self,
        *,
        conversation_id: str,
        payload: dict,
        author_id: str,
        member_user_ids: list,
        now: Optional[datetime] = None,
    ) -> None:
        """Envoie des notifications push aux membres eligibles (hors auteur), avec previsualisation."""
        if not self.realtime or not member_user_ids:
            return
        current_time = now or datetime.now(timezone.utc)
        target_user_ids = await self._filter_notification_targets(member_user_ids, now=current_time)
        if not target_user_ids:
            return
        preview = (payload.get("content") or "").strip()
        if not preview and payload.get("attachments"):
            preview = "Message contenant des pièces jointes."
        created_at = payload.get("created_at") or current_time.isoformat()
        message_id = payload.get("id")
        data = {
            "type": "message.received",
            "conversation_id": conversation_id,
            "message_id": message_id,
            "preview": preview,
            "sender": payload.get("author_display_name") or "Participant",
            "created_at": created_at,
            "author_id": author_id,
        }
        for user_id in target_user_ids:
            if user_id == author_id:
                continue
            await self.realtime.publish_user_event(
                user_id,
                {
                    "event": "notification",
                    "payload": data,
                },
            )
