"""
############################################################
# Schemas : Audit (Pydantic)
# Auteur : Valentin Masurelle
# Date   : 2025-05-04
#
# Description:
# - Serialisation des entrees d'audit exposees par l'API.
# - from_attributes active pour mapper depuis SQLAlchemy.
############################################################
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
