"""Notification routes."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import JSONResponse

from ...dependencies import get_notification_service, get_current_user
from ...schemas.notification import (
    NotificationPreferenceOut,
    NotificationPreferenceUpdate,
    OutboundNotificationOut,
    NotificationTestResponse,
)
from ...services.auth_service import build_login_alert_payload, should_send_login_alert
from ...services.notification_service import NotificationService
from app.models import NotificationChannel, NotificationPreference, OutboundNotification, UserAccount

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("/preferences", response_model=list[NotificationPreferenceOut])
async def list_preferences(
    current_user: UserAccount = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service),
) -> list[NotificationPreferenceOut]:
    prefs = await service.list_preferences(current_user)
    return [NotificationPreferenceOut.model_validate(pref) for pref in prefs]


@router.put("/preferences/{channel}", response_model=NotificationPreferenceOut)
async def update_preference(
    channel: NotificationChannel,
    payload: NotificationPreferenceUpdate,
    current_user: UserAccount = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service),
) -> NotificationPreferenceOut:
    pref = await service.upsert_preference(
        current_user,
        channel,
        is_enabled=payload.is_enabled,
        quiet_hours=payload.quiet_hours,
    )
    await service.session.flush()
    await service.session.commit()
    return NotificationPreferenceOut.model_validate(pref)


@router.post("/outbox", response_model=OutboundNotificationOut, status_code=status.HTTP_201_CREATED)
async def enqueue_notification(
    channel: NotificationChannel,
    payload: dict,
    current_user: UserAccount = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service),
) -> OutboundNotificationOut:
    notification = await service.enqueue_notification(
        organization_id=None,
        user_id=str(current_user.id),
        channel=channel,
        payload=payload,
    )
    await service.session.flush()
    await service.session.commit()
    return OutboundNotificationOut.model_validate(notification)


@router.post("/test/login-alert", response_model=NotificationTestResponse, status_code=status.HTTP_200_OK)
async def send_login_alert_test(
    request: Request,
    current_user: UserAccount = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service),
) -> NotificationTestResponse:
    login_time = datetime.now(timezone.utc)
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    if not should_send_login_alert(current_user, now_utc=login_time):
        return NotificationTestResponse(
            skipped=True,
            detail="Aucune alerte envoyée : plage silencieuse active ou canal désactivé.",
        )

    session_id = f"TEST-{uuid.uuid4().hex[:12].upper()}"
    timezone_pref = current_user.profile.timezone if current_user.profile else None
    payload = build_login_alert_payload(
        user=current_user,
        session_id=session_id,
        login_time=login_time,
        ip_address=ip_address,
        user_agent=user_agent,
        timezone_pref=timezone_pref,
    )
    notification = await service.enqueue_notification(
        organization_id=None,
        user_id=str(current_user.id),
        channel=NotificationChannel.EMAIL,
        payload=payload,
    )
    await service.session.flush()
    await service.session.commit()
    return NotificationTestResponse(
        skipped=False,
        detail="E-mail de test programmé.",
        notification=OutboundNotificationOut.model_validate(notification),
    )

