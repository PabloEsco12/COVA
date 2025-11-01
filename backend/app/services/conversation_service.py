"""Conversation domain services."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import Select, and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from ..models.conversation import (
    ArchivedConversation,
    Conversation,
    ConversationMember,
    Message,
    MessageAttachment,
    MessageReaction,
    MessageRead as MessageReadModel,
)
from ..models.enums import MessageState, UserRole
from ..models.user import User
from ..schemas import MessageRead as MessageReadSchema
from .events import publish_message_created, publish_messages_read


class ConversationService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_for_user(self, user_id: UUID, *, include_archived: bool = False) -> list[Conversation]:
        stmt: Select[tuple[Conversation]] = (
            select(Conversation)
            .join(ConversationMember)
            .where(ConversationMember.user_id == user_id)
            .options(
                selectinload(Conversation.members).joinedload(ConversationMember.user),
            )
            .order_by(Conversation.updated_at.desc())
        )
        if not include_archived:
            stmt = stmt.outerjoin(
                ArchivedConversation,
                and_(
                    ArchivedConversation.conversation_id == Conversation.id,
                    ArchivedConversation.user_id == user_id,
                ),
            ).where(ArchivedConversation.user_id.is_(None))

        result = await self.session.execute(stmt)
        return result.scalars().unique().all()

    async def create_conversation(
        self,
        owner_id: UUID,
        title: str | None,
        topic: str | None,
        participant_ids: Iterable[UUID],
        *,
        settings: dict | None = None,
    ) -> Conversation:
        members: set[UUID] = {owner_id}
        members.update({pid for pid in participant_ids if pid})

        users_stmt = select(User.id).where(User.id.in_(members))
        users_result = await self.session.execute(users_stmt)
        found_ids = {row[0] for row in users_result}
        missing = members - found_ids
        if missing:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown participants")

        conversation = Conversation(
            title=title,
            topic=topic,
            owner_id=owner_id,
            is_group=len(members) > 2,
            settings=settings or {},
        )

        async with self.session.begin():
            self.session.add(conversation)
            await self.session.flush()
            for member_id in members:
                role = UserRole.OWNER if member_id == owner_id else UserRole.MEMBER
                membership = ConversationMember(
                    conversation_id=conversation.id,
                    user_id=member_id,
                    role=role,
                    invited_by_id=owner_id if member_id != owner_id else None,
                )
                self.session.add(membership)

        return await self._load_conversation(conversation.id)

    async def add_member(self, conversation_id: UUID, user_id: UUID, *, invited_by: UUID | None = None) -> ConversationMember:
        if await self._get_membership(conversation_id, user_id):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Utilisateur déjà membre")
        membership = ConversationMember(
            conversation_id=conversation_id,
            user_id=user_id,
            role=UserRole.MEMBER,
            invited_by_id=invited_by,
        )
        async with self.session.begin():
            self.session.add(membership)
        return membership

    async def update_settings(self, conversation_id: UUID, user_id: UUID, settings: dict) -> Conversation:
        membership = await self._get_membership(conversation_id, user_id)
        if membership is None or membership.role == UserRole.MEMBER:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permissions insuffisantes")
        conversation = await self._load_conversation(conversation_id)
        async with self.session.begin():
            conversation.settings = settings
            conversation.updated_at = datetime.now(timezone.utc)
        return conversation

    async def archive(self, conversation_id: UUID, user_id: UUID, *, archived: bool) -> None:
        if not await self._get_membership(conversation_id, user_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation introuvable")
        stmt = select(ArchivedConversation).where(
            ArchivedConversation.conversation_id == conversation_id,
            ArchivedConversation.user_id == user_id,
        )
        result = await self.session.execute(stmt)
        archive = result.scalar_one_or_none()
        async with self.session.begin():
            if archive and not archived:
                await self.session.delete(archive)
            elif not archive and archived:
                archive = ArchivedConversation(user_id=user_id, conversation_id=conversation_id)
                self.session.add(archive)

    async def get_for_user(self, conversation_id: UUID, user_id: UUID) -> Conversation:
        membership = await self._get_membership(conversation_id, user_id)
        if membership is None:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a member of this conversation")
        return await self._load_conversation(conversation_id)

    async def touch_conversation(self, conversation_id: UUID, timestamp: datetime | None = None) -> None:
        stmt = select(Conversation).where(Conversation.id == conversation_id)
        result = await self.session.execute(stmt)
        conversation = result.scalar_one_or_none()
        if conversation is not None:
            conversation.updated_at = timestamp or datetime.now(timezone.utc)
            await self.session.flush()

    async def _load_conversation(self, conversation_id: UUID) -> Conversation:
        stmt = (
            select(Conversation)
            .where(Conversation.id == conversation_id)
            .options(
                selectinload(Conversation.members).joinedload(ConversationMember.user),
                selectinload(Conversation.invitations),
            )
        )
        result = await self.session.execute(stmt)
        conversation = result.scalar_one_or_none()
        if conversation is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
        return conversation

    async def _get_membership(self, conversation_id: UUID, user_id: UUID) -> ConversationMember | None:
        stmt = select(ConversationMember).where(
            ConversationMember.conversation_id == conversation_id,
            ConversationMember.user_id == user_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()


class MessageService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_messages(
        self,
        conversation: Conversation,
        limit: int = 50,
        before: datetime | None = None,
    ) -> list[Message]:
        stmt = (
            select(Message)
            .where(Message.conversation_id == conversation.id)
            .options(
                joinedload(Message.author),
                selectinload(Message.reads).joinedload(MessageReadModel.user),
                selectinload(Message.reactions).joinedload(MessageReaction.user),
                selectinload(Message.attachments),
            )
            .order_by(Message.created_at.desc())
            .limit(min(max(limit, 1), 200))
        )
        if before is not None:
            stmt = stmt.where(Message.created_at < before)
        result = await self.session.execute(stmt)
        messages = result.scalars().unique().all()
        return list(reversed(messages))

    async def create_message(self, conversation: Conversation, author_id: UUID, content_json: dict) -> Message:
        message = Message(
            conversation_id=conversation.id,
            author_id=author_id,
            content_json=content_json,
            state=MessageState.SENT,
        )
        async with self.session.begin():
            self.session.add(message)
            await self.session.flush()
            # mark author read by default
            self.session.add(MessageReadModel(message_id=message.id, user_id=author_id))
            conversation.updated_at = message.created_at

        await self.session.refresh(message)
        await self.session.refresh(message, attribute_names=["author", "reads"])

        message_schema = MessageReadSchema.model_validate(message, from_attributes=True)
        await publish_message_created(message_schema)
        return message

    async def mark_read(self, conversation: Conversation, message_ids: Iterable[UUID], user_id: UUID) -> None:
        ids = list(message_ids)
        if not ids:
            return
        existing_stmt = select(MessageReadModel.message_id).where(
            MessageReadModel.user_id == user_id, MessageReadModel.message_id.in_(ids)
        )
        existing = await self.session.execute(existing_stmt)
        already = {row[0] for row in existing}

        valid_stmt = select(Message.id).where(Message.conversation_id == conversation.id, Message.id.in_(ids))
        valid = await self.session.execute(valid_stmt)
        valid_ids = {row[0] for row in valid}

        to_insert = [msg_id for msg_id in ids if msg_id in valid_ids and msg_id not in already]
        async with self.session.begin():
            for msg_id in to_insert:
                self.session.add(MessageReadModel(message_id=msg_id, user_id=user_id))
        if to_insert:
            await publish_messages_read(conversation.id, to_insert, user_id)

    async def add_reaction(self, message_id: UUID, user_id: UUID, emoji: str) -> Message:
        message = await self._get_message(message_id)
        stmt = select(MessageReaction).where(
            MessageReaction.message_id == message_id,
            MessageReaction.user_id == user_id,
            MessageReaction.emoji == emoji,
        )
        result = await self.session.execute(stmt)
        if result.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Réaction déjà enregistrée")
        reaction = MessageReaction(message_id=message_id, user_id=user_id, emoji=emoji)
        async with self.session.begin():
            self.session.add(reaction)
        return await self.get_message(message_id)

    async def remove_reaction(self, message_id: UUID, user_id: UUID, emoji: str) -> Message:
        stmt = select(MessageReaction).where(
            MessageReaction.message_id == message_id,
            MessageReaction.user_id == user_id,
            MessageReaction.emoji == emoji,
        )
        result = await self.session.execute(stmt)
        reaction = result.scalar_one_or_none()
        if reaction is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Réaction introuvable")
        async with self.session.begin():
            await self.session.delete(reaction)
        return await self.get_message(message_id)

    async def add_attachment(
        self,
        message_id: UUID,
        *,
        uploaded_by_id: UUID | None,
        storage_path: str,
        filename: str | None,
        mime_type: str | None,
        size_bytes: int | None,
    ) -> Message:
        await self._get_message(message_id)
        attachment = MessageAttachment(
            message_id=message_id,
            uploaded_by_id=uploaded_by_id,
            storage_path=storage_path,
            filename=filename,
            mime_type=mime_type,
            size_bytes=size_bytes,
        )
        async with self.session.begin():
            self.session.add(attachment)
        return await self.get_message(message_id)

    async def _get_message(self, message_id: UUID) -> Message:
        stmt = select(Message).where(Message.id == message_id)
        result = await self.session.execute(stmt)
        message = result.scalar_one_or_none()
        if message is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message introuvable")
        return message

    async def get_message(self, message_id: UUID) -> Message:
        stmt = (
            select(Message)
            .where(Message.id == message_id)
            .options(
                joinedload(Message.author),
                selectinload(Message.reads).joinedload(MessageReadModel.user),
                selectinload(Message.reactions).joinedload(MessageReaction.user),
                selectinload(Message.attachments),
            )
        )
        result = await self.session.execute(stmt)
        message = result.scalar_one_or_none()
        if message is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message introuvable")
        return message
