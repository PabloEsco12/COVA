from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import (
    Conversation,
    ConversationMember,
    ConversationMemberRole,
    MembershipState,
    OrganizationMembership,
    UserAccount,
    Workspace,
    WorkspaceMembership,
)
from ..audit_service import AuditService
from ...core.redis import RealtimeBroker
from ...core.storage import ObjectStorage
from ...config import settings
from ..attachment_service import AttachmentService


class ConversationBase:
    """Initialisation et helpers communs (session, audit, membres, workspaces)."""

    def __init__(
        self,
        session: AsyncSession,
        *,
        audit_service: AuditService | None = None,
        realtime_broker: RealtimeBroker | None = None,
        storage_service: ObjectStorage | None = None,
        attachment_decoder: AttachmentService | None = None,
    ) -> None:
        """Injecte la session et les intégrations (audit, temps réel, stockage, décodeur PJ)."""
        self.session = session
        self.audit = audit_service
        self.realtime = realtime_broker
        self.storage = storage_service
        self.attachment_decoder = attachment_decoder
        self._rsa_public_key = self._load_rsa_public_key()
        self._rsa_private_key = self._load_rsa_private_key()
        self._encryption_enabled = bool(
            settings.MESSAGE_ENCRYPTION_ENABLED and self._rsa_public_key and self._rsa_private_key
        )

    async def ensure_membership(self, conversation_id: uuid.UUID, user_id: uuid.UUID) -> ConversationMember:
        """Expose _get_membership pour les consommateurs externes."""
        return await self._get_membership(conversation_id, user_id)

    async def _get_membership(
        self,
        conversation_id: uuid.UUID,
        user_id: uuid.UUID,
        *,
        active_only: bool = True,
    ) -> ConversationMember:
        """Charge l'appartenance d'un utilisateur à une conversation (optionnellement active)."""
        stmt = (
            select(ConversationMember)
            .where(
                ConversationMember.conversation_id == conversation_id,
                ConversationMember.user_id == user_id,
            )
            .options(
                selectinload(ConversationMember.user).selectinload(UserAccount.profile),
            )
        )
        if active_only:
            stmt = stmt.where(ConversationMember.state == MembershipState.ACTIVE)
        result = await self.session.execute(stmt)
        membership = result.scalar_one_or_none()
        if membership is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation introuvable ou acces refuse.")
        return membership

    async def _load_message(self, message_id: uuid.UUID):
        """Charge un message avec toutes ses relations nécessaires aux réponses API."""
        from app.models import Message  # import local pour éviter les cycles

        stmt = (
            select(Message)
            .where(Message.id == message_id)
            .options(
                selectinload(Message.author).selectinload(UserAccount.profile),
                selectinload(Message.deliveries),
                selectinload(Message.reactions),
                selectinload(Message.pins),
                selectinload(Message.attachments),
                selectinload(Message.reply_to)
                .selectinload(Message.author)
                .selectinload(UserAccount.profile),
                selectinload(Message.reply_to).selectinload(Message.attachments),
                selectinload(Message.forwarded_from)
                .selectinload(Message.author)
                .selectinload(UserAccount.profile),
                selectinload(Message.forwarded_from).selectinload(Message.attachments),
            )
        )
        result = await self.session.execute(stmt)
        message = result.scalar_one_or_none()
        if message is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message introuvable.")
        return message

    def _ensure_message_in_conversation(self, message, conversation_id: uuid.UUID) -> None:
        """Verifie que le message appartient a la conversation cible, sinon leve 404."""
        if message.conversation_id != conversation_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message introuvable.")

    def _get_metadata(self, conversation: Conversation) -> dict:
        """Retourne une copie mutable des metadonnees de conversation."""
        return dict(conversation.extra_metadata or {})

    async def _load_conversation_with_members(self, conversation_id: uuid.UUID) -> Conversation:
        """Charge une conversation avec ses membres/profils pour reponses API."""
        stmt = (
            select(Conversation)
            .where(Conversation.id == conversation_id)
            .options(
                selectinload(Conversation.members).selectinload(ConversationMember.user).selectinload(UserAccount.profile)
            )
        )
        result = await self.session.execute(stmt)
        conversation = result.scalar_one_or_none()
        if conversation is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation introuvable.")
        return conversation

    async def _promote_fallback_owner(
        self, conversation_id: uuid.UUID, *, exclude_user_id: uuid.UUID | None
    ) -> ConversationMember | None:
        """Promouvoit le plus ancien membre actif non owner quand aucun autre owner n'est present."""
        stmt = (
            select(ConversationMember)
            .where(
                ConversationMember.conversation_id == conversation_id,
                ConversationMember.state == MembershipState.ACTIVE,
                ConversationMember.role != ConversationMemberRole.OWNER,
            )
            .order_by(ConversationMember.joined_at.asc())
        )
        if exclude_user_id:
            stmt = stmt.where(ConversationMember.user_id != exclude_user_id)
        result = await self.session.execute(stmt)
        candidate = result.scalars().first()
        if candidate is None:
            return None
        candidate.role = ConversationMemberRole.OWNER
        await self.session.flush()
        return candidate

    async def _has_other_active_owner(self, conversation_id: uuid.UUID, *, exclude_user_id: uuid.UUID | None) -> bool:
        """Retourne True si un autre owner actif existe (en excluant eventuellement un utilisateur)."""
        stmt = (
            select(func.count(ConversationMember.id))
            .where(
                ConversationMember.conversation_id == conversation_id,
                ConversationMember.role == ConversationMemberRole.OWNER,
                ConversationMember.state == MembershipState.ACTIVE,
            )
        )
        if exclude_user_id:
            stmt = stmt.where(ConversationMember.user_id != exclude_user_id)
        result = await self.session.execute(stmt)
        count = result.scalar_one()
        return int(count or 0) > 0

    def _require_owner(self, membership: ConversationMember) -> None:
        """Lève une 403 si le membre n'est pas owner."""
        if membership.role != ConversationMemberRole.OWNER:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Action réservée au propriétaire.")

    async def _get_primary_membership(self, user_id: uuid.UUID) -> OrganizationMembership:
        """Récupère la première appartenance organisationnelle d'un utilisateur (nécessaire pour créer une conversation)."""
        stmt = select(OrganizationMembership).where(OrganizationMembership.user_id == user_id)
        result = await self.session.execute(stmt)
        membership = result.scalar_one_or_none()
        if membership is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User is not part of an organization")
        return membership

    async def _get_default_workspace(self, membership: OrganizationMembership) -> Workspace | None:
        """Renvoie le premier workspace lié à l'appartenance, ou None si absent."""
        stmt = (
            select(Workspace)
            .join(WorkspaceMembership, WorkspaceMembership.workspace_id == Workspace.id)
            .where(WorkspaceMembership.membership_id == membership.id)
            .order_by(Workspace.created_at.asc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def _log(self, user: UserAccount, action: str, *, resource_id: str | None = None, metadata: dict | None = None) -> None:
        """Facade vers AuditService pour tracer les événements conversation/messagerie."""
        if self.audit:
            await self.audit.record(
                action,
                user_id=str(user.id),
                resource_type="conversation",
                resource_id=resource_id,
                metadata=metadata,
            )
