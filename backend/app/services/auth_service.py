"""Authentication service for FastAPI v2."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time, timedelta, timezone
import ipaddress
from secrets import token_urlsafe
import uuid
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

import pyotp

from ..config import settings
from ..core.security import create_access_token, get_password_hash, verify_password
from .audit_service import AuditService
from .notification_service import NotificationService
from ..core.redis import RealtimeBroker
from app.models import (
    EmailConfirmationToken,
    NotificationChannel,
    Organization,
    OrganizationMembership,
    PasswordResetToken,
    RefreshToken,
    SessionToken,
    UserAccount,
    UserProfile,
    UserSecurityState,
    Workspace,
    WorkspaceMembership,
)

DEFAULT_TIMEZONE = "UTC"


def describe_ip(raw_ip: str) -> tuple[str, str | None]:
    try:
        parsed = ipaddress.ip_address(raw_ip)
    except ValueError:
        return "Adresse non valide", None
    if parsed.is_loopback:
        return "Boucle locale", "Connexion locale"
    if parsed.is_private:
        return "Reseau prive ou VPN", "Localisation non disponible (adresse privee)"
    if parsed.is_reserved or parsed.is_unspecified:
        return "Adresse reservee", None
    return "Adresse publique", None


def build_login_alert_payload(
    *,
    user: UserAccount,
    session_id: str,
    login_time: datetime,
    ip_address: str | None,
    user_agent: str | None,
    timezone_pref: str | None = None,
) -> dict:
    frontend_origin = (settings.FRONTEND_ORIGIN or "").rstrip("/") or "http://localhost:5176"
    security_url = f"{frontend_origin}/dashboard/settings"
    devices_url = f"{frontend_origin}/dashboard/devices"
    reset_url = f"{frontend_origin}/reset-password"

    ip_value = ip_address or ""
    ip_label, location_hint = describe_ip(ip_value) if ip_value else ("Adresse inconnue", None)
    profile = user.profile
    tz_pref = timezone_pref or (profile.timezone if profile else None)

    return {
        "type": "security.login_alert",
        "login_time": login_time.astimezone(timezone.utc).isoformat(),
        "ip_address": ip_value,
        "ip_label": ip_label,
        "approx_location": location_hint,
        "user_agent": user_agent or "",
        "session_id": str(session_id),
        "timezone": tz_pref,
        "security_url": security_url,
        "devices_url": devices_url,
        "reset_url": reset_url,
        "display_name": profile.display_name if profile else None,
        "email": user.email,
    }


def quiet_hours_active(
    quiet_hours: dict,
    now_utc: datetime,
    profile: UserProfile | None,
) -> bool:
    start = (quiet_hours.get("start") or "").strip()
    end = (quiet_hours.get("end") or "").strip()
    if not start or not end or start == end:
        return False
    try:
        start_time = time.fromisoformat(start)
        end_time = time.fromisoformat(end)
    except ValueError:
        return False
    tz_name = (
        (quiet_hours.get("timezone") or "").strip()
        or (profile.timezone if profile and profile.timezone else None)
        or DEFAULT_TIMEZONE
    )
    try:
        zone = ZoneInfo(tz_name)
    except (ZoneInfoNotFoundError, ValueError):
        zone = timezone.utc
    local_time = now_utc.astimezone(zone).time()
    if start_time < end_time:
        return start_time <= local_time < end_time
    return local_time >= start_time or local_time < end_time


def should_send_login_alert(user: UserAccount, now_utc: datetime | None = None) -> bool:
    profile = user.profile
    profile_data = dict(profile.profile_data or {}) if profile and profile.profile_data else {}
    notify_login = bool(profile_data.get("notify_login"))
    if not notify_login:
        return False
    current = now_utc or datetime.now(timezone.utc)
    for pref in user.notification_preferences or []:
        if pref.channel != NotificationChannel.EMAIL:
            continue
        if not pref.is_enabled:
            return False
        if pref.quiet_hours and quiet_hours_active(pref.quiet_hours, current, profile):
            return False
    return True


@dataclass
class RegisterResult:
    user: UserAccount
    confirmation_token: str | None


@dataclass
class AuthResult:
    user: UserAccount
    access_token: str
    refresh_token: str
    refresh_expires_at: datetime


class TotpRequiredError(Exception):
    """Raised when a TOTP challenge must be completed before issuing tokens."""


class AuthService:
    """Handles registration, authentication, and session lifecycle."""

    def __init__(
        self,
        session: AsyncSession,
        *,
        audit_service: AuditService | None = None,
        notification_service: NotificationService | None = None,
    ) -> None:
        self.session = session
        self.audit = audit_service
        self.notifications = notification_service

    async def register_user(self, email: str, password: str, display_name: str | None = None) -> RegisterResult:
        stmt = select(UserAccount).where(UserAccount.email == email.lower())
        result = await self.session.execute(stmt)
        if result.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

        hashed = get_password_hash(password)
        user = UserAccount(
            email=email.lower(),
            hashed_password=hashed,
            is_active=True,
            is_confirmed=False,
        )
        user.profile = UserProfile(display_name=display_name)

        org = Organization(name=f"{display_name or email}'s Organization", slug=str(uuid.uuid4())[:12])
        membership = OrganizationMembership(organization=org, user=user)
        workspace = Workspace(organization=org, name="General", slug="general")
        workspace_membership = WorkspaceMembership(workspace=workspace, membership=membership)
        workspace.memberships.append(workspace_membership)

        confirmation_token_value = token_urlsafe(48)
        confirmation_token = EmailConfirmationToken(
            user=user,
            token=confirmation_token_value,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
        )

        self.session.add_all([user, org, workspace, confirmation_token])
        await self.session.flush()
        await self.session.refresh(user)

        await self._log("auth.register", user_id=str(user.id), organization_id=str(org.id))
        if self.notifications:
            await self.notifications.enqueue_notification(
                organization_id=str(org.id),
                user_id=str(user.id),
                channel=NotificationChannel.EMAIL,
                payload={
                    "type": "email_confirmation",
                    "user_id": str(user.id),
                    "token": confirmation_token_value,
                    "confirmation_path": f"/api/auth/confirm/{confirmation_token_value}",
                },
            )
        return RegisterResult(user=user, confirmation_token=confirmation_token_value)

    async def authenticate_user(self, email: str, password: str, totp_code: str | None = None) -> UserAccount:
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

    async def issue_tokens(
        self,
        user: UserAccount,
        *,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> AuthResult:
        now = datetime.now(timezone.utc)
        access_token = create_access_token({"sub": str(user.id)})
        refresh_token_value = token_urlsafe(24)
        refresh_expires = now + timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES)

        session_token = SessionToken(
            id=uuid.uuid4(),
            user_id=user.id,
            created_at=now,
            expires_at=refresh_expires,
            last_activity_at=now,
            ip_address=ip_address,
            user_agent=user_agent,
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
        )
        return AuthResult(user=user, access_token=access_token, refresh_token=refresh_token_value, refresh_expires_at=refresh_expires)

    async def refresh_session(self, refresh_token_value: str) -> AuthResult:
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

    async def revoke_all_tokens(self, user: UserAccount) -> int:
        now = datetime.now(timezone.utc)
        result = await self.session.execute(
            select(RefreshToken).where(RefreshToken.user_id == user.id, RefreshToken.revoked_at.is_(None))
        )
        tokens = result.scalars().all()
        for token in tokens:
            token.revoked_at = now
            if token.session_id is not None:
                await self.session.execute(
                    update(SessionToken)
                    .where(SessionToken.id == token.session_id)
                    .values(revoked_at=now)
                )
        await self._log("auth.logout_all", user_id=str(user.id), metadata={"revoked": len(tokens)})
        return len(tokens)

    async def resend_confirmation_email(self, email: str) -> str:
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

    async def _enforce_totp_if_required(self, user: UserAccount, totp_code: str | None) -> None:
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

    async def _queue_login_alert(
        self,
        user: UserAccount,
        *,
        session_token: SessionToken,
        login_time: datetime,
        ip_address: str | None,
        user_agent: str | None,
    ) -> None:
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
        )
        await self.notifications.enqueue_notification(
            organization_id=None,
            user_id=str(user.id),
            channel=NotificationChannel.EMAIL,
            payload=payload,
        )

    def _should_send_login_alert(self, user: UserAccount) -> bool:
        return should_send_login_alert(user)

    def _build_login_alert_payload(
        self,
        *,
        user: UserAccount,
        session_token: SessionToken,
        login_time: datetime,
        ip_address: str | None,
        user_agent: str | None,
    ) -> dict:
        profile = user.profile
        timezone_pref = profile.timezone if profile else None

        return build_login_alert_payload(
            user=user,
            session_id=str(session_token.id),
            login_time=login_time,
            ip_address=ip_address,
            user_agent=user_agent,
            timezone_pref=timezone_pref,
        )

    async def _ensure_security_state(self, user: UserAccount) -> UserSecurityState:
        if user.security_state is None:
            user.security_state = UserSecurityState(user_id=user.id)
            self.session.add(user.security_state)
            await self.session.flush()
        return user.security_state

    async def _log(self, action: str, **kwargs) -> None:
        if self.audit:
            await self.audit.record(action, **kwargs)

    async def confirm_email(self, token_value: str) -> UserAccount:
        stmt = (
            select(EmailConfirmationToken)
            .options(selectinload(EmailConfirmationToken.user).selectinload(UserAccount.profile))
            .where(EmailConfirmationToken.token == token_value)
        )
        result = await self.session.execute(stmt)
        token = result.scalar_one_or_none()
        if token is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Token not found")
        if token.consumed_at is not None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token already used")
        if token.expires_at < datetime.now(timezone.utc):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token expired")
        user = token.user
        if user is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Associated user missing")
        user.is_confirmed = True
        token.consumed_at = datetime.now(timezone.utc)
        await self._log("auth.confirm_email", user_id=str(user.id))
        return user
