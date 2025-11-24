"""
############################################################
# Entrypoint FastAPI v2
# Auteur : Valentin Masurelle
# Date   : 2025-05-04
#
# Description:
# - Initialise l'application FastAPI (routes API + WS, middleware CORS).
# - Monte les fichiers statiques (avatars, etc.) depuis MEDIA_ROOT.
# - Expose une route /healthz minimale pour la supervision.
############################################################
"""

from __future__ import annotations

import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .config import settings
from .api.routes import api_router
from .api.ws import ws_api_router

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    app = FastAPI(title=settings.PROJECT_NAME, openapi_url=f"{settings.API_V1_PREFIX}/openapi.json")

    # CORS
    if settings.BACKEND_CORS_ORIGINS:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.BACKEND_CORS_ORIGINS,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    # Routes HTTP et WS
    app.include_router(api_router, prefix=settings.API_V1_PREFIX)
    app.include_router(ws_api_router, prefix=f"{settings.API_V1_PREFIX}/ws")

    # Fichiers statiques (avatars, media)
    media_root = Path(settings.MEDIA_ROOT)
    media_root.mkdir(parents=True, exist_ok=True)
    app.mount("/static", StaticFiles(directory=str(media_root)), name="static")

    # Healthcheck minimal
    @app.get("/healthz", tags=["health"])
    async def healthz() -> dict:
        return {"status": "ok"}

    return app


app = create_app()
