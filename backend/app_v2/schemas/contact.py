"""Contact API schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from db_v2 import ContactStatus


class ContactCreateRequest(BaseModel):
    email: EmailStr
    alias: str | None = Field(default=None, max_length=160)


class ContactStatusUpdate(BaseModel):
    status: ContactStatus


class ContactAliasUpdate(BaseModel):
    alias: str | None = Field(default=None, max_length=160)


class ContactOut(BaseModel):
    id: uuid.UUID
    contact_user_id: uuid.UUID
    email: EmailStr
    display_name: str | None
    avatar_url: str | None = None
    job_title: str | None = None
    department: str | None = None
    phone_number: str | None = None
    status_message: str | None = None
    status: ContactStatus
    alias: str | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
