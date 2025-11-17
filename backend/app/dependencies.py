"""Common FastAPI dependencies for the v2 application."""

from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from .db.session import get_session
from app.models import UserAccount  # type: ignore[import]
from .core.security import decode_token
from .core.redis import get_redis, RealtimeBroker
from .core.storage import get_storage, ObjectStorage
from .core.antivirus import get_antivirus_scanner
from .services.audit_service import AuditService
from .services.notification_service import NotificationService
from .services.auth_service import AuthService
from .services.contact_service import ContactService
from .services.conversation_service import ConversationService
from .services.security_service import SecurityService
from .services.device_service import DeviceService
from .services.attachment_service import AttachmentService
from .services.organization_service import OrganizationService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


async def get_db(session: AsyncSession = Depends(get_session)) -> AsyncSession:
    return session


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_session),
) -> UserAccount:
    try:
        payload = decode_token(token)
        user_id = payload.get("sub")
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    stmt = (
        select(UserAccount)
        .options(
            selectinload(UserAccount.profile),
            selectinload(UserAccount.security_state),
            selectinload(UserAccount.totp_secret),
            selectinload(UserAccount.notification_preferences),
        )
        .where(UserAccount.id == user_id)
    )
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Inactive or unknown user")
    return user


__all__ = [
    "get_db",
    "get_current_user",
    "oauth2_scheme",
    "get_audit_service",
    "get_notification_service",
    "get_realtime_broker",
    "get_storage_service",
    "get_attachment_service",
    "get_auth_service",
    "get_contact_service",
    "get_conversation_service",
    "get_security_service",
    "get_device_service",
    "get_organization_service",
]


async def get_audit_service(db: AsyncSession = Depends(get_session)) -> AuditService:
    return AuditService(db)


async def get_notification_service(db: AsyncSession = Depends(get_session)) -> NotificationService:
    return NotificationService(db)


async def get_realtime_broker() -> RealtimeBroker:
    redis = await get_redis()
    return RealtimeBroker(redis)


def get_storage_service() -> ObjectStorage | None:
    return get_storage()


def get_attachment_service() -> AttachmentService:
    storage = get_storage()
    if storage is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Stockage des pièces jointes indisponible.")
    scanner = get_antivirus_scanner()
    return AttachmentService(storage, scanner)


async def get_auth_service(db: AsyncSession = Depends(get_session)) -> AuthService:
    audit = AuditService(db)
    notifications = NotificationService(db)
    return AuthService(db, audit_service=audit, notification_service=notifications)


async def get_contact_service(db: AsyncSession = Depends(get_session)) -> ContactService:
    audit = AuditService(db)
    notifications = NotificationService(db)
    redis = await get_redis()
    realtime = RealtimeBroker(redis)
    return ContactService(db, audit_service=audit, notification_service=notifications, realtime_broker=realtime)


async def get_conversation_service(db: AsyncSession = Depends(get_session)) -> ConversationService:
    audit = AuditService(db)
    redis = await get_redis()
    realtime = RealtimeBroker(redis)
    storage = get_storage()
    attachment_service = AttachmentService(storage, None) if storage else None  # reuse token decoder
    return ConversationService(
        db,
        audit_service=audit,
        realtime_broker=realtime,
        storage_service=storage,
        attachment_decoder=attachment_service,
    )


async def get_security_service(db: AsyncSession = Depends(get_session)) -> SecurityService:
    audit = AuditService(db)
    return SecurityService(db, audit_service=audit)


async def get_device_service(db: AsyncSession = Depends(get_session)) -> DeviceService:
    audit = AuditService(db)
    return DeviceService(db, audit_service=audit)


async def get_organization_service(db: AsyncSession = Depends(get_session)) -> OrganizationService:
    audit = AuditService(db)
    return OrganizationService(db, audit_service=audit)
