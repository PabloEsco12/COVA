from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pyotp
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models import UserAccount
from ...core.security import verify_password
from .base import AuthBase
from .models import TotpRequiredError


class AuthTotpMixin(AuthBase):
    """Authentification et enforcement TOTP."""

    async def authenticate_user(self, email: str, password: str, totp_code: str | None = None) -> UserAccount:
        """Valide les identifiants et impose un challenge TOTP si nécessaire."""
        stmt = (
            select(UserAccount)
            .options(
                selectinload(UserAccount.profile),
                selectinload(UserAccount.security_state),
                selectinload(UserAccount.totp_secret),
                selectinload(UserAccount.notification_preferences),
            )
            .where(UserAccount.email == email.lower())
        )
        result = await self.session.execute(stmt)
        user = result.scalar_one_or_none()
        if user is None or not verify_password(password, user.hashed_password):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect credentials")
        if not user.is_active:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")
        if not user.is_confirmed:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Email not confirmed")

        await self._enforce_totp_if_required(user, totp_code)

        user.last_login_at = datetime.now(timezone.utc)
        await self._log("auth.login_attempt", user_id=str(user.id))
        return user

    async def _enforce_totp_if_required(self, user: UserAccount, totp_code: str | None) -> None:
        """Valide le TOTP si l'utilisateur l'a activé, avec verrouillage temporaire en cas d'échecs répétés."""
        state = await self._ensure_security_state(user)
        if not state.totp_enabled:
            return
        if not user.totp_secret or not user.totp_secret.confirmed_at:
            state.totp_enabled = False
            await self.session.flush()
            return
        now = datetime.now(timezone.utc)
        if state.totp_locked_until and state.totp_locked_until > now:
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail="TOTP temporarily locked after repeated failures. Please try again later.",
            )
        if not totp_code:
            raise TotpRequiredError()
        totp = pyotp.TOTP(user.totp_secret.secret)
        if not totp.verify(totp_code, valid_window=1):
            state.failed_totp_attempts += 1
            state.last_totp_failure_at = now
            if state.failed_totp_attempts >= 5:
                state.totp_locked_until = now + timedelta(minutes=15)
                state.failed_totp_attempts = 0
            await self.session.flush()
            await self._log("auth.totp_failure", user_id=str(user.id))
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid TOTP code")
        state.failed_totp_attempts = 0
        state.totp_locked_until = None
        state.last_totp_failure_at = None
        await self.session.flush()
        await self._log("auth.totp_success", user_id=str(user.id))


__all__ = ["AuthTotpMixin"]
