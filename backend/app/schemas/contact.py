"""Contact schemas."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ContactUserInfo(BaseModel):
    id: UUID
    email: str
    display_name: str | None = None
    avatar_url: str | None = None

    model_config = ConfigDict(from_attributes=True)


class ContactRead(BaseModel):
    id: UUID
    owner_id: UUID
    contact_id: UUID
    alias: str | None = None
    status: str
    created_at: datetime
    updated_at: datetime
    is_sender: bool
    contact: ContactUserInfo | None = None
    owner: ContactUserInfo | None = None

    model_config = ConfigDict(from_attributes=True)


class ContactCreate(BaseModel):
    email: str | None = None
    contact_id: UUID | None = None
    alias: str | None = None


class ContactUpdateAlias(BaseModel):
    alias: str | None = None


class ContactRespond(BaseModel):
    status: str


ContactRead.model_rebuild()
