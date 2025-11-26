"""
############################################################
# Routes : Conversations & Messages
# Auteur  : Valentin Masurelle
# Date    : 2025-06-05

#
# Description:
# - Cree/edite/supprime des conversations et leurs membres/invitations.
# - Gere les messages (liste, search, post, edit, delete, pin, reactions) et PJ.
# - Controle d'acces via ConversationService (membership/roles).
# - Commit explicite apres chaque mutation.
#
# Points de vigilance:
# - Respecter les etats de conversation (archived) et roles owner pour operations sensibles.
# - Toujours verifier le membership avant d'acceder aux messages.
# - Parser les metadonnees de chiffrement PJ avec prudence (JSON).
############################################################
"""

from __future__ import annotations

import json
import uuid

from fastapi import APIRouter, Body, Depends, File, Form, HTTPException, Query, Response, UploadFile, status
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
from app.models import Conversation, ConversationMember, UserAccount

router = APIRouter(prefix="/conversations", tags=["conversations"])


# ============
# Helpers
# ============

def _member_to_schema(link) -> ConversationMemberOut:
    """Transforme un membre en schema enrichi avec profil/affichage."""
    user = getattr(link, "user", None)
    profile = getattr(user, "profile", None) if user else None
    display_name = None
    status_message = None
    if profile and profile.profile_data:
        status_message = profile.profile_data.get("status_message")
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
        status_message=status_message,
    )


def _conversation_to_schema(conversation, *, block_state: dict | None = None) -> ConversationOut:
    """Assemble la vue conversation pour l'API en injectant etats de blocage."""
    members = [_member_to_schema(member) for member in conversation.members]
    metadata = dict(conversation.extra_metadata or {})
    blocked_view = block_state or {}
    return ConversationOut(
        id=conversation.id,
        title=conversation.title,
        topic=conversation.topic,
        type=conversation.type,
        created_at=conversation.created_at,
        archived=bool(metadata.get("archived", False)),
        members=members,
        blocked_by_viewer=bool(blocked_view.get("blocked_by_me")),
        blocked_by_other=bool(blocked_view.get("blocked_by_other")),
    )


def _invite_to_schema(invite) -> ConversationInviteOut:
    return ConversationInviteOut.model_validate(invite, from_attributes=True)


async def _fetch_conversation_with_members(session: AsyncSession, conversation_id: uuid.UUID) -> Conversation:
    """Charge une conversation avec ses membres/profils ou leve 404."""
    stmt = (
        select(Conversation)
        .options(
            selectinload(Conversation.members).selectinload(ConversationMember.user).selectinload(UserAccount.profile)
        )
        .where(Conversation.id == conversation_id)
    )
    result = await session.execute(stmt)
    conversation = result.scalar_one_or_none()
    if conversation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation introuvable.")
    return conversation


@router.get("/", response_model=list[ConversationOut])
async def list_conversations(
    current_user: UserAccount = Depends(get_current_user),
    service: ConversationService = Depends(get_conversation_service),
) -> list[ConversationOut]:
    """Liste les conversations actives de l'utilisateur avec etat de blocage."""
    conversations = await service.list_conversations(current_user)
    block_states = await service.get_block_states(current_user, conversations)
    return [_conversation_to_schema(conv, block_state=block_states.get(conv.id)) for conv in conversations]


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
    hydrated = await _fetch_conversation_with_members(service.session, conversation.id)
    block_state = (await service.get_block_states(current_user, [hydrated])).get(hydrated.id)
    return _conversation_to_schema(hydrated, block_state=block_state)


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
    hydrated = await _fetch_conversation_with_members(service.session, conversation.id)
    block_state = (await service.get_block_states(current_user, [hydrated])).get(hydrated.id)
    return _conversation_to_schema(hydrated, block_state=block_state)


@router.get("/{conversation_id}/messages", response_model=list[MessageOut])
async def list_messages(
    conversation_id: uuid.UUID,
    current_user: UserAccount = Depends(get_current_user),
    service: ConversationService = Depends(get_conversation_service),
    limit: int = 50,
) -> list[MessageOut]:
    """Recupere les messages d'une conversation avec pagination simple."""
    membership = await service.ensure_membership(conversation_id, current_user.id)
    messages, _meta = await service.list_messages(conversation_id, limit=limit, member=membership)
    payloads = []
    for message in messages:
        data = await service.serialize_message(message, viewer_membership=membership)
        payloads.append(MessageOut(**data))
    return payloads


@router.get("/{conversation_id}/messages/search", response_model=list[MessageOut])
async def search_conversation_messages(
    conversation_id: uuid.UUID,
    q: str = Query(..., min_length=1, description="Terme a rechercher"),
    limit: int = Query(50, ge=1, le=200),
    current_user: UserAccount = Depends(get_current_user),
    service: ConversationService = Depends(get_conversation_service),
) -> list[MessageOut]:
    """Recherche plein texte dans une conversation pour l'utilisateur courant."""
    results = await service.search_messages(
        conversation_id=conversation_id,
        user=current_user,
        query=q,
        limit=limit,
    )
    return [MessageOut(**item) for item in results]


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


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: uuid.UUID,
    current_user: UserAccount = Depends(get_current_user),
    service: ConversationService = Depends(get_conversation_service),
) -> Response:
    await service.delete_conversation(conversation_id, actor=current_user)
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
    hydrated = await _fetch_conversation_with_members(service.session, conversation.id)
    block_state = (await service.get_block_states(current_user, [hydrated])).get(hydrated.id)
    return _conversation_to_schema(hydrated, block_state=block_state)



