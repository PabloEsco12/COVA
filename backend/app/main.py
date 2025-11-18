"""FastAPI application entrypoint for the v2 backend."""

from __future__ import annotations

import asyncio
import os
from pathlib import Path
from typing import Any, Dict

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .api.routes import api_router
from .api.ws import ws_api_router
from .config import settings

HEALTH_DEBUG = os.getenv("HEALTH_DEBUG", "false").lower() == "true"


async def _check_tcp(host: str, port: int, timeout: float = 2.0) -> tuple[bool, str | None]:
    """Attempt to connect to host:port via TCP; return (ok, error)."""
    try:
        reader, writer = await asyncio.wait_for(asyncio.open_connection(host, port), timeout=timeout)
        writer.close()
        await writer.wait_closed()
        return True, None
    except Exception as exc:  # pragma: no cover - network checks
        return False, str(exc)


def create_app() -> FastAPI:
    app = FastAPI(title=settings.PROJECT_NAME)

    media_dir = Path(settings.MEDIA_ROOT).resolve()
    media_dir.mkdir(parents=True, exist_ok=True)
    app.mount("/static", StaticFiles(directory=str(media_dir)), name="static")

    cors_origins = [origin.rstrip("/") for origin in settings.BACKEND_CORS_ORIGINS or [settings.FRONTEND_ORIGIN]]
    server_logger = logging.getLogger("uvicorn.error")
    server_logger.info("CORS origins: %s", cors_origins)
    server_logger.info(
        "Storage config -> endpoint=%s bucket=%s access_key=%s",
        settings.STORAGE_ENDPOINT,
        settings.STORAGE_BUCKET,
        settings.STORAGE_ACCESS_KEY,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_origin_regex=r"https?://localhost(:\d+)?$",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router, prefix=settings.API_V1_PREFIX)
    app.include_router(ws_api_router, prefix=settings.API_V1_PREFIX)

    @app.get("/healthz", tags=["health"])
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/health/live", tags=["health"])
    async def health_live() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/health/ready", tags=["health"])
    async def health_ready() -> Dict[str, Any]:
        db_host = getattr(settings, "DB_HOST", None) or os.getenv("DB_HOST", "db")
        redis_host = getattr(settings, "REDIS_HOST", None) or os.getenv("REDIS_HOST", "redis")
        minio_host = (
            getattr(settings, "MINIO_HOST", None) or os.getenv("MINIO_HOST") or os.getenv("STORAGE_ENDPOINT", "minio")
        )
        clamav_host = getattr(settings, "CLAMAV_HOST", None) or os.getenv("CLAMAV_HOST", "clamav")

        def parse_port(value: Any, default: int) -> int:
            try:
                return int(value)
            except (TypeError, ValueError):
                return default

        checks: dict[str, tuple[str, int]] = {
            "db": (db_host, parse_port(getattr(settings, "DB_PORT", os.getenv("DB_PORT")), 5432)),
            "redis": (redis_host, parse_port(getattr(settings, "REDIS_PORT", os.getenv("REDIS_PORT")), 6379)),
            "minio": (minio_host, parse_port(getattr(settings, "MINIO_PORT", os.getenv("MINIO_PORT")), 9000)),
            "clamav": (clamav_host, parse_port(getattr(settings, "CLAMAV_PORT", os.getenv("CLAMAV_PORT")), 3310)),
        }

        results: Dict[str, str] = {}
        details: Dict[str, str] = {}

        async def run_check(name: str, host: str, port: int) -> None:
            ok, error = await _check_tcp(host, port)
            results[name] = "ok" if ok else "down"
            if error and HEALTH_DEBUG:
                details[name] = error

        await asyncio.gather(*(run_check(name, host, port) for name, (host, port) in checks.items()))

        if all(status == "ok" for status in results.values()):
            global_status = "ok"
        elif any(status == "ok" for status in results.values()):
            global_status = "degraded"
        else:
            global_status = "down"

        payload: Dict[str, Any] = {"status": global_status, "services": results}
        if HEALTH_DEBUG:
            payload["details"] = details
        return payload

    return app


app = create_app()
