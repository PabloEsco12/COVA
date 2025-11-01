"""Contact management API."""

from __future__ import annotations

from typing import Callable
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, Response, status

from ..deps import CurrentUser, DBSession
from ...models.enums import ContactStatus
from ...schemas import ContactCreate, ContactRead, ContactRespond, ContactUpdateAlias, ContactUserInfo
from ...services import ContactService
from ...models.contact import Contact

router = APIRouter(prefix="/contacts", tags=["contacts"])


def _serialize_contact(contact: Contact, viewer_id: UUID) -> ContactRead:
    is_sender = contact.owner_id == viewer_id
    contact_profile = contact.contact if is_sender else contact.owner
    owner_profile = contact.owner
    contact_info = ContactUserInfo.model_validate(contact_profile) if contact_profile else None
    owner_info = ContactUserInfo.model_validate(owner_profile) if owner_profile else None
    return ContactRead(
        id=contact.id,
        owner_id=contact.owner_id,
        contact_id=contact.contact_id,
        alias=contact.alias,
        status=contact.status.value if isinstance(contact.status, ContactStatus) else str(contact.status),
        created_at=contact.created_at,
        updated_at=contact.updated_at,
        is_sender=is_sender,
        contact=contact_info,
        owner=owner_info,
    )


def _resolve_status(param: str | None, *, allow_none: bool = True) -> ContactStatus | None:
    if param is None:
        return None if allow_none else ContactStatus.PENDING
    try:
        return ContactStatus(param)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Statut de contact invalide") from exc


@router.get("/", response_model=list[ContactRead])
async def list_contacts(
    db: DBSession,
    current_user: CurrentUser,
    status: str | None = Query(default=None, description="Filtrer par statut (pending, accepted, blocked)"),
) -> list[ContactRead]:
    contact_service = ContactService(db)
    contact_status = _resolve_status(status) if status else None
    contacts = await contact_service.list_contacts(current_user.id, status_filter=contact_status)
    return [_serialize_contact(contact, current_user.id) for contact in contacts]


@router.get("/pending", response_model=list[ContactRead])
async def list_pending_invitations(db: DBSession, current_user: CurrentUser) -> list[ContactRead]:
    contact_service = ContactService(db)
    invitations = await contact_service.list_pending_requests(current_user.id)
    return [_serialize_contact(contact, current_user.id) for contact in invitations]


@router.post("/", response_model=ContactRead, status_code=status.HTTP_201_CREATED)
async def request_contact(payload: ContactCreate, db: DBSession, current_user: CurrentUser) -> ContactRead:
    contact_service = ContactService(db)
    contact = await contact_service.request_contact(
        current_user.id,
        contact_email=payload.email,
        contact_id=payload.contact_id,
        alias=payload.alias,
    )
    return _serialize_contact(contact, current_user.id)


@router.patch("/{contact_id}/status", response_model=ContactRead)
async def respond_contact(
    contact_id: UUID,
    payload: ContactRespond,
    db: DBSession,
    current_user: CurrentUser,
) -> ContactRead:
    contact_service = ContactService(db)
    status_value = _resolve_status(payload.status, allow_none=False)
    if status_value == ContactStatus.PENDING:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Statut invalide")
    contact = await contact_service.respond_to_request(contact_id, current_user.id, status_value=status_value)
    return _serialize_contact(contact, current_user.id)


@router.patch("/{contact_id}/alias", response_model=ContactRead)
async def update_alias(
    contact_id: UUID,
    payload: ContactUpdateAlias,
    db: DBSession,
    current_user: CurrentUser,
) -> ContactRead:
    contact_service = ContactService(db)
    contact = await contact_service.update_alias(contact_id, current_user.id, payload.alias)
    return _serialize_contact(contact, current_user.id)


@router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
async def delete_contact(contact_id: UUID, db: DBSession, current_user: CurrentUser) -> Response:
    contact_service = ContactService(db)
    await contact_service.remove_contact(contact_id, current_user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
