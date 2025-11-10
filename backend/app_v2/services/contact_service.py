"""Contact management service."""

from __future__ import annotations

import uuid

from fastapi import HTTPException, status
from sqlalchemy import and_, delete, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from db_v2 import ContactLink, ContactStatus, NotificationChannel, UserAccount
from .audit_service import AuditService
from .notification_service import NotificationService


class ContactService:
    """Business logic for contacts."""

    def __init__(
        self,
        session: AsyncSession,
        *,
        audit_service: AuditService | None = None,
        notification_service: NotificationService | None = None,
    ) -> None:
        self.session = session
        self.audit = audit_service
        self.notifications = notification_service

    async def list_contacts(self, owner: UserAccount, status: ContactStatus | None = None) -> list[ContactLink]:
        stmt = (
            select(ContactLink)
            .options(selectinload(ContactLink.contact).selectinload(UserAccount.profile))
            .where(ContactLink.owner_id == owner.id)
        )
        if status is not None:
            stmt = stmt.where(ContactLink.status == status)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def create_contact(self, owner: UserAccount, target_email: str, alias: str | None = None) -> ContactLink:
        stmt_user = select(UserAccount).where(UserAccount.email == target_email.lower())
        result_user = await self.session.execute(stmt_user)
        target = result_user.scalar_one_or_none()
        if target is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
        if target.id == owner.id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot add yourself as contact")

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
        )
        reciprocal_link = ContactLink(
            owner_id=target.id,
            contact_id=owner.id,
            status=ContactStatus.PENDING,
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
        return await self._get_contact(owner.id, owner_link.id)

    async def update_status(self, owner: UserAccount, contact_id: uuid.UUID, status_value: ContactStatus) -> ContactLink:
        contact = await self._get_contact(owner.id, contact_id)
        reciprocal = await self._get_contact(contact.contact_id, owner.id, raise_not_found=False)

        contact.status = status_value
        if reciprocal:
            reciprocal.status = status_value
        await self.session.flush()
        await self._log(owner, "contacts.status", resource_id=str(contact.id), metadata={"status": status_value.value})
        return contact

    async def update_alias(self, owner: UserAccount, contact_id: uuid.UUID, alias: str | None) -> ContactLink:
        contact = await self._get_contact(owner.id, contact_id)
        normalized = self._normalize_alias(alias)
        contact.alias = normalized
        await self.session.flush()
        await self._log(owner, "contacts.alias", resource_id=str(contact.id), metadata={"alias": normalized})
        return contact

    async def delete_contact(self, owner: UserAccount, contact_id: uuid.UUID) -> None:
        contact = await self._get_contact(owner.id, contact_id)
        reciprocal_stmt = delete(ContactLink).where(
            or_(
                and_(ContactLink.owner_id == contact.owner_id, ContactLink.contact_id == contact.contact_id),
                and_(ContactLink.owner_id == contact.contact_id, ContactLink.contact_id == contact.owner_id),
            )
        )
        await self.session.execute(reciprocal_stmt)
        await self._log(owner, "contacts.delete", resource_id=str(contact.id))

    async def _get_contact(self, owner_id: uuid.UUID, contact_id: uuid.UUID, raise_not_found: bool = True) -> ContactLink | None:
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

    @staticmethod
    def _normalize_alias(value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None

    async def _log(self, owner: UserAccount, action: str, *, resource_id: str | None = None, metadata: dict | None = None) -> None:
        if self.audit:
            await self.audit.record(
                action,
                user_id=str(owner.id),
                resource_type="contact",
                resource_id=resource_id,
                metadata=metadata,
            )
