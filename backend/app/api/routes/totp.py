"""
############################################################
# Routes : MFA/TOTP
# Auteur  : Valentin Masurelle
# Date    : 2025-05-04
#
# Description:
# - Active/Confirme/Desactive la MFA TOTP pour l'utilisateur courant.
# - Commit explicite apres mutation de l'etat de securite.
############################################################
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from ...dependencies import get_current_user, get_security_service
from ...schemas.security import (
    TotpActivateResponse,
    TotpConfirmRequest,
    TotpConfirmResponse,
    TotpDeactivateResponse,
)
from ...services.security_service import SecurityService
from app.models import UserAccount

router = APIRouter(prefix="/auth/totp", tags=["mfa"])


@router.post("/activate", response_model=TotpActivateResponse)
async def activate_totp(
    current_user: UserAccount = Depends(get_current_user),
    security: SecurityService = Depends(get_security_service),
) -> TotpActivateResponse:
    """Démarre l'activation TOTP et retourne secret + QR code base64."""
    enrollment = await security.start_totp_enrollment(current_user)
    await security.session.commit()
    return TotpActivateResponse(
        secret=enrollment["secret"],
        provisioning_uri=enrollment["provisioning_uri"],
        qr_code=enrollment["qr_code"],
    )


@router.post("/confirm", response_model=TotpConfirmResponse)
async def confirm_totp(
    payload: TotpConfirmRequest,
    current_user: UserAccount = Depends(get_current_user),
    security: SecurityService = Depends(get_security_service),
) -> TotpConfirmResponse:
    """Valide le code TOTP fourni et génère les codes de récupération."""
    recovery_codes = await security.confirm_totp(current_user, payload.code)
    await security.session.commit()
    return TotpConfirmResponse(
        message="Double authentification activée.",
        recovery_codes=recovery_codes,
    )


@router.post("/deactivate", response_model=TotpDeactivateResponse)
async def deactivate_totp(
    current_user: UserAccount = Depends(get_current_user),
    security: SecurityService = Depends(get_security_service),
) -> TotpDeactivateResponse:
    """Désactive la double authentification TOTP pour l'utilisateur."""
    await security.deactivate_totp(current_user)
    await security.session.commit()
    return TotpDeactivateResponse(message="Double authentification désactivée.")