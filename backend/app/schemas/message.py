"""
Schemas Pydantic pour les statistiques/messages non lus.

Infos utiles:
- Utilises pour exposer le nombre de messages non lus par conversation et le total.
"""

from __future__ import annotations

import uuid
from typing import List

from pydantic import BaseModel


class ConversationUnread(BaseModel):
    """Compteur de non lus pour une conversation."""
    conversation_id: uuid.UUID
    unread: int


class UnreadSummaryResponse(BaseModel):
    """Synthese globale des non lus."""
    total: int
    conversations: List[ConversationUnread]

