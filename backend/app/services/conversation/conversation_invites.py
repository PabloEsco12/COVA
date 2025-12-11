from __future__ import annotations

import secrets
import uuid
from datetime import datetime, timezone, timedelta

from fastapi import HTTPException, status
from sqlalchemy import select

from app.models import Conversation, ConversationInvite, ConversationMember, ConversationMemberRole, MembershipState, UserAccount
from .conversation_base import ConversationBase


class ConversationInvitesMixin(ConversationBase):
    """Gestion des invitations de conversation."""

    async def list_invites(self, conversation_id: uuid.UUID, actor: UserAccount) -> list[ConversationInvite]:
        """Liste les invitations d'une conversation (owner uniquement)."""
        membership = await self._get_membership(conversation_id, actor.id)
        self._require_owner(membership)
        stmt = (
            select(ConversationInvite)
            .where(ConversationInvite.conversation_id == conversation_id)
            .order_by(ConversationInvite.expires_at.desc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def create_invite(
        self,
        conversation_id: uuid.UUID,
        *,
        actor: UserAccount,
        email: str,
        role: ConversationMemberRole,
        expires_in_hours: int,
    ) -> ConversationInvite:
        """Crée une invitation partageable avec rôle attribué et expiration configurée."""
        conversation = await self.session.get(Conversation, conversation_id)
        membership = await self._get_membership(conversation_id, actor.id)
        self._require_owner(membership)
        if conversation is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found.")
        if self._get_metadata(conversation).get("archived"):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Conversation est archivée.")
        token = secrets.token_urlsafe(24)
        expires_at = datetime.now(timezone.utc) + timedelta(hours=expires_in_hours)
        invite = ConversationInvite(
            conversation_id=conversation_id,
            email=email.lower(),
            role=role,
            token=token,
            expires_at=expires_at,
            invited_by=actor.id,
        )
        self.session.add(invite)
        await self.session.flush()
        await self._log(
            actor,
            "conversation.invite.create",
            resource_id=str(conversation_id),
            metadata={"invite_id": str(invite.id), "email": email.lower(), "role": role.value},
        )
        return invite

    async def revoke_invite(self, conversation_id: uuid.UUID, invite_id: uuid.UUID, actor: UserAccount) -> None:
        """Supprime une invitation spécifique (owner requis)."""
        membership = await self._get_membership(conversation_id, actor.id)
        self._require_owner(membership)
        stmt = (
            select(ConversationInvite)
            .where(
                ConversationInvite.conversation_id == conversation_id,
                ConversationInvite.id == invite_id,
            )
        )
        result = await self.session.execute(stmt)
        invite = result.scalar_one_or_none()
        if invite is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invitation not found.")
        await self.session.delete(invite)
        await self.session.flush()
        await self._log(
            actor,
            "conversation.invite.revoke",
            resource_id=str(conversation_id),
            metadata={"invite_id": str(invite_id)},
        )

    async def accept_invite(self, *, token: str, user: UserAccount) -> Conversation:
        """Accepte une invitation via jeton et active/crée le membre avec le rôle attendu."""
        from sqlalchemy.orm import selectinload

        stmt = (
            select(ConversationInvite)
            .options(selectinload(ConversationInvite.conversation))
            .where(ConversationInvite.token == token)
        )
        result = await self.session.execute(stmt)
        invite = result.scalar_one_or_none()
        if invite is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invitation non trouvée.")
        now = datetime.now(timezone.utc)
        if invite.expires_at < now:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invitation expirée.")
        if invite.accepted_at:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invitation déjà utilisée.")

        conv_id = invite.conversation_id
        conversation = invite.conversation or await self.session.get(Conversation, conv_id)
        if conversation is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation non trouvée.")
        if self._get_metadata(conversation).get("archived"):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Conversation est archivée.")
        stmt_member = select(ConversationMember).where(
            ConversationMember.conversation_id == conv_id,
            ConversationMember.user_id == user.id,
        )
        member_result = await self.session.execute(stmt_member)
        membership = member_result.scalar_one_or_none()
        if membership is None:
            membership = ConversationMember(
                conversation_id=conv_id,
                user_id=user.id,
                role=invite.role,
                state=MembershipState.ACTIVE,
            )
            self.session.add(membership)
        else:
            membership.state = MembershipState.ACTIVE
            if membership.role != ConversationMemberRole.OWNER:
                membership.role = invite.role
        membership.joined_at = membership.joined_at or now

        invite.accepted_at = now
        await self.session.flush()
        await self._log(
            user,
            "conversation.invite.accept",
            resource_id=str(conv_id),
            metadata={"invite_id": str(invite.id)},
        )

        return await self._load_conversation_with_members(conv_id)
