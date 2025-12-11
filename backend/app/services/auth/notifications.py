from __future__ import annotations

from datetime import datetime

from app.models import NotificationChannel, SessionToken, UserAccount
from .base import AuthBase
from .helpers import build_login_alert_payload, should_send_login_alert


class AuthNotificationMixin(AuthBase):
    """Gestion des notifications d'alerte de connexion."""

    async def _queue_login_alert(
        self,
        user: UserAccount,
        *,
        session_token: SessionToken,
        login_time: datetime,
        ip_address: str | None,
        user_agent: str | None,
        timezone_pref: str | None = None,
    ) -> None:
        """Planifie l'envoi d'une alerte de connexion si les préférences l'autorisent."""
        if not self.notifications:
            return
        if not self._should_send_login_alert(user):
            return

        payload = self._build_login_alert_payload(
            user=user,
            session_token=session_token,
            login_time=login_time,
            ip_address=ip_address,
            user_agent=user_agent,
            timezone_pref=timezone_pref,
        )
        await self.notifications.enqueue_notification(
            organization_id=None,
            user_id=str(user.id),
            channel=NotificationChannel.EMAIL,
            payload=payload,
        )

    def _should_send_login_alert(self, user: UserAccount) -> bool:
        """Wrapper injectable pour faciliter les tests de la logique d'alerte de connexion."""
        return should_send_login_alert(user)

    def _build_login_alert_payload(
        self,
        *,
        user: UserAccount,
        session_token: SessionToken,
        login_time: datetime,
        ip_address: str | None,
        user_agent: str | None,
        timezone_pref: str | None = None,
    ) -> dict:
        """Assemble les données de l'alerte de connexion en injectant les préférences utilisateur."""
        profile = user.profile
        timezone_pref = timezone_pref or (profile.timezone if profile else None)

        return build_login_alert_payload(
            user=user,
            session_id=str(session_token.id),
            login_time=login_time,
            ip_address=ip_address,
            user_agent=user_agent,
            timezone_pref=timezone_pref,
        )


__all__ = ["AuthNotificationMixin"]
