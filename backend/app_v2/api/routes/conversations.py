"""Conversation routes."""

from __future__ import annotations

import json
import uuid

from fastapi import APIRouter, Body, Depends, File, Form, HTTPException, Response, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ...dependencies import get_attachment_service, get_conversation_service, get_current_user
from ...schemas.conversation import (
    AttachmentUploadResponse,
    ConversationCreateRequest,
    ConversationInviteCreateRequest,
    ConversationInviteOut,
    ConversationMemberOut,
    ConversationMemberUpdateRequest,
    ConversationOut,
    ConversationUpdateRequest,
    MessageCreateRequest,
    MessageUpdateRequest,
    MessageOut,
    MessageReadRequest,
    MessageReactionRequest,
)
from ...services.attachment_service import AttachmentService
from ...services.conversation_service import ConversationService
from db_v2 import Conversation, ConversationMember, UserAccount

router = APIRouter(prefix="/conversations", tags=["conversations"])


def _member_to_schema(link) -> ConversationMemberOut:
    user = getattr(link, "user", None)
    profile = getattr(user, "profile", None) if user else None
    display_name = None
    if profile and profile.display_name:
        display_name = profile.display_name
    elif user and user.email:
        display_name = user.email
    return ConversationMemberOut(
        user_id=link.user_id,
        role=link.role,
        state=link.state,
        joined_at=link.joined_at,
        muted_until=link.muted_until,
        display_name=display_name,
        email=getattr(user, "email", None) if user else None,
        avatar_url=getattr(profile, "avatar_url", None) if profile else None,
    )


def _conversation_to_schema(conversation) -> ConversationOut:
    members = [_member_to_schema(member) for member in conversation.members]
    metadata = dict(conversation.extra_metadata or {})
    return ConversationOut(
        id=conversation.id,
        title=conversation.title,
        topic=conversation.topic,
        type=conversation.type,
        created_at=conversation.created_at,
        archived=bool(metadata.get("archived", False)),
        members=members,
    )


def _invite_to_schema(invite) -> ConversationInviteOut:
    return ConversationInviteOut.model_validate(invite, from_attributes=True)


@router.get("/", response_model=list[ConversationOut])
async def list_conversations(
    current_user: UserAccount = Depends(get_current_user),
    service: ConversationService = Depends(get_conversation_service),
) -> list[ConversationOut]:
    conversations = await service.list_conversations(current_user)
    return [_conversation_to_schema(conv) for conv in conversations]


@router.post("/", response_model=ConversationOut, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    payload: ConversationCreateRequest,
    current_user: UserAccount = Depends(get_current_user),
    service: ConversationService = Depends(get_conversation_service),
) -> ConversationOut:
    conversation = await service.create_conversation(
        owner=current_user,
        title=payload.title,
        participant_ids=payload.participant_ids,
        conv_type=payload.type,
    )
    await service.session.commit()
    await service.session.refresh(conversation)

    stmt = (
        select(Conversation)
        .options(
            selectinload(Conversation.members).selectinload(ConversationMember.user).selectinload(UserAccount.profile)
        )
        .where(Conversation.id == conversation.id)
    )
    result = await service.session.execute(stmt)
    hydrated = result.scalar_one()
    return _conversation_to_schema(hydrated)


@router.patch("/{conversation_id}", response_model=ConversationOut)
async def update_conversation(
    conversation_id: uuid.UUID,
    payload: ConversationUpdateRequest,
    current_user: UserAccount = Depends(get_current_user),
    service: ConversationService = Depends(get_conversation_service),
) -> ConversationOut:
    conversation = await service.update_conversation(
        conversation_id=conversation_id,
        actor=current_user,
        title=payload.title,
        topic=payload.topic,
        archived=payload.archived,
    )
    await service.session.commit()
    await service.session.refresh(conversation)
    return _conversation_to_schema(conversation)


@router.get("/{conversation_id}/messages", response_model=list[MessageOut])
async def list_messages(
    conversation_id: uuid.UUID,
    current_user: UserAccount = Depends(get_current_user),
    service: ConversationService = Depends(get_conversation_service),
    limit: int = 50,
) -> list[MessageOut]:
    membership = await service.ensure_membership(conversation_id, current_user.id)
    messages, _meta = await service.list_messages(conversation_id, limit=limit, member=membership)
    payloads = []
    for message in messages:
        data = await service.serialize_message(message, viewer_membership=membership)
        payloads.append(MessageOut(**data))
    return payloads


@router.post("/{conversation_id}/messages", response_model=MessageOut, status_code=status.HTTP_201_CREATED)
async def post_message(
    conversation_id: uuid.UUID,
    payload: MessageCreateRequest,
    current_user: UserAccount = Depends(get_current_user),
    service: ConversationService = Depends(get_conversation_service),
) -> MessageOut:
    attachment_tokens = [item.upload_token for item in payload.attachments] if payload.attachments else None
    message, payload = await service.post_message(
        conversation_id=conversation_id,
        author=current_user,
        content=payload.content,
        message_type=payload.message_type,
        attachment_tokens=attachment_tokens,
        reply_to_id=payload.reply_to_message_id,
        forward_message_id=payload.forward_message_id,
    )
    await service.session.commit()
    await service.session.refresh(message)
    return MessageOut(**payload)


@router.post("/{conversation_id}/attachments", response_model=AttachmentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_attachment(
    conversation_id: uuid.UUID,
    file: UploadFile = File(...),
    encryption: str | None = Form(default=None),
    current_user: UserAccount = Depends(get_current_user),
    conversation_service: ConversationService = Depends(get_conversation_service),
    attachment_service: AttachmentService = Depends(get_attachment_service),
) -> AttachmentUploadResponse:
    await conversation_service.ensure_membership(conversation_id, current_user.id)
    encryption_metadata = None
    if encryption:
        try:
            encryption_metadata = json.loads(encryption)
        except json.JSONDecodeError as exc:  # pragma: no cover - invalid client payload
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Métadonnées de chiffrement invalides.") from exc
    descriptor = await attachment_service.upload_attachment(
        conversation_id=conversation_id,
        user=current_user,
        file=file,
        encryption_metadata=encryption_metadata,
    )
    return AttachmentUploadResponse(**descriptor)


@router.patch("/{conversation_id}/messages/{message_id}", response_model=MessageOut)
async def edit_message(
    conversation_id: uuid.UUID,
    message_id: uuid.UUID,
    payload: MessageUpdateRequest,
    current_user: UserAccount = Depends(get_current_user),
    service: ConversationService = Depends(get_conversation_service),
) -> MessageOut:
    membership = await service.ensure_membership(conversation_id, current_user.id)
    message = await service.edit_message(
        conversation_id=conversation_id,
        message_id=message_id,
        membership=membership,
        user=current_user,
        content=payload.content,
    )
    await service.session.commit()
    await service.session.refresh(message)
    data = await service.serialize_message(message, viewer_membership=membership)
    return MessageOut(**data)


@router.delete("/{conversation_id}/messages/{message_id}", response_model=MessageOut)
async def delete_message(
    conversation_id: uuid.UUID,
    message_id: uuid.UUID,
    current_user: UserAccount = Depends(get_current_user),
    service: ConversationService = Depends(get_conversation_service),
) -> MessageOut:
    membership = await service.ensure_membership(conversation_id, current_user.id)
    message = await service.delete_message(
        conversation_id=conversation_id,
        message_id=message_id,
        membership=membership,
        user=current_user,
    )
    await service.session.commit()
    await service.session.refresh(message)
    data = await service.serialize_message(message, viewer_membership=membership)
    return MessageOut(**data)


@router.post("/{conversation_id}/leave", status_code=status.HTTP_204_NO_CONTENT)
async def leave_conversation(
    conversation_id: uuid.UUID,
    current_user: UserAccount = Depends(get_current_user),
    service: ConversationService = Depends(get_conversation_service),
) -> Response:
    await service.leave_conversation(conversation_id, current_user)
    await service.session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{conversation_id}/read", status_code=status.HTTP_204_NO_CONTENT)
async def mark_read(
    conversation_id: uuid.UUID,
    payload: MessageReadRequest = Body(default=MessageReadRequest()),
    current_user: UserAccount = Depends(get_current_user),
    service: ConversationService = Depends(get_conversation_service),
) -> Response:
    await service.mark_messages_read(current_user, conversation_id, payload.message_ids)
    await service.session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{conversation_id}/messages/{message_id}/pin", response_model=MessageOut)
async def pin_message(
    conversation_id: uuid.UUID,
    message_id: uuid.UUID,
    current_user: UserAccount = Depends(get_current_user),
    service: ConversationService = Depends(get_conversation_service),
) -> MessageOut:
    membership = await service.ensure_membership(conversation_id, current_user.id)
    message = await service.pin_message(
        conversation_id=conversation_id,
        message_id=message_id,
        user=current_user,
        membership=membership,
    )
    payload = await service.serialize_message(message, viewer_membership=membership)
    await service.session.commit()
    return MessageOut(**payload)


@router.delete("/{conversation_id}/messages/{message_id}/pin", response_model=MessageOut)
async def unpin_message(
    conversation_id: uuid.UUID,
    message_id: uuid.UUID,
    current_user: UserAccount = Depends(get_current_user),
    service: ConversationService = Depends(get_conversation_service),
) -> MessageOut:
    membership = await service.ensure_membership(conversation_id, current_user.id)
    message = await service.unpin_message(
        conversation_id=conversation_id,
        message_id=message_id,
        user=current_user,
        membership=membership,
    )
    payload = await service.serialize_message(message, viewer_membership=membership)
    await service.session.commit()
    return MessageOut(**payload)


@router.post("/{conversation_id}/messages/{message_id}/reactions", response_model=MessageOut)
async def update_reaction(
    conversation_id: uuid.UUID,
    message_id: uuid.UUID,
    payload: MessageReactionRequest,
    current_user: UserAccount = Depends(get_current_user),
    service: ConversationService = Depends(get_conversation_service),
) -> MessageOut:
    membership = await service.ensure_membership(conversation_id, current_user.id)
    message = await service.update_reaction(
        conversation_id=conversation_id,
        message_id=message_id,
        emoji=payload.emoji,
        action=payload.action,
        user=current_user,
        membership=membership,
    )
    data = await service.serialize_message(message, viewer_membership=membership)
    await service.session.commit()
    return MessageOut(**data)


@router.patch("/{conversation_id}/members/{user_id}", response_model=ConversationMemberOut)
async def update_member(
    conversation_id: uuid.UUID,
    user_id: uuid.UUID,
    payload: ConversationMemberUpdateRequest,
    current_user: UserAccount = Depends(get_current_user),
    service: ConversationService = Depends(get_conversation_service),
) -> ConversationMemberOut:
    membership = await service.update_member(
        conversation_id=conversation_id,
        member_user_id=user_id,
        actor=current_user,
        role=payload.role,
        state=payload.state,
        muted_until=payload.muted_until,
    )
    await service.session.commit()
    await service.session.refresh(membership)
    return _member_to_schema(membership)


@router.get("/{conversation_id}/invites", response_model=list[ConversationInviteOut])
async def list_invites(
    conversation_id: uuid.UUID,
    current_user: UserAccount = Depends(get_current_user),
    service: ConversationService = Depends(get_conversation_service),
) -> list[ConversationInviteOut]:
    invites = await service.list_invites(conversation_id, current_user)
    return [_invite_to_schema(invite) for invite in invites]


@router.post("/{conversation_id}/invites", response_model=ConversationInviteOut, status_code=status.HTTP_201_CREATED)
async def create_invite(
    conversation_id: uuid.UUID,
    payload: ConversationInviteCreateRequest,
    current_user: UserAccount = Depends(get_current_user),
    service: ConversationService = Depends(get_conversation_service),
) -> ConversationInviteOut:
    invite = await service.create_invite(
        conversation_id=conversation_id,
        actor=current_user,
        email=payload.email,
        role=payload.role,
        expires_in_hours=payload.expires_in_hours,
    )
    await service.session.commit()
    await service.session.refresh(invite)
    return _invite_to_schema(invite)


@router.delete("/{conversation_id}/invites/{invite_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_invite(
    conversation_id: uuid.UUID,
    invite_id: uuid.UUID,
    current_user: UserAccount = Depends(get_current_user),
    service: ConversationService = Depends(get_conversation_service),
) -> Response:
    await service.revoke_invite(conversation_id, invite_id, current_user)
    await service.session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/invites/{token}/accept", response_model=ConversationOut)
async def accept_invite(
    token: str,
    current_user: UserAccount = Depends(get_current_user),
    service: ConversationService = Depends(get_conversation_service),
) -> ConversationOut:
    conversation = await service.accept_invite(token=token, user=current_user)
    await service.session.commit()
    await service.session.refresh(conversation)
    return _conversation_to_schema(conversation)
