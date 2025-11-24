"""
Routes d'authentification de l'API v2.

Infos utiles:
- Couvre inscription/confirmation, login avec TOTP, refresh et revocation de sessions.
- Commit explicite de la session apres chaque operation pour garder le controle transactionnel.
- Les tokens renvoient l'expiration en secondes pour l'UI.
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import JSONResponse

from ...config import settings
from ...dependencies import (
    get_auth_service,
    get_current_user,
)
from ...schemas.auth import (
    AuthSession,
    ConfirmEmailResponse,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    LoginRequest,
    LogoutAllResponse,
    LogoutResponse,
    ResendConfirmationRequest,
    ResendConfirmationResponse,
    RefreshRequest,
    RegisterRequest,
    RegisterResponse,
    ResetPasswordRequest,
    ResetPasswordResponse,
)
from ...schemas.token import TokenPair
from ...schemas.user import UserOut
from ...services.auth_service import AuthService, TotpRequiredError
from app.models import UserAccount

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=RegisterResponse, status_code=201)
async def register(payload: RegisterRequest, service: AuthService = Depends(get_auth_service)) -> RegisterResponse:
    """Cree un utilisateur puis envoie l'email de confirmation si necessaire."""
    result = await service.register_user(
        email=payload.email,
        password=payload.password,
        display_name=payload.display_name,
    )
    await service.session.commit()
    confirmation_url = None
    if result.confirmation_token:
        confirmation_url = f"{settings.FRONTEND_ORIGIN.rstrip('/')}/confirm-email/{result.confirmation_token}"
    return RegisterResponse(
        message="Registration successful. Please confirm your email.",
        user_id=str(result.user.id),
        confirmation_url=confirmation_url,
    )


@router.get("/confirm/{token}", response_model=ConfirmEmailResponse)
async def confirm_email(token: str, service: AuthService = Depends(get_auth_service)) -> ConfirmEmailResponse:
    """Confirme un email a partir d'un token unique."""
    user = await service.confirm_email(token)
    await service.session.commit()
    return ConfirmEmailResponse(
        message="Confirmation de mail réussie.",
        user=UserOut.model_validate(user, from_attributes=True),
    )


@router.post("/resend-confirmation", response_model=ResendConfirmationResponse)
async def resend_confirmation(
    payload: ResendConfirmationRequest,
    service: AuthService = Depends(get_auth_service),
) -> ResendConfirmationResponse:
    """Rengendre et envoie un token de confirmation pour un email non confirme."""
    await service.resend_confirmation_email(payload.email)
    await service.session.commit()
    return ResendConfirmationResponse(message="Confirmation email resent.")


@router.post("/forgot-password", response_model=ForgotPasswordResponse)
async def forgot_password(
    payload: ForgotPasswordRequest,
    service: AuthService = Depends(get_auth_service),
) -> ForgotPasswordResponse:
    """Declenche une demande de reset mot de passe."""
    await service.request_password_reset(payload.email)
    await service.session.commit()
    return ForgotPasswordResponse()


@router.post("/reset-password", response_model=ResetPasswordResponse)
async def reset_password(
    payload: ResetPasswordRequest,
    service: AuthService = Depends(get_auth_service),
) -> ResetPasswordResponse:
    """Applique un nouveau mot de passe apres validation du token de reset."""
    await service.reset_password(token_value=payload.token, new_password=payload.password)
    await service.session.commit()
    return ResetPasswordResponse()


@router.post("/login", response_model=AuthSession)
async def login(
    payload: LoginRequest,
    request: Request,
    service: AuthService = Depends(get_auth_service),
) -> AuthSession:
    """Authentifie l'utilisateur (TOTP si actif) et emet les tokens."""
    try:
        user = await service.authenticate_user(payload.email, payload.password, payload.totp_code)
    except TotpRequiredError:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                "require_totp": True,
                "detail": "Two-factor authentication code required.",
            },
        )
    auth_result = await service.issue_tokens(
        user,
        user_agent=request.headers.get("user-agent"),
        ip_address=request.client.host if request.client else None,
    )
    await service.session.commit()
    expires_in = int((auth_result.refresh_expires_at - datetime.now(timezone.utc)).total_seconds())
    return AuthSession(
        tokens=TokenPair(
            access_token=auth_result.access_token,
            refresh_token=auth_result.refresh_token,
            expires_in=expires_in,
        ),
        user=UserOut.model_validate(auth_result.user, from_attributes=True),
    )


@router.post("/refresh", response_model=AuthSession)
async def refresh_tokens(payload: RefreshRequest, service: AuthService = Depends(get_auth_service)) -> AuthSession:
    """Recree un couple de tokens a partir d'un refresh valide."""
    auth_result = await service.refresh_session(payload.refresh_token)
    await service.session.commit()
    expires_in = int((auth_result.refresh_expires_at - datetime.now(timezone.utc)).total_seconds())
    return AuthSession(
        tokens=TokenPair(
            access_token=auth_result.access_token,
            refresh_token=auth_result.refresh_token,
            expires_in=expires_in,
        ),
        user=UserOut.model_validate(auth_result.user, from_attributes=True),
    )


@router.post("/logout", response_model=LogoutResponse)
async def logout(payload: RefreshRequest, service: AuthService = Depends(get_auth_service)) -> LogoutResponse:
    """Revoque un refresh token et sa session associee."""
    await service.revoke_refresh_token(payload.refresh_token)
    await service.session.commit()
    return LogoutResponse()


@router.post("/logout-all", response_model=LogoutAllResponse)
async def logout_all(
    current_user: UserAccount = Depends(get_current_user),
    service: AuthService = Depends(get_auth_service),
) -> LogoutAllResponse:
    """Revoque toutes les sessions de l'utilisateur courant."""
    revoked = await service.revoke_all_tokens(current_user)
    await service.session.commit()
    return LogoutAllResponse(revoked_count=revoked)
