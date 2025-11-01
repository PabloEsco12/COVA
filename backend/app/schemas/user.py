"""User schemas."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserBase(BaseModel):
    email: EmailStr
    display_name: str | None = None


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=72)
    notification_login: bool | None = None


class UserRead(UserBase):
    id: UUID
    role: str
    avatar_url: str | None = None
    public_key: str | None = None
    notification_login: bool = False
    is_active: bool
    is_confirmed: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserPrivate(UserRead):
    failed_totp_attempts: int = 0
    totp_locked_until: datetime | None = None


UserRead.model_rebuild()
UserPrivate.model_rebuild()
