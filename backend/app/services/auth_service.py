"""
############################################################
# Service : AuthService (authentification & sessions)
# Auteur  : Valentin Masurelle
# Date    : 2025-05-04
#
# Description:
# - Gere l'inscription, la connexion, le rafraichissement et les controles TOTP.
# - Pilote les notifications (emails) et l'audit via services injectes.
# - Toutes les dates sont manipulees en UTC; lever des HTTPException cote routes.
#
# Points de vigilance:
# - Toujours commit/flush dans les routes après usage pour persister.
# - Respecter les verrous TOTP (locked_until) et les quiet hours de notifications.
# - Les tokens sont signes avec les secrets configurees dans settings.
#
# Dependances principales:
# - SQLAlchemy AsyncSession
# - AuditService, NotificationService
# - pyotp pour TOTP, security helpers pour hash/JWT
############################################################
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time, timedelta, timezone
import re
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
    OrganizationRole,
    PasswordResetToken,
    RefreshToken,
    SessionToken,
    UserAccount,
    UserProfile,
    UserRole,
    UserSecurityState,
    Workspace,
    WorkspaceMembership,
)

DEFAULT_TIMEZONE = "UTC"
DEFAULT_WORKSPACE_NAME = "General"
DEFAULT_WORKSPACE_SLUG = "general"

# ===============================
# Helpers techniques (IP, alertes)
# ===============================

def describe_ip(raw_ip: str) -> tuple[str, str | None]:
    """Decrit une adresse IP et retourne une etiquette lisible et une localisation approximative."""
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
    """Construit le payload d'alerte de connexion pour le canal email."""
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
    """Determine si une plage de silence est active en tenant compte du fuseau souhaite."""
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
    # Cas ou la plage deborde apres minuit (ex: 22h-06h).
    return local_time >= start_time or local_time < end_time


def should_send_login_alert(user: UserAccount, now_utc: datetime | None = None) -> bool:
    """Evalue si une alerte de connexion doit partir selon les preferences et horaires de silence."""
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


# ===============================
# DTO / resultats de service
# ===============================

@dataclass
class RegisterResult:
    """Resultat de l'inscription: utilisateur cree et jeton de confirmation eventuel."""
    user: UserAccount
    confirmation_token: str | None


@dataclass
class AuthResult:
    """Resultat d'authentification incluant tokens d'acces et de rafraichissement."""
    user: UserAccount
    access_token: str
    refresh_token: str
    refresh_expires_at: datetime


class TotpRequiredError(Exception):
    """Declenche un challenge TOTP obligatoire avant d'emettre de nouveaux tokens."""


# ===============================
# Service principal (AuthService)
# ===============================

class AuthService:
    """Gere l'inscription, l'authentification, les tokens et le cycle de vie des sessions."""

    def __init__(
        self,
        session: AsyncSession,
        *,
        audit_service: AuditService | None = None,
        notification_service: NotificationService | None = None,
    ) -> None:
        """Initialise le service avec la session SQLAlchemy et les services annexes."""
        self.session = session
        self.audit = audit_service
        self.notifications = notification_service

    # --- Flux d'inscription et connexion ---
    async def register_user(self, email: str, password: str, display_name: str | None = None) -> RegisterResult:
        """Cree un nouvel utilisateur, son organisation par defaut et envoie l'email de confirmation."""
        stmt = select(UserAccount).where(UserAccount.email == email.lower())
        result = await self.session.execute(stmt)
        if result.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="E-mail déjà utilisé")

        normalized_email = email.lower()
        hashed = get_password_hash(password)
        user = UserAccount(
            email=normalized_email,
            hashed_password=hashed,
            is_active=True,
            is_confirmed=False,
            role=UserRole.SUPERADMIN if self._is_default_admin_email(normalized_email) else UserRole.MEMBER,
        )
        user.profile = UserProfile(display_name=display_name)

        # Cree l'organisation et l'espace de travail de base si absents.
        organization, workspace = await self._ensure_default_organization()
        membership_role = OrganizationRole.OWNER if self._is_default_admin_email(normalized_email) else OrganizationRole.MEMBER
        membership = OrganizationMembership(organization=organization, user=user, role=membership_role)
        workspace_membership = WorkspaceMembership(workspace=workspace, membership=membership)
        membership.workspaces.append(workspace_membership)

        confirmation_token_value = token_urlsafe(48)
        confirmation_token = EmailConfirmationToken(
            user=user,
            token=confirmation_token_value,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
        )

        self.session.add_all([user, organization, workspace, membership, workspace_membership, confirmation_token])
        await self.session.flush()
        await self.session.refresh(user)

        await self._log("auth.register", user_id=str(user.id), organization_id=str(organization.id))
        if self.notifications:
            await self.notifications.enqueue_notification(
                organization_id=str(organization.id),
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
        """Valide les identifiants et impose un challenge TOTP si necessaire."""
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

    # --- Cycle de vie des tokens / sessions ---
    async def issue_tokens(
        self,
        user: UserAccount,
        *,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> AuthResult:
        """Cree une session, genere les tokens JWT et alerte l'utilisateur si necessaire."""
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
        """Invalide le refresh token fourni et recree un couple de tokens et une session."""
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
        """Revoque un refresh token et marque la session associee comme invalide."""
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
        """Revoque tous les tokens actifs d'un utilisateur et retourne le nombre de tokens touches."""
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
        """Genere un nouveau jeton de confirmation pour un email non confirme et envoie la notification."""
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
        """Cree un jeton de reinitialisation de mot de passe et envoie l'email associe."""
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
        """Valide un token de reinitialisation puis applique le nouveau mot de passe."""
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
        """Valide le TOTP si l'utilisateur l'a active, avec verrouillage temporaire en cas d'echecs repetes."""
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
                # Verrouille temporairement l'authentification apres plusieurs echecs consecutifs.
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
        """Planifie l'envoi d'une alerte de connexion si les preferences l'autorisent."""
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
    ) -> dict:
        """Assemble les donnees de l'alerte de connexion en injectant les preferences utilisateur."""
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
        """Garanti l'existence de l'etat de securite utilisateur avant utilisation."""
        if user.security_state is None:
            user.security_state = UserSecurityState(user_id=user.id)
            self.session.add(user.security_state)
            await self.session.flush()
        return user.security_state

    def _is_default_admin_email(self, email: str) -> bool:
        """Indique si l'adresse correspond a l'administrateur par defaut configure."""
        configured = (settings.DEFAULT_ADMIN_EMAIL or "").strip().lower()
        return bool(configured) and email.lower() == configured

    async def _ensure_default_organization(self) -> tuple[Organization, Workspace]:
        """Cree l'organisation et l'espace par defaut si ils n'existent pas, ou met a jour le nom si besoin."""
        name = (settings.DEFAULT_ORG_NAME or "Default Organization").strip()
        slug = self._slugify(settings.DEFAULT_ORG_SLUG or name or "default-org")

        org_stmt = select(Organization).where(Organization.slug == slug)
        org_result = await self.session.execute(org_stmt)
        organization = org_result.scalar_one_or_none()
        if organization is None:
            organization = Organization(name=name, slug=slug)
            self.session.add(organization)
            await self.session.flush()
        elif organization.name != name:
            organization.name = name
            await self.session.flush()

        ws_stmt = select(Workspace).where(
            Workspace.organization_id == organization.id,
            Workspace.slug == DEFAULT_WORKSPACE_SLUG,
        )
        ws_result = await self.session.execute(ws_stmt)
        workspace = ws_result.scalar_one_or_none()
        if workspace is None:
            workspace = Workspace(
                organization_id=organization.id,
                name=DEFAULT_WORKSPACE_NAME,
                slug=DEFAULT_WORKSPACE_SLUG,
            )
            self.session.add(workspace)
            await self.session.flush()
        return organization, workspace

    def _slugify(self, value: str) -> str:
        """Genere un slug URL-safe, ou un hash court si le resultat est vide."""
        slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
        return slug or uuid.uuid4().hex[:12]

    async def _log(self, action: str, **kwargs) -> None:
        """Delegue la journalisation a l'AuditService si disponible."""
        if self.audit:
            await self.audit.record(action, **kwargs)

    async def confirm_email(self, token_value: str) -> UserAccount:
        """Confirme l'email a partir d'un token valide et marque le compte comme confirme."""
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
