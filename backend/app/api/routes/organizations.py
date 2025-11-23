"""Organisation management routes."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, status

from ...dependencies import get_current_user, get_organization_service
from ...schemas.organization import (
    OrganizationMemberList,
    OrganizationMemberOut,
    OrganizationMembershipInfo,
    OrganizationRoleUpdate,
    OrganizationSummary,
)
from ...services.organization_service import OrganizationService
from app.models import OrganizationMembership, UserAccount
from fastapi import Query

router = APIRouter(prefix="/organizations", tags=["organizations"])


def _membership_info(service: OrganizationService, membership: OrganizationMembership) -> OrganizationMembershipInfo:
    return OrganizationMembershipInfo(
        id=membership.id,
        role=membership.role,
        joined_at=membership.joined_at,
        is_admin=service.is_admin_role(membership.role),
        can_manage_admins=service.can_manage_admins(membership),
    )


def _organization_summary(
    service: OrganizationService,
    *,
    membership: OrganizationMembership,
    member_count: int,
    admin_count: int,
) -> OrganizationSummary:
    organization = membership.organization
    return OrganizationSummary(
        id=organization.id,
        name=organization.name,
        slug=organization.slug,
        created_at=organization.created_at,
        member_count=member_count,
        admin_count=admin_count,
        membership=_membership_info(service, membership),
    )


def _member_out(service: OrganizationService, membership: OrganizationMembership) -> OrganizationMemberOut:
    user = membership.user
    profile = user.profile if user else None
    return OrganizationMemberOut(
        membership_id=membership.id,
        user_id=membership.user_id,
        email=user.email if user else "",
        display_name=profile.display_name if profile else None,
        role=membership.role,
        is_admin=service.is_admin_role(membership.role),
        joined_at=membership.joined_at,
    )


@router.get("/current", response_model=OrganizationSummary)
async def get_current_organization(
    current_user: UserAccount = Depends(get_current_user),
    service: OrganizationService = Depends(get_organization_service),
) -> OrganizationSummary:
    membership = await service.get_membership_for_user(current_user.id)
    member_count, admin_count = await service.get_member_counts(membership.organization_id)
    return _organization_summary(
        service,
        membership=membership,
        member_count=member_count,
        admin_count=admin_count,
    )


@router.get("/current/members", response_model=OrganizationMemberList)
async def list_current_organization_members(
    current_user: UserAccount = Depends(get_current_user),
    service: OrganizationService = Depends(get_organization_service),
) -> OrganizationMemberList:
    membership = await service.get_membership_for_user(current_user.id)
    members = await service.list_members(membership.organization_id)
    member_count, admin_count = await service.get_member_counts(membership.organization_id)
    return OrganizationMemberList(
        organization=_organization_summary(
            service,
            membership=membership,
            member_count=member_count,
            admin_count=admin_count,
        ),
        members=[_member_out(service, item) for item in members],
    )


@router.put("/current/members/{membership_id}", response_model=OrganizationMemberOut, status_code=status.HTTP_200_OK)
async def update_member_role(
    membership_id: uuid.UUID,
    payload: OrganizationRoleUpdate,
    current_user: UserAccount = Depends(get_current_user),
    service: OrganizationService = Depends(get_organization_service),
    ) -> OrganizationMemberOut:
        updated = await service.update_role(actor=current_user, membership_id=membership_id, role=payload.role)
        await service.session.commit()
        return _member_out(service, updated)


@router.get("/current/members/suggest", response_model=list[OrganizationMemberOut])
async def suggest_members(
    q: str | None = Query(default=None, description="Search term for email or display name"),
    limit: int = Query(default=10, ge=1, le=50),
    current_user: UserAccount = Depends(get_current_user),
    service: OrganizationService = Depends(get_organization_service),
) -> list[OrganizationMemberOut]:
    membership = await service.get_membership_for_user(current_user.id)
    members = await service.search_members(membership.organization_id, query=q, limit=limit)
    return [_member_out(service, member) for member in members]
