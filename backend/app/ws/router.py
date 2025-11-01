"""WebSocket route registration."""

from fastapi import APIRouter, FastAPI

from . import routes as ws_routes


def register_websocket_routes(app: FastAPI) -> None:
    router = APIRouter()
    router.include_router(ws_routes.router, prefix="/ws", tags=["websocket"])
    app.include_router(router)

