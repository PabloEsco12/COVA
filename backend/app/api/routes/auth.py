"""Authentication routes."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, Request, status

from ..deps import CurrentUser, DBSession
from ...core.config import settings
from ...core.security import decode_refresh_token
from ...schemas import (
    AuthSession,
    ConfirmEmailResponse,
    LoginRequest,
    LogoutAllResponse,
    LogoutResponse,
    RefreshRequest,
    RegisterRequest,
    RegisterResponse,
    TokenPair,
    UserPrivate,
)
from ...services import AuthService, LoginContext

router = APIRouter(prefix="/auth", tags=["auth"])
logger = logging.getLogger(__name__)


def _build_login_context(request: Request, payload: LoginRequest | None = None) -> LoginContext:
    client_host = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    device_name = payload.device_name if payload else None
    device_platform = payload.device_platform if payload else None
    return LoginContext(
        ip_address=client_host,
        user_agent=user_agent,
        device_name=device_name or user_agent,
        device_platform=device_platform,
    )


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest, db: DBSession) -> RegisterResponse:
    auth = AuthService(db)
    user, token_value = await auth.register_user(payload)
    confirmation_url = f"{settings.FRONTEND_URL.rstrip('/')}/confirm-email/{token_value}"
    email_sent = await auth.send_confirmation_email(user, token_value)
    if not email_sent:
        logger.warning("Failed to send confirmation email to %s", user.email)
        if settings.DEBUG:
            logger.info("Confirmation URL for %s: %s", user.email, confirmation_url)
            return RegisterResponse(
                message="Inscription enregistree, confirmation en attente.",
                user_id=user.id,
                confirmation_url=confirmation_url,
            )
        return RegisterResponse(
            message="Inscription enregistree, mais l'e-mail de confirmation n'a pas pu etre envoye. Contactez le support.",
            user_id=user.id,
        )
    return RegisterResponse(user_id=user.id)


@router.get("/confirm/{token}", response_model=ConfirmEmailResponse)
async def confirm_email(token: str, db: DBSession) -> ConfirmEmailResponse:
    auth = AuthService(db)
    user = await auth.confirm_email(token)
    return ConfirmEmailResponse(
        message="Adresse e-mail confirmee avec succes.",
        confirmed_at=user.updated_at,
    )


@router.post("/login", response_model=AuthSession)
async def login(payload: LoginRequest, request: Request, db: DBSession) -> AuthSession:
    auth = AuthService(db)
    context = _build_login_context(request, payload)
    user, access_token, refresh_token, _ = await auth.login(payload, context)
    tokens = TokenPair(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
    return AuthSession(tokens=tokens, user=UserPrivate.model_validate(user))


@router.post("/refresh", response_model=AuthSession)
async def refresh(payload: RefreshRequest, request: Request, db: DBSession) -> AuthSession:
    auth = AuthService(db)
    context = _build_login_context(request)
    user, access_token, refresh_token, _ = await auth.refresh_session(payload.refresh_token, context)
    tokens = TokenPair(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
    return AuthSession(tokens=tokens, user=UserPrivate.model_validate(user))


@router.post("/logout", response_model=LogoutResponse)
async def logout(payload: RefreshRequest, db: DBSession) -> LogoutResponse:
    _, jti = decode_refresh_token(payload.refresh_token)
    auth = AuthService(db)
    await auth.revoke_refresh_token(jti)
    return LogoutResponse()


@router.post("/logout-all", response_model=LogoutAllResponse)
async def logout_all(current_user: CurrentUser, db: DBSession) -> LogoutAllResponse:
    auth = AuthService(db)
    revoked = await auth.revoke_all_tokens(current_user.id)
    return LogoutAllResponse(revoked_count=revoked)


@router.get("/me", response_model=UserPrivate)
async def read_me(current_user: CurrentUser) -> UserPrivate:
    return UserPrivate.model_validate(current_user)
