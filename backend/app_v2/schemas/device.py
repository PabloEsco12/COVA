"""Device schemas."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class DeviceRegisterRequest(BaseModel):
    device_id: str = Field(..., max_length=128, description="Client generated identifier / fingerprint.")
    push_token: str = Field(..., description="Base64 encoded metadata payload for the device.")
    platform: str | None = Field(default=None, max_length=64)


class DeviceOut(BaseModel):
    id: str
    record_id: UUID
    display_name: str | None
    platform: str | None
    push_token: str | None
    trust_level: int
    created_at: datetime
    last_seen_at: datetime | None
    last_seen_ip: str | None

    class Config:
        from_attributes = True


class DeviceListResponse(BaseModel):
    devices: list[DeviceOut]
