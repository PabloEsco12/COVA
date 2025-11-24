"""
############################################################
# Routes : Contacts (liste, creation, statut, alias, suppression)
# Auteur  : Valentin Masurelle
# Date    : 2025-05-04
#
# Description:
# - Expose les operations de gestion des contacts pour l'utilisateur courant.
# - Mappe explicitement les profils pour enrichir la reponse (display_name, avatar, etc.).
# - Commit explicite apres chaque mutation.
#
# Points de vigilance:
# - Verifier l'appartenance organisationnelle dans le service (create).
# - Toujours renvoyer ContactOut enrichi pour UI.
############################################################
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, Response, status

from ...dependencies import get_contact_service, get_current_user
from ...schemas.contact import (
    ContactAliasUpdate,
    ContactCreateRequest,
    ContactOut,
    ContactStatusUpdate,
)
from ...services.contact_service import ContactService
from app.models import ContactStatus, UserAccount

router = APIRouter(prefix="/contacts", tags=["contacts"])


# ============
# Helpers
# ============

def _to_contact_out(link) -> ContactOut:
    """Transforme un lien de contact en schema de sortie enrichi avec profil."""
    contact_user = link.contact
    display_name = None
    avatar_url = None
    job_title = None
    department = None
    phone_number = None
    status_message = None
    if contact_user and contact_user.profile:
        profile = contact_user.profile
        display_name = profile.display_name
        avatar_url = profile.avatar_url
        profile_data = profile.profile_data or {}
        job_title = profile_data.get("job_title")
        department = profile_data.get("department")
        phone_number = profile_data.get("phone_number")
        status_message = profile_data.get("status_message")
    awaiting_my_response = (
        link.status == ContactStatus.PENDING and not getattr(link, "initiated_by_owner", False)
    )
    return ContactOut(
        id=link.id,
        contact_user_id=link.contact_id,
        email=contact_user.email if contact_user else "",
        display_name=display_name,
        avatar_url=avatar_url,
        job_title=job_title,
        department=department,
        phone_number=phone_number,
        status_message=status_message,
        status=link.status,
        alias=link.alias,
        created_at=link.created_at,
        updated_at=link.updated_at,
        awaiting_my_response=awaiting_my_response,
    )


@router.get("/", response_model=list[ContactOut])
async def list_contacts(
    status_filter: ContactStatus | None = Query(default=None, alias="status"),
    current_user: UserAccount = Depends(get_current_user),
    service: ContactService = Depends(get_contact_service),
) -> list[ContactOut]:
    """Liste les contacts visibles de l'utilisateur courant (filtrable par statut)."""
    contacts = await service.list_contacts(current_user, status=status_filter)
    return [_to_contact_out(link) for link in contacts]


@router.post("/", response_model=ContactOut, status_code=status.HTTP_201_CREATED)
async def create_contact(
    payload: ContactCreateRequest,
    current_user: UserAccount = Depends(get_current_user),
    service: ContactService = Depends(get_contact_service),
) -> ContactOut:
    """Cree une demande de contact et retourne la representation enrichie."""
    contact_link = await service.create_contact(current_user, target_email=payload.email, alias=payload.alias)
    await service.session.commit()
    return _to_contact_out(contact_link)


@router.patch("/{contact_id}/status", response_model=ContactOut)
async def update_contact_status(
    contact_id: uuid.UUID,
    payload: ContactStatusUpdate,
    current_user: UserAccount = Depends(get_current_user),
    service: ContactService = Depends(get_contact_service),
) -> ContactOut:
    """Met a jour le statut d'un contact (block/accept/etc.)."""
    contact_link = await service.update_status(current_user, contact_id, payload.status)
    await service.session.commit()
    return _to_contact_out(contact_link)


@router.patch("/{contact_id}/alias", response_model=ContactOut)
async def update_contact_alias(
    contact_id: uuid.UUID,
    payload: ContactAliasUpdate,
    current_user: UserAccount = Depends(get_current_user),
    service: ContactService = Depends(get_contact_service),
) -> ContactOut:
    """Modifie l'alias associe a un contact."""
    contact_link = await service.update_alias(current_user, contact_id, payload.alias)
    await service.session.commit()
    return _to_contact_out(contact_link)


@router.delete("/{contact_id}", status_code=status.HTTP_200_OK)
async def delete_contact(
    contact_id: uuid.UUID,
    current_user: UserAccount = Depends(get_current_user),
    service: ContactService = Depends(get_contact_service),
) -> dict[str, str]:
    """Supprime le lien de contact pour les deux utilisateurs."""
    await service.delete_contact(current_user, contact_id)
    await service.session.commit()
    return {"detail": "Contact deleted"}
