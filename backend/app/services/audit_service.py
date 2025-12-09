"""
############################################################
# Service : AuditService (journalisation)
# Auteur  : Valentin Masurelle
# Date    : 2025-05-04
#
# Description:
# - Enregistre les evenements dans AuditLog (UTC, metadata JSON).
# - Pas de commit automatique: a gerer en amont.
############################################################
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi.encoders import jsonable_encoder
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AuditLog


class AuditService:
    """Enregistre et consulte les evenements d'audit."""

    def __init__(self, session: AsyncSession) -> None:
        """Injecte une session SQLAlchemy async pour persister les logs."""
        self.session = session

    async def record(
        self,
        action: str,
        *,
        organization_id: str | None = None,
        user_id: str | None = None,
        resource_type: str | None = None,
        resource_id: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Enregistre un événement d'audit avec contexte optionnel (ressource, IP, user agent)."""
        details = jsonable_encoder(metadata) if metadata is not None else None
        log = AuditLog(
            organization_id=organization_id,
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=ip_address,
            user_agent=user_agent,
            details=details,
            created_at=datetime.now(timezone.utc),
        )
        self.session.add(log)

    async def recent_for_user(self, user_id: uuid.UUID, limit: int = 10) -> list[AuditLog]:
        """Retourne les derniers événements d'audit d'un utilisateur (ordre antichronologique)."""
        stmt = (
            select(AuditLog)
            .where(AuditLog.user_id == user_id)
            .order_by(AuditLog.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars())
