from __future__ import annotations

from datetime import datetime, timedelta, timezone
from secrets import token_urlsafe

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models import (
    EmailConfirmationToken,
    NotificationChannel,
    OrganizationMembership,
    OrganizationRole,
    UserAccount,
    UserProfile,
    UserRole,
    WorkspaceMembership,
)
from ...core.security import get_password_hash
from .base import AuthBase
from .models import RegisterResult


class AuthRegistrationMixin(AuthBase):
    """Inscription, confirmation email et profils initiaux."""

    async def register_user(
        self,
        email: str,
        password: str,
        display_name: str | None = None,
        *,
        role: UserRole | None = None,
        is_confirmed: bool | None = None,
    ) -> RegisterResult:
        """Crée un nouvel utilisateur, son organisation par défaut et envoie l'email de confirmation."""
        stmt = select(UserAccount).where(UserAccount.email == email.lower())
        result = await self.session.execute(stmt)
        if result.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="E-mail déjà utilisé")

        normalized_email = email.lower()
        hashed = get_password_hash(password)
        desired_role = role or (UserRole.SUPERADMIN if self._is_default_admin_email(normalized_email) else UserRole.MEMBER)
        confirmed_flag = bool(is_confirmed) if is_confirmed is not None else False
        user = UserAccount(
            email=normalized_email,
            hashed_password=hashed,
            is_active=True,
            is_confirmed=confirmed_flag,
            role=desired_role,
        )
        user.profile = UserProfile(display_name=display_name)

        organization, workspace = await self._ensure_default_organization()
        membership_role = OrganizationRole.MEMBER
        if self._is_default_admin_email(normalized_email):
            membership_role = OrganizationRole.OWNER
        elif desired_role == UserRole.SUPERADMIN:
            membership_role = OrganizationRole.ADMIN
        membership = OrganizationMembership(organization=organization, user=user, role=membership_role)
        workspace_membership = WorkspaceMembership(workspace=workspace, membership=membership)
        membership.workspaces.append(workspace_membership)

        confirmation_token_value = None
        confirmation_token = None
        if not confirmed_flag:
            confirmation_token_value = token_urlsafe(48)
            confirmation_token = EmailConfirmationToken(
                user=user,
                token=confirmation_token_value,
                expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
            )

        items_to_add = [user, organization, workspace, membership, workspace_membership]
        if confirmation_token is not None:
            items_to_add.append(confirmation_token)

        self.session.add_all(items_to_add)
        await self.session.flush()
        await self.session.refresh(user, attribute_names=["profile"])

        await self._log("auth.register", user_id=str(user.id), organization_id=str(organization.id))
        if confirmation_token_value and self.notifications:
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

    async def confirm_email(self, token_value: str) -> UserAccount:
        """Confirme l'email à partir d'un token valide et marque le compte comme confirmé."""
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


__all__ = ["AuthRegistrationMixin"]
