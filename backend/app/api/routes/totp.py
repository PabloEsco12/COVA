"""Routes to manage TOTP-based multi-factor authentication."""

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
    recovery_codes = await security.confirm_totp(current_user, payload.code)
    await security.session.commit()
    return TotpConfirmResponse(
        message="Double authentification activee.",
        recovery_codes=recovery_codes,
    )


@router.post("/deactivate", response_model=TotpDeactivateResponse)
async def deactivate_totp(
    current_user: UserAccount = Depends(get_current_user),
    security: SecurityService = Depends(get_security_service),
) -> TotpDeactivateResponse:
    await security.deactivate_totp(current_user)
    await security.session.commit()
    return TotpDeactivateResponse(message="Double authentification desactivee.")
