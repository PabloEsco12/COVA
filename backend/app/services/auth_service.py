"""Authentication domain service."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from uuid import UUID

import sqlalchemy as sa
from fastapi import HTTPException, status
from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

import pyotp

from ..core.config import settings
from ..core.security import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    generate_jti,
    generate_token,
    hash_token,
)
from ..models.auth import EmailConfirmationToken, RefreshToken, TotpSecret
from ..models.enums import UserRole
from ..models.user import User
from ..schemas import LoginRequest, RegisterRequest
from .email_service import EmailService
from .user_service import UserService


@dataclass(slots=True)
class LoginContext:
    ip_address: str | None = None
    user_agent: str | None = None
    device_name: str | None = None
    device_platform: str | None = None


class AuthService:
    """High-level authentication orchestration (registration, tokens, TOTP)."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.user_service = UserService(session)
        self.email_service = EmailService()

    async def register_user(self, payload: RegisterRequest, *, role: UserRole = UserRole.MEMBER) -> tuple[User, str]:
        async with self.session.begin():
            user = await self.user_service.create_user(
                email=payload.email,
                password=payload.password,
                display_name=payload.display_name,
                notification_login=payload.notification_login or False,
                role=role,
                is_active=True,
                is_confirmed=False,
            )
            token_value = generate_token()
            token = EmailConfirmationToken(
                user_id=user.id,
                token=hash_token(token_value),
                expires_at=datetime.now(timezone.utc) + timedelta(hours=settings.EMAIL_CONFIRMATION_EXPIRY_HOURS),
            )
            self.session.add(token)
        return user, token_value

    async def send_confirmation_email(self, user: User, token_value: str) -> bool:
        confirm_link = f"{settings.FRONTEND_URL.rstrip('/')}/confirm-email/{token_value}"
        return await self.email_service.send_email_confirmation(user.email, confirm_link, user.display_name)

    async def confirm_email(self, token_value: str) -> User:
        hashed = hash_token(token_value)
        stmt: Select[tuple[EmailConfirmationToken]] = select(EmailConfirmationToken).where(
            EmailConfirmationToken.token == hashed,
            EmailConfirmationToken.consumed_at.is_(None),
        )
        result = await self.session.execute(stmt)
        token = result.scalar_one_or_none()
        if token is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token invalide ou expiré")
        if token.expires_at < datetime.now(timezone.utc):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token invalide ou expiré")

        user = await self.user_service.get_by_id(token.user_id)
        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilisateur introuvable")

        async with self.session.begin():
            token.consumed_at = datetime.now(timezone.utc)
            await self.user_service.mark_email_confirmed(user)

        return user

    async def login(self, payload: LoginRequest, context: LoginContext) -> tuple[User, str, str, str]:
        user = await self.user_service.authenticate(payload.email, payload.password)
        if user is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Identifiants invalides")

        now = datetime.now(timezone.utc)
        if user.totp_locked_until and user.totp_locked_until > now:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Compte verrouillé suite à trop de tentatives TOTP",
            )
        if not user.is_confirmed:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Compte non confirmé.")
        if not user.is_active:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Compte désactivé.")

        totp_secret = await self._get_totp_secret(user.id)
        if totp_secret and totp_secret.confirmed_at:
            if not payload.totp_code:
                await self.user_service.record_totp_failure(user)
                await self.session.commit()
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Code TOTP requis",
                )
            totp = pyotp.TOTP(totp_secret.secret)
            if not totp.verify(payload.totp_code, valid_window=1):
                await self.user_service.record_totp_failure(user)
                await self.session.commit()
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Code TOTP invalide")
            await self.user_service.reset_totp_failures(user)

        async with self.session.begin():
            access_token, refresh_token, jti = await self._issue_tokens(user, context)

        if user.notification_login:
            await self.email_service.send_login_notification(
                user.email,
                ip_address=context.ip_address,
                user_agent=context.user_agent,
                timestamp=datetime.now(timezone.utc).isoformat(),
            )

        return user, access_token, refresh_token, jti

    async def refresh_session(self, refresh_token_value: str, context: LoginContext) -> tuple[User, str, str, str]:
        user_id, jti = decode_refresh_token(refresh_token_value)
        stmt = select(RefreshToken).where(RefreshToken.token_jti == jti)
        result = await self.session.execute(stmt)
        token = result.scalar_one_or_none()
        if token is None or token.revoked_at is not None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token invalide")
        if token.expires_at < datetime.now(timezone.utc):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token expiré")

        user = await self.user_service.get_by_id(user_id)
        if user is None or not user.is_active:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Utilisateur invalide")

        async with self.session.begin():
            token.revoked_at = datetime.now(timezone.utc)
            access_token, new_refresh_token, new_jti = await self._issue_tokens(user, context)
        return user, access_token, new_refresh_token, new_jti

    async def revoke_refresh_token(self, jti: str) -> None:
        async with self.session.begin():
            stmt = (
                sa.update(RefreshToken)
                .where(RefreshToken.token_jti == jti, RefreshToken.revoked_at.is_(None))
                .values(revoked_at=datetime.now(timezone.utc))
            )
            await self.session.execute(stmt)

    async def revoke_all_tokens(self, user_id: UUID) -> int:
        async with self.session.begin():
            stmt = (
                sa.update(RefreshToken)
                .where(RefreshToken.user_id == user_id, RefreshToken.revoked_at.is_(None))
                .values(revoked_at=datetime.now(timezone.utc))
                .returning(RefreshToken.token_jti)
            )
            result = await self.session.execute(stmt)
            rows = result.fetchall()
        return len(rows)

    async def _issue_tokens(self, user: User, context: LoginContext) -> tuple[str, str, str]:
        access_token = create_access_token(user.id)
        jti = generate_jti()
        refresh_token = create_refresh_token(user.id, jti=jti)

        refresh = RefreshToken(
            user_id=user.id,
            token_jti=jti,
            user_agent=context.user_agent,
            ip_address=context.ip_address,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES),
        )
        self.session.add(refresh)
        await self.session.flush()
        return access_token, refresh_token, jti

    async def _get_totp_secret(self, user_id: UUID) -> TotpSecret | None:
        stmt = select(TotpSecret).where(TotpSecret.user_id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
