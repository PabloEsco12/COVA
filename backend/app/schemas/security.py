"""
############################################################
# Schemas : Security (TOTP & preferences)
# Auteur : Valentin Masurelle
# Date   : 2025-05-04
#
# Description:
# - Reglages de securite (MFA/TOTP, alertes) et codes de recuperation.
# - QR code de provisioning en PNG base64.
############################################################
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class SecuritySettingsOut(BaseModel):
    """Etat des reglages de securite exposes au frontend."""
    totp_enabled: bool
    notification_login: bool
    last_totp_failure_at: datetime | None = None
    totp_locked_until: datetime | None = None
    has_recovery_codes: bool = False


class SecuritySettingsUpdate(BaseModel):
    """Mise a jour partielle des preferences de securite."""
    notification_login: bool | None = Field(default=None)


class TotpActivateResponse(BaseModel):
    """Retour lors du demarrage d'activation TOTP (secret + QR)."""
    secret: str
    provisioning_uri: str
    qr_code: str  # base64 encoded PNG data


class TotpConfirmRequest(BaseModel):
    """Code fourni par l'utilisateur pour confirmer le TOTP."""
    code: str = Field(..., min_length=6, max_length=8, pattern=r"^\d+$")


class TotpConfirmResponse(BaseModel):
    """Reponse de confirmation incluant les codes de recuperation."""
    message: str
    recovery_codes: list[str]


class TotpDeactivateResponse(BaseModel):
    """Message de confirmation de desactivation TOTP."""
    message: str

