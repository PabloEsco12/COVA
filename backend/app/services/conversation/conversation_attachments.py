from __future__ import annotations

import contextlib

from sqlalchemy import select

from app.models import (
    ConversationMember,
    Message,
    MessageAttachment,
    MessageDelivery,
    MessageDeliveryState,
    MessageType,
    UserAccount,
)
from .conversation_base import ConversationBase
from ..attachment_service import AttachmentDescriptor
from ...config import settings


class ConversationAttachmentMixin(ConversationBase):
    """Persistance et sérialisation des pièces jointes et messages."""

    async def _persist_attachments(self, message: Message, descriptors: list[AttachmentDescriptor]) -> None:
        """Enregistre les métadonnées des pièces jointes associées à un message."""
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
        """Prépare le payload API d'un message, incluant réactions, pins et état de livraison."""
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

        viewer_member_id = viewer_membership.id if viewer_membership else None
        if viewer_member_id:
            delivery = self._match_delivery(message, viewer_member_id)
            if delivery is None:
                delivery = await self._fetch_delivery(message.id, viewer_member_id)
            if delivery:
                payload["delivery_state"] = delivery.state.value
                payload["delivered_at"] = delivery.delivered_at.isoformat() if delivery.delivered_at else None
                payload["read_at"] = delivery.read_at.isoformat() if delivery.read_at else None

        deliveries = getattr(message, "deliveries", None)
        if deliveries is None:
            stmt = select(MessageDelivery).where(MessageDelivery.message_id == message.id)
            result = await self.session.execute(stmt)
            deliveries = result.scalars().all()
        summary = {"total": 0, "delivered": 0, "read": 0, "pending": 0}
        for delivery in deliveries or []:
            if viewer_member_id and delivery.member_id == viewer_member_id:
                continue
            summary["total"] += 1
            if delivery.state == MessageDeliveryState.READ:
                summary["read"] += 1
                summary["delivered"] += 1
            elif delivery.state == MessageDeliveryState.DELIVERED:
                summary["delivered"] += 1
            else:
                summary["pending"] += 1
        payload["delivery_summary"] = summary

        attachments = getattr(message, "attachments", None) or []
        payload["attachments"] = [self._serialize_attachment(attachment) for attachment in attachments]
        payload["reply_to"] = self._serialize_reference(getattr(message, "reply_to", None))
        payload["forward_from"] = self._serialize_reference(getattr(message, "forwarded_from", None))
        if payload["deleted"]:
            payload["content"] = ""
            payload["attachments"] = []

        return payload

    def _serialize_attachment(self, attachment: MessageAttachment) -> dict:
        """Prepare les metadonnees exposees d'une piece jointe (lien presigne si stockage dispo)."""
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
        """Formate une reference de message (reply/forward) avec un extrait en clair."""
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
