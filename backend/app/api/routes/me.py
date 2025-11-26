"""
############################################################
# Routes : Me (profil, devices, overview, securite)
# Auteur  : Valentin Masurelle
# Date    : 2025-06-04
#
# Description:
# - Gère le compte courant: profil, avatar, devices, overview, audit, securite.
# - Inclut la suppression de compte et le changement de mot de passe.
#
# Points de vigilance:
# - Toujours rafraichir/commit les entites modifiees.
# - Nettoyer les fichiers avatars supprimes pour eviter les orphelins.
# - Respecter les verifications de mot de passe sur suppression/modification.
############################################################
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from urllib.parse import urlparse

from fastapi import APIRouter, Body, Depends, File, HTTPException, Request, Response, UploadFile, status
from PIL import Image, UnidentifiedImageError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete, func, select, update

from ...config import settings
from ...dependencies import (
    get_audit_service,
    get_conversation_service,
    get_current_user,
    get_db,
    get_device_service,
    get_organization_service,
    get_security_service,
)
from ...schemas.audit import AuditLogEntry
from ...schemas.device import DeviceListResponse, DeviceOut, DeviceRegisterRequest
from ...schemas.organization import OrganizationMembershipInfo, OrganizationSummary
from ...schemas.overview import (
    ConversationSummary,
    OverviewProfile,
    OverviewResponse,
    OverviewSecurity,
    OverviewStats,
)
from ...schemas.security import SecuritySettingsOut, SecuritySettingsUpdate
from ...schemas.user import (
    AccountDeleteRequest,
    AvatarResponse,
    MeProfileOut,
    MeProfileUpdate,
    MeSummaryOut,
    PasswordUpdateRequest,
)
from ...services.audit_service import AuditService
from ...services.conversation_service import ConversationService
from ...services.device_service import DeviceService
from ...services.organization_service import OrganizationService
from ...services.security_service import SecurityService
from ...core.security import get_password_hash, verify_password
from app.models import (
    ContactLink,
    ContactStatus,
    Conversation,
    ConversationMember,
    Device,
    Message,
    MessageDelivery,
    MessageDeliveryState,
    OrganizationMembership,
    UserAccount,
    UserProfile,
)

router = APIRouter(prefix="/me", tags=["me"])


MEDIA_ROOT = Path(settings.MEDIA_ROOT).resolve()
AVATAR_DIR = MEDIA_ROOT / "avatars"
ALLOWED_CONTENT_TYPES = {"image/png", "image/jpeg", "image/webp", "image/gif"}
MAX_AVATAR_BYTES = settings.AVATAR_MAX_BYTES
MAX_AVATAR_SIZE = settings.AVATAR_MAX_SIZE

AVATAR_DIR.mkdir(parents=True, exist_ok=True)


def _clean(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    return value or None


def _build_avatar_url(filename: str) -> str:
    base = settings.PUBLIC_BASE_URL.rstrip("/")
    return f"{base}/static/avatars/{filename}"


def _avatar_path_from_url(url: str | None) -> Path | None:
    if not url:
        return None
    parsed = urlparse(url)
    path = parsed.path.lstrip("/")
    if not path:
        return None
    if path.startswith("static/"):
        path = path[len("static/") :]
    return MEDIA_ROOT / path


def _remove_avatar_file(url: str | None) -> None:
    path = _avatar_path_from_url(url)
    if path and path.is_file():
        try:
            path.unlink()
        except OSError:
            pass


async def _reassign_conversations_before_delete(db: AsyncSession, user_id: uuid.UUID) -> None:
    """Reassigne les conversations possedees ou les supprime si orphelines avant suppression de compte."""
    conversation_ids = (
        await db.execute(select(Conversation.id).where(Conversation.created_by == user_id))
    ).scalars().all()
    for conv_id in conversation_ids:
        replacement = (
            await db.execute(
                select(ConversationMember.user_id)
                .where(ConversationMember.conversation_id == conv_id)
                .where(ConversationMember.user_id != user_id)
                .limit(1)
            )
        ).scalar_one_or_none()
        if replacement:
            await db.execute(
                update(Conversation).where(Conversation.id == conv_id).values(created_by=replacement)
            )
        else:
            await db.execute(delete(Conversation).where(Conversation.id == conv_id))


def _ensure_profile(user: UserAccount, db: AsyncSession) -> UserProfile:
    """Cree le profil utilisateur si absent et le rattache a la session."""
    profile = user.profile
    if profile is None:
        profile = UserProfile(user_id=user.id)
        db.add(profile)
        user.profile = profile
    return profile


def _guess_avatar_filename(url: str | None) -> str | None:
    if not url:
        return None
    parsed = urlparse(url)
    return Path(parsed.path).name or None


def _build_profile_response(user: UserAccount) -> MeProfileOut:
    """Assemble le schema de profil API a partir des donnees utilisateur."""
    profile = user.profile
    profile_data = profile.profile_data if profile and profile.profile_data else {}
    return MeProfileOut(
        email=user.email,
        display_name=profile.display_name if profile else None,
        avatar_url=profile.avatar_url if profile else None,
        locale=profile.locale if profile else None,
        timezone=profile.timezone if profile else None,
        job_title=profile_data.get("job_title"),
        department=profile_data.get("department"),
        phone_number=profile_data.get("phone_number"),
        pgp_public_key=profile_data.get("pgp_public_key"),
        status_message=profile_data.get("status_message"),
    )


def _build_device_response(device: Device) -> DeviceOut:
    metadata = device.device_metadata or {}
    push_token = metadata.get("push_token")
    return DeviceOut(
        id=device.fingerprint or str(device.id),
        record_id=device.id,
        display_name=device.display_name,
        platform=device.platform,
        push_token=push_token,
        trust_level=device.trust_level,
        created_at=device.registered_at,
        last_seen_at=device.last_seen_at,
        last_seen_ip=device.last_seen_ip,
    )


async def _count_contact_stats(db: AsyncSession, user_id: uuid.UUID) -> tuple[int, int]:
    """Calcule le nombre total de contacts et le nombre en attente."""
    total_stmt = select(func.count(ContactLink.id)).where(ContactLink.owner_id == user_id)
    pending_stmt = (
        select(func.count(ContactLink.id))
        .where(ContactLink.owner_id == user_id)
        .where(ContactLink.status == ContactStatus.PENDING)
    )
    total_result = await db.execute(total_stmt)
    pending_result = await db.execute(pending_stmt)
    total = int(total_result.scalar_one() or 0)
    pending = int(pending_result.scalar_one() or 0)
    return total, pending


def _summarize_devices(devices: list[Device]) -> dict[str, object]:
    """Retourne un snapshot des appareils (total, a risque, dernier vu)."""
    total = len(devices)
    at_risk = 0
    last_seen_at = None
    for device in devices:
        trust_level = device.trust_level or 0
        if trust_level < 50:
            at_risk += 1
        if device.last_seen_at and (last_seen_at is None or device.last_seen_at > last_seen_at):
            last_seen_at = device.last_seen_at
    return {"total": total, "at_risk": at_risk, "last_seen_at": last_seen_at}


async def _summarize_conversations(
    db: AsyncSession,
    conversations: list[Conversation],
    user_id: uuid.UUID,
) -> tuple[list[ConversationSummary], int]:
    """Construit un resume des conversations recentes et le total des non lus."""
    if not conversations:
        return [], 0

    conversation_ids = [conversation.id for conversation in conversations]

    unread_stmt = (
        select(
            ConversationMember.conversation_id,
            func.count(MessageDelivery.id).label("unread"),
        )
        .join(MessageDelivery, MessageDelivery.member_id == ConversationMember.id)
        .where(ConversationMember.user_id == user_id)
        .where(ConversationMember.conversation_id.in_(conversation_ids))
        .where(MessageDelivery.state != MessageDeliveryState.READ)
        .where(MessageDelivery.read_at.is_(None))
        .group_by(ConversationMember.conversation_id)
    )
    unread_result = await db.execute(unread_stmt)
    unread_map = {row.conversation_id: int(row.unread) for row in unread_result}

    last_messages = await _last_message_map(db, conversation_ids)

    summaries: list[ConversationSummary] = []
    for conversation in conversations:
        last_entry = last_messages.get(conversation.id)
        last_activity = last_entry.created_at if last_entry else conversation.created_at
        preview = _safe_decode(last_entry.ciphertext) if last_entry else None
        title = conversation.title or _fallback_conversation_title(conversation, user_id)
        participants = _conversation_participants(conversation, user_id)
        summaries.append(
            ConversationSummary(
                id=conversation.id,
                title=title,
                type=conversation.type,
                last_activity_at=last_activity,
                last_message_preview=preview,
                unread_count=unread_map.get(conversation.id, 0),
                participants=participants,
            )
        )

    epoch = datetime(1970, 1, 1, tzinfo=timezone.utc)
    summaries.sort(key=lambda item: item.last_activity_at or epoch, reverse=True)
    total_unread = sum(unread_map.values())
    return summaries[:5], int(total_unread)


async def _last_message_map(db: AsyncSession, conversation_ids: list[uuid.UUID]) -> dict[uuid.UUID, object]:
    """Recupere le dernier message (id/created_at/ciphertext) pour chaque conversation."""
    if not conversation_ids:
        return {}

    ranking = func.row_number().over(
        partition_by=Message.conversation_id,
        order_by=Message.created_at.desc(),
    )
    subquery = (
        select(
            Message.conversation_id.label("conversation_id"),
            Message.created_at.label("created_at"),
            Message.ciphertext.label("ciphertext"),
            ranking.label("row_rank"),
        )
        .where(Message.conversation_id.in_(conversation_ids))
        .subquery()
    )
    stmt = select(subquery.c.conversation_id, subquery.c.created_at, subquery.c.ciphertext).where(subquery.c.row_rank == 1)
    result = await db.execute(stmt)
    return {row.conversation_id: row for row in result}


def _safe_decode(payload: bytes | memoryview | None) -> str | None:
    if not payload:
        return None
    data = bytes(payload)
    text = data.decode("utf-8", errors="ignore").strip()
    return text or None


def _fallback_conversation_title(conversation: Conversation, current_user_id: uuid.UUID) -> str:
    participants = _conversation_participants(conversation, current_user_id)
    if participants:
        return ", ".join(participants)
    return "Conversation"


def _conversation_participants(conversation: Conversation, current_user_id: uuid.UUID) -> list[str]:
    names: list[str] = []
    for member in conversation.members:
        if member.user_id == current_user_id:
            continue
        display_name = None
        if member.user and member.user.profile and member.user.profile.display_name:
            display_name = member.user.profile.display_name
        elif member.user:
            display_name = member.user.email
        if display_name:
            names.append(display_name)
    return names[:4]


def _build_security_recommendations(stats: OverviewStats, snapshot: dict) -> list[str]:
    """Genere des recommandations de securite basees sur l'etat utilisateur."""
    recommendations: list[str] = []
    if not snapshot.get("totp_enabled"):
        recommendations.append("Activez la double authentification pour protéger vos sessions.")
    if not snapshot.get("notification_login"):
        recommendations.append("Activez les alertes de connexion pour détecter les accès suspects.")
    if not snapshot.get("has_recovery_codes"):
        recommendations.append("Générez des codes de récupération pour récupérer votre compte.")
    if stats.devices_at_risk > 0:
        recommendations.append("Contrôlez les appareils marqués à risque dans la section Appareils.")
    if stats.contacts_pending > 0:
        recommendations.append("Traitez vos invitations en attente pour garder vos contacts sous contrôle.")
    if stats.unread_messages > 50:
        recommendations.append("Archivez ou lisez vos conversations en attente pour rester à jour.")
    return recommendations[:4]


@router.get("/", response_model=MeSummaryOut, include_in_schema=False)
@router.get("", response_model=MeSummaryOut)
async def get_me_summary(current_user: UserAccount = Depends(get_current_user)) -> MeSummaryOut:
    """Retourne un resume minimal de l'utilisateur courant."""
    profile = current_user.profile
    pseudo = profile.display_name if profile and profile.display_name else current_user.email.split("@")[0]
    avatar_url = profile.avatar_url if profile else None
    return MeSummaryOut(
        id=current_user.id,
        email=current_user.email,
        pseudo=pseudo,
        avatar=_guess_avatar_filename(avatar_url),
        avatar_url=avatar_url,
        date_crea=current_user.created_at,
    )


@router.get("/profile", response_model=MeProfileOut)
async def get_profile(current_user: UserAccount = Depends(get_current_user)) -> MeProfileOut:
    """Retourne le profil detaille de l'utilisateur."""
    return _build_profile_response(current_user)


@router.put("/profile", response_model=MeProfileOut)
async def update_profile(
    payload: MeProfileUpdate,
    current_user: UserAccount = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    audit: AuditService = Depends(get_audit_service),
) -> MeProfileOut:
    """Met a jour les champs du profil et trace l'audit."""
    profile = _ensure_profile(current_user, db)

    fields_set = payload.model_fields_set

    updated_fields: list[str] = []
    if "display_name" in fields_set:
        profile.display_name = _clean(payload.display_name)
        updated_fields.append("display_name")
    if "locale" in fields_set:
        profile.locale = _clean(payload.locale)
        updated_fields.append("locale")
    if "timezone" in fields_set:
        profile.timezone = _clean(payload.timezone)
        updated_fields.append("timezone")

    profile_data = dict(profile.profile_data or {})
    updates = {}
    if "job_title" in fields_set:
        updates["job_title"] = _clean(payload.job_title)
    if "department" in fields_set:
        updates["department"] = _clean(payload.department)
    if "phone_number" in fields_set:
        updates["phone_number"] = _clean(payload.phone_number)
    if "pgp_public_key" in fields_set:
        updates["pgp_public_key"] = _clean(payload.pgp_public_key)
    if "status_message" in fields_set:
        updates["status_message"] = _clean(payload.status_message)
    for key, value in updates.items():
        if value is None:
            if key in profile_data:
                profile_data.pop(key, None)
                updated_fields.append(key)
        else:
            profile_data[key] = value
            updated_fields.append(key)
    profile.profile_data = profile_data or None

    await db.flush()
    await audit.record(
        "user.profile.update",
        user_id=str(current_user.id),
        metadata={"updated": updated_fields},
    )
    await db.commit()
    await db.refresh(profile)
    current_user.profile = profile
    return _build_profile_response(current_user)


@router.post("/avatar", response_model=AvatarResponse, status_code=status.HTTP_201_CREATED)
async def upload_avatar(
    file: UploadFile = File(..., alias="avatar"),
    current_user: UserAccount = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    audit: AuditService = Depends(get_audit_service),
) -> AvatarResponse:
    """Charge un avatar, le redimensionne et met a jour le profil."""
    data = await file.read()
    if not data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Avatar file is empty.")
    if len(data) > MAX_AVATAR_BYTES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Avatar file is too large.")
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported image format.")

    try:
        image = Image.open(BytesIO(data))
    except UnidentifiedImageError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Corrupted image file.") from exc

    image = image.convert("RGBA")
    image.thumbnail((MAX_AVATAR_SIZE, MAX_AVATAR_SIZE), Image.LANCZOS)

    filename = f"{uuid.uuid4().hex}.png"
    output_path = AVATAR_DIR / filename
    image.save(output_path, format="PNG", optimize=True)

    profile = _ensure_profile(current_user, db)
    previous_url = profile.avatar_url
    profile.avatar_url = _build_avatar_url(filename)

    await db.flush()
    await audit.record("user.avatar.upload", user_id=str(current_user.id), metadata={"filename": filename})
    await db.commit()
    await db.refresh(profile)
    current_user.profile = profile

    _remove_avatar_file(previous_url)

    return AvatarResponse(avatar_url=profile.avatar_url)


@router.delete("/avatar", response_model=AvatarResponse)
async def delete_avatar(
    current_user: UserAccount = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    audit: AuditService = Depends(get_audit_service),
) -> AvatarResponse:
    """Supprime l'avatar de l'utilisateur et le fichier associe."""
    profile = _ensure_profile(current_user, db)
    if not profile.avatar_url:
        return AvatarResponse(avatar_url=None)

    previous_url = profile.avatar_url
    profile.avatar_url = None

    await db.flush()
    await audit.record("user.avatar.delete", user_id=str(current_user.id))
    await db.commit()
    await db.refresh(profile)
    current_user.profile = profile

    _remove_avatar_file(previous_url)

    return AvatarResponse(avatar_url=None)


@router.get("/overview", response_model=OverviewResponse)
async def get_overview(
    current_user: UserAccount = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    conversation_service: ConversationService = Depends(get_conversation_service),
    security: SecurityService = Depends(get_security_service),
    device_service: DeviceService = Depends(get_device_service),
    organization_service: OrganizationService = Depends(get_organization_service),
) -> OverviewResponse:
    """Construit la vue d'ensemble dashboard (profil, stats, securite, org)."""
    profile = _build_profile_response(current_user)
    contacts_total, contacts_pending = await _count_contact_stats(db, current_user.id)

    devices = await device_service.list_devices(current_user)
    device_snapshot = _summarize_devices(devices)

    security_snapshot = await security.get_security_snapshot(current_user)
    conversations = await conversation_service.list_conversations(current_user)
    conversation_summaries, unread_total = await _summarize_conversations(db, conversations, current_user.id)

    stats = OverviewStats(
        unread_messages=unread_total,
        conversations=len(conversations),
        contacts_total=contacts_total,
        contacts_pending=contacts_pending,
        devices_total=device_snapshot["total"],
        devices_at_risk=device_snapshot["at_risk"],
        last_device_seen_at=device_snapshot["last_seen_at"],
    )

    security_recommendations = _build_security_recommendations(stats, security_snapshot)

    security_out = OverviewSecurity(
        totp_enabled=bool(security_snapshot.get("totp_enabled")),
        notification_login=bool(security_snapshot.get("notification_login")),
        has_recovery_codes=bool(security_snapshot.get("has_recovery_codes")),
        last_totp_failure_at=security_snapshot.get("last_totp_failure_at"),
        recommendations=security_recommendations,
    )

    profile_out = OverviewProfile(
        email=profile.email,
        display_name=profile.display_name,
        avatar_url=profile.avatar_url,
        job_title=profile.job_title,
        department=profile.department,
        status_message=profile.status_message,
    )

    organization_out = None
    try:
        membership = await organization_service.get_membership_for_user(current_user.id)
        member_count, admin_count = await organization_service.get_member_counts(membership.organization_id)
        org = membership.organization
        organization_out = OrganizationSummary(
            id=org.id,
            name=org.name,
            slug=org.slug,
            created_at=org.created_at,
            member_count=member_count,
            admin_count=admin_count,
            membership=OrganizationMembershipInfo(
                id=membership.id,
                role=membership.role,
                joined_at=membership.joined_at,
                is_admin=organization_service.is_admin_role(membership.role),
                can_manage_admins=organization_service.can_manage_admins(membership),
            ),
        )
    except HTTPException as exc:
        if exc.status_code not in (status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND):
            raise
        organization_out = None

    return OverviewResponse(
        profile=profile_out,
        stats=stats,
        security=security_out,
        recent_conversations=conversation_summaries,
        generated_at=datetime.now(timezone.utc),
        organization=organization_out,
    )


@router.get("/devices", response_model=DeviceListResponse)
async def list_devices(
    current_user: UserAccount = Depends(get_current_user),
    service: DeviceService = Depends(get_device_service),
) -> DeviceListResponse:
    """Liste les appareils enregistrés de l'utilisateur."""
    devices = await service.list_devices(current_user)
    return DeviceListResponse(devices=[_build_device_response(device) for device in devices])


@router.post("/devices", response_model=DeviceOut, status_code=status.HTTP_201_CREATED)
async def register_device(
    payload: DeviceRegisterRequest,
    request: Request,
    current_user: UserAccount = Depends(get_current_user),
    service: DeviceService = Depends(get_device_service),
) -> DeviceOut:
    """Enregistre ou synchronise un appareil et retourne ses metadonnees."""
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    device = await service.register_device(
        current_user,
        device_id=payload.device_id,
        push_token=payload.push_token,
        platform=payload.platform,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    await service.session.commit()
    await service.session.refresh(device)
    return _build_device_response(device)


@router.delete("/devices/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_device(
    device_id: str,
    current_user: UserAccount = Depends(get_current_user),
    service: DeviceService = Depends(get_device_service),
) -> Response:
    """Revoque un appareil et les sessions associees."""
    await service.revoke_device(current_user, device_id)
    await service.session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(
    payload: AccountDeleteRequest = Body(...),
    current_user: UserAccount = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    audit: AuditService = Depends(get_audit_service),
) -> Response:
    """Supprime le compte utilisateur apres verification du mot de passe."""
    if not verify_password(payload.password, current_user.hashed_password):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Mot de passe incorrect.")

    avatar_url = current_user.profile.avatar_url if current_user.profile else None

    await _reassign_conversations_before_delete(db, current_user.id)
    await db.execute(delete(OrganizationMembership).where(OrganizationMembership.user_id == current_user.id))
    await db.execute(delete(ConversationMember).where(ConversationMember.user_id == current_user.id))

    await audit.record("user.account.delete", user_id=str(current_user.id))
    await db.delete(current_user)
    await db.commit()

    _remove_avatar_file(avatar_url)

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.put("/password", status_code=status.HTTP_204_NO_CONTENT)
async def update_password(
    payload: PasswordUpdateRequest,
    current_user: UserAccount = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    audit: AuditService = Depends(get_audit_service),
) -> Response:
    """Change le mot de passe apres validation de l'ancien."""
    if not payload.old_password or not payload.new_password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Les mots de passe sont requis.")
    if not verify_password(payload.old_password, current_user.hashed_password):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Mot de passe actuel incorrect.")
    if payload.old_password == payload.new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Le nouveau mot de passe doit être différent de l'actuel.",
        )
    current_user.hashed_password = get_password_hash(payload.new_password)
    await audit.record("user.password.update", user_id=str(current_user.id))
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/security", response_model=SecuritySettingsOut)
async def get_security_settings(
    current_user: UserAccount = Depends(get_current_user),
    security: SecurityService = Depends(get_security_service),
) -> SecuritySettingsOut:
    """Retourne les reglages de securite (MFA, alertes)."""
    snapshot = await security.get_security_snapshot(current_user)
    return SecuritySettingsOut(**snapshot)


@router.put("/security", response_model=SecuritySettingsOut)
async def update_security_settings(
    payload: SecuritySettingsUpdate,
    current_user: UserAccount = Depends(get_current_user),
    security: SecurityService = Depends(get_security_service),
) -> SecuritySettingsOut:
    """Met a jour les preferences de securite (alertes de connexion)."""
    updated = await security.update_security_preferences(
        current_user,
        notification_login=payload.notification_login,
    )
    await security.session.commit()
    return SecuritySettingsOut(**updated)


@router.get("/audit", response_model=list[AuditLogEntry])
async def list_audit_logs(
    limit: int = 5,
    current_user: UserAccount = Depends(get_current_user),
    audit: AuditService = Depends(get_audit_service),
) -> list[AuditLogEntry]:
    """Retourne les derniers evenements d'audit pour l'utilisateur."""
    size = max(1, min(limit, 50))
    entries = await audit.recent_for_user(current_user.id, size)
    return [
        AuditLogEntry(
            id=entry.id,
            action=entry.action,
            timestamp=entry.created_at,
            ip=entry.ip_address,
            user_agent=entry.user_agent,
            details=entry.details,
        )
        for entry in entries
    ]
