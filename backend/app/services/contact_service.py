"""
############################################################
# Service : ContactService (contacts & invitations)
# Auteur  : Valentin Masurelle
# Date    : 2025-05-04
#
# Description:
# - Gere la creation de liens de contact, mise a jour de statut et alias.
# - Verifie l'appartenance a la meme organisation avant de lier deux utilisateurs.
# - Peut publier des notifications (email/realtime) si injecte.
#
# Points de vigilance:
# - Aucun commit automatique: a piloter depuis la couche route.
# - Synchroniser les liens reciproques lors des changements de statut.
# - Tenir compte des preferences de notification du destinataire.
############################################################
"""

from __future__ import annotations

import uuid

from fastapi import HTTPException, status
from sqlalchemy import and_, delete, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import ContactLink, ContactStatus, NotificationChannel, UserAccount, OrganizationMembership
from .audit_service import AuditService
from .notification_service import NotificationService
from ..core.redis import RealtimeBroker


# ===============================
# Service principal (ContactService)
# ===============================

class ContactService:
    """Logique metier des contacts et orchestration des notifications associees."""

    def __init__(
        self,
        session: AsyncSession,
        *,
        audit_service: AuditService | None = None,
        notification_service: NotificationService | None = None,
        realtime_broker: RealtimeBroker | None = None,
    ) -> None:
        """Injecte la session et les services optionnels (audit, notifications email, temps reel)."""
        self.session = session
        self.audit = audit_service
        self.notifications = notification_service
        self.realtime = realtime_broker

    # --- Lecture ---
    async def list_contacts(self, owner: UserAccount, status: ContactStatus | None = None) -> list[ContactLink]:
        """Retourne la liste des contacts visibles d'un proprietaire, filtreable par statut."""
        stmt = (
            select(ContactLink)
            .options(selectinload(ContactLink.contact).selectinload(UserAccount.profile))
            .where(ContactLink.owner_id == owner.id, ContactLink.is_hidden.is_(False))
        )
        if status is not None:
            stmt = stmt.where(ContactLink.status == status)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    # --- Creation / Invitation interne ---
    async def create_contact(self, owner: UserAccount, target_email: str, alias: str | None = None) -> ContactLink:
        """Cree une demande de contact bilaterale apres verification d'organisation commune."""
        stmt_user = select(UserAccount).where(UserAccount.email == target_email.lower())
        result_user = await self.session.execute(stmt_user)
        target = result_user.scalar_one_or_none()
        if target is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
        if target.id == owner.id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Vous ne pouvez  pas vous ajouter vous-même en tant que contact.")

        # Ensure both users belong to the same organization
        org_stmt = select(OrganizationMembership.organization_id).where(OrganizationMembership.user_id == owner.id)
        owner_orgs = {row[0] for row in (await self.session.execute(org_stmt)).all()}
        if not owner_orgs:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Owner has no organization")

        target_org_stmt = select(OrganizationMembership.organization_id).where(OrganizationMembership.user_id == target.id)
        target_orgs = {row[0] for row in (await self.session.execute(target_org_stmt)).all()}
        common_orgs = owner_orgs & target_orgs
        if not common_orgs:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Contact outside your organization")

        stmt_existing = select(ContactLink).where(
            ContactLink.owner_id == owner.id,
            ContactLink.contact_id == target.id,
        )
        result_existing = await self.session.execute(stmt_existing)
        if result_existing.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Contact already exists")

        owner_link = ContactLink(
            owner_id=owner.id,
            contact_id=target.id,
            status=ContactStatus.PENDING,
            alias=self._normalize_alias(alias),
            initiated_by_owner=True,
            is_hidden=False,
        )
        reciprocal_link = ContactLink(
            owner_id=target.id,
            contact_id=owner.id,
            status=ContactStatus.PENDING,
            initiated_by_owner=False,
            is_hidden=False,
        )
        self.session.add_all([owner_link, reciprocal_link])
        await self.session.flush()
        await self._log(owner, "contacts.create", resource_id=str(owner_link.id), metadata={"target": target_email})
        if self.notifications:
            display_name = None
            if owner.profile and owner.profile.display_name:
                display_name = owner.profile.display_name
            await self.notifications.enqueue_notification(
                organization_id=None,
                user_id=str(target.id),
                channel=NotificationChannel.EMAIL,
                payload={
                    "type": "contact_request",
                    "from_email": owner.email,
                    "from_display_name": display_name,
                    "contact_link_id": str(reciprocal_link.id),
                },
            )
        await self._notify_user_event(
            target.id,
            {
                "type": "contact.request",
                "title": "Nouvelle demande de contact",
                "body": f"{owner.email} souhaite collaborer.",
                "contact_id": str(reciprocal_link.id),
                "from_email": owner.email,
                "from_display_name": owner.profile.display_name if owner.profile else None,
            },
        )
        return await self._get_contact(owner.id, owner_link.id)

    # --- Mise a jour des statuts / alias ---
    async def update_status(self, owner: UserAccount, contact_id: uuid.UUID, status_value: ContactStatus) -> ContactLink:
        """Met a jour le statut d'un contact et synchronise le lien reciproque + notifications."""
        contact = await self._get_contact(owner.id, contact_id)
        reciprocal = await self._get_contact_between(contact.contact_id, owner.id)

        contact.status = status_value
        if status_value != ContactStatus.BLOCKED:
            contact.is_hidden = False
        if reciprocal:
            if status_value == ContactStatus.BLOCKED:
                reciprocal.status = ContactStatus.BLOCKED
                reciprocal.is_hidden = True
                await self._notify_user_event(
                    contact.contact_id,
                    {
                        "type": "contact.blocked",
                        "title": "Contact bloqué",
                        "body": f"{owner.email} a bloqué cette conversation.",
                        "contact_id": str(reciprocal.id) if reciprocal else None,
                        "blocked_by": str(owner.id),
                        "blocked_by_email": owner.email,
                    },
                )
                await self._notify_user_event(
                    owner.id,
                    {
                        "type": "contact.blocked",
                        "title": "Contact bloqué",
                        "body": f"Vous avez bloqué {contact.contact.email}.",
                        "contact_id": str(contact.id),
                        "blocked_target": str(contact.contact_id),
                        "blocked_target_email": contact.contact.email if contact.contact else None,
                    },
                )
            else:
                reciprocal.status = status_value
                reciprocal.is_hidden = False
                await self._notify_user_event(
                    contact.contact_id,
                    {
                        "type": "contact.unblocked",
                        "title": "Contact débloqué",
                        "body": f"{owner.email} a réactivé la conversation.",
                        "contact_id": str(reciprocal.id) if reciprocal else None,
                        "unblocked_by": str(owner.id),
                        "unblocked_by_email": owner.email,
                    },
                )
                await self._notify_user_event(
                    owner.id,
                    {
                        "type": "contact.unblocked",
                        "title": "Contact débloqué",
                        "body": f"Vous avez réactivé la conversation avec {contact.contact.email}.",
                        "contact_id": str(contact.id),
                        "unblocked_target": str(contact.contact_id),
                        "unblocked_target_email": contact.contact.email if contact.contact else None,
                    },
                )
        await self.session.flush()
        await self._log(owner, "contacts.status", resource_id=str(contact.id), metadata={"status": status_value.value})
        if status_value == ContactStatus.ACCEPTED:
            await self._notify_user_event(
                contact.contact_id,
                {
                    "type": "contact.accepted",
                    "title": "Contact confirmé",
                    "body": f"{owner.email} a accepté votre invitation.",
                    "contact_id": str(reciprocal.id) if reciprocal else None,
                },
            )
            await self._notify_user_event(
                owner.id,
                {
                    "type": "contact.accepted",
                    "title": "Contact confirmé",
                    "body": f"{contact.contact.email} est désormais disponible.",
                    "contact_id": str(contact.id),
                },
            )
        return contact

    async def update_alias(self, owner: UserAccount, contact_id: uuid.UUID, alias: str | None) -> ContactLink:
        """Met a jour l'alias d'un contact pour le proprietaire."""
        contact = await self._get_contact(owner.id, contact_id)
        normalized = self._normalize_alias(alias)
        contact.alias = normalized
        await self.session.flush()
        await self._log(owner, "contacts.alias", resource_id=str(contact.id), metadata={"alias": normalized})
        return contact

    async def delete_contact(self, owner: UserAccount, contact_id: uuid.UUID) -> None:
        """Supprime le lien de contact pour les deux utilisateurs."""
        contact = await self._get_contact(owner.id, contact_id)
        reciprocal_stmt = delete(ContactLink).where(
            or_(
                and_(ContactLink.owner_id == contact.owner_id, ContactLink.contact_id == contact.contact_id),
                and_(ContactLink.owner_id == contact.contact_id, ContactLink.contact_id == contact.owner_id),
            )
        )
        await self.session.execute(reciprocal_stmt)
        await self._log(owner, "contacts.delete", resource_id=str(contact.id))

    async def _get_contact(
        self, owner_id: uuid.UUID, contact_id: uuid.UUID, raise_not_found: bool = True
    ) -> ContactLink | None:
        """Recupere un lien de contact pour un owner, avec option de lever une 404 sinon."""
        stmt = (
            select(ContactLink)
            .options(selectinload(ContactLink.contact).selectinload(UserAccount.profile))
            .where(ContactLink.owner_id == owner_id, ContactLink.id == contact_id)
        )
        result = await self.session.execute(stmt)
        contact = result.scalar_one_or_none()
        if contact is None and raise_not_found:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
        return contact

    async def _get_contact_between(
        self, owner_id: uuid.UUID, target_user_id: uuid.UUID
    ) -> ContactLink | None:
        """Recupere un lien de contact entre deux utilisateurs si il existe."""
        stmt = (
            select(ContactLink)
            .options(selectinload(ContactLink.contact).selectinload(UserAccount.profile))
            .where(ContactLink.owner_id == owner_id, ContactLink.contact_id == target_user_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    def _normalize_alias(value: str | None) -> str | None:
        """Nettoie un alias (trim) et retourne None si vide."""
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None

    async def _log(self, owner: UserAccount, action: str, *, resource_id: str | None = None, metadata: dict | None = None) -> None:
        """Enveloppe l'appel AuditService pour tracer les actions contact."""
        if self.audit:
            await self.audit.record(
                action,
                user_id=str(owner.id),
                resource_type="contact",
                resource_id=resource_id,
                metadata=metadata,
            )

    async def _notify_user_event(self, user_id: uuid.UUID, payload: dict) -> None:
        """Publie une notification temps reel sur Redis si le broker est injecte."""
        if not self.realtime:
            return
        await self.realtime.publish_user_event(
            str(user_id),
            {
                "event": "notification",
                "payload": payload,
            },
        )
