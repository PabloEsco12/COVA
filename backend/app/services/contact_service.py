"""Contact management service."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import Select, and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from ..models.contact import Contact
from ..models.enums import ContactStatus
from ..models.user import User


class ContactService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_contacts(
        self,
        user_id: UUID,
        *,
        status_filter: ContactStatus | None = None,
    ) -> list[Contact]:
        stmt: Select[tuple[Contact]] = (
            select(Contact)
            .where(or_(Contact.owner_id == user_id, Contact.contact_id == user_id))
            .options(joinedload(Contact.contact), joinedload(Contact.owner))
            .order_by(Contact.updated_at.desc())
        )
        if status_filter is not None:
            stmt = stmt.where(Contact.status == status_filter)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def list_pending_requests(self, user_id: UUID) -> list[Contact]:
        stmt = (
            select(Contact)
            .where(Contact.contact_id == user_id, Contact.status == ContactStatus.PENDING)
            .options(joinedload(Contact.owner))
            .order_by(Contact.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def request_contact(
        self,
        owner_id: UUID,
        *,
        contact_email: str | None = None,
        contact_id: UUID | None = None,
        alias: str | None = None,
    ) -> Contact:
        target_user = await self._resolve_user(contact_email=contact_email, contact_id=contact_id)
        if target_user.id == owner_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Impossible de s'ajouter soi-même")

        existing = await self._find_relationship(owner_id, target_user.id)
        if existing:
            if (
                existing.status == ContactStatus.PENDING
                and existing.owner_id == target_user.id
                and existing.contact_id == owner_id
            ):
                # Auto-accept reciprocal pending request
                async with self.session.begin():
                    existing.status = ContactStatus.ACCEPTED
                    existing.updated_at = datetime.now(timezone.utc)
                return existing
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Contact already exists or pending")

        contact = Contact(
            owner_id=owner_id,
            contact_id=target_user.id,
            status=ContactStatus.PENDING,
            alias=alias,
        )
        async with self.session.begin():
            self.session.add(contact)
        await self.session.refresh(contact, attribute_names=["contact"])
        return contact

    async def respond_to_request(self, contact_id: UUID, user_id: UUID, *, status_value: ContactStatus) -> Contact:
        contact = await self._get_contact(contact_id)
        if contact.contact_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Action non autorisée")
        if contact.status != ContactStatus.PENDING:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invitation déjà traitée")
        if status_value not in (ContactStatus.ACCEPTED, ContactStatus.BLOCKED):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Statut invalide")

        async with self.session.begin():
            contact.status = status_value
            contact.updated_at = datetime.now(timezone.utc)
        await self.session.refresh(contact, attribute_names=["owner", "contact"])
        return contact

    async def update_alias(self, contact_id: UUID, user_id: UUID, alias: str | None) -> Contact:
        contact = await self._get_contact(contact_id)
        if contact.owner_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Seul l'émetteur peut modifier l'alias")
        async with self.session.begin():
            contact.alias = alias
            contact.updated_at = datetime.now(timezone.utc)
        return contact

    async def remove_contact(self, contact_id: UUID, user_id: UUID) -> None:
        contact = await self._get_contact(contact_id)
        if user_id not in (contact.owner_id, contact.contact_id):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Suppression non autorisée")
        async with self.session.begin():
            await self.session.delete(contact)

    async def _get_contact(self, contact_id: UUID) -> Contact:
        stmt = select(Contact).where(Contact.id == contact_id)
        result = await self.session.execute(stmt)
        contact = result.scalar_one_or_none()
        if contact is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact introuvable")
        return contact

    async def _resolve_user(self, *, contact_email: str | None, contact_id: UUID | None) -> User:
        if contact_id is not None:
            stmt = select(User).where(User.id == contact_id)
        elif contact_email:
            stmt = select(User).where(User.email == contact_email.lower())
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="email ou identifiant requis")

        result = await self.session.execute(stmt)
        user = result.scalar_one_or_none()
        if user is None or not user.is_active:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilisateur introuvable")
        return user

    async def _find_relationship(self, user_a: UUID, user_b: UUID) -> Contact | None:
        stmt = select(Contact).where(
            or_(
                and_(Contact.owner_id == user_a, Contact.contact_id == user_b),
                and_(Contact.owner_id == user_b, Contact.contact_id == user_a),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()


