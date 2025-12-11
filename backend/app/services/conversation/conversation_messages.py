from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.models import (
    Conversation,
    ConversationMember,
    ConversationMemberRole,
    ConversationType,
    MembershipState,
    Message,
    MessageAttachment,
    MessageDelivery,
    MessageDeliveryState,
    MessagePin,
    MessageReaction,
    MessageType,
    UserAccount,
)
from ..attachment_service import AttachmentDescriptor
from .conversation_base import ConversationBase


class ConversationMessagesMixin(ConversationBase):
    """Messages : list/search/post/edit/delete + livraisons initiales."""

    async def list_messages(
        self,
        conversation_id: uuid.UUID,
        *,
        limit: int = 50,
        before: int | None = None,
        after: int | None = None,
        member: ConversationMember | None = None,
    ) -> tuple[list[Message], dict]:
        """Liste les messages avec pagination (before/after) et retourne aussi les metadonnees de navigation."""
        if before and after:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="before et after ne peuvent être combinés.")
        fetch_limit = min(max(limit, 1), 200)
        query_limit = fetch_limit + 1
        stmt = select(Message).where(Message.conversation_id == conversation_id)
        if before is not None:
            stmt = stmt.where(Message.stream_position < before)
        if after is not None:
            stmt = stmt.where(Message.stream_position > after)

        order_desc = after is None
        order_clause = Message.stream_position.desc() if order_desc else Message.stream_position.asc()
        stmt = (
            stmt.order_by(order_clause)
            .limit(query_limit)
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
        rows = result.scalars().all()
        has_more = len(rows) > fetch_limit
        if has_more:
            rows = rows[:-1]
        items = list(reversed(rows)) if order_desc else rows

        if member:
            await self._mark_delivered(member, items)

        meta = {
            "next_before": items[0].stream_position if items else before,
            "next_after": items[-1].stream_position if items else after,
            "has_more_before": has_more if order_desc else bool(before),
            "has_more_after": has_more if not order_desc else bool(after),
        }
        return items, meta

    async def search_messages(
        self,
        conversation_id: uuid.UUID,
        *,
        user: UserAccount,
        query: str,
        limit: int = 50,
    ) -> list[dict]:
        """Recherche plein texte (tsvector simple) dans une conversation pour l'utilisateur connecte."""
        term = (query or "").strip()
        if not term:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Un terme de recherche est requis.")
        membership = await self._get_membership(conversation_id, user.id)
        ts_query = func.plainto_tsquery("simple", term)
        text_vector = func.to_tsvector(
            "simple",
            func.coalesce(Message.search_text, ""),
        )
        stmt = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .where(Message.deleted_at.is_(None))
            .where(text_vector.op("@@")(ts_query))
            .order_by(Message.created_at.desc())
            .limit(max(1, min(limit, 200)))
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
        rows = result.scalars().all()
        payloads: list[dict] = []
        for message in rows:
            payloads.append(await self.serialize_message(message, viewer_membership=membership))
        return payloads

    async def post_message(
        self,
        conversation_id: uuid.UUID,
        author: UserAccount,
        content: str,
        message_type: MessageType,
        attachment_tokens: list[str] | None = None,
        reply_to_id: uuid.UUID | None = None,
        forward_message_id: uuid.UUID | None = None,
    ) -> tuple[Message, dict]:
        """Crée un message, attache les PJ décodées, vérifie les blocages et diffuse notifications."""
        membership = await self._get_membership(conversation_id, author.id)
        conversation = await self.session.get(Conversation, conversation_id)
        if conversation is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation non trouvée.")
        if self._get_metadata(conversation).get("archived"):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Conversation est archivée")
        block_states = {}
        if conversation.type == ConversationType.DIRECT:
            block_states = await self.get_block_states(author, [conversation])
            state = block_states.get(conversation.id, {})
            if state.get("blocked_by_me") or state.get("blocked_by_other"):
                reason = "blocked_by_other" if state.get("blocked_by_other") else "blocked_by_you"
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "code": "conversation_blocked",
                        "reason": reason,
                        "blocked_by_you": bool(state.get("blocked_by_me")),
                        "blocked_by_other": bool(state.get("blocked_by_other")),
                    },
                )

        attachment_descriptors: list[AttachmentDescriptor] = []
        if attachment_tokens:
            if not self.attachment_decoder:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Pièces jointes indisponibles.",
                )
            for token in attachment_tokens:
                descriptor = self.attachment_decoder.decode_token(
                    token,
                    conversation_id=conversation_id,
                    user_id=author.id,
                )
                attachment_descriptors.append(descriptor)
        reply_to_message = None
        if reply_to_id:
            reply_to_message = await self._load_message(reply_to_id)
            self._ensure_message_in_conversation(reply_to_message, conversation_id)
        forward_source = None
        if forward_message_id:
            forward_source = await self._load_message(forward_message_id)
            self._ensure_message_in_conversation(forward_source, conversation_id)

        pos_stmt = select(func.coalesce(func.max(Message.stream_position), 0) + 1).where(Message.conversation_id == conversation_id)
        pos_result = await self.session.execute(pos_stmt)
        next_position = pos_result.scalar_one()

        ciphertext, encryption_scheme, encryption_metadata = self._encrypt_content(
            conversation_id=conversation_id, content=content
        )

        message = Message(
            conversation_id=conversation_id,
            author_id=author.id,
            type=message_type,
            stream_position=next_position,
            ciphertext=ciphertext,
            encryption_scheme=encryption_scheme,
            encryption_metadata=encryption_metadata,
            search_text=content,
            reply_to_message_id=reply_to_message.id if reply_to_message else None,
            forward_from_message_id=forward_source.id if forward_source else None,
        )
        self.session.add(message)
        await self.session.flush()

        now = datetime.now(timezone.utc)
        delivery_members_stmt = (
            select(
                ConversationMember.id,
                ConversationMember.user_id,
                ConversationMember.state,
                ConversationMember.muted_until,
            )
            .where(ConversationMember.conversation_id == conversation_id)
        )
        result_members = await self.session.execute(delivery_members_stmt)
        members_info = result_members.all()
        member_ids = [row.id for row in members_info]
        member_user_ids = [row.user_id for row in members_info]
        notify_candidates = []
        for row in members_info:
            if row.user_id == author.id:
                continue
            if row.state != MembershipState.ACTIVE:
                continue
            if row.muted_until and row.muted_until > now:
                continue
            notify_candidates.append(row.user_id)
        deliveries: list[MessageDelivery] = []
        for member_id in member_ids:
            if member_id == membership.id:
                deliveries.append(
                    MessageDelivery(
                        message_id=message.id,
                        member_id=member_id,
                        state=MessageDeliveryState.READ,
                        delivered_at=now,
                        read_at=now,
                    )
                )
            else:
                deliveries.append(
                    MessageDelivery(
                        message_id=message.id,
                        member_id=member_id,
                        state=MessageDeliveryState.QUEUED,
                        delivered_at=None,
                    )
                )
        self.session.add_all(deliveries)
        await self.session.flush()
        await self._persist_attachments(message, attachment_descriptors)
        hydrated = await self._load_message(message.id)

        payload = await self.serialize_message(hydrated, viewer_membership=membership)

        await self._log(author, "conversation.message", resource_id=str(message.id), metadata={"conversation": str(conversation_id)})
        if self.realtime:
            await self.realtime.publish_conversation(
                str(conversation_id),
                {
                    "event": "message",
                    **payload,
                },
            )
            await self._push_message_notifications(
                conversation_id=str(conversation_id),
                payload=payload,
                author_id=str(author.id),
                member_user_ids=notify_candidates,
                now=now,
            )
        return hydrated, payload

    async def edit_message(
        self,
        *,
        conversation_id: uuid.UUID,
        message_id: uuid.UUID,
        membership: ConversationMember,
        user: UserAccount,
        content: str,
    ) -> Message:
        """Édite le contenu d'un message (owner ou auteur), puis diffuse la mise à jour."""
        message = await self._load_message(message_id)
        self._ensure_message_in_conversation(message, conversation_id)
        if message.deleted_at:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Message supprimé.")
        if message.author_id != user.id and membership.role != ConversationMemberRole.OWNER:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Action non autorisée.")
        ciphertext, scheme, metadata = self._encrypt_content(conversation_id=conversation_id, content=content)
        message.ciphertext = ciphertext
        message.encryption_scheme = scheme
        message.encryption_metadata = metadata
        message.search_text = content
        message.edited_at = datetime.now(timezone.utc)
        await self.session.flush()
        await self._log(
            user,
            "message.edit",
            resource_id=str(message_id),
            metadata={"conversation": str(conversation_id)},
        )
        refreshed = await self._load_message(message_id)
        await self._broadcast_message_update(refreshed)
        return refreshed

    async def delete_message(
        self,
        *,
        conversation_id: uuid.UUID,
        message_id: uuid.UUID,
        membership: ConversationMember,
        user: UserAccount,
        reason: str | None = None,
    ) -> Message:
        """Supprime logiquement un message (owner ou auteur) et notifie les abonnés."""
        message = await self._load_message(message_id)
        self._ensure_message_in_conversation(message, conversation_id)
        if message.deleted_at:
            return message
        if message.author_id != user.id and membership.role != ConversationMemberRole.OWNER:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Action non autorisée.")
        message.deleted_at = datetime.now(timezone.utc)
        message.deletion_reason = reason or "deleted_by_user"
        await self.session.flush()
        await self._log(
            user,
            "message.delete",
            resource_id=str(message_id),
            metadata={"conversation": str(conversation_id)},
        )
        refreshed = await self._load_message(message_id)
        await self._broadcast_message_update(refreshed)
        return refreshed
