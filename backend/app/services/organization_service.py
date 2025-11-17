"""Service utilities to manage organisations and their memberships."""

from __future__ import annotations

import uuid

from fastapi import HTTPException, status
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models import OrganizationMembership, OrganizationRole, UserAccount
from .audit_service import AuditService


class OrganizationService:
    """Encapsulates common organisation membership operations."""

    def __init__(self, session: AsyncSession, audit_service: AuditService | None = None) -> None:
        self.session = session
        self.audit = audit_service

    async def get_membership_for_user(self, user_id: uuid.UUID) -> OrganizationMembership:
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
        if membership is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Utilisateur non rattache a une organisation."
            )
        return membership

    async def get_membership_by_id(self, membership_id: uuid.UUID) -> OrganizationMembership:
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
        return membership

    async def list_members(self, organization_id: uuid.UUID) -> list[OrganizationMembership]:
        stmt = (
            select(OrganizationMembership)
            .options(joinedload(OrganizationMembership.user).joinedload(UserAccount.profile))
            .where(OrganizationMembership.organization_id == organization_id)
            .order_by(OrganizationMembership.role.asc(), OrganizationMembership.joined_at.asc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_member_counts(self, organization_id: uuid.UUID) -> tuple[int, int]:
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
        actor_membership = await self.get_membership_for_user(actor.id)
        if not self.can_manage_admins(actor_membership):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Vous n'avez pas les droits suffisants pour gerer les administrateurs.",
            )

        target = await self.get_membership_by_id(membership_id)
        if target.organization_id != actor_membership.organization_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Membre introuvable.")
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
        return role in {OrganizationRole.OWNER, OrganizationRole.ADMIN}

    @staticmethod
    def can_manage_admins(membership: OrganizationMembership) -> bool:
        return membership.role in {OrganizationRole.OWNER, OrganizationRole.ADMIN}
