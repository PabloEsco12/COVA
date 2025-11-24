"""
Regroupe les routeurs HTTP publics de l'API.
"""

from fastapi import APIRouter

from .auth import router as auth_router
from .contacts import router as contacts_router
from .conversations import router as conversations_router
from .notifications import router as notifications_router
from .organizations import router as organizations_router
from .me import router as me_router
from .messages import router as messages_router
from .totp import router as totp_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(contacts_router)
api_router.include_router(conversations_router)
api_router.include_router(notifications_router)
api_router.include_router(me_router)
api_router.include_router(messages_router)
api_router.include_router(totp_router)
api_router.include_router(organizations_router)

__all__ = ["api_router"]
