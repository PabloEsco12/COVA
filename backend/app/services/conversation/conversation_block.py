from __future__ import annotations

import uuid

from sqlalchemy import select

from app.models import (
    ContactLink,
    ContactStatus,
    Conversation,
    ConversationMember,
    ConversationType,
    MembershipState,
)
from .conversation_base import ConversationBase


class ConversationBlockMixin(ConversationBase):
    """Calcul des états de blocage pour les conversations directes."""

    async def get_block_states(
        self,
        viewer,
        conversations: list[Conversation],
    ) -> dict[uuid.UUID, dict[str, bool]]:
        """Retourne pour chaque conversation directe si elle est bloquee par moi ou par l'autre utilisateur."""
        states: dict[uuid.UUID, dict[str, bool]] = {
            conv.id: {"blocked_by_me": False, "blocked_by_other": False} for conv in conversations
        }
        if not conversations:
            return states

        viewer_id = viewer.id
        direct_conv_ids = [conv.id for conv in conversations if conv.type == ConversationType.DIRECT]
        if not direct_conv_ids:
            return states

        stmt = (
            select(ConversationMember.conversation_id, ConversationMember.user_id)
            .where(ConversationMember.conversation_id.in_(direct_conv_ids))
            .where(ConversationMember.user_id != viewer_id)
            .where(ConversationMember.state == MembershipState.ACTIVE)
        )
        result = await self.session.execute(stmt)
        direct_pairs: dict[uuid.UUID, uuid.UUID] = {}
        for conv_id, other_user_id in result.all():
            direct_pairs.setdefault(conv_id, other_user_id)

        if not direct_pairs:
            return states

        other_ids = list({user_id for user_id in direct_pairs.values()})
        viewer_stmt = select(ContactLink).where(
            ContactLink.owner_id == viewer_id,
            ContactLink.contact_id.in_(other_ids),
        )
        viewer_rows = await self.session.execute(viewer_stmt)
        viewer_links = {link.contact_id: link for link in viewer_rows.scalars().all()}

        reciprocal_stmt = select(ContactLink).where(
            ContactLink.owner_id.in_(other_ids),
            ContactLink.contact_id == viewer_id,
        )
        reciprocal_rows = await self.session.execute(reciprocal_stmt)
        reciprocal_links = {link.owner_id: link for link in reciprocal_rows.scalars().all()}

        for conv_id, other_id in direct_pairs.items():
            viewer_link = viewer_links.get(other_id)
            reciprocal_link = reciprocal_links.get(other_id)
            states[conv_id] = {
                "blocked_by_me": bool(viewer_link and viewer_link.status == ContactStatus.BLOCKED),
                "blocked_by_other": bool(reciprocal_link and reciprocal_link.status == ContactStatus.BLOCKED),
            }

        return states
