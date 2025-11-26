"""
############################################################
# Service utilitaire : administration des comptes utilisateurs
# Auteur  : Valentin Masurelle
# Date    : 2025-11-25
#
# Description:
# - Fonctions de support pour les operations d'administration (suppression).
# - Reassigne les conversations avant suppression pour eviter les orphelins.
# - Nettoie les avatars lies aux comptes supprimes.
############################################################
"""

from __future__ import annotations

import uuid
from pathlib import Path
from urllib.parse import urlparse

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from app.models import Conversation, ConversationMember, OrganizationMembership

MEDIA_ROOT = Path(settings.MEDIA_ROOT).resolve()


def avatar_path_from_url(url: str | None) -> Path | None:
    """Retourne le chemin disque correspondant a une URL d'avatar sous /static."""
    if not url:
        return None
    parsed = urlparse(url)
    path = parsed.path.lstrip("/")
    if not path:
        return None
    if path.startswith("static/"):
        path = path[len("static/") :]
    return MEDIA_ROOT / path


def remove_avatar_file(url: str | None) -> None:
    """Supprime le fichier d'avatar si present sur le disque."""
    path = avatar_path_from_url(url)
    if path and path.is_file():
        try:
            path.unlink()
        except OSError:
            pass


async def reassign_conversations_before_delete(db: AsyncSession, user_id: uuid.UUID) -> None:
    """Reattribue ou supprime les conversations creees par l'utilisateur avant suppression."""
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


async def cleanup_memberships(db: AsyncSession, user_id: uuid.UUID) -> None:
    """Supprime les memberships organisation et conversation d'un utilisateur."""
    await db.execute(delete(OrganizationMembership).where(OrganizationMembership.user_id == user_id))
    await db.execute(delete(ConversationMember).where(ConversationMember.user_id == user_id))
