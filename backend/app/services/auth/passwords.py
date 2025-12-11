from __future__ import annotations

from datetime import datetime, timedelta, timezone
from secrets import token_urlsafe

from fastapi import HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

from app.models import EmailConfirmationToken, NotificationChannel, PasswordResetToken, UserAccount
from ...core.security import get_password_hash
from .base import AuthBase


class AuthPasswordsMixin(AuthBase):
    """Reset/Résend tokens de confirmation et mots de passe."""

    async def resend_confirmation_email(self, email: str) -> str:
        """Génère un nouveau jeton de confirmation pour un email non confirmé et envoie la notification."""
        stmt = (
            select(UserAccount)
            .options(selectinload(UserAccount.profile))
            .where(UserAccount.email == email.lower())
        )
        result = await self.session.execute(stmt)
        user = result.scalar_one_or_none()
        if user is None:
            return ""
        if user.is_confirmed:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already confirmed")

        now = datetime.now(timezone.utc)
        await self.session.execute(
            update(EmailConfirmationToken)
            .where(EmailConfirmationToken.user_id == user.id, EmailConfirmationToken.consumed_at.is_(None))
            .values(consumed_at=now)
        )

        token_value = token_urlsafe(48)
        confirmation_token = EmailConfirmationToken(
            user_id=user.id,
            token=token_value,
            expires_at=now + timedelta(hours=24),
        )
        self.session.add(confirmation_token)
        await self.session.flush()

        if self.notifications:
            await self.notifications.enqueue_notification(
                organization_id=None,
                user_id=str(user.id),
                channel=NotificationChannel.EMAIL,
                payload={
                    "type": "email_confirmation",
                    "user_id": str(user.id),
                    "token": token_value,
                    "confirmation_path": f"/api/auth/confirm/{token_value}",
                },
            )
        await self._log("auth.resend_confirmation", user_id=str(user.id))
        return token_value

    async def request_password_reset(self, email: str) -> None:
        """Crée un jeton de réinitialisation de mot de passe et envoie l'email associé."""
        stmt = select(UserAccount).where(UserAccount.email == email.lower())
        result = await self.session.execute(stmt)
        user = result.scalar_one_or_none()
        now = datetime.now(timezone.utc)
        if user is None:
            await self._log("auth.forgot_password_requested", metadata={"email": email})
            return

        await self.session.execute(
            update(PasswordResetToken)
            .where(PasswordResetToken.user_id == user.id, PasswordResetToken.used_at.is_(None))
            .values(used_at=now)
        )

        token_value = token_urlsafe(32)
        reset_token = PasswordResetToken(
            user_id=user.id,
            token=token_value,
            expires_at=now + timedelta(hours=1),
        )
        self.session.add(reset_token)
        await self.session.flush()

        if self.notifications:
            await self.notifications.enqueue_notification(
                organization_id=None,
                user_id=str(user.id),
                channel=NotificationChannel.EMAIL,
                payload={
                    "type": "password_reset",
                    "user_id": str(user.id),
                    "token": token_value,
                    "reset_path": f"/new-password?token={token_value}",
                },
            )
        await self._log("auth.forgot_password_requested", user_id=str(user.id))

    async def reset_password(self, token_value: str, new_password: str) -> None:
        """Valide un token de réinitialisation puis applique le nouveau mot de passe."""
        stmt = (
            select(PasswordResetToken)
            .options(selectinload(PasswordResetToken.user))
            .where(PasswordResetToken.token == token_value)
        )
        result = await self.session.execute(stmt)
        token = result.scalar_one_or_none()
        if token is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Token not found")
        if token.used_at is not None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token already used")
        if token.expires_at < datetime.now(timezone.utc):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token expired")

        user = token.user
        if user is None or not user.is_active:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user")

        user.hashed_password = get_password_hash(new_password)
        user.failed_login_attempts = 0
        user.locked_until = None
        token.used_at = datetime.now(timezone.utc)

        await self.session.execute(
            update(PasswordResetToken)
            .where(
                PasswordResetToken.user_id == user.id,
                PasswordResetToken.used_at.is_(None),
                PasswordResetToken.id != token.id,
            )
            .values(used_at=datetime.now(timezone.utc))
        )

        await self._log("auth.reset_password", user_id=str(user.id))


__all__ = ["AuthPasswordsMixin"]
