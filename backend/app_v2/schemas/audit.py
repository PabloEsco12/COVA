"""Audit log schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel


class AuditLogEntry(BaseModel):
    id: uuid.UUID
    action: str
    timestamp: datetime
    ip: str | None = None
    user_agent: str | None = None
    details: dict | None = None

    class Config:
        from_attributes = True
