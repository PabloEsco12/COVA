from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select

from app.models import ConversationMember, Message, MessageDelivery, MessageDeliveryState, MembershipState, UserAccount
from .conversation_base import ConversationBase


class ConversationDeliveryMixin(ConversationBase):
    """Livraisons, marquage lu, résumés unread et helpers réactions/livraisons."""

    async def mark_messages_read(
        self,
        user: UserAccount,
        conversation_id: uuid.UUID,
        message_ids: list[uuid.UUID] | None = None,
    ) -> int:
        """Marque des messages comme lus pour l'utilisateur (tous ou liste ciblée) et retourne le nombre mis à jour."""
        membership = await self._get_membership(conversation_id, user.id)
        stmt = select(MessageDelivery).where(MessageDelivery.member_id == membership.id)
        if message_ids:
            stmt = stmt.where(MessageDelivery.message_id.in_(message_ids))
        else:
            stmt = stmt.where(MessageDelivery.state != MessageDeliveryState.READ)
        result = await self.session.execute(stmt)
        deliveries = result.scalars().all()
        if not deliveries:
            return 0
        now = datetime.now(timezone.utc)
        updated = 0
        for delivery in deliveries:
            delivery.state = MessageDeliveryState.READ
            delivery.read_at = now
            updated += 1
        await self.session.flush()
        return updated

    async def _mark_delivered(self, member: ConversationMember, messages: list[Message]) -> None:
        """Passe les livraisons d'un membre à DELIVERED lorsque les messages sont déjà disponibles."""
        if not messages:
            return
        now = datetime.now(timezone.utc)
        updated = False
        for message in messages:
            for delivery in getattr(message, "deliveries", []) or []:
                if delivery.member_id == member.id and delivery.state == MessageDeliveryState.QUEUED:
                    delivery.state = MessageDeliveryState.DELIVERED
                    delivery.delivered_at = now
                    updated = True
        if updated:
            await self.session.flush()

    def _summarize_reactions(self, message: Message, viewer: ConversationMember | None) -> list[dict]:
        """Agrège les réactions par emoji et signale si le viewer a déjà réagi."""
        reactions = getattr(message, "reactions", []) or []
        summary: dict[str, dict] = {}
        viewer_member_id = viewer.id if viewer else None
        for reaction in reactions:
            entry = summary.setdefault(
                reaction.emoji,
                {"emoji": reaction.emoji, "count": 0, "reacted": False},
            )
            entry["count"] += 1
            if viewer_member_id and reaction.member_id == viewer_member_id:
                entry["reacted"] = True
        return list(summary.values())

    def _match_delivery(self, message: Message, member_id: uuid.UUID) -> MessageDelivery | None:
        """Trouve en memoire la livraison correspondant a un membre."""
        for delivery in getattr(message, "deliveries", []) or []:
            if delivery.member_id == member_id:
                return delivery
        return None

    async def _fetch_delivery(self, message_id: uuid.UUID, member_id: uuid.UUID) -> MessageDelivery | None:
        """Charge une livraison ciblee depuis la base (fallback si non prechargee)."""
        stmt = select(MessageDelivery).where(
            MessageDelivery.message_id == message_id,
            MessageDelivery.member_id == member_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_unread_summary(self, user: UserAccount) -> dict:
        """Calcule le nombre total de messages non lus et la repartition par conversation."""
        stmt = (
            select(
                ConversationMember.conversation_id.label("conversation_id"),
                func.count(MessageDelivery.id).label("unread"),
            )
            .join(
                MessageDelivery,
                (MessageDelivery.member_id == ConversationMember.id)
                & (MessageDelivery.state != MessageDeliveryState.READ),
            )
            .where(
                ConversationMember.user_id == user.id,
                ConversationMember.state == MembershipState.ACTIVE,
            )
            .group_by(ConversationMember.conversation_id)
        )
        result = await self.session.execute(stmt)
        entries = result.all()
        total = int(sum(row.unread for row in entries))
        conversations = [
            {"conversation_id": row.conversation_id, "unread": int(row.unread)} for row in entries
        ]
        return {"total": total, "conversations": conversations}
