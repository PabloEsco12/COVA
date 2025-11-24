"""
############################################################
# Service : OrganizationService (organisations & memberships)
# Auteur  : Valentin Masurelle
# Date    : 2025-05-04
#
# Description:
# - Normalise l'organisation/workspace par defaut et gere les roles.
# - Garantit les droits de l'admin par defaut.
# - Optionnellement trace via AuditService.
############################################################
"""

from __future__ import annotations

import uuid
import re

from fastapi import HTTPException, status
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from ..config import settings
from app.models import (
    Organization,
    OrganizationMembership,
    OrganizationRole,
    UserAccount,
    UserProfile,
    Workspace,
    WorkspaceMembership,
)
from .audit_service import AuditService


class OrganizationService:
    """Regroupe les operations courantes sur les organisations et les memberships."""

    def __init__(self, session: AsyncSession, audit_service: AuditService | None = None) -> None:
        """Injecte la session SQLAlchemy et eventuellement le service d'audit."""
        self.session = session
        self.audit = audit_service

    def _is_primary_admin(self, membership: OrganizationMembership) -> bool:
        """Detecte si le membership correspond a l'admin par defaut configure dans les settings."""
        admin_email = (settings.DEFAULT_ADMIN_EMAIL or "").strip().lower()
        user_email = (membership.user.email if membership.user else "").lower()
        return bool(admin_email) and user_email == admin_email

    def _slugify(self, value: str) -> str:
        """Genere un slug en minuscules (alphanumerique avec tirets)."""
        slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
        return slug or uuid.uuid4().hex[:12]

    async def _ensure_default_org(self) -> Organization:
        """Cree ou met a jour l'organisation par defaut selon la configuration."""
        desired_name = (settings.DEFAULT_ORG_NAME or "Default Organization").strip()
        desired_slug = self._slugify(settings.DEFAULT_ORG_SLUG or desired_name or "default-org")

        stmt = select(Organization).where(Organization.slug == desired_slug)
        result = await self.session.execute(stmt)
        organization = result.scalars().first()
        if organization is None:
            organization = Organization(name=desired_name, slug=desired_slug)
            self.session.add(organization)
            await self.session.flush()
        elif organization.name != desired_name:
            organization.name = desired_name
            await self.session.flush()
        return organization

    async def _ensure_default_workspace(self, organization: Organization) -> Workspace:
        """Garanti l'existence du workspace 'general' pour l'organisation donnee."""
        stmt = select(Workspace).where(
            Workspace.organization_id == organization.id,
            Workspace.slug == "general",
        )
        result = await self.session.execute(stmt)
        workspace = result.scalars().first()
        if workspace is None:
            workspace = Workspace(
                organization_id=organization.id,
                name="General",
                slug="general",
            )
            self.session.add(workspace)
            await self.session.flush()
        return workspace

    async def _normalize_membership(self, membership: OrganizationMembership) -> OrganizationMembership:
        """Reassocie le membership a l'organisation/workspace par defaut et ajuste le role si besoin."""
        changed = False
        default_org = await self._ensure_default_org()
        if membership.organization_id != default_org.id:
            # Re-use an existing default-org membership if present to avoid uniqueness errors.
            existing_stmt = select(OrganizationMembership).where(
                OrganizationMembership.organization_id == default_org.id,
                OrganizationMembership.user_id == membership.user_id,
            )
            existing_result = await self.session.execute(existing_stmt)
            existing = existing_result.scalars().first()
            if existing:
                return await self._normalize_membership(existing)
            else:
                membership.organization_id = default_org.id
                membership.organization = default_org
                changed = True

        desired_role = OrganizationRole.OWNER if self._is_primary_admin(membership) else OrganizationRole.MEMBER
        if membership.role != desired_role:
            membership.role = desired_role
            changed = True

        # ensure a workspace membership exists for the default workspace
        default_workspace = await self._ensure_default_workspace(default_org)
        # Avoid autoflush issues by querying directly instead of relying on relationship state
        with self.session.no_autoflush:
            ws_stmt = select(WorkspaceMembership.id).where(
                WorkspaceMembership.workspace_id == default_workspace.id,
                WorkspaceMembership.membership_id == membership.id,
            )
            ws_result = await self.session.execute(ws_stmt)
            has_workspace = ws_result.scalar_one_or_none() is not None

        if not has_workspace:
            workspace_membership = WorkspaceMembership(workspace_id=default_workspace.id, membership=membership)
            self.session.add(workspace_membership)
            changed = True

        if changed:
            await self.session.flush()
            await self.session.commit()
        return membership

    async def get_membership_for_user(self, user_id: uuid.UUID) -> OrganizationMembership:
        """Retourne (ou cree) le membership d'un utilisateur en s'assurant des defaults."""
        stmt = (
            select(OrganizationMembership)
            .options(
                joinedload(OrganizationMembership.organization),
                joinedload(OrganizationMembership.user).joinedload(UserAccount.profile),
            )
            .where(OrganizationMembership.user_id == user_id)
        )
        result = await self.session.execute(stmt)
        membership = result.scalars().first()
        if membership:
            return await self._normalize_membership(membership)

        user = await self.session.get(UserAccount, user_id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Utilisateur non rattache a une organisation."
            )

        organization = await self._ensure_default_org()
        workspace = await self._ensure_default_workspace(organization)
        role = OrganizationRole.OWNER if user.email.lower() == (settings.DEFAULT_ADMIN_EMAIL or "").strip().lower() else OrganizationRole.MEMBER

        membership = OrganizationMembership(organization_id=organization.id, user_id=user.id, role=role)
        workspace_membership = WorkspaceMembership(workspace_id=workspace.id, membership=membership)
        self.session.add_all([membership, workspace_membership])
        await self.session.flush()
        await self.session.commit()
        return await self._normalize_membership(membership)

    async def get_membership_by_id(self, membership_id: uuid.UUID) -> OrganizationMembership:
        """Charge un membership par ID avec organisation et profil utilisateur."""
        stmt = (
            select(OrganizationMembership)
            .options(
                joinedload(OrganizationMembership.organization),
                joinedload(OrganizationMembership.user).joinedload(UserAccount.profile),
            )
            .where(OrganizationMembership.id == membership_id)
        )
        result = await self.session.execute(stmt)
        membership = result.scalars().first()
        if membership is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Membre introuvable.")
        return await self._normalize_membership(membership)

    async def list_members(self, organization_id: uuid.UUID) -> list[OrganizationMembership]:
        """Liste les membres d'une organisation (ordre role puis date d'arrivee)."""
        stmt = (
            select(OrganizationMembership)
            .options(joinedload(OrganizationMembership.user).joinedload(UserAccount.profile))
            .where(OrganizationMembership.organization_id == organization_id)
            .order_by(OrganizationMembership.role.asc(), OrganizationMembership.joined_at.asc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def search_members(
        self,
        organization_id: uuid.UUID,
        query: str | None = None,
        limit: int = 10,
    ) -> list[OrganizationMembership]:
        """Recherche des membres par email/nom d'affichage, limitee en taille."""
        size = max(1, min(limit, 50))
        stmt = (
            select(OrganizationMembership)
            .join(UserAccount, UserAccount.id == OrganizationMembership.user_id)
            .outerjoin(UserProfile, UserProfile.user_id == UserAccount.id)
            .options(
                joinedload(OrganizationMembership.user).joinedload(UserAccount.profile),
            )
            .where(OrganizationMembership.organization_id == organization_id)
            .order_by(OrganizationMembership.role.asc(), OrganizationMembership.joined_at.asc())
            .limit(size)
        )
        if query:
            pattern = f"%{query.lower()}%"
            stmt = stmt.where(
                func.lower(UserAccount.email).like(pattern)
                | func.lower(UserProfile.display_name).like(pattern)
            )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_member_counts(self, organization_id: uuid.UUID) -> tuple[int, int]:
        """Retourne le total des membres et le nombre d'admins/owners."""
        stmt = (
            select(
                func.count(OrganizationMembership.id),
                func.coalesce(
                    func.sum(
                        case(
                            (OrganizationMembership.role.in_([OrganizationRole.OWNER, OrganizationRole.ADMIN]), 1),
                            else_=0,
                        )
                    ),
                    0,
                ),
            )
            .where(OrganizationMembership.organization_id == organization_id)
        )
        total, admins = (await self.session.execute(stmt)).one()
        return int(total or 0), int(admins or 0)

    async def update_role(
        self,
        *,
        actor: UserAccount,
        membership_id: uuid.UUID,
        role: OrganizationRole,
    ) -> OrganizationMembership:
        """Met a jour le role d'un membre en respectant les contraintes de l'admin principal."""
        actor_membership = await self.get_membership_for_user(actor.id)
        if not self.can_manage_admins(actor_membership):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Vous n'avez pas les droits suffisants pour gerer les administrateurs.",
            )

        target = await self.get_membership_by_id(membership_id)
        if target.organization_id != actor_membership.organization_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Membre introuvable.")
        target_is_primary_admin = self._is_primary_admin(target)
        if role in {OrganizationRole.ADMIN, OrganizationRole.OWNER} and not target_is_primary_admin:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Seul le compte administrateur principal peut avoir un role administrateur.",
            )
        if target_is_primary_admin and role not in {OrganizationRole.ADMIN, OrganizationRole.OWNER}:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Le compte administrateur principal ne peut pas perdre ses droits administrateur.",
            )
        if target.role == OrganizationRole.OWNER:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Le proprietaire ne peut pas changer de role via cette operation.",
            )
        if role == OrganizationRole.OWNER:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La promotion en proprietaire doit se faire par un transfert dedie.",
            )
        if target.role == role:
            return target

        target.role = role
        await self.session.flush()
        if self.audit:
            await self.audit.record(
                "organization.member.update",
                user_id=str(actor.id),
                resource_type="organization",
                resource_id=str(actor_membership.organization_id),
                metadata={"target_membership_id": str(target.id), "role": role.value},
            )
        return target

    @staticmethod
    def is_admin_role(role: OrganizationRole) -> bool:
        """Indique si le role est de type administrateur ou proprietaire."""
        return role in {OrganizationRole.OWNER, OrganizationRole.ADMIN}

    @staticmethod
    def can_manage_admins(membership: OrganizationMembership) -> bool:
        """Verifie si un membership peut gerer les roles admin/owner."""
        return membership.role in {OrganizationRole.OWNER, OrganizationRole.ADMIN}
