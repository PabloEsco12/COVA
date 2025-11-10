"""Schemas related to account security settings."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class SecuritySettingsOut(BaseModel):
    totp_enabled: bool
    notification_login: bool
    last_totp_failure_at: datetime | None = None
    totp_locked_until: datetime | None = None
    has_recovery_codes: bool = False


class SecuritySettingsUpdate(BaseModel):
    notification_login: bool | None = Field(default=None)


class TotpActivateResponse(BaseModel):
    secret: str
    provisioning_uri: str
    qr_code: str  # base64 encoded PNG data


class TotpConfirmRequest(BaseModel):
    code: str = Field(..., min_length=6, max_length=8, pattern=r"^\d+$")


class TotpConfirmResponse(BaseModel):
    message: str
    recovery_codes: list[str]


class TotpDeactivateResponse(BaseModel):
    message: str

