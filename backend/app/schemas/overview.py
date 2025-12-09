"""
############################################################
# Schemas : Overview (dashboard)
# Auteur : Valentin Masurelle
# Date   : 2025-05-04
#
# Description:
# - Profil, stats, securite et conversations recentes pour le dashboard.
# - Champs préparés pour affichage direct dans l'UI.
############################################################
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import List

from pydantic import BaseModel

from app.models import ConversationType
from .organization import OrganizationSummary


class OverviewProfile(BaseModel):
    """Infos de profil affichées dans l'overview."""
    email: str
    display_name: str | None = None
    avatar_url: str | None = None
    job_title: str | None = None
    department: str | None = None
    status_message: str | None = None


class OverviewStats(BaseModel):
    """Statistiques générales du compte."""
    unread_messages: int = 0
    conversations: int = 0
    contacts_total: int = 0
    contacts_pending: int = 0
    devices_total: int = 0
    devices_at_risk: int = 0
    last_device_seen_at: datetime | None = None


class OverviewSecurity(BaseModel):
    """État synthétique des protections de compte."""
    totp_enabled: bool = False
    notification_login: bool = False
    has_recovery_codes: bool = False
    last_totp_failure_at: datetime | None = None
    recommendations: List[str] = []


class ConversationSummary(BaseModel):
    """Résumé d'une conversation pour l'aperçu rapide."""
    id: uuid.UUID
    title: str | None = None
    type: ConversationType
    last_activity_at: datetime | None = None
    last_message_preview: str | None = None
    unread_count: int = 0
    participants: List[str] = []


class OverviewResponse(BaseModel):
    """Payload complet de l'overview dashboard."""
    profile: OverviewProfile
    stats: OverviewStats
    security: OverviewSecurity
    recent_conversations: List[ConversationSummary]
    generated_at: datetime
    organization: OrganizationSummary | None = None

