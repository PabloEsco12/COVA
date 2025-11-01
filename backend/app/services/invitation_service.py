"""Conversation invitation management service."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import Select, and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from ..core.security import generate_token, hash_token
from ..models.conversation import Conversation, ConversationMember
from ..models.enums import InvitationRole, UserRole
from ..models.invitation import Invitation
from ..models.user import User


class InvitationService:
    """Handle invitation lifecycle for conversations."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_invitation(
        self,
        conversation_id: UUID,
        inviter_id: UUID,
        email: str,
        *,
        role: InvitationRole = InvitationRole.MEMBER,
        expires_in_hours: int = 72,
    ) -> tuple[Invitation, str]:
        conversation = await self._get_conversation(conversation_id)
        inviter_membership = await self._get_membership(conversation_id, inviter_id)
        if inviter_membership is None:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accès refusé à la conversation")
        if inviter_membership.role == UserRole.MEMBER and role != InvitationRole.MEMBER:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Rôle insuffisant pour inviter avec ce statut")

        existing_member = await self._find_member_by_email(conversation, email)
        if existing_member is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="L'utilisateur fait déjà partie de la conversation")

        existing_invite = await self._find_active_invitation(conversation_id, email)
        if existing_invite:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Une invitation est déjà en cours pour cet e-mail")

        raw_token = generate_token(32)
        invitation = Invitation(
            conversation_id=conversation_id,
            inviter_id=inviter_id,
            email=email.lower(),
            role=role,
            token=hash_token(raw_token),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=expires_in_hours),
        )
        async with self.session.begin():
            self.session.add(invitation)
        await self.session.refresh(invitation, attribute_names=["conversation"])
        return invitation, raw_token

    async def list_invitations(self, conversation_id: UUID) -> list[Invitation]:
        stmt = (
            select(Invitation)
            .where(Invitation.conversation_id == conversation_id)
            .options(joinedload(Invitation.conversation))
            .order_by(Invitation.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def revoke_invitation(self, invitation_id: UUID, requester_id: UUID) -> None:
        invitation = await self._get_invitation(invitation_id)
        membership = await self._get_membership(invitation.conversation_id, requester_id)
        if membership is None or membership.role == UserRole.MEMBER:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Non autorisé à révoquer cette invitation")
        if invitation.accepted_at:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invitation déjà acceptée")

        async with self.session.begin():
            await self.session.delete(invitation)

    async def resolve_invitation(self, token_value: str) -> Invitation:
        hashed = hash_token(token_value)
        stmt: Select[tuple[Invitation]] = select(Invitation).where(Invitation.token == hashed)
        result = await self.session.execute(stmt)
        invitation = result.scalar_one_or_none()
        if invitation is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invitation invalide")
        if invitation.expires_at < datetime.now(timezone.utc):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invitation expirée")
        return invitation

    async def mark_accepted(self, invitation: Invitation) -> None:
        async with self.session.begin():
            invitation.accepted_at = datetime.now(timezone.utc)

    async def _get_conversation(self, conversation_id: UUID) -> Conversation:
        stmt = select(Conversation).where(Conversation.id == conversation_id)
        result = await self.session.execute(stmt)
        conversation = result.scalar_one_or_none()
        if conversation is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation introuvable")
        return conversation

    async def _get_invitation(self, invitation_id: UUID) -> Invitation:
        stmt = select(Invitation).where(Invitation.id == invitation_id)
        result = await self.session.execute(stmt)
        invitation = result.scalar_one_or_none()
        if invitation is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invitation introuvable")
        return invitation

    async def _get_membership(self, conversation_id: UUID, user_id: UUID) -> ConversationMember | None:
        stmt = select(ConversationMember).where(
            ConversationMember.conversation_id == conversation_id,
            ConversationMember.user_id == user_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def _find_member_by_email(self, conversation: Conversation, email: str) -> ConversationMember | None:
        stmt = (
            select(ConversationMember)
            .join(User, ConversationMember.user_id == User.id)
            .where(
                ConversationMember.conversation_id == conversation.id,
                User.email == email.lower(),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def _find_active_invitation(self, conversation_id: UUID, email: str) -> Invitation | None:
        stmt = select(Invitation).where(
            Invitation.conversation_id == conversation_id,
            Invitation.email == email.lower(),
            Invitation.accepted_at.is_(None),
            Invitation.expires_at > datetime.now(timezone.utc),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
