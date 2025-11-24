"""
Modèles SQLAlchemy pour les demandes de confidentialité/conformité.

Infos utiles:
- Suivi des demandes d'export ou suppression avec statut et horodatages.
- Suppressions en cascade sur organisation et utilisateur pour eviter les orphelins.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .enums import PrivacyRequestStatus, PrivacyRequestType


class PrivacyRequest(Base):
    """Trace les demandes RGPD type export ou suppression."""

    __tablename__ = "privacy_requests"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("user_accounts.id", ondelete="CASCADE"), nullable=False
    )
    request_type: Mapped[PrivacyRequestType] = mapped_column(Enum(PrivacyRequestType, name="privacy_request_type"), nullable=False)
    status: Mapped[PrivacyRequestStatus] = mapped_column(
        Enum(PrivacyRequestStatus, name="privacy_request_status"),
        nullable=False,
        default=PrivacyRequestStatus.RECEIVED,
    )
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    notes: Mapped[str | None] = mapped_column(Text)

    organization = relationship("Organization")
    user = relationship("UserAccount", back_populates="privacy_requests")
