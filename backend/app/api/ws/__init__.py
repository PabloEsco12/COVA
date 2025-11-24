"""
Regroupe les routeurs WebSocket.
"""

from fastapi import APIRouter

from .conversations import ws_router as conversation_ws_router
from .notifications import notifications_ws_router

ws_api_router = APIRouter()
ws_api_router.include_router(conversation_ws_router)
ws_api_router.include_router(notifications_ws_router)

__all__ = ['ws_api_router']

