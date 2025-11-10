"""FastAPI application entrypoint for the v2 backend."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .config import settings
from .api.routes import api_router
from .api.ws import ws_api_router


def create_app() -> FastAPI:
    app = FastAPI(title=settings.PROJECT_NAME)

    media_dir = Path(settings.MEDIA_ROOT).resolve()
    media_dir.mkdir(parents=True, exist_ok=True)
    app.mount("/static", StaticFiles(directory=str(media_dir)), name="static")

    if settings.BACKEND_CORS_ORIGINS:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=[origin.rstrip("/") for origin in settings.BACKEND_CORS_ORIGINS],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    app.include_router(api_router, prefix=settings.API_V1_PREFIX)
    app.include_router(ws_api_router, prefix=settings.API_V1_PREFIX)

    @app.get("/healthz", tags=["health"])
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()

