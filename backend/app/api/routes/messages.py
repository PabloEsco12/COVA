"""
Endpoints analytics des messages (compteurs de non lus).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from ...dependencies import get_conversation_service, get_current_user
from ...schemas.message import UnreadSummaryResponse
from ...services.conversation_service import ConversationService
from app.models import UserAccount

router = APIRouter(prefix="/messages", tags=["messages"])


@router.get("/unread_summary", response_model=UnreadSummaryResponse)
async def unread_summary(
    current_user: UserAccount = Depends(get_current_user),
    service: ConversationService = Depends(get_conversation_service),
) -> UnreadSummaryResponse:
    """Retourne le total de messages non lus par conversation pour l'utilisateur."""
    summary = await service.get_unread_summary(current_user)
    return UnreadSummaryResponse(**summary)


__all__ = ["router"]
