from __future__ import annotations

import uuid

from sqlalchemy import select

from app.models import ConversationMember, ConversationMemberRole, Message, MessagePin, MessageReaction, UserAccount
from .conversation_base import ConversationBase


class ConversationPinsMixin(ConversationBase):
    """Pins et réactions emoji."""

    async def pin_message(
        self,
        *,
        conversation_id: uuid.UUID,
        message_id: uuid.UUID,
        user: UserAccount,
        membership: ConversationMember | None = None,
    ) -> Message:
        """Épingle un message (owner requis) et diffuse la mise à jour si changement."""
        membership = membership or await self._get_membership(conversation_id, user.id)
        self._require_owner(membership)
        message = await self._load_message(message_id)
        self._ensure_message_in_conversation(message, conversation_id)
        stmt = select(MessagePin).where(
            MessagePin.conversation_id == conversation_id,
            MessagePin.message_id == message_id,
        )
        result = await self.session.execute(stmt)
        pin = result.scalar_one_or_none()
        changed = False
        if pin is None:
            pin = MessagePin(conversation_id=conversation_id, message_id=message_id, pinned_by=user.id)
            self.session.add(pin)
            await self.session.flush()
            changed = True
            await self._log(user, "message.pin", resource_id=str(message_id), metadata={"conversation": str(conversation_id)})
        refreshed = await self._load_message(message_id)
        if changed:
            await self._broadcast_message_update(refreshed)
        return refreshed

    async def unpin_message(
        self,
        *,
        conversation_id: uuid.UUID,
        message_id: uuid.UUID,
        user: UserAccount,
        membership: ConversationMember | None = None,
    ) -> Message:
        """Retire l'épingle d'un message (owner requis) et notifie si besoin."""
        membership = membership or await self._get_membership(conversation_id, user.id)
        self._require_owner(membership)
        message = await self._load_message(message_id)
        self._ensure_message_in_conversation(message, conversation_id)
        stmt = select(MessagePin).where(
            MessagePin.conversation_id == conversation_id,
            MessagePin.message_id == message_id,
        )
        result = await self.session.execute(stmt)
        pin = result.scalar_one_or_none()
        changed = False
        if pin:
            await self.session.delete(pin)
            await self.session.flush()
            changed = True
            await self._log(user, "message.unpin", resource_id=str(message_id), metadata={"conversation": str(conversation_id)})
        refreshed = await self._load_message(message_id)
        if changed:
            await self._broadcast_message_update(refreshed)
        return refreshed

    async def update_reaction(
        self,
        *,
        conversation_id: uuid.UUID,
        message_id: uuid.UUID,
        emoji: str,
        action: str,
        user: UserAccount,
        membership: ConversationMember,
    ):
        """Ajoute/supprime/bascule une réaction emoji pour le membre, puis diffuse l'état."""
        message = await self._load_message(message_id)
        self._ensure_message_in_conversation(message, conversation_id)
        stmt = select(MessageReaction).where(
            MessageReaction.message_id == message_id,
            MessageReaction.member_id == membership.id,
            MessageReaction.emoji == emoji,
        )
        result = await self.session.execute(stmt)
        reaction = result.scalar_one_or_none()

        should_add = action == "add" or (action == "toggle" and reaction is None)
        should_remove = action == "remove" or (action == "toggle" and reaction is not None)
        changed = False
        if should_add and reaction is None:
            self.session.add(
                MessageReaction(
                    message_id=message_id,
                    member_id=membership.id,
                    emoji=emoji,
                )
            )
            await self.session.flush()
            changed = True
            await self._log(user, "message.reaction.add", resource_id=str(message_id), metadata={"emoji": emoji})
        elif should_remove and reaction:
            await self.session.delete(reaction)
            await self.session.flush()
            changed = True
            await self._log(user, "message.reaction.remove", resource_id=str(message_id), metadata={"emoji": emoji})

        refreshed = await self._load_message(message_id)
        if changed:
            await self._broadcast_message_update(refreshed)
        return refreshed
