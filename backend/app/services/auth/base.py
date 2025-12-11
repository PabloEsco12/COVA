from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...config import settings
from ..audit_service import AuditService
from ..notification_service import NotificationService
from ...core.redis import RealtimeBroker  # conservé pour compatibilité potentielle
from app.models import Organization, OrganizationMembership, OrganizationRole, UserSecurityState, Workspace, WorkspaceMembership

DEFAULT_WORKSPACE_NAME = "General"
DEFAULT_WORKSPACE_SLUG = "general"


class AuthBase:
    """Initialisation et helpers communs pour AuthService."""

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

    async def _ensure_security_state(self, user) -> UserSecurityState:
        """Garantit l'existence de l'état de sécurité utilisateur avant utilisation."""
        if user.security_state is None:
            user.security_state = UserSecurityState(user_id=user.id)
            self.session.add(user.security_state)
            await self.session.flush()
        return user.security_state

    def _is_default_admin_email(self, email: str) -> bool:
        """Indique si l'adresse correspond à l'administrateur par défaut configuré."""
        configured = (settings.DEFAULT_ADMIN_EMAIL or "").strip().lower()
        return bool(configured) and email.lower() == configured

    async def _ensure_default_organization(self) -> tuple[Organization, Workspace]:
        """Crée l'organisation et l'espace par défaut si absents, ou met à jour le nom si besoin."""
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
        """Génère un slug URL-safe, ou un hash court si le résultat est vide."""
        slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
        return slug or uuid.uuid4().hex[:12]

    async def _log(self, action: str, **kwargs) -> None:
        """Délègue la journalisation à l'AuditService si disponible."""
        if self.audit:
            await self.audit.record(action, **kwargs)


__all__ = [
    "AuthBase",
    "DEFAULT_WORKSPACE_NAME",
    "DEFAULT_WORKSPACE_SLUG",
    "AuditService",
    "NotificationService",
    "RealtimeBroker",
]
