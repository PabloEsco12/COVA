"""
Schemas Pydantic pour les journaux d'audit.

Infos utiles:
- Utilises pour serialiser les entrees d'audit exposees par l'API.
- Config from_attributes activee pour mapper directement depuis les models SQLAlchemy.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel


class AuditLogEntry(BaseModel):
    """Entree d'audit exposee a l'API."""
    id: uuid.UUID
    action: str
    timestamp: datetime
    ip: str | None = None
    user_agent: str | None = None
    details: dict | None = None

    class Config:
        from_attributes = True
