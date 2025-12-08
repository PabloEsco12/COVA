"""
############################################################
# Service : DeviceService (appareils & sessions)
# Auteur  : Valentin Masurelle
# Date    : 2025-05-04
#
# Description:
# - Inscription/synchronisation des appareils et mise a jour des sessions associees.
# - Decode les metadonnees base64 (push_token) et derive un trust_level.
# - Audit optionnel via AuditService.
############################################################
"""

from __future__ import annotations

import base64
import json
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Device, SessionToken, UserAccount
from .audit_service import AuditService


class DeviceService:
    """Encapsule le cycle de vie des appareils et leurs sessions associees."""

    def __init__(self, session: AsyncSession, audit_service: AuditService | None = None) -> None:
        """Injecte la session SQLAlchemy et le service d'audit."""
        self.session = session
        self.audit = audit_service

    async def list_devices(self, user: UserAccount) -> list[Device]:
        """Retourne les appareils d'un utilisateur avec leurs sessions."""
        stmt = (
            select(Device)
            .options(selectinload(Device.sessions))
            .where(Device.user_id == user.id)
            .order_by(Device.registered_at.desc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def register_device(
        self,
        user: UserAccount,
        *,
        device_id: str,
        push_token: str,
        platform: str | None,
        ip_address: str | None,
        user_agent: str | None,
    ) -> Device:
        """Crée ou met à jour un appareil et synchronise les métadonnées/fiabilité."""
        fingerprint = self._sanitize(device_id, limit=128)
        if not fingerprint:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid device identifier.")
        if not push_token:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing device metadata payload.")

        metadata = self._decode_metadata(push_token)
        display_name = self._sanitize(str(metadata.get("label", "")).strip() or None, limit=120)
        now = datetime.now(timezone.utc)

        stmt = (
            select(Device)
            .options(selectinload(Device.sessions))
            .where(Device.user_id == user.id, Device.fingerprint == fingerprint)
        )
        result = await self.session.execute(stmt)
        device = result.scalar_one_or_none()

        if device is None:
            device = Device(
                user_id=user.id,
                fingerprint=fingerprint,
                display_name=display_name,
                platform=self._sanitize(platform, limit=64),
                device_metadata=self._build_metadata_blob(push_token, metadata),
                trust_level=self._derive_trust_level(metadata),
                last_seen_at=now,
                last_seen_ip=ip_address,
            )
            self.session.add(device)
            await self.session.flush()
            await self._log(
                user,
                "device.register",
                device_id=str(device.id),
                metadata={"platform": platform, "fingerprint": fingerprint},
            )
        else:
            device.display_name = display_name or device.display_name
            device.platform = self._sanitize(platform, limit=64) or device.platform
            device.device_metadata = self._merge_metadata(device.device_metadata, push_token, metadata)
            device.last_seen_at = now
            device.last_seen_ip = ip_address or device.last_seen_ip
            device.trust_level = self._derive_trust_level(metadata, fallback=device.trust_level)
            await self.session.flush()
            await self._log(
                user,
                "device.sync",
                device_id=str(device.id),
                metadata={"platform": platform, "fingerprint": fingerprint},
            )

        await self._update_sessions(device, ip_address=ip_address, user_agent=user_agent)
        return device

    async def revoke_device(self, user: UserAccount, device_identifier: str) -> None:
        """Révoque un appareil et invalide les sessions liées."""
        fingerprint = self._sanitize(device_identifier, limit=128)
        stmt = select(Device).where(Device.user_id == user.id)
        if fingerprint:
            stmt = stmt.where(Device.fingerprint == fingerprint)
        result = await self.session.execute(stmt)
        device = result.scalar_one_or_none()
        if device is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found.")

        await self.session.execute(
            update(SessionToken)
            .where(
                SessionToken.user_id == user.id,
                SessionToken.device_id == device.id,
                SessionToken.revoked_at.is_(None),
            )
            .values(revoked_at=datetime.now(timezone.utc))
        )
        await self.session.delete(device)
        await self._log(user, "device.revoke", device_id=str(device.id))

    def _decode_metadata(self, payload: str) -> dict[str, Any]:
        """Décode le token metadata base64 -> JSON; retourne un dict même en cas d'échec."""
        if not payload:
            return {}
        try:
            decoded = base64.b64decode(payload.encode("ascii"), validate=True)
            text = decoded.decode("utf-8", errors="replace")
            data = json.loads(text)
            if isinstance(data, dict):
                return data
            return {}
        except (ValueError, json.JSONDecodeError):
            return {"raw": payload}

    def _build_metadata_blob(self, push_token: str, metadata: dict[str, Any]) -> dict[str, Any]:
        """Assemble la structure stockée pour un appareil (token + métadonnées)."""
        return {
            "push_token": push_token,
            "metadata": metadata,
            "synced_at": metadata.get("syncedAt"),
        }

    def _merge_metadata(self, existing: dict | None, push_token: str, metadata: dict[str, Any]) -> dict[str, Any]:
        """Fusionne metadonnees deja stockees avec les nouvelles informations."""
        base = dict(existing or {})
        base["push_token"] = push_token
        base["metadata"] = metadata
        base["synced_at"] = metadata.get("syncedAt")
        return base

    def _derive_trust_level(self, metadata: dict[str, Any], fallback: int | None = None) -> int:
        """Calcule un score de confiance simple à partir du type d'appareil/navigateur."""
        device_type = str(metadata.get("deviceType", "")).lower()
        browser = str(metadata.get("browser", "")).lower()
        trust = 60
        if "mobile" in device_type:
            trust = 70
        elif "tablet" in device_type:
            trust = 65
        elif "desktop" in device_type:
            trust = 60

        if "unknown" in browser or not browser:
            trust -= 10

        if fallback is not None:
            return max(trust, fallback)
        return trust

    def _sanitize(self, value: str | None, *, limit: int) -> str | None:
        """Nettoie une chaine (trim + longueur max) et retourne None si vide."""
        if value is None:
            return None
        cleaned = value.strip()
        if not cleaned:
            return None
        return cleaned[:limit]

    async def _update_sessions(self, device: Device, *, ip_address: str | None, user_agent: str | None) -> None:
        """Met à jour les sessions actives liées à l'appareil (IP, user-agent, dernière activité)."""
        if not device.id:
            await self.session.flush()
        stmt = (
            select(SessionToken)
            .where(
                SessionToken.device_id == device.id,
                SessionToken.revoked_at.is_(None),
            )
        )
        result = await self.session.execute(stmt)
        sessions = result.scalars().all()
        if not sessions:
            return

        now = datetime.now(timezone.utc)
        for session in sessions:
            session.last_activity_at = now
            if ip_address:
                session.ip_address = ip_address
            if user_agent:
                session.user_agent = user_agent
        await self.session.flush()

    async def _log(self, user: UserAccount, action: str, *, device_id: str, metadata: dict | None = None) -> None:
        """Relais vers AuditService pour tracer les actions d'appareil."""
        if not self.audit:
            return
        await self.audit.record(
            action,
            user_id=str(user.id),
            resource_type="device",
            resource_id=device_id,
            metadata=metadata,
        )


__all__ = ["DeviceService"]
