"""Conversation and message API routes."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Body, HTTPException, Query, Response, status

from ..deps import CurrentUser, DBSession
from ...models.enums import InvitationRole
from ...schemas import (
    ConversationArchiveRequest,
    ConversationCreate,
    ConversationRead,
    ConversationSettingsUpdate,
    InvitationCreate,
    InvitationCreateResponse,
    InvitationRead,
    MessageAttachmentCreate,
    MessageCreate,
    MessageRead,
    MessageReactionCreate,
)
from ...services import ConversationService, InvitationService, MessageService

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.get("/", response_model=list[ConversationRead])
async def list_conversations(
    db: DBSession,
    current_user: CurrentUser,
    include_archived: bool = Query(False),
) -> list[ConversationRead]:
    service = ConversationService(db)
    conversations = await service.list_for_user(current_user.id, include_archived=include_archived)
    return conversations


@router.post("/", response_model=ConversationRead, status_code=status.HTTP_201_CREATED)
async def create_conversation(payload: ConversationCreate, db: DBSession, current_user: CurrentUser) -> ConversationRead:
    service = ConversationService(db)
    conversation = await service.create_conversation(
        owner_id=current_user.id,
        title=payload.title,
        topic=payload.topic,
        participant_ids=payload.participant_ids,
        settings=payload.settings,
    )
    return conversation


@router.get("/{conversation_id}", response_model=ConversationRead)
async def get_conversation(conversation_id: UUID, db: DBSession, current_user: CurrentUser) -> ConversationRead:
    service = ConversationService(db)
    conversation = await service.get_for_user(conversation_id, current_user.id)
    return conversation


@router.patch("/{conversation_id}/settings", response_model=ConversationRead)
async def update_settings(
    conversation_id: UUID,
    payload: ConversationSettingsUpdate,
    db: DBSession,
    current_user: CurrentUser,
) -> ConversationRead:
    service = ConversationService(db)
    conversation = await service.update_settings(conversation_id, current_user.id, payload.settings)
    return conversation


@router.post("/{conversation_id}/archive", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
async def toggle_archive(
    conversation_id: UUID,
    payload: ConversationArchiveRequest,
    db: DBSession,
    current_user: CurrentUser,
) -> Response:
    service = ConversationService(db)
    await service.archive(conversation_id, current_user.id, archived=payload.archived)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{conversation_id}/messages", response_model=list[MessageRead])
async def list_messages(
    conversation_id: UUID,
    db: DBSession,
    current_user: CurrentUser,
    limit: int = Query(50, ge=1, le=200),
    before: datetime | None = Query(None),
) -> list[MessageRead]:
    conversation_service = ConversationService(db)
    conversation = await conversation_service.get_for_user(conversation_id, current_user.id)
    message_service = MessageService(db)
    messages = await message_service.list_messages(conversation, limit=limit, before=before)
    return messages


@router.post("/{conversation_id}/messages", response_model=MessageRead, status_code=status.HTTP_201_CREATED)
async def create_message(
    conversation_id: UUID,
    payload: MessageCreate,
    db: DBSession,
    current_user: CurrentUser,
) -> MessageRead:
    conversation_service = ConversationService(db)
    conversation = await conversation_service.get_for_user(conversation_id, current_user.id)
    message_service = MessageService(db)
    message = await message_service.create_message(conversation, current_user.id, payload.content_json)
    return message


@router.post(
    "/{conversation_id}/read",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
async def mark_messages_read(
    conversation_id: UUID,
    db: DBSession,
    current_user: CurrentUser,
    message_ids: list[UUID] = Body(default_factory=list, embed=True),
) -> Response:
    if not message_ids:
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    conversation_service = ConversationService(db)
    conversation = await conversation_service.get_for_user(conversation_id, current_user.id)
    message_service = MessageService(db)
    await message_service.mark_read(conversation, message_ids, current_user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{conversation_id}/messages/{message_id}/reactions",
    response_model=MessageRead,
    status_code=status.HTTP_201_CREATED,
)
async def add_reaction(
    conversation_id: UUID,
    message_id: UUID,
    payload: MessageReactionCreate,
    db: DBSession,
    current_user: CurrentUser,
) -> MessageRead:
    conversation_service = ConversationService(db)
    await conversation_service.get_for_user(conversation_id, current_user.id)
    message_service = MessageService(db)
    message = await message_service.add_reaction(message_id, current_user.id, payload.emoji)
    if message.conversation_id != conversation_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message introuvable")
    return message


@router.delete(
    "/{conversation_id}/messages/{message_id}/reactions",
    response_model=MessageRead,
)
async def remove_reaction(
    conversation_id: UUID,
    message_id: UUID,
    db: DBSession,
    current_user: CurrentUser,
    emoji: str = Query(..., min_length=1, max_length=16),
) -> MessageRead:
    conversation_service = ConversationService(db)
    await conversation_service.get_for_user(conversation_id, current_user.id)
    message_service = MessageService(db)
    message = await message_service.remove_reaction(message_id, current_user.id, emoji)
    if message.conversation_id != conversation_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message introuvable")
    return message


@router.post(
    "/{conversation_id}/messages/{message_id}/attachments",
    response_model=MessageRead,
    status_code=status.HTTP_201_CREATED,
)
async def add_attachment(
    conversation_id: UUID,
    message_id: UUID,
    payload: MessageAttachmentCreate,
    db: DBSession,
    current_user: CurrentUser,
) -> MessageRead:
    conversation_service = ConversationService(db)
    await conversation_service.get_for_user(conversation_id, current_user.id)
    message_service = MessageService(db)
    message = await message_service.add_attachment(
        message_id,
        uploaded_by_id=current_user.id,
        storage_path=payload.storage_path,
        filename=payload.filename,
        mime_type=payload.mime_type,
        size_bytes=payload.size_bytes,
    )
    if message.conversation_id != conversation_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message introuvable")
    return message


@router.post("/{conversation_id}/invitations", response_model=InvitationCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_invitation(
    conversation_id: UUID,
    payload: InvitationCreate,
    db: DBSession,
    current_user: CurrentUser,
) -> InvitationCreateResponse:
    invitation_service = InvitationService(db)
    try:
        invitation_role = InvitationRole(payload.role) if payload.role else InvitationRole.MEMBER
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Rôle d'invitation invalide") from exc
    invitation, token = await invitation_service.create_invitation(
        conversation_id,
        current_user.id,
        payload.email,
        role=invitation_role,
        expires_in_hours=payload.expires_in_hours or 72,
    )
    return InvitationCreateResponse(invitation=InvitationRead.model_validate(invitation), token=token)


@router.get("/{conversation_id}/invitations", response_model=list[InvitationRead])
async def list_invitations(conversation_id: UUID, db: DBSession, current_user: CurrentUser) -> list[InvitationRead]:
    conversation_service = ConversationService(db)
    await conversation_service.get_for_user(conversation_id, current_user.id)
    invitation_service = InvitationService(db)
    invitations = await invitation_service.list_invitations(conversation_id)
    return [InvitationRead.model_validate(invitation) for invitation in invitations]
