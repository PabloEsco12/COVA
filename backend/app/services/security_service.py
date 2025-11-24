"""
############################################################
# Service : SecurityService (MFA/TOTP & preferences)
# Auteur  : Valentin Masurelle
# Date    : 2025-05-04
#
# Description:
# - Gere l'enrollement/confirmation/desactivation TOTP et les codes de secours.
# - Maintient l'etat de securite utilisateur (verrouillage, preferences).
# - Toutes les horodatations sont en UTC.
############################################################
"""

from __future__ import annotations

import base64
import io
import secrets
import string
from datetime import datetime, timedelta, timezone

import pyotp
import qrcode
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from .audit_service import AuditService
from app.models import (
    TotpSecret,
    UserAccount,
    UserProfile,
    UserSecurityState,
)


def _utcnow() -> datetime:
    """Wrapper pour obtenir maintenant en UTC (facilite les tests)."""
    return datetime.now(timezone.utc)


class SecurityService:
    """Encapsule les operations MFA/TOTP et preferences de securite d'un compte."""

    def __init__(self, session: AsyncSession, audit_service: AuditService | None = None) -> None:
        """Injecte la session async SQLAlchemy et le service d'audit optionnel."""
        self.session = session
        self.audit = audit_service

    async def get_security_snapshot(self, user: UserAccount) -> dict:
        """Retourne l'etat courant des protections (TOTP, alertes login, verrous)."""
        state = await self._ensure_security_state(user)
        profile = await self._ensure_profile(user)
        profile_data = dict(profile.profile_data or {})
        notify_login = bool(profile_data.get("notify_login"))
        return {
            "totp_enabled": bool(state.totp_enabled),
            "notification_login": notify_login,
            "last_totp_failure_at": state.last_totp_failure_at,
            "totp_locked_until": state.totp_locked_until,
            "has_recovery_codes": bool(state.recovery_codes),
        }

    async def update_security_preferences(self, user: UserAccount, *, notification_login: bool | None = None) -> dict:
        """Met a jour les preferences de securite (ex: alerte de connexion) puis renvoie l'etat."""
        state = await self._ensure_security_state(user)
        profile = await self._ensure_profile(user)
        profile_data = dict(profile.profile_data or {})

        updated_fields: list[str] = []

        if notification_login is not None:
            profile_data["notify_login"] = bool(notification_login)
            profile.profile_data = profile_data
            updated_fields.append("notify_login")

        if updated_fields:
            await self._log("security.preferences.update", user_id=str(user.id), metadata={"updated": updated_fields})
        await self.session.flush()
        return await self.get_security_snapshot(user)

    async def start_totp_enrollment(self, user: UserAccount) -> dict:
        """Demarre un enrollement TOTP en generant secret, URI et QR code base64."""
        state = await self._ensure_security_state(user)
        if state.totp_enabled and user.totp_secret and user.totp_secret.confirmed_at:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="TOTP already enabled – deactivate first.")

        secret_value = pyotp.random_base32()
        if user.totp_secret is None:
            user.totp_secret = TotpSecret(user_id=user.id, secret=secret_value)
            self.session.add(user.totp_secret)
        else:
            user.totp_secret.secret = secret_value
            user.totp_secret.confirmed_at = None

        state.totp_enabled = False
        state.failed_totp_attempts = 0
        state.totp_locked_until = None
        state.last_totp_failure_at = None
        await self.session.flush()

        provisioning_uri = pyotp.TOTP(secret_value).provisioning_uri(
            name=user.email,
            issuer_name=settings.PROJECT_NAME,
        )
        qr_png_b64 = self._generate_qr_base64(provisioning_uri)

        await self._log("security.totp.enrollment_started", user_id=str(user.id))
        return {
            "secret": secret_value,
            "provisioning_uri": provisioning_uri,
            "qr_code": qr_png_b64,
        }

    async def confirm_totp(self, user: UserAccount, code: str) -> list[str]:
        """Verifie le code TOTP saisi, active la MFA et genere des codes de secours."""
        state = await self._ensure_security_state(user)
        secret = user.totp_secret
        if secret is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No TOTP enrollment in progress.")

        totp = pyotp.TOTP(secret.secret)
        if not totp.verify(code, valid_window=1):
            await self._register_totp_failure(state)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid TOTP code.")

        secret.confirmed_at = _utcnow()
        state.totp_enabled = True
        state.failed_totp_attempts = 0
        state.totp_locked_until = None
        state.last_totp_failure_at = None

        recovery_codes = self._generate_recovery_codes()
        state.recovery_codes = recovery_codes

        await self._log("security.totp.activated", user_id=str(user.id))
        await self.session.flush()
        return recovery_codes

    async def deactivate_totp(self, user: UserAccount) -> None:
        """Desactive le TOTP et nettoie les secrets/codes stockes."""
        state = await self._ensure_security_state(user)
        secret = user.totp_secret
        if secret is None or not secret.confirmed_at:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="TOTP is not active.")

        await self.session.delete(secret)
        user.totp_secret = None

        state.totp_enabled = False
        state.recovery_codes = None
        state.failed_totp_attempts = 0
        state.last_totp_failure_at = None
        state.totp_locked_until = None

        await self._log("security.totp.deactivated", user_id=str(user.id))
        await self.session.flush()

    async def consume_recovery_code(self, user: UserAccount, code: str) -> bool:
        """Consomme un code de recuperation s'il est valide, retourne True si accepte."""
        state = await self._ensure_security_state(user)
        codes = state.recovery_codes or []
        if code not in codes:
            return False
        codes.remove(code)
        state.recovery_codes = codes or None
        await self._log("security.totp.recovery_code_used", user_id=str(user.id))
        await self.session.flush()
        return True

    async def _ensure_profile(self, user: UserAccount) -> UserProfile:
        """Cree un profil utilisateur si absent pour stocker les preferences de securite."""
        if user.profile is None:
            user.profile = UserProfile(user_id=user.id)
            self.session.add(user.profile)
            await self.session.flush()
        return user.profile

    async def _ensure_security_state(self, user: UserAccount) -> UserSecurityState:
        """S'assure que l'etat de securite existe pour l'utilisateur avant manipulation."""
        if user.security_state is None:
            user.security_state = UserSecurityState(user_id=user.id)
            self.session.add(user.security_state)
            await self.session.flush()
        return user.security_state

    async def _register_totp_failure(self, state: UserSecurityState) -> None:
        """Enregistre un echec TOTP et applique un verrouillage apres plusieurs tentatives."""
        state.failed_totp_attempts += 1
        state.last_totp_failure_at = _utcnow()
        if state.failed_totp_attempts >= 5:
            state.totp_locked_until = _utcnow() + timedelta(minutes=15)
            state.failed_totp_attempts = 0

    def _generate_qr_base64(self, provisioning_uri: str) -> str:
        """Genere une image QR code encodee en base64 a partir de l'URI TOTP."""
        qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_Q, border=2)
        qr.add_data(provisioning_uri)
        qr.make(fit=True)
        image = qr.make_image(fill_color="black", back_color="white")
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        return base64.b64encode(buffer.getvalue()).decode("ascii")

    def _generate_recovery_codes(self, count: int = 8) -> list[str]:
        """Cree une liste de codes de recuperation pseudo-aleatoires."""
        alphabet = string.ascii_uppercase + string.digits
        codes: list[str] = []
        for _ in range(count):
            chunk = "-".join("".join(secrets.choice(alphabet) for _ in range(4)) for _ in range(3))
            codes.append(chunk)
        return codes

    async def _log(self, action: str, **metadata) -> None:
        """Relais vers AuditService pour tracer les evenements de securite."""
        if not self.audit:
            return
        await self.audit.record(action, metadata=metadata)


__all__ = ["SecurityService"]


