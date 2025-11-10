"""Conversation and messaging services."""

from __future__ import annotations

import uuid
import secrets
from datetime import datetime, timezone, timedelta
import contextlib

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from db_v2 import (
    Conversation,
    ConversationInvite,
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
    OrganizationMembership,
    UserAccount,
    Workspace,
    WorkspaceMembership,
)
from .audit_service import AuditService
from ..core.redis import RealtimeBroker
from ..core.storage import ObjectStorage
from ..config import settings
from .attachment_service import AttachmentDescriptor, AttachmentService


class ConversationService:
    """High level operations for conversations and messages."""

    def __init__(
        self,
        session: AsyncSession,
        *,
        audit_service: AuditService | None = None,
        realtime_broker: RealtimeBroker | None = None,
        storage_service: ObjectStorage | None = None,
        attachment_decoder: AttachmentService | None = None,
    ) -> None:
        self.session = session
        self.audit = audit_service
        self.realtime = realtime_broker
        self.storage = storage_service
        self.attachment_decoder = attachment_decoder

    async def list_conversations(self, user: UserAccount) -> list[Conversation]:
        stmt = (
            select(Conversation)
            .join(ConversationMember, ConversationMember.conversation_id == Conversation.id)
            .where(
                ConversationMember.user_id == user.id,
                ConversationMember.state == MembershipState.ACTIVE,
            )
            .options(
                selectinload(Conversation.members).selectinload(ConversationMember.user).selectinload(UserAccount.profile)
            )
        )
        result = await self.session.execute(stmt)
        return result.scalars().unique().all()

    async def create_conversation(
        self,
        owner: UserAccount,
        title: str | None,
        participant_ids: list[uuid.UUID],
        conv_type: ConversationType,
    ) -> Conversation:
        membership = await self._get_primary_membership(owner.id)
        workspace = await self._get_default_workspace(membership)

        conversation = Conversation(
            organization_id=membership.organization_id,
            workspace_id=workspace.id if workspace else None,
            created_by=owner.id,
            title=title,
            type=conv_type,
            extra_metadata={"archived": False},
        )
        owner_member = ConversationMember(
            conversation=conversation,
            user_id=owner.id,
            role=ConversationMemberRole.OWNER,
            state=MembershipState.ACTIVE,
        )
        conversation.members.append(owner_member)

        participants = set(participant_ids)
        participants.discard(owner.id)
        if participants:
            stmt_users = select(UserAccount).where(UserAccount.id.in_(participants))
            result_users = await self.session.execute(stmt_users)
            users = {user.id: user for user in result_users.scalars().all()}
            missing = participants - set(users.keys())
            if missing:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid participant IDs")
            for participant_id in users.keys():
                conversation.members.append(
                    ConversationMember(
                        conversation=conversation,
                        user_id=participant_id,
                        role=ConversationMemberRole.MEMBER,
                        state=MembershipState.ACTIVE,
                    )
                )

        self.session.add(conversation)
        await self.session.flush()
        await self._log(owner, "conversation.create", resource_id=str(conversation.id))
        return conversation

    async def update_conversation(
        self,
        conversation_id: uuid.UUID,
        *,
        actor: UserAccount,
        title: str | None = None,
        topic: str | None = None,
        archived: bool | None = None,
    ) -> Conversation:
        membership = await self._get_membership(conversation_id, actor.id)
        self._require_owner(membership)
        conversation = await self.session.get(Conversation, conversation_id)
        if conversation is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found.")

        changed = False
        normalized_title = None
        normalized_topic = None
        if title is not None:
            normalized_title = (title or "").strip() or None
            if conversation.title != normalized_title:
                conversation.title = normalized_title
                changed = True
        if topic is not None:
            normalized_topic = (topic or "").strip() or None
            if conversation.topic != normalized_topic:
                conversation.topic = normalized_topic
                changed = True
        if archived is not None:
            metadata = self._get_metadata(conversation)
            if bool(metadata.get("archived")) != bool(archived):
                metadata["archived"] = bool(archived)
                conversation.extra_metadata = metadata
                changed = True
        if changed:
            await self.session.flush()
            await self._log(
                actor,
                "conversation.update",
                resource_id=str(conversation_id),
                metadata={"title": normalized_title, "topic": normalized_topic, "archived": archived},
            )
        return await self._load_conversation_with_members(conversation_id)

    async def leave_conversation(self, conversation_id: uuid.UUID, user: UserAccount) -> None:
        membership = await self._get_membership(conversation_id, user.id)
        if membership.role == ConversationMemberRole.OWNER:
            if not await self._has_other_active_owner(conversation_id, exclude_user_id=user.id):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot leave as the last owner of the conversation.",
                )
        membership.state = MembershipState.LEFT
        membership.muted_until = None
        await self.session.flush()
        await self._log(user, "conversation.leave", resource_id=str(conversation_id))

    async def update_member(
        self,
        conversation_id: uuid.UUID,
        *,
        member_user_id: uuid.UUID,
        actor: UserAccount,
        role: ConversationMemberRole | None = None,
        state: MembershipState | None = None,
        muted_until: datetime | None = None,
    ) -> ConversationMember:
        actor_membership = await self._get_membership(conversation_id, actor.id)
        self._require_owner(actor_membership)

        target = await self._get_membership(conversation_id, member_user_id, active_only=False)
        changed = False

        if role is not None and target.role != role:
            if target.role == ConversationMemberRole.OWNER and role != ConversationMemberRole.OWNER:
                if not await self._has_other_active_owner(conversation_id, exclude_user_id=target.user_id):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Conversation must keep at least one owner.",
                    )
            target.role = role
            changed = True

        if state is not None and target.state != state:
            if target.role == ConversationMemberRole.OWNER and state != MembershipState.ACTIVE:
                if not await self._has_other_active_owner(conversation_id, exclude_user_id=target.user_id):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Conversation must keep at least one owner.",
                    )
            target.state = state
            if state == MembershipState.ACTIVE and target.joined_at is None:
                target.joined_at = datetime.now(timezone.utc)
            changed = True

        if muted_until is not None or target.muted_until is not None:
            if target.muted_until != muted_until:
                target.muted_until = muted_until
                changed = True

        if changed:
            await self.session.flush()
            await self._log(
                actor,
                "conversation.member.update",
                resource_id=str(conversation_id),
                metadata={
                    "member_id": str(target.user_id),
                    "role": target.role.value,
                    "state": target.state.value,
                },
            )
        return target

    async def list_invites(self, conversation_id: uuid.UUID, actor: UserAccount) -> list[ConversationInvite]:
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
        membership = await self._get_membership(conversation_id, actor.id)
        self._require_owner(membership)
        conversation = await self.session.get(Conversation, conversation_id)
        if conversation is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found.")
        if self._get_metadata(conversation).get("archived"):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Conversation is archived.")
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
        stmt = (
            select(ConversationInvite)
            .options(selectinload(ConversationInvite.conversation))
            .where(ConversationInvite.token == token)
        )
        result = await self.session.execute(stmt)
        invite = result.scalar_one_or_none()
        if invite is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invitation not found.")
        now = datetime.now(timezone.utc)
        if invite.expires_at < now:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invitation expired.")
        if invite.accepted_at:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invitation already used.")

        conv_id = invite.conversation_id
        conversation = invite.conversation or await self.session.get(Conversation, conv_id)
        if conversation is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found.")
        if self._get_metadata(conversation).get("archived"):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Conversation is archived.")
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

    async def mark_messages_read(
        self,
        user: UserAccount,
        conversation_id: uuid.UUID,
        message_ids: list[uuid.UUID] | None = None,
    ) -> int:
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
        for delivery in getattr(message, "deliveries", []) or []:
            if delivery.member_id == member_id:
                return delivery
        return None

    async def _fetch_delivery(self, message_id: uuid.UUID, member_id: uuid.UUID) -> MessageDelivery | None:
        stmt = select(MessageDelivery).where(
            MessageDelivery.message_id == message_id,
            MessageDelivery.member_id == member_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_unread_summary(self, user: UserAccount) -> dict:
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
            .where(ConversationMember.user_id == user.id)
            .group_by(ConversationMember.conversation_id)
        )
        result = await self.session.execute(stmt)
        entries = result.all()
        total = int(sum(row.unread for row in entries))
        conversations = [
            {"conversation_id": row.conversation_id, "unread": int(row.unread)} for row in entries
        ]
        return {"total": total, "conversations": conversations}

    async def list_messages(
        self,
        conversation_id: uuid.UUID,
        *,
        limit: int = 50,
        before: int | None = None,
        after: int | None = None,
        member: ConversationMember | None = None,
    ) -> tuple[list[Message], dict]:
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
        membership = await self._get_membership(conversation_id, author.id)
        conversation = await self.session.get(Conversation, conversation_id)
        if conversation is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found.")
        if self._get_metadata(conversation).get("archived"):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Conversation is archived.")
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

        message = Message(
            conversation_id=conversation_id,
            author_id=author.id,
            type=message_type,
            stream_position=next_position,
            ciphertext=content.encode("utf-8"),
            encryption_scheme="plaintext",
            encryption_metadata={"encoding": "utf-8"},
            reply_to_message_id=reply_to_message.id if reply_to_message else None,
            forward_from_message_id=forward_source.id if forward_source else None,
        )
        self.session.add(message)
        await self.session.flush()

        delivery_members_stmt = select(ConversationMember.id).where(ConversationMember.conversation_id == conversation_id)
        result_members = await self.session.execute(delivery_members_stmt)
        member_ids = result_members.scalars().all()
        deliveries = [
            MessageDelivery(
                message_id=message.id,
                member_id=member_id,
                state=MessageDeliveryState.DELIVERED if member_id == membership.id else MessageDeliveryState.QUEUED,
                delivered_at=datetime.now(timezone.utc) if member_id == membership.id else None,
            )
            for member_id in member_ids
        ]
        self.session.add_all(deliveries)
        await self.session.flush()
        await self._persist_attachments(message, attachment_descriptors)
        await self.session.refresh(
            message,
            attribute_names=["reactions", "pins", "deliveries", "attachments"],
        )

        payload = await self.serialize_message(message, viewer_membership=membership)

        await self._log(author, "conversation.message", resource_id=str(message.id), metadata={"conversation": str(conversation_id)})
        if self.realtime:
            await self.realtime.publish_conversation(
                str(conversation_id),
                {
                    "event": "message",
                    **payload,
                },
            )
        return message, payload

    async def edit_message(
        self,
        *,
        conversation_id: uuid.UUID,
        message_id: uuid.UUID,
        membership: ConversationMember,
        user: UserAccount,
        content: str,
    ) -> Message:
        message = await self._load_message(message_id)
        self._ensure_message_in_conversation(message, conversation_id)
        if message.deleted_at:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Message supprimé.")
        if message.author_id != user.id and membership.role != ConversationMemberRole.OWNER:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Action non autorisée.")
        message.ciphertext = content.encode("utf-8")
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

    async def _persist_attachments(self, message: Message, descriptors: list[AttachmentDescriptor]) -> None:
        if not descriptors:
            return
        entities: list[MessageAttachment] = []
        for descriptor in descriptors:
            entities.append(
                MessageAttachment(
                    message_id=message.id,
                    storage_url=descriptor.storage_url,
                    file_name=descriptor.file_name,
                    mime_type=descriptor.mime_type,
                    size_bytes=descriptor.size_bytes,
                    sha256=descriptor.sha256,
                    encryption_info=descriptor.encryption_metadata,
                )
            )
        self.session.add_all(entities)
        await self.session.flush()

    async def serialize_message(self, message: Message, *, viewer_membership: ConversationMember | None = None) -> dict:
        author = message.author
        if author is None and message.author_id:
            author = await self.session.get(UserAccount, message.author_id)
        if author and getattr(author, "profile", None) is None:
            with contextlib.suppress(Exception):
                await self.session.refresh(author, attribute_names=["profile"])

        profile = author.profile if author and getattr(author, "profile", None) else None
        display_name = None
        if profile and profile.display_name:
            display_name = profile.display_name
        elif author and author.email:
            display_name = author.email

        avatar_url = profile.avatar_url if profile else None

        content = self._extract_plaintext(message)

        payload = {
            "id": str(message.id),
            "conversation_id": str(message.conversation_id),
            "author_id": str(message.author_id) if message.author_id else None,
            "author_display_name": display_name,
            "author_avatar_url": avatar_url,
            "type": message.type.value if message.type else MessageType.TEXT.value,
            "content": content,
            "created_at": message.created_at.isoformat(),
            "stream_position": int(message.stream_position) if message.stream_position is not None else None,
            "is_system": bool(message.is_system),
            "encryption_scheme": message.encryption_scheme,
            "encryption_metadata": message.encryption_metadata or {},
            "reactions": self._summarize_reactions(message, viewer_membership),
            "pinned": False,
            "pinned_at": None,
            "pinned_by": None,
            "delivery_state": None,
            "delivered_at": None,
            "read_at": None,
            "attachments": [],
            "edited_at": message.edited_at.isoformat() if message.edited_at else None,
            "deleted_at": message.deleted_at.isoformat() if message.deleted_at else None,
            "deleted": bool(message.deleted_at),
        }

        pin = next(iter(getattr(message, "pins", []) or []), None)
        if pin:
            payload["pinned"] = True
            payload["pinned_at"] = pin.pinned_at.isoformat() if pin.pinned_at else None
            payload["pinned_by"] = str(pin.pinned_by) if pin.pinned_by else None

        if viewer_membership:
            delivery = self._match_delivery(message, viewer_membership.id)
            if delivery is None:
                delivery = await self._fetch_delivery(message.id, viewer_membership.id)
            if delivery:
                payload["delivery_state"] = delivery.state.value
                payload["delivered_at"] = delivery.delivered_at.isoformat() if delivery.delivered_at else None
                payload["read_at"] = delivery.read_at.isoformat() if delivery.read_at else None

        attachments = getattr(message, "attachments", None) or []
        payload["attachments"] = [self._serialize_attachment(attachment) for attachment in attachments]
        payload["reply_to"] = self._serialize_reference(getattr(message, "reply_to", None))
        payload["forward_from"] = self._serialize_reference(getattr(message, "forwarded_from", None))
        if payload["deleted"]:
            payload["content"] = ""
            payload["attachments"] = []

        return payload

    async def pin_message(
        self,
        *,
        conversation_id: uuid.UUID,
        message_id: uuid.UUID,
        user: UserAccount,
        membership: ConversationMember | None = None,
    ) -> Message:
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
    ) -> Message:
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

    async def ensure_membership(self, conversation_id: uuid.UUID, user_id: uuid.UUID) -> ConversationMember:
        return await self._get_membership(conversation_id, user_id)

    async def _get_membership(
        self,
        conversation_id: uuid.UUID,
        user_id: uuid.UUID,
        *,
        active_only: bool = True,
    ) -> ConversationMember:
        stmt = select(ConversationMember).where(
            ConversationMember.conversation_id == conversation_id,
            ConversationMember.user_id == user_id,
        )
        if active_only:
            stmt = stmt.where(ConversationMember.state == MembershipState.ACTIVE)
        result = await self.session.execute(stmt)
        membership = result.scalar_one_or_none()
        if membership is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation introuvable ou acces refuse.")
        return membership

    async def _load_message(self, message_id: uuid.UUID) -> Message:
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

    def _ensure_message_in_conversation(self, message: Message, conversation_id: uuid.UUID) -> None:
        if message.conversation_id != conversation_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message introuvable.")

    def _serialize_attachment(self, attachment: MessageAttachment) -> dict:
        download_url = attachment.storage_url
        if self.storage and attachment.storage_url:
            key = self.storage.key_from_url(attachment.storage_url)
            try:
                download_url = self.storage.generate_presigned_url(
                    key,
                    expires_in=settings.ATTACHMENT_DOWNLOAD_TTL_SECONDS,
                )
            except RuntimeError:
                download_url = attachment.storage_url
        return {
            "id": str(attachment.id),
            "file_name": attachment.file_name,
            "mime_type": attachment.mime_type,
            "size_bytes": attachment.size_bytes,
            "sha256": attachment.sha256,
            "download_url": download_url,
            "encryption": attachment.encryption_info or {},
        }

    def _serialize_reference(self, reference: Message | None) -> dict | None:
        if reference is None:
            return None
        author_name = None
        author = reference.author
        if author and getattr(author, "profile", None):
            profile = author.profile
            if profile.display_name:
                author_name = profile.display_name
        if author_name is None and author and author.email:
            author_name = author.email
        excerpt = self._extract_plaintext(reference)
        return {
            "id": str(reference.id),
            "author_display_name": author_name,
            "excerpt": excerpt[:160],
            "created_at": reference.created_at.isoformat() if reference.created_at else None,
            "deleted": bool(reference.deleted_at),
            "attachments": len(getattr(reference, "attachments", []) or []),
        }

    def _extract_plaintext(self, message: Message) -> str:
        if isinstance(message.ciphertext, (bytes, bytearray, memoryview)):
            return bytes(message.ciphertext).decode("utf-8", errors="ignore")
        return str(message.ciphertext or "")

    async def _broadcast_message_update(self, message: Message) -> None:
        if not self.realtime:
            return
        payload = await self.serialize_message(message)
        await self.realtime.publish_conversation(
            str(message.conversation_id),
            {
                "event": "message.updated",
                **payload,
            },
        )

    def _get_metadata(self, conversation: Conversation) -> dict:
        return dict(conversation.extra_metadata or {})

    async def _load_conversation_with_members(self, conversation_id: uuid.UUID) -> Conversation:
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

    async def _has_other_active_owner(self, conversation_id: uuid.UUID, *, exclude_user_id: uuid.UUID | None) -> bool:
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
        if membership.role != ConversationMemberRole.OWNER:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Action reservee au proprietaire.")

    async def _get_primary_membership(self, user_id: uuid.UUID) -> OrganizationMembership:
        stmt = select(OrganizationMembership).where(OrganizationMembership.user_id == user_id)
        result = await self.session.execute(stmt)
        membership = result.scalar_one_or_none()
        if membership is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User is not part of an organization")
        return membership

    async def _get_default_workspace(self, membership: OrganizationMembership) -> Workspace | None:
        stmt = (
            select(Workspace)
            .join(WorkspaceMembership, WorkspaceMembership.workspace_id == Workspace.id)
            .where(WorkspaceMembership.membership_id == membership.id)
            .order_by(Workspace.created_at.asc())
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def _log(self, user: UserAccount, action: str, *, resource_id: str | None = None, metadata: dict | None = None) -> None:
        if self.audit:
            await self.audit.record(
                action,
                user_id=str(user.id),
                resource_type="conversation",
                resource_id=resource_id,
                metadata=metadata,
            )
