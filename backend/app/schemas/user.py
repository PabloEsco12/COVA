"""User schemas for API responses."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    id: uuid.UUID
    email: EmailStr
    role: str
    is_confirmed: bool


class UserProfileOut(BaseModel):
    display_name: str | None = None
    avatar_url: str | None = None
    locale: str | None = None
    timezone: str | None = None
    profile_data: dict | None = None


class UserOut(UserBase):
    is_active: bool
    created_at: datetime
    profile: UserProfileOut | None = None

    class Config:
        from_attributes = True


class MeSummaryOut(BaseModel):
    id: uuid.UUID
    email: EmailStr
    pseudo: str
    avatar: str | None = None
    avatar_url: str | None = None
    date_crea: datetime | None = None


class MeProfileOut(BaseModel):
    email: EmailStr
    display_name: str | None = None
    avatar_url: str | None = None
    locale: str | None = None
    timezone: str | None = None
    job_title: str | None = None
    department: str | None = None
    phone_number: str | None = None
    pgp_public_key: str | None = None
    status_message: str | None = None


class MeProfileUpdate(BaseModel):
    display_name: str | None = None
    locale: str | None = None
    timezone: str | None = None
    job_title: str | None = None
    department: str | None = None
    phone_number: str | None = None
    pgp_public_key: str | None = None
    status_message: str | None = None


class AvatarResponse(BaseModel):
    avatar_url: str | None = None


class AccountDeleteRequest(BaseModel):
    password: str
