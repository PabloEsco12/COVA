"""API route registration."""

from fastapi import APIRouter, FastAPI

from . import auth, contacts, conversations, devices, health


def register_routes(app: FastAPI) -> None:
    api_router = APIRouter(prefix="/api")
    api_router.include_router(health.router, tags=["health"])
    api_router.include_router(auth.router)
    api_router.include_router(contacts.router)
    api_router.include_router(devices.router)
    api_router.include_router(conversations.router)

    app.include_router(api_router)
