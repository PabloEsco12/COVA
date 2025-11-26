"""
############################################################
# Routes : Administration (gestion des utilisateurs)
# Auteur  : Valentin Masurelle
# Date    : 2025-11-25
#
# Description:
# - Permet aux super-administrateurs de creer ou supprimer des utilisateurs.
# - Reutilise AuthService pour la creation afin de beneficier des workflows existants.
############################################################
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ...config import settings
from ...dependencies import get_auth_service, get_audit_service, get_current_user, get_db
from ...schemas.admin import AdminUserCreateRequest, AdminUserCreateResponse, AdminUserDeleteResponse
from ...schemas.user import UserOut
from ...services.auth_service import AuthService
from ...services.audit_service import AuditService
from ...services.user_admin_service import cleanup_memberships, reassign_conversations_before_delete, remove_avatar_file
from app.models import UserAccount, UserRole

router = APIRouter(prefix="/admin", tags=["admin"])


def _require_superadmin(user: UserAccount) -> None:
    """Verifie que l'utilisateur courant est superadmin."""
    if user.role != UserRole.SUPERADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operation reservee aux administrateurs.",
        )


@router.post("/users", response_model=AdminUserCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_user_as_admin(
    payload: AdminUserCreateRequest,
    current_user: UserAccount = Depends(get_current_user),
    auth: AuthService = Depends(get_auth_service),
    audit: AuditService = Depends(get_audit_service),
) -> AdminUserCreateResponse:
    """Cree un utilisateur en forcant eventuellement son role ou la confirmation."""
    _require_superadmin(current_user)
    result = await auth.register_user(
        email=payload.email,
        password=payload.password,
        display_name=payload.display_name,
        role=payload.role,
        is_confirmed=payload.confirm_now,
    )
    await auth.session.refresh(result.user, attribute_names=["profile"])

    confirmation_url = None
    if result.confirmation_token:
        confirmation_url = f"{settings.FRONTEND_ORIGIN.rstrip('/')}/confirm-email/{result.confirmation_token}"

    await audit.record(
        "admin.user.create",
        user_id=str(current_user.id),
        resource_type="user",
        resource_id=str(result.user.id),
    )
    await auth.session.commit()

    return AdminUserCreateResponse(
        user=UserOut.model_validate(result.user, from_attributes=True),
        confirmation_url=confirmation_url,
    )


@router.delete("/users/{user_id}", response_model=AdminUserDeleteResponse, status_code=status.HTTP_200_OK)
async def delete_user_as_admin(
    user_id: uuid.UUID,
    current_user: UserAccount = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    audit: AuditService = Depends(get_audit_service),
) -> AdminUserDeleteResponse:
    """Supprime un utilisateur et nettoie ses ressources associees."""
    _require_superadmin(current_user)
    stmt = (
        select(UserAccount)
        .options(selectinload(UserAccount.profile))
        .where(UserAccount.id == user_id)
    )
    result = await db.execute(stmt)
    target = result.scalar_one_or_none()
    if target is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilisateur introuvable.")

    if target.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Utilisez /me pour supprimer votre propre compte.",
        )

    default_admin_email = (settings.DEFAULT_ADMIN_EMAIL or "").strip().lower()
    if target.email.lower() == default_admin_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Impossible de supprimer l'administrateur principal configure.",
        )

    avatar_url = target.profile.avatar_url if target.profile else None

    await reassign_conversations_before_delete(db, target.id)
    await cleanup_memberships(db, target.id)

    await audit.record(
        "admin.user.delete",
        user_id=str(current_user.id),
        resource_type="user",
        resource_id=str(target.id),
    )
    await db.delete(target)
    await db.commit()

    remove_avatar_file(avatar_url)

    return AdminUserDeleteResponse()
