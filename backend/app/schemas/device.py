"""Device schemas."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class DeviceRead(BaseModel):
    id: UUID
    name: str
    user_agent: str | None = None
    last_seen_at: datetime | None = None
    trusted: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DeviceCreate(BaseModel):
    name: str
    user_agent: str | None = None


DeviceRead.model_rebuild()
