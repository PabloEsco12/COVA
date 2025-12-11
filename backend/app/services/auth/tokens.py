from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from secrets import token_urlsafe

from fastapi import HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

from app.models import NotificationChannel, RefreshToken, SessionToken, UserAccount
from ...config import settings
from ...core.security import create_access_token
from .base import AuthBase
from .models import AuthResult


class AuthTokensMixin(AuthBase):
    """Cycle de vie des tokens / sessions."""

    async def issue_tokens(
        self,
        user: UserAccount,
        *,
        user_agent: str | None = None,
        ip_address: str | None = None,
        timezone_pref: str | None = None,
    ) -> AuthResult:
        """Crée une session, génère les tokens JWT et alerte l'utilisateur si nécessaire."""
        now = datetime.now(timezone.utc)
        session_id = uuid.uuid4()
        access_token = create_access_token({"sub": str(user.id), "sid": str(session_id)})
        refresh_token_value = token_urlsafe(24)
        refresh_expires = now + timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES)

        session_token = SessionToken(
            id=session_id,
            user_id=user.id,
            created_at=now,
            expires_at=refresh_expires,
            last_activity_at=now,
            ip_address=ip_address,
            user_agent=user_agent,
            access_token_jti=str(session_id),
            refresh_token_jti=refresh_token_value,
        )
        refresh_token = RefreshToken(
            token_jti=refresh_token_value,
            user_id=user.id,
            session_id=session_token.id,
            expires_at=refresh_expires,
            created_at=now,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        user.last_login_at = now
        if ip_address:
            user.last_login_ip = ip_address

        self.session.add_all([session_token, refresh_token])
        await self.session.flush()
        await self.session.refresh(user)

        await self._log(
            "auth.issue_tokens",
            user_id=str(user.id),
            metadata={"session_id": str(session_token.id)},
        )

        await self._queue_login_alert(
            user,
            session_token=session_token,
            login_time=now,
            ip_address=ip_address,
            user_agent=user_agent,
            timezone_pref=timezone_pref,
        )
        return AuthResult(user=user, access_token=access_token, refresh_token=refresh_token_value, refresh_expires_at=refresh_expires)

    async def refresh_session(self, refresh_token_value: str) -> AuthResult:
        """Invalide le refresh token fourni et recrée un couple de tokens et une session."""
        stmt = (
            select(RefreshToken)
            .options(selectinload(RefreshToken.user).selectinload(UserAccount.profile))
            .where(RefreshToken.token_jti == refresh_token_value)
        )
        result = await self.session.execute(stmt)
        token = result.scalar_one_or_none()
        if token is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
        if token.revoked_at is not None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token revoked")
        if token.expires_at < datetime.now(timezone.utc):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token expired")

        user = token.user
        if user is None or not user.is_active:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user")

        token.revoked_at = datetime.now(timezone.utc)
        if token.session_id is not None:
            await self.session.execute(
                update(SessionToken)
                .where(SessionToken.id == token.session_id)
                .values(revoked_at=datetime.now(timezone.utc), refresh_token_jti=None)
            )

        auth_result = await self.issue_tokens(user, user_agent=token.user_agent, ip_address=token.ip_address)
        await self._log("auth.refresh", user_id=str(user.id), metadata={"old_session": token.session_id})
        return auth_result

    async def revoke_refresh_token(self, refresh_token_value: str) -> None:
        """Révoque un refresh token et marque la session associée comme invalide."""
        stmt = select(RefreshToken).where(RefreshToken.token_jti == refresh_token_value)
        result = await self.session.execute(stmt)
        token = result.scalar_one_or_none()
        if token is None:
            return
        now = datetime.now(timezone.utc)
        if token.revoked_at is None:
            token.revoked_at = now
        if token.session_id is not None:
            await self.session.execute(
                update(SessionToken)
                .where(SessionToken.id == token.session_id)
                .values(revoked_at=now)
            )
        await self._log("auth.logout", user_id=str(token.user_id), metadata={"session_id": token.session_id})

    async def revoke_all_tokens(self, user: UserAccount, keep_session_id: uuid.UUID | None = None) -> int:
        """Revoque tous les tokens actifs d'un utilisateur et retourne le nombre de tokens touchés."""
        now = datetime.now(timezone.utc)
        result = await self.session.execute(
            select(RefreshToken).where(RefreshToken.user_id == user.id, RefreshToken.revoked_at.is_(None))
        )
        tokens = result.scalars().all()
        revoked_count = 0
        for token in tokens:
            if keep_session_id and token.session_id == keep_session_id:
                continue
            token.revoked_at = now
            revoked_count += 1
            if token.session_id is not None:
                await self.session.execute(
                    update(SessionToken)
                    .where(SessionToken.id == token.session_id)
                    .values(revoked_at=now)
                )
        await self._log("auth.logout_all", user_id=str(user.id), metadata={"revoked": revoked_count})
        return revoked_count


__all__ = ["AuthTokensMixin"]
